# --- STL Imports ---
import unittest
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent.parent)) # needed to run this script directly

# --- Internal Imports ---
from myanee.stream import StreamWrapper, StreamMultiplex


class TestStreams( unittest.TestCase ):

    def setUp( self ):
        self._test = ""


    def test_StreamWrapper( self ):
        def writeFunction( content ):
            self._test += content

        stream = StreamWrapper( writeFunction )

        self._test = ""
        stream.write( "content" )
        self.assertEqual( self._test, "content" )

        self._test = ""
        stream.writelines( ['c', "on", "tents"] )
        self.assertEqual( self._test, "contents" )


    def test_StreamMultiplex( self ):
        def writeFunction0( content ):
            self._test += "0:" + content + ";"

        def writeFunction1( content ):
            self._test += "1:" + content + ";"

        stream0 = StreamWrapper( writeFunction0 )
        stream1 = StreamWrapper( writeFunction1 )
        stream = StreamMultiplex( stream0, stream1 )

        self._test = ""
        stream.write( "content" )
        self.assertTrue( "0:content;" in self._test )
        self.assertTrue( "1:content;" in self._test )

        self._test = ""
        stream.writelines( ['c', "on", "tents"] )
        self.assertTrue( "0:c;" in self._test )
        self.assertTrue( "0:on;" in self._test )
        self.assertTrue( "0:tents;" in self._test )
        self.assertTrue( "1:c;" in self._test )
        self.assertTrue( "1:on;" in self._test )
        self.assertTrue( "1:tents;" in self._test )




if __name__ == "__main__":
    unittest.main()