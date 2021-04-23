# --- External Imports ---
import discord
import youtube_dl

# --- Internal Imports ---
from .Logger import Logger

# --- STL Imports ---
import shutil
import asyncio
import pathlib
import random


class ChannelStatus:


    def __init__( self,
                  discordClient: discord.Client,
                  guild: discord.guild,
                  channel: discord.ChannelType,
                  logger: Logger ):
        self._discordClient = discordClient
        self._guild         = guild
        self._channel       = channel
        self._log           = logger


    async def connect( self ):
        pass


    async def disconnect( self ):
        pass


    @property
    def channel( self ):
        return self._channel




class TextChannelStatus( ChannelStatus ):


    def __init__( self,
                  discordClient: discord.Client,
                  guild: discord.guild,
                  channel: discord.TextChannel,
                  logger: Logger ):
        ChannelStatus.__init__( self, discordClient, guild, channel, logger )

        self._log( "Initialize text channel: \"{}\"".format(channel.name) )
        self._log.increaseIndent()

        self._log( "Members:" )
        self._log.increaseIndent()
        for member in channel.members:
            self._log( member.name )
        self._log.decreaseIndent()

        self._log.decreaseIndent()



def requireVoiceClient( function ):
    def wrapper( instance, *args, **kwargs ):
        if instance._voiceClient == None:
            raise RuntimeError( "Voice client is not set" )
        return function( instance, *args, **kwargs )
    return wrapper


class VoiceChannelStatus( ChannelStatus ):


    def __init__( self,
                  discordClient: discord.Client,
                  guild: discord.guild,
                  channel: discord.VoiceChannel,
                  logger: Logger ):
        ChannelStatus.__init__( self, discordClient, guild, channel, logger )

        self._log( "Initialize voice channel: \"{}\"".format(channel.name) )
        self._log.increaseIndent()
        
        self._log( "Members:" )
        self._log.increaseIndent()
        for member in channel.members:
            self._log( member.name )
        self._log.decreaseIndent()

        self._log.decreaseIndent()

        self._voiceClient = None
        self._playList    = []
        self._isLooping   = False

    
    async def connect( self ):
        if self._voiceClient == None or not self._voiceClient:
            self._voiceClient = await self._channel.connect()


    async def disconnect( self ):
        if self._voiceClient != None and self._voiceClient:
            await self._voiceClient.disconnect()
        self._voiceClient = None


    def isLooping( self ):
        return self._isLooping


    def enableLooping( self ):
        self._isLooping = True


    def disableLooping( self ):
        self._isLooping = False


    @requireVoiceClient
    def recursePlayList( self ):
        if self._playList:
            item = self._playList.pop( 0 )
            
            if self._isLooping:
                self._playList.append( item )

            self.play( item )


    @requireVoiceClient
    def enqueue( self, filePath: pathlib.Path ):
        if not self._playList and not self._voiceClient.is_playing():
            self._playList.append( filePath )
            self.recursePlayList()
        else:
            self._playList.append( filePath )


    @requireVoiceClient
    def skip( self, *args ):
        self._voiceClient.stop()


    @requireVoiceClient
    def stop( self, *args ):
        self._playList = []
        self._voiceClient.stop()


    @requireVoiceClient
    def play( self, filePath: pathlib.Path ):
        if filePath.is_file():
            self._log( "Now playing ", filePath )
            self._voiceClient.play( discord.FFmpegPCMAudio( source=str(filePath) ), after=lambda x: self.recursePlayList() )
        else:
            self._log.error( filePath, " not found" )