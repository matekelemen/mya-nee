# --- External Imports ---
import discord

# --- Internal Imports ---
from pymyaa.messages import *


class Logger:


    def __init__( self,
                  discordClient : discord.Client,
                  dumpToTextChannel = False ):
        self._discordClient = discordClient
        self._dumpToTextChannel = dumpToTextChannel

        self._prefix    = ""
        self._indent    = "    "
        self._separator = "-------------------------------"


    def log( self, *args, formatted=True ):
        message = self.toString( *args )

        if formatted:
            message = self.format( message )

        print( message )
        #if ( self.dumpToTextChannel ):
        #    self.discordClient.


    def __call__( self, *args ):
        return self.log( *args )


    def toString( self, *args ):
        if len(args) == 0:
            return ""
        else:
            return str( args[0] ) + self.toString( *args[1:] )

    
    def format( self, message ):
        return self._prefix + message


    def increaseIndent( self ):
        self._prefix += self._indent

    
    def decreaseIndent( self ):
        self._prefix = self._prefix[:len(self._prefix) - len(self._indent)]

    
    def separate( self ):
        self.log( self._separator, formatted=False )


    def error( self, *args ):
        self.log( *args )
        raise RuntimeError( *args )