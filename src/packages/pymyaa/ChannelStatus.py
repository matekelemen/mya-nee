# --- External Imports ---
import discord
import youtube_dl

# --- Internal Imports ---
from .Logger import Logger
from .essentials import YOUTUBE_DL_OPTIONS, DOWNLOAD_DIR, AUDIO_DIR, getDownloadFilePathFromTitle, isURL

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

    
    async def connect( self ):
        if self._voiceClient == None or not self._voiceClient:
            self._voiceClient = await self._channel.connect()


    async def disconnect( self ):
        if self._voiceClient != None and self._voiceClient:
            await self._voiceClient.disconnect()
        self._voiceClient = None


    @requireVoiceClient
    def recursePlayList( self ):
        if self._playList:
            item = self._playList.pop(0)
            self.play( item )


    @requireVoiceClient
    def enqueue( self, item: str ):
        if not self._playList and not self._voiceClient.is_playing():
            self._playList.append( item )
            self.recursePlayList()
        else:
            self._playList.append( item )


    @requireVoiceClient
    def skip( self, *args ):
        self._voiceClient.stop()


    @requireVoiceClient
    def stop( self, *args ):
        self._playList = []
        self._voiceClient.stop()


    @requireVoiceClient
    def play( self, item: str ):
        ## Wait until available
        #while self._voiceClient.is_playing():
        #    asyncio.sleep( 0.1 )

        filePath = pathlib.Path("")

        if isURL( item ): # Request is a link (assuming from youtube)
            options  = YOUTUBE_DL_OPTIONS.copy()

            # Get file name
            with youtube_dl.YoutubeDL( options ) as ytdl:
                title = ytdl.extract_info( item, download=False )["title"]
                self._log( "Request video: ", title )
                filePath = getDownloadFilePathFromTitle( title, extension=".mp3" )

            if filePath.is_file(): # file has already been downloaded before
                self._log( str(filePath), " already exists, no need to download" )

            else: # file was not downloaded yet, get it now
                self._log( "Downloading to ", filePath )
                options["outtmpl"] = str( filePath.with_suffix( r".%(ext)s" ) )

                with youtube_dl.YoutubeDL( options ) as ytdl:
                    ytdl.extract_info( item, download=True )
                
                self._log( "Finished downloading to ", filePath )

        else: # Request is not a link
            globString = "**/*{}*".format(item)
            matches = list(AUDIO_DIR.glob(globString)) + list(DOWNLOAD_DIR.glob(globString))
            if 0 < len( matches ):
                filePath = pathlib.Path( matches[random.randint(0,len(matches)-1)] )

        if filePath.is_file():
            self._log( "Now playing ", filePath )
            self._voiceClient.play( discord.FFmpegPCMAudio( source=str(filePath) ), after=lambda x: self.recursePlayList() )