# --- STL Imports ---
import importlib.util
import pathlib
import sys
import tempfile
import functools
import json
import argparse
import os
import traceback
import requests
import random
import re
import typing
import abc

# --- Internal Imports ---
driverPath  = pathlib.Path(__file__).absolute() # full path to this file
rootPath    = driverPath.parent.parent.parent   # path to the local mya-nee repo
modulePath  = rootPath / "src/packages"         # path to directory containing the mya-nee python module

# Import modules
MyaNeeModuleSpec   = importlib.util.spec_from_file_location("myanee", str(modulePath / "myanee/__init__.py"))
TelegramModuleSpec = importlib.util.spec_from_file_location("telegram", str(modulePath / "python-telegram-bot/telegram/__init__.py"))

myanee = importlib.util.module_from_spec(MyaNeeModuleSpec)
sys.modules[MyaNeeModuleSpec.name] = myanee
MyaNeeModuleSpec.loader.exec_module(myanee)

from myanee.utilities import IMAGE_DIR, URLUtilities

# --- External Imports ---
import yt_dlp
from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageFilter, MessageHandler


class YTDLContext(object):
    def __init__(self, userAgent: str, settings: dict, defaultUserAgent=yt_dlp.utils.std_headers['User-Agent']):
        self.userAgent = userAgent
        self.defaultUserAgent = defaultUserAgent
        self.ytdl = yt_dlp.YoutubeDL(settings)

    def __enter__(self) -> yt_dlp.YoutubeDL:
        yt_dlp.utils.std_headers['User-Agent'] = self.userAgent
        return self.ytdl

    def __exit__(self, exceptionType, exceptionValue, traceback):
        yt_dlp.utils.std_headers['User-Agent'] = self.defaultUserAgent
        return False


class DownloadManager:
    _defaultUserAgent = yt_dlp.utils.std_headers["User-Agent"]
    _userAgents = (yt_dlp.utils.std_headers["User-Agent"],"facebookexternalhit/1.1")
    _maxFileSize = 1e7

    @staticmethod
    def download(url: str, directory: pathlib.Path=myanee.utilities.DOWNLOAD_DIR, ffmpegArguments: str="") -> pathlib.Path:
        settings = {"outtmpl" : str(directory / r"%(id)s.mp4")}

        # Try downloading with different user agents
        for userAgent in DownloadManager._userAgents:
            try:
                # First, get the available formats and select the best quality that has both audio and video
                with YTDLContext(userAgent, {}) as ytdl:
                    info = ytdl.extract_info(url, download=False)

                formatID = next((f["format_id"] for f in info["formats"][::-1] if all((f["vcodec"] != "none", f["acodec"] != "none", f["ext"]=="mp4"))), "")
                if not formatID:
                    raise RuntimeError(f"[DownloadManager] Cannot find suitable format for '{url}'")

                if ffmpegArguments: # Download externally with ffmpeg
                    # Assemble the ffmpeg command but replace the url with the selected format's url
                    filePath = pathlib.Path(settings["outtmpl"].replace(r"%(id)s", info["id"]))
                    command = 'ffmpeg ' + ffmpegArguments + f' {filePath}'
                    command = command.replace(url, f'"{next(f["url"] for f in info["formats"] if f["format_id"] == formatID)}"')
                    print(f"System call: {command}")
                    os.system(command)

                else: # Download with yt_dlp
                    settings["format"] = formatID
                    with YTDLContext(userAgent, settings) as ytdl:
                        ytdl.download(url)

                # Break on successful download
                break

            except Exception as exception:
                print(f"[DownloadManager] Failed to download '{url}' using '{userAgent}' agent. Traceback:" + "\n" + traceback.format_exc())
                #raise exception

        filePath = pathlib.Path(settings["outtmpl"].replace(r"%(id)s", info["id"]))
        if filePath.is_file():
            return filePath
        else:
            raise RuntimeError(f"Failed to download {url}")


def loggedCallback(function):
    @functools.wraps(function)
    def wrapped(update: Update, context: CallbackContext):
        print(f"[MessageCallback] {update.message}")
        return function(update, context)
    return wrapped


# Argument parser to limit what can be passed on to ffmpeg
ffmpegParser = argparse.ArgumentParser(description="ffmpeg argument interface")
ffmpegParser.add_argument("-ss", type=str, default="00:00:00")
ffmpegParser.add_argument("-t", type=str)
ffmpegParser.add_argument("-to", type=str)
ffmpegParser.add_argument("-c", type=str, default = "copy")
ffmpegParser.add_argument("-i", type=str, default="")

class DirectFilter(MessageFilter):
    _prefix = json.loads((myanee.utilities.SOURCE_DIR / "config.json").read_text())["prefix"]

    @staticmethod
    def match(string: str) -> bool:
        return string.startswith(DirectFilter._prefix)

    def filter(self, message) -> bool:
        if message.text:
            return self.match(message.text)
        else:
            return False

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        arguments = update.message.text.strip().split(' ')[1:]

        # Validate arguments, then forward them in the original order
        # (important for fast seeking)
        parsedArguments = ffmpegParser.parse_args(arguments)
        forwardedArguments = " ".join(arguments)

        with tempfile.TemporaryDirectory() as directory:
            filePath = DownloadManager.download(
                parsedArguments.i,
                directory = pathlib.Path(directory),
                ffmpegArguments = forwardedArguments
            )
            with open(filePath, "rb") as file:
                context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    video=file
                )


class URLFilter(MessageFilter):
    @staticmethod
    def match(string: str) -> bool:
        if not DirectFilter.match(string):
            url = URLUtilities.extract(string)
            return url and any(domain in url for domain in ("tiktok.com", "reddit.com"))
        else:
            return False

    def filter(self, message) -> bool:
        if message.text:
            return URLFilter.match(message.text)
        else:
            return False

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        if update.message.text:
            url = URLUtilities.extract(update.message.text)
            with tempfile.TemporaryDirectory() as directory:
                filePath = DownloadManager.download(url, directory=pathlib.Path(directory))
                with open(filePath, 'rb') as file:
                    context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        reply_to_message_id=update.message.message_id,
                        video=file
                    )


class RegexMap:
    """@brief Container associating values to regexes.

    @details Item access is provided through strings that are checked against the stored regexes.
             Since neither the patterns nor the values need to be unique, an input string key may
             match multiple regexes. All stored patterns are tested in insertion order and each
             hit's regex and value is appended to the output list.
    """

    def __init__(self, initMap: list[tuple[re.Pattern, typing.Any]]):
        """@brief Construct a @ref RegexMap [from a list of pattern-value pairs]."""
        self.__container = initMap

    def emplace(self, pattern: re.Pattern, value: typing.Any) -> None:
        """@brief Insert a pattern-value pair into the map.
        @details May raise a @c KeyError is the pattern is identical to an already stored one."""
        if any(pattern == pair[0] for pair in self.__container):
            raise KeyError(f"'{pattern}' is already part of the map")
        self.__container.append((pattern, value))

    def erase(self, key: str) -> None:
        """"@brief Remove all entries that match the provided key."""
        self.__container = [(pattern, value) for pattern, value in self.__container if not pattern.search(key)]

    def __getitem__(self, key: str) -> list[tuple[re.Pattern,typing.Any]]:
        """@brief Collect all patterns that match the input key, along with their associated values."""
        return [(pattern, value) for pattern, value in self.__container if pattern.search(key)]

    def __contains__(self, key: str) -> bool:
        """@brief True if any of the stored patterns matches the provided key."""
        return any(True for pattern, value in self.__container if pattern.search(key))


class TelegramCallback(abc.ABC):
    """@brief Interface for implementing telegram callbacks."""

    @abc.abstractmethod
    def __call__(self, update: Update, context: CallbackContext) -> None:
        pass


class ConstMessageCallback(TelegramCallback):
    """@brief Always send the same text message in response to the one that triggered this."""

    def __init__(self, message: str):
        self.__message = message

    def __call__(self, update: Update, context: CallbackContext) -> None:
        context.bot.send_message(chat_id = update.effective_chat.id,
                                 reply_to_message_id = update.message.message_id,
                                 text = self.__message)


class ConstStickerCallback(TelegramCallback):
    """@brief Always send the same sticker in response to the one that triggered this."""

    def __init__(self, stickerPath: pathlib.Path):
        if not stickerPath.is_file():
            raise FileNotFoundError(f"'{stickerPath}' not found")
        self.__path = stickerPath

    def __call__(self, update: Update, context: CallbackContext):
        with open(self.__path, 'rb') as file:
            context.bot.send_sticker(chat_id = update.effective_chat.id,
                                     reply_to_message_id = update.message.message_id,
                                     sticker = file)


class ExcuseFetchCallback(TelegramCallback):
    """@brief Fetch a random line from a list aggregated from the specified URLs."""

    _pattern = re.compile(R"#[kK][iI][fF][oO][gG][aá][sS]((?:0$|(?:[1-9]+[0-9]*)))?")

    def __init__(self, urls: list[str]):
        self.__sources = urls.copy()

    def __call__(self, update: Update, context: CallbackContext) -> None:
        # Collect and flatten all non-empty lines from all registered URLs
        lines = sum((sum(([line.strip()] for line in requests.get(url).text.split("\n") if line.strip()), []) for url in self.__sources), [])
        if not lines:
            raise RuntimeError(f"No lines could be fetched from {self.__sources}")

        # Get the requested line or pick a random one
        match = ExcuseFetchCallback._pattern.search(update.message.text).group(1)
        line = lines[int(match) % len(lines)] if match else random.choice(lines)

        # Send message
        context.bot.send_message(chat_id = update.effective_chat.id,
                                 reply_to_message_id = update.message.message_id,
                                 text = line)


class RegexFilter(MessageFilter):
    _callbackMap: "RegexMap[re.Pattern, TelegramCallback]" = RegexMap([
        (re.compile(R"[kK][aA][kK][aA]"), ConstMessageCallback("https://www.reddit.com/r/Shinobu/")), # URL for position-independent case-insensitive "kaka"
        (re.compile(R"^0$"),      ConstStickerCallback(IMAGE_DIR / "hachikuji_0.webp")),              # Sticker for exact "0"
        (re.compile(R"^1$"),      ConstStickerCallback(IMAGE_DIR / "plastic_neesan.webp")),           # Sticker for exact "1"
        (re.compile(R"^2$"),      ConstStickerCallback(IMAGE_DIR / "klee.webp")),                     # Sticker for exact "2"
        (re.compile(R"^3$"),      ConstStickerCallback(IMAGE_DIR / "3.webp")),                        # Sticker for exact "3"
        (re.compile(R"^4$"),      ConstStickerCallback(IMAGE_DIR / "4.webp")),                        # Sticker for exact "4"
        (re.compile(R"^5$"),      ConstStickerCallback(IMAGE_DIR / "5.webp")),                        # Sticker for exact "5"
        (re.compile(R"^6$"),      ConstStickerCallback(IMAGE_DIR / "keqing_6.webp")),                 # Sticker for exact "6"
        (re.compile(R"^10$"),     ConstStickerCallback(IMAGE_DIR / "10.webp")),                       # Sticker for exact "10"
        (re.compile(R"[cC]\+\+"), ConstStickerCallback(IMAGE_DIR / "cpp.webp")),                      # Sticker for location-independent case-insensitive C++
        (ExcuseFetchCallback._pattern, ExcuseFetchCallback(["https://raw.githubusercontent.com/matekelemen/kifogasok/main/kifogasok.txt"]))
    ])

    @staticmethod
    def match(string: str) -> bool:
        """@brief Defer membership test to @ref RegexMap."""
        return string in RegexFilter._callbackMap

    def filter(self, message) -> bool:
        if message.text:
            return self.match(message.text)
        else:
            return False

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext) -> None:
        """@brief Collect all stored callbacks matching the message and invoke each of them."""
        for pattern, callback in RegexFilter._callbackMap[update.message.text]:
            callback(update, context)


if __name__ == "__main__":
    # Get the telegram bot token
    with open(rootPath / "config.json", 'r') as configFile:
        token = json.load(configFile)["telegramToken"]

    # Create loop handler and register callbacks
    updater = Updater(token=token, use_context=True)

    for observer in (URLFilter, DirectFilter, RegexFilter):
        updater.dispatcher.add_handler(MessageHandler(observer(), observer.callback))

    # Begin callback loop
    updater.start_polling()
