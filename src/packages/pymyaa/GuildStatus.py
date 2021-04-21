# --- External Imports ---
import discord

# --- Internal Imports ---
from .Logger import Logger
from .ChannelStatus import TextChannelStatus, VoiceChannelStatus
from .messages import *
from .essentials import SOURCE_DIR, DATA_DIR, IMAGE_DIR

# --- STL Imports ---
import json
import random


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
            "echo"          : self.echoCommand,
            "show"          : self.showCommand,
            "connect"       : self.connectCommand,
            "disconnect"    : self.disconnectCommand,
            "play"          : self.playCommand,
            "skip"          : self.skipCommand,
            "stop"          : self.stopCommand,
            "loop"          : self.loopCommand,
            "list"          : self.listCommand
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
        if channel == None and self._activeVoiceChannel != None:
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

            await self._commands[command]( message, *args )


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
            self._activeVoiceChannel.enqueue( arg )


    @requireVoiceChannel
    async def skipCommand( self, message: discord.Message, *args ):
        self._activeVoiceChannel.skip( *args )


    @requireVoiceChannel
    async def stopCommand( self, message: discord.Message, *args ):
        self._activeVoiceChannel.stop( *args )


    @requireVoiceChannel
    async def loopCommand( self, message: discord.Message, *args ):
        if args:
            arg = args[0]
            offSwitches = ["0", "false", "False", "off"]
            if not (arg in offSwitches):
                self._activeVoiceChannel.enableLooping()
            else:
                self._activeVoiceChannel.disableLooping()

        if self._activeVoiceChannel.isLooping():
            await self.messageActiveTextChannel( "Looping enabled" )
        else:
            await self.messageActiveTextChannel( "Looping disabled" )


    @requireTextChannel
    async def listCommand( self, message: discord.Message, *args ):
        for arg in args:
            if arg == "commands":
                output = ""
                for index, command in enumerate(self._commands.keys()):
                    output += command + "\n"
                await self.messageActiveTextChannel( output )

            elif arg == "queue":
                if not self._activeVoiceChannel._playList:
                    await self.messageActiveTextChannel( "[empty]" )
                else:
                    output = ""
                    for index, item in enumerate(self._activeVoiceChannel._playList[::-1]):
                        output += "{}) {}\n".format( index, item )    
                    await self.messageActiveTextChannel( output )

            else:
                path = DATA_DIR / arg
                if path.is_dir():
                    output = ""
                    for index, filePath in enumerate(path.glob( "**/*" )):
                        output += "{}) {}\n".format( index, filePath.stem )
                    await self.messageActiveTextChannel( output )