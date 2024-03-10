

class Client:

    def __init__(self) -> None:
        # register with server.
        self.register()
    
    def __exit__(self) -> None:
        """ De-register with the server """
        # make request to server with self.id
        ...
    
    def register(self) -> None:
        """ Register with the server """
        # make request to client to retreive client_id
        self.id = 0
    
    """
    CLI support
    """

    def get_data(self, time_spec : str) -> None:
        """
        Get latest available data from the server for the time specified.
        If data is not available, prints an error message

        Args
        ----
        time_spec : str
            Ensure format is "YYYY-MM-DD-HH:MM"
        """

        # Make request to server : include self.id ; time_spec
        ...
        # get return value
        retval = " Got data "
        # print return value
        if retval:
            print(retval)
        else:
            print("The server does not support data so far back. Try again with a more recent date.")
    

    def change_ticker(self, ticker : str, operation : str) -> None:
        """
        Instruct client to add ticker to it's offering.

        Args
        ----
        ticker : str
        operation : str
            Either 'add' or 'delete'
        """
        # Make request to server : include self.id ; ticker; operation
        ...

    
    def reconstruct_report(self) -> None:
        """
        Instruct client to recomstruct report with the latest data, signal, pnl.
        """
        # Make request to server : include self.id
        ...





if __name__ == "__main__":


