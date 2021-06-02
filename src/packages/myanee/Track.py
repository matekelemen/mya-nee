# --- STL Imports ---
import pathlib
import datetime


class Track:

    def __init__( self,
                  filePath: pathlib.Path,
                  lastPlayed: str,
                  playCount=0,
                  url="",
                  volume=100 ):
        self._filePath   = filePath
        self._lastPlayed = self.parseDateTime( lastPlayed )
        self._url        = url
        self._volume     = volume
        self._playCount  = playCount


    def isDownloaded( self ):
        return self._filePath.is_file()


    def hasURL( self ):
        return bool( self._url )


    def updateLastPlayed( self, date=datetime.datetime.now() ):
        self._lastPlayed = date
        self._playCount += 1


    @staticmethod
    def fromDict( data: dict ):
        return Track(
            pathlib.Path( data["filePath"] ),
            data["lastPlayed"],
            playCount=data["playCount"],
            url=data["url"],
            volume=data["volume"]
        )


    @staticmethod
    def parseDateTime( date: str ):
        return datetime.datetime.strptime( date, Track.dateTimeFormat() )


    @staticmethod
    def formatDateTime( date: datetime.datetime ):
        return date.strftime( Track.dateTimeFormat() )


    @property
    def formattedLastPlayed( self ):
        return self.formatDateTime( self._lastPlayed )


    @property
    def directory( self ):
        return self._filePath.parent


    @property
    def name( self ):
        return self._filePath.stem


    @property
    def extension( self ):
        return self._filePath.suffix


    @staticmethod
    def defaultDateTime():
        return datetime.datetime( 2021, 5, 1, 0, 0 )


    @staticmethod
    def dateTimeFormat():
        """day-month-year_hour:minute"""
        return "%d-%m-%Y_%H:%M"


    @property
    def filePath( self ):
        return self._filePath


    @property
    def lastPlayed( self ):
        return self._lastPlayed


    @property
    def url( self ):
        return self._url


    @property
    def volume( self ):
        return self._volume


    def dict( self ):
        return {
            "filePath"   : str(self._filePath),
            "lastPlayed" : self.formattedLastPlayed,
            "playCount"  : self._playCount,
            "url"        : self._url,
            "volume"     : str( self._volume )
        }


    def __str__( self ):
        return str(self.dict())