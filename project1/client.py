import sys
import rpc
import zoneinfo
import datetime as dt

class Client:

    def __init__(self, port : int = rpc.DEFAULT_PORT) -> None:
        # register with server.
        self.client_rpc = rpc.RPCClient(port=port)

        self.register()
    
    def __exit__(self) -> None:
        """ De-register with the server """
        self.client_rpc.disconnect()
        
    
    def register(self) -> None:
        """ Register with the server """
        # make request to client to retreive client_id
        self.client_rpc.connect()
    
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

        # Format time
        
        # get return value
        retval = self.client_rpc.client_get_data( time_spec )
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
        if operation == 'add':
            self.client_rpc.client_add_ticker(ticker.upper())
        else:
            self.client_rpc.client_delete_ticker(ticker.upper())

    
    def reconstruct_report(self) -> None:
        """
        Instruct client to recomstruct report with the latest data, signal, pnl.
        """
        # Make request to server : include self.id
        self.client_rpc.client_reconstruct_reports()



def _help_CLI():
    s = """
    ERROR: CLI arguments can't be parsed.
    """
    print(s)

def _help():
    s = """
    Supported arguments:

    """
    print(s)


def _process_arguments( client : Client ):
    while True:
        inp = input("> ")

        if inp.startswith("data "):
            client.get_data(inp.split(" ")[1])

        elif inp.startswith("add "):
            client.change_ticker(inp.split(" ")[1], "add")

        elif inp.startswith("delete "):
            client.change_ticker(inp.split(" ")[1], "delete")

        elif inp.startswith("report"):
            client.reconstruct_report()

        elif inp.startswith("q"):
            break
        else:
            _help()


if __name__ == '__main__':

    port = rpc.DEFAULT_PORT

    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    elif len(sys.argv) > 1:
        _help_CLI()
        raise
        
    # global SERVER
    # SERVER = Server(supported_tickers, port)

    # while True:

    #     if SERVER.is_request_queue_empty():
    #         # we have one or more requests to process
    #         req = SERVER.process_request()

    client = Client(port=port)

    _process_arguments(client)




