class Status:


    def __init__( self, status: str ):
        self.set( status )


    def __call__( self ):
        return self._status


    def set( self, status: str ):
        self._status = status