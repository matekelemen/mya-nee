# --- STL Imports ---
import unittest
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent.parent)) # needed to run this script directly

# --- Internal Imports ---
from myanee.Track import Track
from myanee.utilities import SOURCE_DIR


class TestTrack(unittest.TestCase):

    def test_Track( self ):

        defaultDateTime = Track.defaultDateTime()
        formatted = Track.formatDateTime( defaultDateTime )
        self.assertEqual( formatted, "01-05-2021_00:00" )

        track = Track(
            self.trackPath,
            formatted,
            url = "https://www.youtube.com/watch?v=cSa1DJUbVSs",
            volume = 100
        )
        self.assertEqual( track.lastPlayed, defaultDateTime )

        self.assertTrue( track.isDownloaded() )
        self.assertEqual( track.directory, SOURCE_DIR )
        self.assertEqual( track.name, "mya-nee_!!!" )
        self.assertEqual( track.extension, ".webm" )
        self.assertEqual( track.url, "https://www.youtube.com/watch?v=cSa1DJUbVSs" )
        self.assertEqual( track.volume, 100 )


    @property
    def trackPath( self ):
        return SOURCE_DIR / "mya-nee_!!!.webm"


    def setUp( self ):
        """Create test file"""
        file = open( self.trackPath, 'w' )
        file.close()

    
    def tearDown( self ):
        """Delete test file"""
        self.trackPath.unlink( missing_ok = True )




if __name__ == "__main__":
    unittest.main()