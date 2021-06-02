# --- Internal Imports
from .stream import Stream


class Loggee:

    def __init__( self, logStream: Stream, name="" ):
        self._stream = logStream
        self._name = name


    def loggedTryBlock( self, function: callable ):
        def wrapper( *args, **kwargs ):
            try:
                return function( *args, **kwargs )
            except Exception as exception:
                self._stream.write( "{}\n".format(exception) )


    def log( self, content: str ):
        if self._name:
            content = "[{}] {}".format(self._name, content)

        self._stream.write( content + '\n' )


    def error( self, message: str ):
        self.log( message )
        raise Exception( message )