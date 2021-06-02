# --- External Imports ---
import discord

# --- STL Imports ---
import sys

# --- Internal Imports ---
from .Guild import Guild
from .TrackList import TrackList
from .Loggee import Loggee
from .stream import Stream, StreamMultiplex
from .utilities import SOURCE_DIR, AUDIO_DIR, DOWNLOAD_DIR


class Status:

    def __init__( self, status: str ):
        self.set( status )


    def __call__( self ):
        return self._status


    def set( self, status: str ):
        self._status = status




def requiresInitialized( function: callable ):
    def wrapper( instance, *args, **kwargs ):
        if instance._discordClient == None:
            instance.error( "uninitialized!" )
        return function( instance, *args, **kwargs )
    return wrapper




class MyaNee( StreamMultiplex, Loggee ):

    def __init__( self ):
        StreamMultiplex.__init__( self, sys.stderr )
        Loggee.__init__( self, self, name="MyaNee" )

        self._discordClient = None
        self._prefix        = ""
        self._downloadList  = None
        self._audioList     = None
        self._guilds        = {}
        self._status        = Status( "" )


    @requiresInitialized
    async def onMessage( self, message: discord.Message ):
        if message.author != self._discordClient.user:
            if message.content.startswith( self._prefix ):
                await self._guilds[message.guild.id].onMessage(
                    message,
                    message.content[len(self._prefix):].strip()
                )


    def clear( self ):
        self._discordClient = None
        self._prefix        = ""
        self._downloadList  = None
        self._audioList     = None
        self._guilds        = {}
        self._status        = Status( "" )


    async def initialize( self, discordClient: discord.Client, prefix: str ):
        self.setStatus( "initializing" )

        self.clear()

        self._discordClient = discordClient
        self._prefix        = prefix

        self._downloadList  = TrackList( DOWNLOAD_DIR, self )
        self._audioList     = TrackList( AUDIO_DIR, self )

        for discordGuild in self._discordClient.guilds:
            guild = Guild(
                discordGuild,
                self._downloadList,
                self._audioList,
                {
                    "reboot" : self.reboot,
                    "shutdown" : self.shutdown
                },
                self
            )
            guild.setActiveTextChannel()
            self._guilds[discordGuild.id] = guild

        self.setStatus( "running" )


    @requiresInitialized
    async def reboot( self ):
        self.setStatus( "rebooting" )
        await self._discordClient.close()


    @requiresInitialized
    async def shutdown( self ):
        self.setStatus( "shutting down" )
        await self._discordClient.close()


    def release( self ):
        for id, guild in self._guilds.items():
            guild.release()


    def setStatus( self, status: str ):
        self.log( status )
        self._status.set( status )


    @property
    def status( self ):
        return self._status()