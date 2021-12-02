# --- External Imports ---
import discord

# --- STL Imports ---
import datetime
from functools import wraps

# --- Internal Imports ---
from .TrackList import TrackList
from .Track import Track
from .DownloadManager import DownloadManager
from .TextChannel import TextChannel
from .VoiceChannel import VoiceChannel
from .stream import Stream
from .Loggee import Loggee
from .utilities import isURL, randomItem, stringChunks, AUDIO_DIR, IMAGE_DIR, DOWNLOAD_DIR, DATA_DIR, SOURCE_DIR


def requireActiveTextChannel( function: callable ):
    @wraps(function)
    def wrapper( instance, *args, **kwargs ):
        if instance._activeTextChannel == None:
            instance.error( "No active text channel!" )
        return function( instance, *args, **kwargs )
    return wrapper


def requireActiveVoiceChannel( function: callable ):
    @wraps(function)
    def wrapper( instance, *args, **kwargs ):
        """{}""".format(function.__doc__)
        if instance._activeVoiceChannel == None:
            instance.error( "No active voice channel!" )
        return function( instance, *args, **kwargs )
    return wrapper


class Guild(Loggee):

    def __init__( self,
                  guild: discord.Guild,
                  downloadList: TrackList,
                  audioList: TrackList,
                  eventHooks: dict,
                  logStream: Stream ):
        Loggee.__init__( self, logStream, name=str(guild.name) )
        self._guild             = guild
        self._downloadList      = downloadList
        self._audioList         = audioList
        self._eventHooks        = eventHooks
        self._textChannels      = []
        self._voiceChannels     = []
        self._downloadManager   = DownloadManager( logStream )

        self._currentTrack      = None
        self._audioQueue        = []
        self._audioRule         = datetime.timedelta( days=2 )
        self._inRadioMode       = False

        self._activeTextChannel  = None
        self._activeVoiceChannel = None

        self._commands = {
            "echo"          : self.echoCommand,
            "show"          : self.showCommand,
            "connect"       : self.connectCommand,
            "disconnect"    : self.disconnectCommand,
            "play"          : self.playCommand,
            "skip"          : self.skipCommand,
            "next"          : self.nextCommand,
            "stop"          : self.stopCommand,
            "radio"         : self.radioCommand,
            "list"          : self.listCommand,
            "status"        : self.statusCommand
        }

        self._hiddenCommands = {
            "reboot"        : self.rebootCommand,
            "shutdown"      : self.shutdownCommand
        }

        self.update()


    @requireActiveTextChannel
    async def onMessage( self, message: discord.Message, content: str ):
        arguments = content.split( ' ' )
        command   = ""

        if arguments:
            command   = arguments[0]
            arguments = arguments[1:]

        if command in self._hiddenCommands:
            self.log( "Register hidden command '{}' with arguments '{}'".format(command, arguments) )
            await self._hiddenCommands[command]( message, *arguments )
        elif command in self._commands:
            self.log( "Register command '{}' with arguments '{}'".format(command, arguments) )
            await self._commands[command]( message, *arguments )
            await message.add_reaction( "💖" )
        else:
            await self._activeTextChannel.send( "Wakarimasen! >.<'", reference=message )


    @requireActiveTextChannel
    async def echoCommand( self, message: discord.Message, *args ):
        """Message the active text channel"""
        for arg in args:
            await self._activeTextChannel.send( arg )


    @requireActiveTextChannel
    async def showCommand( self, message: discord.Message, *args ):
        """Post an image/gif matching the argument in the active text channel"""
        for arg in args:
            filePaths = list( IMAGE_DIR.glob("*{}*".format(arg)) )

            if filePaths:
                filePath = randomItem( filePaths )
                with open( filePath, "rb" ) as file:
                    await self._activeTextChannel.send( file=discord.File(file) )
            else:
                self.log( "no hits for image request '{}'".format(arg) )


    async def connectCommand( self, message: discord.Message, *args ):
        """Connect to the sender's voice channel"""
        try:
            targetChannel = message.author.voice.channel
            channel = next((c for c in self._voiceChannels if c.id == targetChannel.id), None)

            if channel != None:
                if self._activeVoiceChannel != None:
                    await self._activeVoiceChannel.disconnect()
                    self._activeVoiceChannel = None

                await channel.connect()
                self._activeVoiceChannel = channel
            else:
                self.error( "could not find voice channel '{}'".format(targetChannel.name) )

        except Exception as exception:
            self.error( "failed to connect to voice channel\n{}".format(exception) )


    @requireActiveVoiceChannel
    async def disconnectCommand( self, message: discord.Message, *args ):
        """Disconnect from the active voice channel"""
        print(self._activeVoiceChannel)
        await self._activeVoiceChannel.disconnect()
        self._activeVoiceChannel = None


    async def playCommand( self, message: discord.Message, *args ):
        """Play audio from a youtube url / the audio or downloads directory"""
        # Connect to voice channel if necessary and possible
        if self._activeVoiceChannel == None:
            if message.author.voice.channel != None:
                await self.connectCommand( message )
            else:
                self.error( "No active voice channel!" )

        # Loop through arguments
        for arg in args:
            track = None

            if arg == '#': # special case: play random audio file subject to the 24h rule
                track = self.getRandomTrack()

                if track == None:
                    await self._activeTextChannel.send( "mya-nee ran out of things to play >.<'" )
                    self.error( "none of the available tracks satisfy the 24h rule" )

            elif isURL( arg ): # url -> assume it's a youtube link
                filePath = await self._downloadManager.enqueue( arg )
                track = self._downloadList.getTrackByFilePath( filePath )
                
                if track == None:
                    track = Track(
                        filePath,
                        Track.formatDateTime(Track.defaultDateTime()),
                        url=arg
                    )
                    self._downloadList.addTrack( track, existOK=False )

            else: # not a url -> play local audio from the audio dir or the track list
                for trackList in (self._audioList, self._downloadList):
                    hits = trackList.getTracksByPartialName( arg )

                    if hits:
                        track = randomItem( hits )
                        break

            if track != None:
                self.enqueueAudio( track )
            else:
                self.error( "Could not find matching audio for request '{}'".format(arg) )


    @requireActiveVoiceChannel
    async def skipCommand( self, message: discord.Message, *args ):
        """Stop playing the current audio file and queue the next one (if any)"""
        # Prevent the currently playing track from getting updated
        self._currentTrack = None

        # Stop playing current track
        self._activeVoiceChannel.stop()


    @requireActiveVoiceChannel
    async def nextCommand( self, message: discord.Message, *args ):
        """Stop playing the current audio file and queue the next one (if any), but update the time stamp"""
        self._currentTrack._playCount -= 1 # dirty
        self._activeVoiceChannel.stop()


    @requireActiveVoiceChannel
    async def stopCommand( self, message: discord.Message, *args ):
        """Stop playing audio and reset playback state"""
        # Reset audio state
        self._inRadioMode = False
        self._audioQueue  = []

        # Prevent the currently playing track from getting updated
        self._currentTrack = None

        # Stop playing current track
        self._activeVoiceChannel.stop()


    async def radioCommand( self, message: discord.Message, *args ):
        """Play random audio files if the queue is empty, until stopped"""
        # Connect to voice channel if necessary and possible
        if self._activeVoiceChannel == None:
            if message.author.voice.channel != None:
                await self.connectCommand( message )
            else:
                self.error( "No active voice channel!" )

        try: # respond
            with open( IMAGE_DIR / "mya-nee_approval.png", "rb" ) as file:
                await self._activeTextChannel.send( "besto radio", file=discord.File(file) )
        finally: # enable radio mode and start playing
            self._inRadioMode = True
            self.recurseAudio()


    @requireActiveTextChannel
    async def listCommand( self, message: discord.Message, *args ):
        """List the contents of the data directory (arguments in unix path style)"""
        if args:
            target = args[0]
            if len(args) < 1:
                args.append("*")

            items = []

            if target == "commands":
                items = [ "**{}**:\t{}".format(name, command.__doc__) for name, command in self._commands.items() ]

            elif target == "queue":
                items = self._audioQueue

            else:
                directory = (DATA_DIR / target).resolve()

                if directory.is_dir():
                    if SOURCE_DIR in directory.parents:
                        for searchTerm in args[1:]:
                            items += [path.stem for path in directory.glob(searchTerm)]
                    else:
                        with open( IMAGE_DIR / "hackerman.gif", "rb" ) as file:
                            await self._activeTextChannel.send(
                                "Uragirimono! >.<'",
                                reference=message,
                                file=discord.File(file)
                            )
                        self.error( "permission to '{}' denied for user '{}'".format(directory, message.author) )
                else:
                    self.error( "could not find directory for list request '{}'".format(arg) )

            for chunk in stringChunks( items ):
                await self._activeTextChannel.send( chunk )



    @requireActiveTextChannel
    async def statusCommand( self, message: discord.Message, *args ):
        """Display the current status in this guild"""
        message = ""

        if self._currentTrack != None:
            message += "PLAYING '{}'\n".format( self._currentTrack.name )
        else:
            message += "NO CURRENT AUDIO\n"

        message += "RADIO STATUS: "
        if self._inRadioMode:
            message += "ON\n"
        else:
            message += "OFF\n"

        message += "QUEUE:\n"
        await self._activeTextChannel.send( message )

        for chunk in stringChunks( [ track.name for track in self._audioQueue ] ):
            await self._activeTextChannel.send( chunk )


    async def rebootCommand( self, message: discord.Message, *args ):
        """Reset mya-nee and reconnect to discord"""
        await self._eventHooks["reboot"]()


    async def shutdownCommand( self, message: discord.Message, *args ):
        """Terminate event loop"""
        await self._eventHooks["shutdown"]()


    async def onChannelLeave( self, channel: discord.VoiceChannel, member: discord.Member ):
        """Leave the voice channel if mya-nee is the last one on it"""
        voiceChannel = next((c for c in self._voiceChannels if c.id == channel.id), None)
        self.log( "'{}' left '{}'".format(member.name, voiceChannel.name) )
        if self._activeVoiceChannel != None and self._activeVoiceChannel.id == voiceChannel.id:
            if len(self._activeVoiceChannel.members) == 1:
                self._inRadioMode = False
                await self._activeVoiceChannel.disconnect()
                self._activeVoiceChannel = None


    async def onChannelJoin( self, channel: discord.VoiceChannel, member: discord.Member ):
        voiceChannel = next((c for c in self._voiceChannels if c.id == channel.id), None)
        self.log( "'{}' joined '{}'".format(member.name, voiceChannel.name) )


    def release( self ):
        """In lieu of a destructor"""
        self._downloadList.writeToFile()
        self._audioList.writeToFile()


    def audioHook( self, *args ):
        """Executed after each call to AudioChannel::play"""
        if self._currentTrack != None:
            self._currentTrack.updateLastPlayed()
            self._currentTrack = None

            self._downloadList.writeToFile()
            self._audioList.writeToFile()

        self.recurseAudio()


    def enqueueAudio( self, track: Track ):
        """Append audio queue"""
        if self._audioQueue or self._currentTrack != None:
            self._audioQueue.append( track )
        else:
            self._audioQueue.append( track )
            self.recurseAudio()


    def recurseAudio( self ):
        if self._audioQueue:
            track = self._audioQueue.pop( 0 )
            self.playAudio( track )

        elif self._inRadioMode:
            track = self.getRandomTrack()
            if track != None:
                self.playAudio( track )


    @requireActiveVoiceChannel
    def playAudio( self, track: Track ):
        self._currentTrack = track
        self.log( "Now playing {}".format(track) )

        self._activeVoiceChannel.play( track.filePath, hook=self.audioHook )


    def getRandomTrack( self ):
        """Get a random track from the download dir (subject to the 24h rule)"""
        def isEligible( name: str, track: Track ):
            return (track.lastPlayed <= datetime.datetime.now() - self._audioRule) and not (track in self._audioQueue)
        hits = self._downloadList.getTracksByFilter( isEligible )

        if hits:
            return randomItem( hits )
        else:
            self.log( "none of the available tracks satisfy the 24h rule" )
            return None


    def update( self ):
        self._textChannels = []
        self._voiceChannels = []

        for channel in self._guild.text_channels:
            self._textChannels.append( TextChannel(channel) )

        for channel in self._guild.voice_channels:
            self._voiceChannels.append( VoiceChannel(channel, self._stream) )

        self.setActiveTextChannel()


    def setActiveTextChannel( self, channel=None ):
        if channel == None:
            for c in self.textChannels:
                if c.name == "general":
                    channel = c
                    break

        if channel != None:
            self._activeTextChannel = channel
        else:
            self.error( "Failed to set active text channel" )


    @property
    def id( self ):
        return self._guild.id


    @property
    def name( self ):
        return self._guild.name


    @property
    def members( self ):
        return self._guild.members


    @property
    def emojis( self ):
        return self._guild.emojis


    @property
    def textChannels( self ):
        return self._textChannels


    @property
    def voiceChannels( self ):
        return self._voiceChannels


    @property
    def channels( self ):
        return self.textChannels + self.voiceChannels
