# --- STL Imports ---
import pathlib
from urllib.parse import urlparse


SOURCE_DIR      = pathlib.Path( __file__ ).absolute().parent.parent.parent.parent
DATA_DIR        = SOURCE_DIR / "data"
IMAGE_DIR       = DATA_DIR / "images"
AUDIO_DIR       = DATA_DIR / "audio"
DOWNLOAD_DIR    = DATA_DIR / "downloads"

YOUTUBE_DL_OPTIONS = {
    "format" : "bestaudio/best",
    "postprocessors" : [{
        "key" : "FFmpegExtractAudio",
        "preferredcodec" : "mp3",
        "preferredquality" : "192"
    }],
    "outtmpl" : str(DOWNLOAD_DIR / r"%(id)s.%(ext)s")
}


def getDownloadFilePathFromTitle( title: str,
                                  extension=".mp3" ):
    # ASCIIfy title
    fileName = "".join( [char if ord(char) < 128 else "_" for char in title] ) + extension
    fileName = fileName.replace( " ", "_" )

    return DOWNLOAD_DIR / fileName


def isURL( string: str ):
    try:
        parseResult = urlparse( string )
        return all( [parseResult.scheme, parseResult.netloc, parseResult.path] )
    except:
        return False