# --- External Imports ---
import discord

# --- Internal Imports ---
from .Channel import Channel
from .stream import StreamWrapper
from .Loggee import Loggee


class TextChannel(Channel, StreamWrapper, Loggee):

    def __init__( self, channel: discord.TextChannel ):
        Channel.__init__( self, channel )
        StreamWrapper.__init__( self, self.writeFunction )
        Loggee.__init__( self, self, name=self.name )


    async def writeFunction( self, content: str ):
        await self.send( content )


    async def send( self, *args, **kwargs ):
        await self._channel.send( *args, **kwargs )