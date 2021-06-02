# --- External Imports ---
import discord


class Channel:

    def __init__( self, channel: discord.abc.GuildChannel ):
        self._channel = channel


    async def connect( self ):
        pass


    async def disconnect( self ):
        pass


    @property
    def name( self ):
        return self._channel.name


    @property
    def guild( self ):
        return self._channel.guild