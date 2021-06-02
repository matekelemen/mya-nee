# --- STL Imports ---
import unittest
import pathlib
import sys
import datetime

sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent.parent)) # needed to run this script directly

# --- Internal Imports ---
from myanee.TrackList import TrackList
from myanee.utilities import DOWNLOAD_DIR


class TestTrackList( unittest.TestCase ):

    def setUp( self ):
        pass


    def tearDown( self ):
        pass


    def test_TrackList( self ):
        # TODO
        trackList = TrackList( DOWNLOAD_DIR, sys.stderr )




if __name__ == "__main__":
    unittest.main()