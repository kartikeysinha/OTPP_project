import sys
import datetime as dt
import pandas as pd
import numpy as np

import data_grabber


DEFAULT_PORT = 8000

class ServerRequest:

    def __init__(self) -> None:
        pass


class Server:

    def __init__(self, supported_assets, port):
        self.request_queue = []
        self.supported_assets = supported_assets
        self.port = port
        self.DG = data_grabber.DataGrabber()

        self.run_process()
    
    """
    Signal and Pnl Calculation
    """
    def _get_data(self, freq : str , month : str | dt.datetime ) -> pd.DataFrame:
        """  """
        return self.DG.get_prices(tickers=self.supported_assets, frequency=freq, time_req=month)
    
    def _calc_signal(self, freq : str, prices : pd.DataFrame) -> pd.DataFrame:
        """  """
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
        return signals * prices.diff().shift(-1)
    
    def run_process( self, freq : str = "1min", month : str | dt.datetime = dt.datetime.now() ):
        prices = self._get_data( freq, month )
        signals = self._calc_signal(freq, prices)
        pnl = self._calc_pnl(signals, prices)

        frames  = []
        for col_name, cur_df in [('price', prices), ('signal', signals), ('pnl', pnl)]:
            frames.append(cur_df.melt(ignore_index=False, value_name=col_name).set_index('ticker', append=True))
        final_df = pd.concat(frames, axis=1).reset_index()

        print(final_df.tail(15))

    """
    Client logic
    """
    def register_client(self, client_info):
        # store client information
        # return client id
        client_id = 0
        return client_id
    
    def delete_client(self, client_info):
        """ NO longer serve this client. The client will have to register again. """
        ...
        return True
    
    """
    Request processing
    """

    def add_new_request(self, req : ServerRequest):
        """ Add new request from client. """
        self.request_queue.append(req)
    
    def is_request_queue_empty(self):
        return len(self.request_queue) == 0

    def get_request_to_process(self):
        """ Assumes that the request queue is not empty. Returns the request to process. """
        return self.request_queue.pop(0)
    

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
    port = DEFAULT_PORT
    
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
        
    server = Server(supported_tickers, port)

    # while True:

    #     if server.is_request_queue_empty():
    #         # we have one or more requests to process
    #         req = server.get_request_to_process()


