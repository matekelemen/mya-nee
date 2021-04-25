# --- External Imports ---
import discord

# --- Internal Imports ---
from .ChannelStatus import TextChannelStatus, VoiceChannelStatus
from .GuildStatus import GuildStatus
from .Logger import Logger
from .Status import Status


def requiresInitialized( function ):
    def wrapper( instance, *args, **kwargs ):
        if instance._discordClient == None:
            raise RuntimeError( "GlobalStatus was not initialized!" )
        return function( instance, *args, **kwargs )
    return wrapper


class GlobalStatus:


    def __init__( self ):
        self._discordClient = None
        self._guilds        = {}
        self._log           = None
        self._activeGuild   = None
        self._status        = Status("")


    async def initialize( self, discordClient: discord.Client ):
        self._discordClient = discordClient
        self._guilds        = {}
        self._log           = Logger( discordClient )
        
        self._log( "Initialize GlobalStatus" )

        for guild in self._discordClient.guilds:
            self.registerGuild( guild )

        # Set active text channel on every guild to "general"
        for guildID, guildStatus in self._guilds.items():
            general = discord.utils.find( lambda channel: channel.name == "general", guildStatus._guild.text_channels )
            await guildStatus.setActiveTextChannel( general )

        self._status.set( "running" )


    @property
    def status( self ):
        return self._status()


    @property
    def guilds( self ):
        return self._guilds


    @requiresInitialized
    def registerGuild( self, guild ):
        self._guilds[guild.id] = GuildStatus( self._discordClient, guild, self._log, self._status )


    @requiresInitialized
    def deregisterGuild( self, guild ):
        self._guilds.popitem( guild.id )