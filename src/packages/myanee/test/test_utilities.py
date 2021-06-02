# --- STL Imports ---
import unittest
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent.parent)) # needed to run this script directly

# --- Internal Imports ---
from myanee.utilities import isURL, chunks, SOURCE_DIR


class TestUtilities(unittest.TestCase):

    def test_isURL(self):
        validURLs = [
            "https://www.youtube.com/",
            "https://www.youtu.be/"
        ]

        invalidURLs = [
            str(SOURCE_DIR),
            "",
            "/"
        ]

        for string in validURLs:
            self.assertTrue( isURL(string), msg=string )

        for string in invalidURLs:
            self.assertFalse( isURL(string), msg=string )


    def test_chunks(self):
        baseList = [i for i in range(10)]

        self.assertRaises( Exception, chunks(baseList, chunkSize=0) )

        test = list( chunks(baseList, chunkSize=1) )
        reference = [[i] for i in range(10)]
        self.assertTrue( test == reference, msg=test )

        test = list( chunks(baseList, chunkSize=2) )
        reference = [ [0, 1], [2, 3], [4, 5], [6, 7], [8, 9] ]
        self.assertTrue( test == reference, msg=test )

        test = list( chunks(baseList, chunkSize=3) )
        reference = [ [0, 1, 2], [3, 4, 5], [6, 7, 8], [9] ]
        self.assertTrue( test == reference, msg=test )




if __name__ == "__main__":
    unittest.main()