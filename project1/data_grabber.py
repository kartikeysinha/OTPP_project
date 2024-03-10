import pandas as pd
import numpy as np
import requests
import os
import dotenv
import finnhub
import datetime as dt
import yfinance as yf
import dateutil

dotenv.load_dotenv()


"""
Alpha Vantage API
"""
class AlphaVantageAPI():

    def __init__(self, api_key=os.environ.get("ALPHA_VANTAGE_API_KEY")) -> None:
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY"
    
    def _get_candles_per_ticker(
        self,
        ticker : str,
        interval : int,
        month : str
    ) -> pd.DataFrame:
        
        args = f"&symbol={ticker}&interval={interval}&apikey={self.api_key}&outputsize=full&month={month}"
        url = self.base_url + args

        r = requests.get(url)
        data = r.json()

        try:
            df = pd.DataFrame.from_dict(data[f'Time Series ({interval})'], orient='index')
            # re-format columns: Ex. "1. open" -> "open"
            df.columns = [x[3:] for x in df.columns]
        except:
            raise(f"Ran out of API Rate Limit.\n{data}")

        return df
    
    def get_candles(
        self,
        tickers : str | list[str],
        interval : int,
        month : str
    ) -> pd.DataFrame:
        
        # Ensure tickers is iterable
        if type(tickers) == str:
            tickers = [tickers]
        
        frames = []
        for sym in tickers:
            tmp_df = self._get_candles_per_ticker(ticker=sym, interval=interval, month=month)
            tmp_df['ticker'] = sym
            frames.append( tmp_df )
        
        return pd.concat( frames )   


"""
FinnHub API
"""
class FinnHubAPI():

    def __init__(self, api_key=os.environ.get("FINNHUB_API_KEY")):
        self.api_key = api_key
    
    def _get_quote_one_ticker(
        self,
        ticker : str
    ) -> pd.DataFrame:
        with finnhub.Client(api_key=self.api_key) as finnhub_client:
            d = finnhub_client.quote(ticker)
        return pd.DataFrame.from_dict(d, orient='columns')
    
    def get_quotes(
        self, 
        tickers : str | list[str]
    ) -> pd.DataFrame:
        
        # Ensure tickers is iterable
        if type(tickers) == str:
            tickers = [tickers]
        
        frames = []
        for sym in tickers:
            frames.append( self._get_quote_one_ticker(sym) )
        
        return pd.concat( frames )
        


"""
Yahoo Finance API
"""
class YahooFinance():

    def __init__(self):
        return
    
    def _format_yfinance_return_df( self, df : pd.DataFrame ) -> pd.DataFrame:
        """
        Yahoo Finance return a multi-column dataframe. To be consistent
        with other vendors (such as AlphaVantage), we reformat the data.
        """
        # Melt dataframe to remove the multi-columns structure
        tmp_df = df.melt(ignore_index=False).reset_index()  
        # Establish common structure as other return points -> this still has 2 columns - needs small processing to remove
        tmp_df = tmp_df.pivot(columns=["Price"], index=["datetime", "Ticker"]).reset_index(level=1)

        # Construct new column names
        new_column_names = [x[1].lower() for x in tmp_df.columns]
        new_column_names[0] = 'ticker'

        # Remove one index and rebale the other with new column names
        tmp_df = tmp_df.droplevel(level=0, axis=1)
        tmp_df.columns = new_column_names

        return tmp_df
    
    def _clean_data(self, df : pd.DataFrame) -> pd.DataFrame:
        df.index.name = df.index.name.lower()
        return df.ffill()

    def get_candles(
        self,
        tickers : str | list[str],
        start_date : str = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d"),
        end_date : str = dt.datetime.now().strftime("%Y-%m-%d"),
        freq : str = '1m'
    ) -> pd.DataFrame:
        """
        Get candle information for the requested tickers, desired date range, and the desired freqeuncy.
        """
        if type(tickers) == str:
            tickers = [tickers]
        
        df = yf.download(tickers=tickers, start=start_date, end=end_date, interval=freq, prepost=True)
        df = self._clean_data(df)

        if len(tickers) == 1:
            df.columns = [x.lower() for x in df.columns]
            df['ticker'] = tickers[0]
            return df

        
        return self._format_yfinance_return_df(df)


"""
Data Grabber
"""
class DataGrabber:
    """
    Collect requested data from available data source(s).

    Purpose: Keep server agnostic of the data source (as much as possible).
    """

    def __init__(self):
        self.AV = AlphaVantageAPI()
        self.FH = FinnHubAPI()
        self.YF = YahooFinance()
    
    def get_realtime_quotes(self, tickers : str | list[str] ) -> pd.DataFrame:
        return self.FH.get_quotes(tickers=tickers)
    
    def get_prices(
        self,
        tickers : str | list[str],
        frequency : str = "1min",
        time_req : str | dt.datetime = dt.datetime.now()
    ) -> pd.Series:
        
        # Convert time_req to datetime object
        if type(time_req) == str:
            time_req = dateutil.parser.parse(time_req)

        # try:
        #     df = self.AV.get_candles(tickers=tickers, interval=frequency, month=time_req.strftime("%Y-%m"))
        # except:
        #     print("NOTE: Getting the latest data available.")
        #     df = self.YF.get_candles(tickers=tickers, freq=frequency[:2])
        df = self.YF.get_candles(tickers=tickers, freq=frequency[:2])

        return df[['ticker', 'close']].reset_index().pivot(index='datetime', columns='ticker').droplevel(level=0, axis=1)

