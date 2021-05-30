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
    "outtmpl" : str(DOWNLOAD_DIR / str(r"%(id)s.%(ext)s").lower())
}


def isURL( string: str ):
    try:
        parseResult = urlparse( string )
        return all( [parseResult.scheme, parseResult.netloc, parseResult.path] )
    except:
        return False


def chunks( items: list, chunkSize=10 ):
    local = list(items)
    return [ local[chunkID*chunkSize:(chunkID+1)*chunkSize] for chunkID in range(len(local)//chunkSize + 1) ]
