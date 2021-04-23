# --- External Imports ---
import discord
import youtube_dl

# --- Internal Imports ---
from .essentials import DOWNLOAD_DIR, AUDIO_DIR, isURL, YOUTUBE_DL_OPTIONS
from .Logger import Logger

# --- STL Imports ---
import pathlib
import random


class DownloadQueue:


    def __init__( self,
                  logger: Logger ):
        self._queue   = []
        self._current = ""
        self._log     = logger


    def getFilePathFromTitle( self, title: str, extension=".mp3" ):
        # ASCIIfy title
        fileName = "".join( [char if ord(char) < 128 else "_" for char in title] ) + extension
        fileName = fileName.replace( " ", "_" ).replace( "/", "_" )

        return DOWNLOAD_DIR / fileName


    def getFilePathFromURL( self, url: str ):
        with youtube_dl.YoutubeDL( YOUTUBE_DL_OPTIONS ) as ytdl:
            title = ytdl.extract_info( url, download=False )["title"]
            self._log( "Request audio from ", title )
            return self.getFilePathFromTitle( title )


    def getAudioFile( self, item: str ):
        filePath = pathlib.Path( "" )

        if isURL( item ): # request is an URL (assume youtube)
            filePath = pathlib.Path( self.getFilePathFromURL(item) )
            self.enqueue( item )

        else: # check if request is a local file
            globString = "**/*{}*".format(item)
            matches = list(AUDIO_DIR.glob(globString)) + list(DOWNLOAD_DIR.glob(globString))
            
            if matches: # request matches a local file
                filePath = pathlib.Path( matches[random.randint(0,len(matches)-1)] )
            else: # request is not an URL and does not match any local file
                self._log.error( "No local audio files match \"{}\"".format(item) )

        return filePath


    def isInQueue( self, url: str ):
        return url is self._queue


    def enqueue( self, url: str ):
        if not self.isInQueue( url ):
            self._queue.append( url )

        if not (self._current == ""):
            self.recurse()


    def recurse( self ):
        if self._queue:
            url = self._queue.pop(0)
            self.download( url )
            self.recurse()


    def download( self, url: str ):
        self._current = url

        filePath           = self.getFilePathFromURL( url )
        options            = YOUTUBE_DL_OPTIONS
        options["outtmpl"] = str( filePath.with_suffix(r".%(ext)s") )

        self._log( "Downloading from ", url, " to ", filePath )
        with youtube_dl.YoutubeDL( options ) as ytdl:
            ytdl.download( url )
        self._log( "Finished downloading from ", url, " to ", filePath )
        

        self._current = ""