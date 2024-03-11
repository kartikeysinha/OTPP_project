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


class Server:

    def __init__(self, supported_assets : str | list[str], freq_minutes : int):
        self.supported_assets = set(supported_assets)
        self.freq = freq_minutes
        self.DG = data_grabber.DataGrabber()
        if self.supported_assets:
            df = self.run_process()
            self.save_report(df)
    

    # ************************ #
    # ------------------------ #
    # Get prices, calculate signal and PnL
    # ------------------------ #
    # ************************ #

    def _get_data_from_API(self, tickers : list[str], dte : str | dt.datetime ) -> pd.DataFrame:
        """
        Get prices data from the accurate API.
        """
        return self.DG.get_prices(tickers=tickers, frequency=self.freq, time_req=dte)
    
    def _calc_signal(self, prices : pd.DataFrame) -> pd.DataFrame:
        """ Given prices, calculate the signal using the momentum logic highlighted in the requirements. """
        rolling_prices = prices.rolling(window = 24 * (60 // self.freq))
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
        dte : str | dt.datetime = dt.datetime.now() 
    ):
        """
        Collects prices, calculates signal and pnl for the tickers in self.supported_assets
        """

        if not tickers:
            tickers = self.supported_assets
        if type(tickers) == str:
            tickers = [tickers]
        
        print("getting data...")
        prices = self._get_data_from_API( tickers, dte )
        if prices.empty:
            print("Got empty prices.")
            return pd.DataFrame()
        print("making signals ...")
        signals = self._calc_signal(prices)
        print("calculating pnl...")
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
        If time_spec if not supported by the current csv file, the process tries to
        get data. If it is successful, it will overwrite the current csv file with 
        old data.
        It if fails, the csv file is not touched.

        side-effect
        ----------
        Changes report.csv
        """
        # Get stored data
        with DATA_LOCK:
            df = pd.read_csv("report.csv", index_col="datetime")
        df.index = pd.to_datetime(df.index)         # Convert index to datetime

        # Get nearest index that is lesser than the time_spec
        time_spec = dt.datetime.strptime(time_spec, "%Y-%m-%d-%H:%M").replace(tzinfo=zoneinfo.ZoneInfo("US/Eastern"))
        idx = min(df.index, key=lambda x: time_spec - x if time_spec >= x else dt.timedelta(days=10))

        # If data doesn't exist, try recalculating data
        if idx > time_spec:
            df = self.run_process( dte = time_spec + dt.timedelta(days=1) )
            if not df.empty:
                with DATA_LOCK:
                    self.save_report(df)        # Save new data if we manage to retrieve it.
            else:
                return ""
        
            # Re run the process
            with DATA_LOCK:
                df = pd.read_csv("report.csv", index_col="datetime")
            df.index = pd.to_datetime(df.index)         # Convert index to datetime
            # Get nearest index that is lesser than the time_spec
            idx = min(df.index, key=lambda x: time_spec - x if time_spec >= x else dt.timedelta(days=10))

        # Data does exist -> get relevant data 
        relevant_data = df.loc[[idx], ['ticker', 'price', 'signal'] ].reset_index(drop=True)

        # Format return string
        s = f"Reporting data for {idx.strftime('%Y-%m-%d-%H:%M')}\n"
        for i in relevant_data.index:
            s += f'{relevant_data.loc[i, "ticker"]}\t\t{np.round(relevant_data.loc[i, "price"],2)},{relevant_data.loc[i, "signal"]}\n'
        
        return s

    def client_add_ticker(self, ticker : str) -> None:
        """
        Support the add ticker call from client.
        Adds recent data for the ticker provided.
        Doesn't touch the rest of the csv.

        side-effect
        ----------
        Changes report.csv
        """
        with DATA_LOCK:
            if ticker not in self.supported_assets:
                self.supported_assets.add(ticker)
                new_df = self.run_process(tickers=ticker)
                df = pd.read_csv("report.csv", index_col="datetime")
                self.save_report(pd.concat([new_df, df], axis=0, ignore_index=False))
        
    def client_delete_ticker(self, ticker : str) -> None:
        """
        Delete ticker from client offering by deleting any occurences from the csv file
        Doesn't touch the rest of the csv.

        side-effect
        ----------
        Changes report.csv
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
        Recomputes data for the most recent data and saves it as csv.
        
        side-effect
        ----------
        Changes report.csv
        """
        with DATA_LOCK:
            df = self.run_process()
            self.save_report(df)
    

def _help():
    s = """
    ERROR: CLI arguments can't be parsed.
    Correct format:
    Optional arguments include:
        --ticker LIST-OF-TICKERS-SEPARATED-BY-SPACES 
        --port XXXX
        --freq int
    """
    print(s)


def _process_args(args):
    """ Process the Command Line Arguments for the server. """

    supported_tickers = []
    port = rpc.DEFAULT_PORT
    freq = 1
    
    try:
        i = 0
        while i < len(args):

            if args[i] == "--port":
                port = int(args[i+1])
                i += 2

            elif args[i] == "--freq":
                freq = int(args[i+1])
                i += 2
                if freq not in set([1, 5, 15, 30, 60]):
                    raise ValueError("Frequency is not supported.")
                
            elif args[i] == "--tickers":   # the next arguments are going to tickers only.
                end_idx = len(args)
                if len(args) - i > 4 and args[-4].startswith("--"):
                    end_idx -= 4
                elif len(args) - i > 2 and args[-2].startswith("--"):
                    end_idx -= 2
                supported_tickers.extend([x.upper() for x in args[i+1:end_idx]])
                i = end_idx

            else:
                raise ValueError("Incorrect formatting of CLI arguments.")
    except:
        _help()
        raise

    return supported_tickers, port, freq


if __name__ == '__main__':

    supported_tickers, port, freq = _process_args( sys.argv[1:] )
    print(f"Server initialized with supported_tickers: {supported_tickers} ; port: {port} ; freq: {freq}")
        
    server = Server(supported_assets=supported_tickers, freq_minutes=freq)

    server_rpc = rpc.RPCServer(port=port)
    server_rpc.registerInstance( server )

    server_rpc.run()
