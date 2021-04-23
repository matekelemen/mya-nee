# --- STL Imports ---
import pathlib
from urllib.parse import urlparse
import multiprocessing


SOURCE_DIR      = pathlib.Path( __file__ ).absolute().parent.parent.parent.parent
DATA_DIR        = SOURCE_DIR / "data"
IMAGE_DIR       = DATA_DIR / "images"
AUDIO_DIR       = DATA_DIR / "audio"
DOWNLOAD_DIR    = DATA_DIR / "downloads"

YOUTUBE_DL_OPTIONS = {
    "format" : "bestaudio/best",
    "outtmpl" : str(DOWNLOAD_DIR / r"%(id)s.%(ext)s")
}


def isURL( string: str ):
    try:
        parseResult = urlparse( string )
        return all( [parseResult.scheme, parseResult.netloc, parseResult.path] )
    except:
        return False