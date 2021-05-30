# --- External Imports ---
import discord

# --- Internal Imports ---
from .Logger import Logger
from .ChannelStatus import TextChannelStatus, VoiceChannelStatus
from .DownloadQueue import DownloadQueue
from .messages import *
from .essentials import SOURCE_DIR, DATA_DIR, IMAGE_DIR, chunks
from .Status import Status

# --- STL Imports ---
import json
import random
import sys
import pathlib


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
                  logger: Logger,
                  globalStatus: Status ):
        self._discordClient = discordClient
        self._guild         = guild
        self._log           = logger
        self._globalStatus  = globalStatus

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
        self._downloadQueue      = DownloadQueue( self._log )

        # Parse config file
        self._prefix = ""
        self.loadConfig()

        # Register commands
        self._commands = {
            "echo"          : (self.echoCommand, "string", "message the active text channel"),
            "show"          : (self.showCommand, "regex-in-images-dir", "post an image/gif from the images directory"),
            "connect"       : (self.connectCommand, "", "connect to the user's voice channel"),
            "disconnect"    : (self.disconnectCommand, "", "disconnect from the active voice channel"),
            "play"          : (self.playCommand, "youtube-link / regex-in-downloads-dir", "play an audio file from youtube or the downloads directory"),
            "skip"          : (self.skipCommand, "", "stop playing the current audio file"),
            "stop"          : (self.stopCommand, "", "stop playing audio"),
            "radio"         : (self.radioCommand, "", "play random audio files from the downloads directory until stopped"),
            "list"          : (self.listCommand, "commands / queue / regex-in-data-dir", "list commands / audio playlist / contents of a data directory"),
            "reboot"        : (self.rebootCommand, "", "reset state and reconnect to discord")
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
        if channel == None and self._activeVoiceChannel != None and self._activeVoiceChannel:
            await self._activeVoiceChannel.disconnect()

        else:
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
                self._log( "Could not find voice channel: ", channel )


    def loadConfig( self ):
        configPath = SOURCE_DIR / "config.json"
        with open( configPath, "r" ) as file:
            contents = json.load( file )
            self._prefix = contents["prefix"]


    @requireTextChannel
    async def messageActiveTextChannel( self, message: str ):
        return await self._activeTextChannel.channel.send( message )


    async def onMessage( self, message: discord.Message ):
        # Do nothing if the message was sen by mya-nee
        if message.author == self._discordClient.user:
            return

        self._log( "Register message: \"{}\" (from: {})".format(message.content, message.author) )

        string = message.content

        # Do nothing if the message wasn't intended for mya-nee
        if not string.startswith( self._prefix ):
            return

        string  = string[len(self._prefix):].strip().split( " " )
        command = string[0]
        args    = string[1:]

        if not command:
            await self.showCommand( message, "mya-nee" )
        else:
            self._log( "Execute command \"{}\" with arguments: ".format(command), *args )

            await self._commands[command][0]( message, *args )


    @requireTextChannel
    async def echoCommand( self, message: discord.Message, *args ):
        if 0 < len( args ):
            msg  = args[0]
            args = args[1:]
            await self._activeTextChannel.channel.send( msg )
        
            if 0 < len(args):
                await self.echoCommand( args[0], *args[1:] )


    @requireTextChannel
    async def showCommand( self, message: discord.Message, *args ):
        if args:
            fileName = args[0]
            args = args[1:]

            filePaths = [ filePath for filePath in IMAGE_DIR.glob( "**/*{}*".format(fileName) ) if filePath.is_file() ]

            if filePaths:
                filePath = filePaths[random.randint(0, len(filePaths)-1)]

                with open( filePath, "rb" ) as file:
                    await self._activeTextChannel.channel.send( file=discord.File(file) )

            if args:
                await self.showCommand( args[0], *args[1:] )


    async def connectCommand( self, message: discord.Message ):
        self._log( "Connect to ", message.author.voice.channel.name )
        try:
            await self.setActiveVoiceChannel( message.author.voice.channel )
        except Exception as exception:
            self._log( exception )
        self._log( "Connected to ", self._activeVoiceChannel.channel.name )


    async def disconnectCommand( self, message: discord.Message ):
        self._log( "Disconnect from ", message.author.voice.channel.name )
        try:
            await self.setActiveVoiceChannel( None )
        except Exception as exception:
            self._log( exception )


    @requireVoiceChannel
    async def playCommand( self, message: discord.Message, *args ):
        for arg in args:
            filePath = self._downloadQueue.getAudioFile( arg )
            self._activeVoiceChannel.enqueue( filePath )


    @requireVoiceChannel
    async def skipCommand( self, message: discord.Message, *args ):
        self._activeVoiceChannel.skip( *args )


    @requireVoiceChannel
    async def stopCommand( self, message: discord.Message, *args ):
        self._activeVoiceChannel.stop( *args )


    @requireVoiceChannel
    async def radioCommand( self, message: discord.Message, *args ):
        self._activeVoiceChannel.enableRadioMode()


    @requireTextChannel
    async def listCommand( self, message: discord.Message, *args ):
        for arg in args:
            index = 0
            output = ""

            if arg == "commands":
                index = 0
                for keyBatch, valueBatch in zip(chunks(self._commands.keys()), chunks(self._commands.values())):
                    output = ""
                    for key, value in zip(keyBatch, valueBatch):
                        output += "{index}) {command} [{arguments}]: {description}\n".format(
                            index = index,
                            command = key,
                            arguments = value[1],
                            description = value[2]
                        )
                        index += 1
                    await self.messageActiveTextChannel( output )

            elif arg == "queue":
                if not self._activeVoiceChannel._playList:
                    await self.messageActiveTextChannel( "[empty]" )
                else:
                    for batch in chunks(self._activeVoiceChannel._playList):
                        output = ""
                        for item in batch:
                            output += "{}) {}\n".format( index, pathlib.Path(item).stem )
                            index += 1
                        await self.messageActiveTextChannel( output )

            else:
                path = DATA_DIR / arg
                if not (SOURCE_DIR in path.parents):
                    await self.showCommand(None, "hackerman")
                else:
                    if path.is_dir():
                        for batch in chunks(sorted(list(path.glob( "*" )))):
                            output = ""
                            for filePath in batch:
                                output += "{}) {}\n".format( index, filePath.stem )
                                index += 1
                            await self.messageActiveTextChannel( output )


    async def rebootCommand( self, message: discord.Message, *args ):
        self._globalStatus.set( "rebooting" )
        await self._discordClient.close()
