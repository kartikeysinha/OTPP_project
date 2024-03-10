import sys
import datetime as dt
import pandas as pd
import numpy as np
import threading
import zoneinfo
import rpc

import data_grabber



CLIENTS_LOCK = threading.Lock()
REQUESTS_LOCK = threading.Lock()
DATA_LOCK = threading.Lock()
DEFAULT_PORT = 8000


class ServerRequest:
    """ A Wrapper for requests to server. """
    def __init__(self, client_id="", req_type="", time_info:str="", ticker:str="") -> None:
        self.client_df = client_id
        self.type = req_type
        self.time_info = time_info
        self.ticker = ticker


class Server:

    def __init__(self, supported_assets):
        self.request_queue = []

        self.supported_assets = set(supported_assets)

        self.clients = dict()
        self.latest_client_number = 1
        
        self.DG = data_grabber.DataGrabber()

        if self.supported_assets:
            df = self.run_process()
            self.save_report(df)
    

    # ************************ #
    # ------------------------ #
    # Get prices, calculate signal and PnL
    # ------------------------ #
    # ************************ #

    def _get_data_from_API(self, tickers : list[str], freq : str , month : str | dt.datetime ) -> pd.DataFrame:
        """
        Get prices data from the accurate API.
        """
        return self.DG.get_prices(tickers=tickers, frequency=freq, time_req=month)
    
    def _calc_signal(self, freq : str, prices : pd.DataFrame) -> pd.DataFrame:
        """ Given prices, calculate the signal using the momentum logic highlighted in the requirements. """
        rolling_prices = prices.rolling(window = 24 * (60 // int(freq.split("m")[0])))
        S_avg = rolling_prices.mean()
        S_sigma = rolling_prices.std()

        signals = pd.DataFrame(data=np.NaN, index=prices.index, columns=prices.columns)
        for ticker in signals.columns:
            signals.loc[:, ticker] = signals.loc[:, ticker].mask( prices[ticker] > (S_avg[ticker] + S_sigma[ticker]), 1 )
            signals.loc[:, ticker] = signals.loc[:, ticker].mask( prices[ticker] < (S_avg[ticker] - S_sigma[ticker]), -1 )
        signals.ffill(inplace=True)

        return signals
    
    def _calc_pnl( self, signals : pd.DataFrame, prices : pd.DataFrame ) -> pd.DataFrame:
        """ Given signal and prices, return the pnl of the signal. """
        return signals.shift(1) * prices.diff()
    

    def run_process( 
        self,
        tickers : str | list[str] = None,
        freq : str = "5min", 
        month : str | dt.datetime = dt.datetime.now() 
    ):
        """
        Collects prices, calculates signal and pnl for the tickers in self.supported_assets
        """

        if not tickers:
            tickers = self.supported_assets
        if type(tickers) == str:
            tickers = [tickers]
        
        prices = self._get_data_from_API( tickers, freq, month )
        signals = self._calc_signal(freq, prices)
        pnl = self._calc_pnl(signals, prices)

        frames  = []
        for col_name, cur_df in [('price', prices), ('signal', signals), ('pnl', pnl)]:
            frames.append(cur_df.melt(ignore_index=False, value_name=col_name).set_index('ticker', append=True))
        final_df = pd.concat(frames, axis=1).reset_index(level=1)

        return final_df
    
    def save_report(self, df:pd.DataFrame, fp="./"):
        """ Save the report. """
        df.to_csv(fp+"report.csv")


    # ************************ #
    # ------------------------ #
    # Logic for getting data, adding & deleting tickers, and reconstructing reports.
    # ------------------------ #
    # ************************ #

    def client_get_data( self, time_spec : str ) -> pd.DataFrame:
        """
        Support the 'data' call from client.
        """
        # Get stored data
        with DATA_LOCK:
            df = pd.read_csv("report.csv", index_col="datetime")
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        # Get nearest index that is lesser than the time_spec
        time_spec = dt.datetime.strptime(time_spec, "%Y-%m-%d-%H:%M").replace(tzinfo=zoneinfo.ZoneInfo("US/Eastern"))
        idx = min(df.index, key=lambda x: time_spec - x if time_spec >= x else dt.timedelta(days=10))

        # If data doesn't exist, return an empty string
        if idx > time_spec:
            return ""

        # Data does exist -> get relevant data 
        relevant_data = df.loc[idx, ['ticker', 'price', 'signal'] ].reset_index(drop=True)
        # Format return string
        s = ""
        for i in relevant_data.index:
            s += f'{relevant_data.loc[i, "ticker"]}\t\t{np.round(relevant_data.loc[i, "price"],2)},{relevant_data.loc[i, "signal"]}\n'
        
        return s

    def client_add_ticker(self, ticker : str) -> None:
        """
        Support the add ticker call from client.
        """
        with DATA_LOCK:
            if ticker not in self.supported_assets:
                self.supported_assets.add(ticker)
                new_df = self.run_process(tickers=ticker)
                df = pd.read_csv("report.csv", index_col="datetime")
                self.save_report(pd.concat([new_df, df], axis=0, ignore_index=False))
        
    def client_delete_ticker(self, ticker : str) -> None:
        """
        Delete ticker from client offering.
        """
        with DATA_LOCK:
            if ticker in self.supported_assets:
                df = pd.read_csv("report.csv", index_col="datetime")
                df.index = pd.to_datetime(df.index)
                df = df.loc[~(df['ticker'] == ticker)]
                self.supported_assets.remove(ticker)
                self.save_report(df)

    def client_reconstruct_reports(self) -> None:
        """
        Support the 'report' call from client.
        """
        with DATA_LOCK:
            df = self.run_process()
            self.save_report(df)
    

    # # ************************ #
    # # ------------------------ #
    # # Request Processing
    # # ------------------------ #
    # # ************************ #

    # def make_request(self, **kwargs):
    #     """ Process new request from client which is passed as an RPC call. """
    #     ...

    # def add_new_request(self, req : ServerRequest):
    #     """ Add new request from client. """
    #     with REQUESTS_LOCK:
    #         self.request_queue.append(req)
    
    # def is_request_queue_empty(self):
    #     return len(self.request_queue) == 0

    # def get_request_to_process(self):
    #     """ Assumes that the request queue is not empty. Returns the request to process. """
    #     with REQUESTS_LOCK:
    #         req = self.request_queue.pop(0)

    #     if req.req_type == "data":
    #         time_info = dt.datetime.strptime(req.time_info, "%Y-%m-%d-%H:%M")
    #         retval = self.client_get_data( time_info.replace(tzinfo=zoneinfo.ZoneInfo("US/Eastern")) )

    #         # TODO: Return value to client -> client is specified in req.client_id.

    #     elif req.req_type == "add":
    #         self.client_add_ticker(req.ticker)
    #     elif req.req_type == "delete":
    #         self.client_delete_ticker(req.ticker)
    #     elif req.req_type == "report":
    #         self.client_reconstruct_reports()
    #     else:
    #         print("Invalid request given to parse.")


    # # ************************ #
    # # ------------------------ #
    # # Client Logic.
    # # ------------------------ #
    # # ************************ #

    # def register_client(self) -> int:
    #     # store client information
    #     # return client id
    #     client_id = 0
    #     with CLIENTS_LOCK:
    #         ret = self.latest_client_number
    #         self.latest_client_number += 1
    #         self.clients[client_id] = None          
    #         # This can be expanded to include assets supported per client as well as timeframe the client is interested in.
    #         # This will help in caching and hence increasing the efficiency of our system with a more flexible offering.

    #     return client_id
    
    # def delete_client(self, client_id) -> bool:
    #     """ 
    #     Returns true if successfully deleted. Server will no longer serve 
    #     this client. The client will have to register again. 
    #     """
    #     with CLIENTS_LOCK:
    #         del self.clients[client_id]
    #     return True




def _help():
    s = """
    ERROR: CLI arguments can't be parsed.
    Correct format:
    Optional arguments include:
        --ticker LIST-OF-TICKERS-SEPARATED-BY-SPACES 
        --port XXXX
    """
    print(s)


def _process_args(args):
    """ Process the Command Line Arguments for the server. """

    supported_tickers = []
    port = rpc.DEFAULT_PORT
    
    try:
        i = 0
        while i < len(args):
            if args[i] == "--port":
                port = int(args[i+1])
                i += 2
            elif args[i] == "--tickers":   # the next arguments are going to tickers only.
                end_idx = len(args)
                if args[-2] == "--port":
                    end_idx -= 2
                supported_tickers.extend([x.upper() for x in args[i+1:end_idx]])
                i = end_idx
            else:
                raise ValueError("Incorrect formatting of CLI arguments.")
    except:
        _help()
        raise

    return supported_tickers, port


if __name__ == '__main__':

    supported_tickers, port = _process_args( sys.argv[1:] )

    print(f"Server initialized with supported_tickers: {supported_tickers} and port: {port}")
        
    # global SERVER
    # SERVER = Server(supported_tickers, port)

    # while True:

    #     if SERVER.is_request_queue_empty():
    #         # we have one or more requests to process
    #         req = SERVER.process_request()

    server = Server(supported_assets=supported_tickers)
    server_rpc = rpc.RPCServer(port=port)

    server_rpc.registerInstance( server )

    server_rpc.run()

            


