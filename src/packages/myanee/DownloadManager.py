# --- External Imports ---
import youtube_dl

# --- STL Imports ---
import pathlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# --- Internal Imports ---
from .utilities import YOUTUBE_DL_OPTIONS, DOWNLOAD_DIR, isURL
from .Loggee import Loggee
from .stream import Stream
from .Track import Track


class DownloadManager(Loggee):

    def __init__( self,
                  logStream: Stream ):
        Loggee.__init__( self, logStream, name="DownloadManager" )
        self._queue = []
        self._current = ""

        DOWNLOAD_DIR.mkdir( parents=True, exist_ok=True )


    async def enqueue( self, url: str ):
        """Queue youtube url to be processed and return the file path it will be downloaded to"""
        if not self.isEnqueued( url ):
            self._queue.append( url )

        if not self._current:
            await self.recurse()

        return self.urlToFilePath( url )


    async def recurse( self ):
        """Process youtube urls in the queue until empty"""
        if self._queue:
            url = self._queue.pop( 0 )
            await self.download( url )
            await self.recurse()


    def isEnqueued( self, url: str ):
        """Checks whether the specified youtube url is to be downloaded"""
        return url in self._queue


    def isDownloaded( self, url: str ):
        """Checks whether the specified youtube url was precessed already"""
        return self.urlToFilePath( url ).is_file()


    async def download( self, url: str ):
        try:
            self._current = url
            filePath = self.urlToFilePath( url )

            settings = YOUTUBE_DL_OPTIONS
            settings["outtmpl"] = str( filePath )

            try:
                with youtube_dl.YoutubeDL( settings ) as youtube:
                    self.log( "Downloading {} to {}".format(url, filePath) )

                    with ThreadPoolExecutor() as pool:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(
                            pool,
                            lambda: youtube.extract_info( url, download=True )
                        )

                    self.log( "Finished downloading {} to {}".format(url, filePath) )

            except Exception as exception:
                self.error( "Error downloading {}\n{}".format(url, exception) )

        finally:
            self._current = ""


    def urlToFilePath( self, url: str ):
        """Converts a youtube video link to a file path in the downloads dir"""
        if self.isYoutubeURL(url):
            settings = YOUTUBE_DL_OPTIONS.copy()
            settings["progress_hooks"] = [self.progressHook]

            try:
                with youtube_dl.YoutubeDL( settings ) as youtube:
                    info = youtube.extract_info( url, download=False )
                    return self.videoTitleToFilePath( info["title"], ".{}".format(info["ext"]) )
            except Exception as exception:
                self.error( "Error while querying youtube url: {}\n{}".format(url, exception) )

        else:
            self.error( "Provided link is not a valid youtube URL: {}".format(url) )


    def progressHook( self, info: dict ):
        """Gets called at events from youtube_dl"""
        if info["status"] == "finished":
            self.log( "Finished downloading to {}".format(info["filename"]) )

        elif info["status"] == "error":
            self.error( "Error downloading to {}".format(info["filename"]) )


    @staticmethod
    def videoTitleToFilePath( title: str, extension: str ):
        """ASCIIfy a video title"""
        fileName = "".join( [char if ord(char) < 128 else "_" for char in title] )
        fileName = fileName.replace( " ", "_" ).replace( "/", "_" ).replace( ".", "_").lower()
        fileName = "".join( currentChar for currentChar, nextChar in zip(fileName, fileName[1:]) if not (currentChar=='_' and nextChar=='_') )
        return DOWNLOAD_DIR / (fileName + extension)


    @staticmethod
    def isYoutubeURL( url: str ):
        return isURL(url) and (("youtube" in url) or ("youtu.be" in url))