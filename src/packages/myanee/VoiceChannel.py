# --- External Imports ---
import discord
import pathlib

# --- Internal Imports ---
from .Channel import Channel
from .stream import Stream
from .Loggee import Loggee


class VoiceChannel(Channel, Loggee):

    def __init__( self, channel: discord.VoiceChannel, logStream: Stream ):
        Channel.__init__( self, channel )
        Loggee.__init__( self, logStream, name=self.name )

        self._voiceClient   = None


    async def connect( self ):
        if self._voiceClient == None or not self._voiceClient:
            self.log( "connecting" )

            try:
                self._voiceClient = await self._channel.connect()
                self.log( "connected" )
            except Exception as exception:
                self.error( "failed to connect\n{}".format(exception) )


    async def disconnect( self ):
        if self._voiceClient != None and self._voiceClient:
            self.log( "disconnecting" )

            try:
                await self._voiceClient.disconnect()
                self._voiceClient = None
                self.log( "disconnected" )
            except Exception as exception:
                self.error( "failed to disconnect\n{}".format(exception) )


    def play( self, filePath: pathlib.Path, hook: callable ):
        if self._voiceClient != None and self._voiceClient:
            try:
                self._voiceClient.play(
                    discord.FFmpegPCMAudio( source=str(filePath) ),
                    after=hook
                )
            except Exception as exception:
                self.error( "error during playback\n{}".format(exception) )
        else:
            self.error( "voice client is unavailable" )


    def stop( self ):
        self._voiceClient.stop()


    @property
    def id( self ):
        return self._channel.id

    
    @property
    def members( self ):
        return list(self._channel.voice_states.keys())