# --- External Imports ---
import discord

# --- Internal Imports ---
from .Logger import Logger
from .ChannelStatus import TextChannelStatus, VoiceChannelStatus

# --- STL Imports ---
import asyncio


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

        # Find "general" text channel
        #self.setActiveTextChannel( discord.utils.find(lambda item: item.name == "general", self._guild.text_channels) )


    @property
    def textChannels( self ):
        return self._textChannels


    @property
    def voiceChannels( self ):
        return self._voiceChannels


    async def setActiveTextChannel( self, channel: discord.TextChannel ):
        if channel.id in self.textChannels:
            self._activeTextChannel = self.textChannels[channel.id]
            try:
                if self._activeTextChannel != None:
                    await self._activeTextChannel.disconnect()
                await self._activeTextChannel.connect()
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


    @requireTextChannel
    async def messageActiveTextChannel( self, message: str ):
        await self._activeTextChannel.channel.send( message )