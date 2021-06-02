# --- STL Imports ---
import pathlib
from urllib.parse import urlparse
import random


# ----------------------------------------------------
# Repo directories
# ----------------------------------------------------

SOURCE_DIR      = pathlib.Path( __file__ ).absolute().parent.parent.parent.parent
DATA_DIR        = SOURCE_DIR / "data"
IMAGE_DIR       = DATA_DIR / "images"
AUDIO_DIR       = DATA_DIR / "audio"
DOWNLOAD_DIR    = DATA_DIR / "downloads"


# ----------------------------------------------------
# Globals
# ----------------------------------------------------

YOUTUBE_DL_OPTIONS = {
    "format" : "bestaudio/best",
    "outtmpl" : str( DOWNLOAD_DIR / r"%(id)s.%(ext)s" ),
    "noplaylist" : True
}


# ----------------------------------------------------
# Utility functions
# ----------------------------------------------------

def isURL( string: str ):
    """Return True if the provided string is a valid URL"""
    try:
        parseResult = urlparse( string )
        return all( [parseResult.scheme, parseResult.netloc, parseResult.path] )
    except:
        return False


def chunks( items: list, chunkSize=10 ):
    """Break up a list into a set of sublists with a maximum size of 'chunkSize'"""
    if not chunkSize:
        raise RuntimeError( "Invalid chunk size ({})".format(chunkSize) )    

    numberOfChunks = len(items) // chunkSize + (0 < (len(items) % chunkSize))

    for chunkID in range(numberOfChunks):
        yield items[chunkID*chunkSize:(chunkID+1)*chunkSize]


def indexGenerator( index: int ):
    return "{}) ".format(index)


def newLineGenerator( index: int ):
    return '\n'


def stringChunks( items, prefixGenerator=indexGenerator, postfixGenerator=newLineGenerator ):
    index = 0
    for chunk in chunks( items ):
        string = ""
        for item in chunk:
            string += str( prefixGenerator(index) ) + str( item ) + str( postfixGenerator(index) )
            index += 1
        yield string


def randomItem( items: list ):
    """Return a random item from a list"""
    if items:
        return items[ random.randint(0, len(items)-1) ]