# --- External Imports ---
import discord

# --- Internal Imports ---
from .Logger import Logger


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


    @property
    def channel( self ):
        return self._channel




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
            self._voiceClient = self._channel.connect()


    async def disconnect( self ):
        if self._voiceClient != None and self._voiceClient:
            self._voiceClient.disconnect()
        self._voiceClient = None