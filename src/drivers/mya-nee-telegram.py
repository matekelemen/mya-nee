# --- STL Imports ---
import importlib.util
import pathlib
import sys
import re
import tempfile

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


class TikTokFilter(MessageFilter):
    def filter(self, message):
        return message.text and "tiktok" in message.text


def onTikTokMessage(update: Update, context: CallbackContext):
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


if __name__ == "__main__":
    # Get the telegram bot token
    import json
    with open(rootPath / "config.json", 'r') as configFile:
        token = json.load(configFile)["telegramToken"]

    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(
        MessageHandler(TikTokFilter(), onTikTokMessage)
    )

    updater.start_polling()
    #https://vm.tiktok.com/ZMLJPCvmE/