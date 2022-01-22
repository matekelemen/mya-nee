# --- STL Imports ---
import importlib.util
import pathlib
import sys
import re
import tempfile
import functools
import json

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

from myanee.utilities import IMAGE_DIR

# --- External Imports ---
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageFilter, MessageHandler


urlExtractor = re.compile(
    r"((?:(https?|s?ftp):\/\/)?(?:www\.)?((?:(?:[A-Z0-9][A-Z0-9-]{0,61}[A-Z0-9]\.)+)([A-Z]{2,6})|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(?::(\d{1,5}))?(?:(\/\S+)*))",
    re.IGNORECASE
)


def extractURL(string: str):
    url = urlExtractor.search(string)
    if url is None or url.group(0) is None:
        return ""
    else:
        return url.group(0)


def download(url: str, directory=myanee.utilities.DOWNLOAD_DIR):
    settings = {
        "outtmpl"                   : str(directory / r"%(id)s.mp4"),
        "external_downloader"       : "ffmpeg",
        "external_downloader_args"  : {"-f" : "mp4"}
    }

    with YoutubeDL(settings) as ytdl:
        output = ytdl.extract_info(url, download=True)

    return directory / f"{output['id']}.mp4"


def loggedCallback(function):
    @functools.wraps(function)
    def wrapped(update: Update, context: CallbackContext):
        print(f"[MessageCallback] {update.message}")
        return function(update, context)
    return wrapped


class URLFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            url = extractURL(message.text)
            return url and "vm.tiktok.com" in url or "reddit.com" in url

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        if update.message.text:
            url = extractURL(update.message.text)
            with tempfile.TemporaryDirectory() as directory:
                filePath = download(url, directory=pathlib.Path(directory))
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

    def filter(self, message):
        if message.text:
            text = message.text.strip()
            return text in self._imageMap or text in self._stringMap

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


class DirectFilter(MessageFilter):
    _prefix = json.loads((myanee.utilities.SOURCE_DIR / "config.json").read_text())["prefix"]

    def filter(self, message):
        if message.text:
            return message.text.startswith(self._prefix)

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        # TODO
        pass


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