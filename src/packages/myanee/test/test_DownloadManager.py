# --- STL Imports ---
import unittest
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent.parent)) # needed to run this script directly

# --- Internal Imports ---
from myanee.DownloadManager import DownloadManager
from myanee.utilities import DOWNLOAD_DIR


class TestDownloadManager(unittest.TestCase):

    def test_DownloadManager( self ):
        manager = DownloadManager( logStream=sys.stderr )
        for url, filePath in zip(self.testLinks, self.testFilePaths):
            self.assertFalse( filePath.is_file() )
            path = manager.enqueue( url )

            self.assertEqual( path, filePath )
            self.assertTrue( path.is_file() )


    def clear( self ):
        """Delete test files"""
        for filePath in self.testFilePaths:
            filePath.unlink( missing_ok=True )


    @property
    def testFilePaths( self ):
        return [DOWNLOAD_DIR / "mya-nee_!!!.webm"]


    @property
    def testLinks( self ):
        return ["https://www.youtube.com/watch?v=cSa1DJUbVSs"]

    
    def setUp( self ):
        self.clear()


    def tearDown( self ):
        self.clear()




if __name__ == "__main__":
    unittest.main()