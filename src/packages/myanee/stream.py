class Stream( object ):

    def write( self, content: str ):
        pass


    def writelines( self, content: str ):
        pass


    def __getattr__( self, attribute ):
        return None




class DummyStream( Stream ):
    pass




class StreamWrapper( Stream ):

    def __init__( self, writeFunction: callable ):
        self._write = writeFunction


    def write( self, content: str ):
        self._write( content )


    def writelines( self, contents ):
        for content in contents:
            self.write( content )




class UnbufferedStream( Stream ):
    """A stream buffer that flushes after every call to write"""

    def __init__( self, stream ):
        self._stream = stream


    def write( self, content: str ):
        self._stream.write( content )
        self._stream.flush()


    def writelines( self, lines ):
        self._stream.writelines( lines )
        self._stream.flush()


    def __getattr__( self, attribute ):
        return getattr( self._stream, attribute )




class StreamMultiplex( Stream ):

    def __init__( self, *streams ):
        self._streams = streams


    def write( self, content ):
        for stream in self._streams:
            stream.write( content )


    def writelines( self, contents ):
        for stream in self._streams:
            stream.writelines( contents )