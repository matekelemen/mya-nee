# --- External Imports ---
import discord
import youtube_dl

# --- Internal Imports ---
from .Logger import Logger

# --- STL Imports ---
import asyncio


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

    
    async def connect( self ):
        if self._voiceClient == None or not self._voiceClient:
            self._voiceClient = await self._channel.connect()


    async def disconnect( self ):
        if self._voiceClient != None and self._voiceClient:
            await self._voiceClient.disconnect()
        self._voiceClient = None


    @requireVoiceClient
    async def play( self, item ):
        ytdl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
        with ytdl:
            player = self._voiceClient.create_ffmpeg_player( ytdl.download([item]) )
            player.start()
            while not player.is_done():
                await asyncio.sleep(1)
            player.stop()