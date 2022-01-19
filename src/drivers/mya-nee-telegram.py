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


class TikTokFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            url = extractURL(message.text)
            return url and "vm.tiktok.com" in url

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


class DigitFilter(MessageFilter):
    _map = {
        '0' : myanee.utilities.IMAGE_DIR / "hachikuji_0.webp",
        '1' : myanee.utilities.IMAGE_DIR / "plastic_neesan.webp",
        '2' : myanee.utilities.IMAGE_DIR / "klee.webp"
    }

    def filter(self, message):
        if message.text:
            text = message.text.strip()
            return len(text)==1 and 47 < ord(text) and ord(text) < 58

    @staticmethod
    @loggedCallback
    def callback(update: Update, context: CallbackContext):
        digit = update.message.text.strip()
        if digit in DigitFilter._map:
            with open(DigitFilter._map[digit], 'rb') as file:
                context.bot.send_sticker(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    sticker=file
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

    for observer in (TikTokFilter, DigitFilter, DirectFilter):
        updater.dispatcher.add_handler(
            MessageHandler(observer(), observer.callback)
        )

    # Begin callback loop
    updater.start_polling()