# --- External Imports ---
import discord

# --- Internal Imports ---
from .Logger import Logger
from .ChannelStatus import TextChannelStatus, VoiceChannelStatus
from .messages import *

# --- STL Imports ---
import pathlib
import json


SOURCE_DIR  = pathlib.Path( __file__ ).absolute().parent.parent.parent.parent
DATA_DIR    = SOURCE_DIR / "data"
IMAGE_DIR   = DATA_DIR / "images"


def requireTextChannel( function ):
    def wrapper( instance, *args, **kwargs ):
        if instance._activeTextChannel == None:
            instance._log.error( "No active text channel!" )
        return function( instance, *args, **kwargs )
    return wrapper


def requireVoiceChannel( function ):
    def wrapper( instance, *args, **kwargs ):
        if instance._activeVoiceChannel == None:
            instance._log.error( "No active voice channel!" )
        return function( instance, *args, **kwargs )
    return wrapper


class GuildStatus:

    def __init__( self,
                  discordClient: discord.Client,
                  guild: discord.Guild,
                  logger: Logger ):
        self._discordClient = discordClient
        self._guild         = guild
        self._log           = logger

        self._log.separate()
        self._log( "Initialize server: \"{}\" (ID {})".format( guild.name, guild.id ) )
        self._log.increaseIndent()

        self._log( "" )
        self._log( "Members:" )
        self._log.increaseIndent()
        for member in guild.members:
            self._log( member.name, "({})".format(member.status) )
        self._log.decreaseIndent()

        self._textChannels  = {}
        self._log( "" )
        self._log( "Text channels:" )
        self._log.increaseIndent()
        for textChannel in self._guild.text_channels:
            self._textChannels[textChannel.id] = TextChannelStatus(discordClient, guild, textChannel, logger)
        self._log.decreaseIndent()

        self._log( "" )
        self._log( "Voice channels:" )
        self._log.increaseIndent()
        self._voiceChannels  = {}
        for voiceChannel in self._guild.voice_channels:
            self._voiceChannels[voiceChannel.id] = VoiceChannelStatus(discordClient, guild, voiceChannel, logger)
        self._log.decreaseIndent()

        self._log.decreaseIndent()
        self._log.separate()

        # Check channels:
        #   - require at least 1 voice and text channel
        if len( self._textChannels ) == 0:
            self._log.error( "Found no text channels" )

        if len( self._voiceChannels ) == 0:
            self._log.error( "Found no voice channels" )

        self._activeTextChannel  = None
        self._activeVoiceChannel = None

        # Parse config file
        self._prefix = ""
        self.loadConfig()

        # Register commands
        self._commands = {
            "echo"  : self.echoCommand,
            "show"  : self.showCommand
        }


    @property
    def textChannels( self ):
        return self._textChannels


    @property
    def voiceChannels( self ):
        return self._voiceChannels


    async def setActiveTextChannel( self, channel: discord.TextChannel ):
        if channel.id in self.textChannels:
            if self._activeTextChannel != None:
                    await self.messageActiveTextChannel( MESSAGE_LOG_OUT )
                    await self._activeTextChannel.disconnect()

            self._activeTextChannel = self.textChannels[channel.id]
            try:
                await self._activeTextChannel.connect()
                await self.messageActiveTextChannel( MESSAGE_LOG_ON )

            except Exception as exception:
                self._activeTextChannel = None
                self._log.error( exception )

        else:
            self._log.error( "Could not find text channel: ", channel )


    async def setActiveVoiceChannel( self, channel: discord.VoiceChannel ):
        if channel.id in self.voiceChannels:
            self._activeVoiceChannel = self.voiceChannels[channel.id]
            try:
                if self._activeVoiceChannel != None:
                    await self._activeVoiceChannel.disconnect()
                await self._activeVoiceChannel.connect()
            except Exception as exception:
                self._activeVoiceChannel = None
                self._log.error( exception )
        else:
            self._log.error( "Could not find voice channel: ", channel )


    def loadConfig( self ):
        configPath = SOURCE_DIR / "config.json"
        with open( configPath, "r" ) as file:
            contents = json.load( file )
            self._prefix = contents["prefix"]


    @requireTextChannel
    async def messageActiveTextChannel( self, message: str ):
        return await self._activeTextChannel.channel.send( message )


    async def onMessage( self, message: discord.Message ):
        self._log( "Register message: \"{}\"".format(message.content) )

        # Do nothing if the message was sen by mya-nee
        if message.author == self._discordClient.user:
            return

        string = message.content

        # Do nothing if the message wasn't intended for mya-nee
        if not string.startswith( self._prefix ):
            return

        string  = string[len(self._prefix):].strip().split( " " )
        command = string[0]
        args    = string[1:]

        self._log( "Execute command \"{}\" with arguments: ".format(command), *args )

        await self._commands[command]( *args )


    @requireTextChannel
    async def echoCommand( self, message: str, *args ):
        await self._activeTextChannel.channel.send( message )
        
        if 0 < len(args):
            await self.echoCommand( args[0], *args[1:] )


    @requireTextChannel
    async def showCommand( self, fileName: str, *args ):
        filePaths = IMAGE_DIR.glob( "**/{}.*".format(fileName) )
        for filePath in filePaths:
            if filePath.is_file():
                with open( filePath, "rb" ) as file:
                    await self._activeTextChannel.channel.send( file=discord.File(file) )

        if 0 < len(args):
            await self.showCommand( args[0], *args[1:] )