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


class KeywordFilter(MessageFilter):
    _imageMap = {
        '0' : IMAGE_DIR / "hachikuji_0.webp",
        '1' : IMAGE_DIR / "plastic_neesan.webp",
        '2' : IMAGE_DIR / "klee.webp",
        '3' : IMAGE_DIR / "3.webp",
        '4' : IMAGE_DIR / "4.webp",
        '5' : IMAGE_DIR / "5.webp",
        '6' : IMAGE_DIR / "keqing_6.webp",
        "10" : IMAGE_DIR / "10.webp",
        "C++" : IMAGE_DIR / "cpp.webp"
    }

    _stringMap = {
        "kaka" : "https://www.reddit.com/r/Shinobu/"
    }

    @staticmethod
    def match(string: str) -> bool:
        string = string.strip()
        return string in KeywordFilter._imageMap or string in KeywordFilter._stringMap

    def filter(self, message) -> bool:
        if message.text:
            return self.match(message.text)
        else:
            return False

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        keyword = update.message.text.strip()
        if keyword in KeywordFilter._imageMap:
            with open(KeywordFilter._imageMap[keyword], 'rb') as file:
                context.bot.send_sticker(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    sticker=file
                )
        elif keyword in KeywordFilter._stringMap:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=KeywordFilter._stringMap[keyword]
            )


if __name__ == "__main__":
    # Get the telegram bot token
    with open(rootPath / "config.json", 'r') as configFile:
        token = json.load(configFile)["telegramToken"]

    # Create loop handler and register callbacks
    updater = Updater(token=token, use_context=True)

    for observer in (URLFilter, KeywordFilter, DirectFilter):
        updater.dispatcher.add_handler(
            MessageHandler(observer(), observer.callback)
        )

    # Begin callback loop
    updater.start_polling()
