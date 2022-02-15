# --- STL Imports ---
import pathlib
import json

# --- Internal Imports ---
from .Track import Track
from .Loggee import Loggee
from .stream import Stream


class TrackList(Loggee):

    def __init__(self, directory: pathlib.Path, logStream: Stream):
        Loggee.__init__(self, logStream, name="TrackList")
        self._directory = directory
        self._filePath  = directory / "track_list.json"
        self._tracks    = {}

        self.load()


    def getTracksByFilter(self, filterFunction: callable):
        """Filter function takes a name and track, and returns a bool"""
        return [ value for key, value in self._tracks.items() if filterFunction(key, value) ]


    def getTrackByFullName(self, trackName: str):
        return self._tracks[trackName]


    def getTracksByPartialName(self, query: str):
        return self.getTracksByFilter(lambda key, value: query in key)


    def getTrackByFilePath(self, path: pathlib.Path):
        hits = self.getTracksByFilter(lambda name, track: track.filePath == path)
        if hits:
            return hits[0]
        else:
            return None


    def getTrackByURL(self, url: str):
        def isURLMatch(name: str, track: Track):
            return track.url == url
        hits = self.getTracksByFilter(isURLMatch)

        if hits:
            return hits[0]
        else:
            return None


    def writeToFile(self):
        with open(self._filePath, 'w') as file:
            json.dump(
                { key : value.dict() for key, value in self._tracks.items() },
                file,
                indent="    "
            )

    def load(self):
        """Populate the track list"""
        if self._filePath.is_file():
            with open(self._filePath, 'r') as file:
                contents = json.load(file)

                for trackName, trackData in contents.items():
                    self._tracks[trackName] = Track.fromDict(trackData)

        self.update()


    def update(self):
        """Make sure only existing tracks are in the list, but all of them are there"""
        # Check whether all tracks in the list point to existing files
        self._tracks = { trackName : track for trackName, track in self._tracks.items() if track.isDownloaded() }

        # Register new tracks
        for filePath in self._directory.glob("*.*"):
            if self.isAudioFile(filePath):
                self.addTrack(
                    Track(
                        filePath,
                        Track.formatDateTime(Track.defaultDateTime())
                   ),
                    existOK=True
                )


    def addTrack(self, track: Track, existOK=False):
        if not track.name in self._tracks:
            self._tracks[track.name] = track
        else:
            if not existOK:
                self.error("Attempt to add existing track to list {}".format(track))

        return track.name


    @staticmethod
    def getEmptyTrackList():
        return r"""{}"""


    @staticmethod
    def isAudioFile(filePath: pathlib.Path):
        """Temporary implementation"""
        return filePath.is_file() and str(filePath.suffix).lower() != ".json"