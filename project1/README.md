# Project 1 description

Note that Alpha Vantage has a revised API limit of 25 calls / day. Hence, I've decided to
use YahooFinance to get the data. One problem with YahooFinance is that for higher frequency,
there is not much histroical data available.

Due to a very strict limit of 25 calls / day, I have focused primarily on making the solution
work with YahooFinance. 

Code to get data from AlphaVantage works but the solution has not been tested thoroughly.
Getting previous data is errorneous and was not able to be fixed due to hitting the rate limit.

# Setup

All the requirements are specified in the requirements.txt file in the root directory.

## Handling API Keys
Create a .env file in the root directory which contains the API keys to both Alpha Vantage 
& Finnhub. Name them as follows:
```
ALPHA_VANTAGE_API_KEY=""
FINNHUB_API_KEY=""
``` 

# Running the code

<u>Server</u>
* `python3 server.py`
  * (Optional) Supported CLI arguments:
    * --port XXXX
    * --tickers space-separated-tickers
    * --freq any_of_(1, 5, 15, 30, 60)
  
Ex. `python3 server.py --port 8000 --tickers AAPL TSLA NVDA --freq 5`

Note: Freq can't be changed in program.

<u>Client</u>
* `python3 client.py`
  * Required CLI arguments:
    * --port XXXX
  
Ex. `python3 client.py --port 8000`

# Development Notes
I've documented my development process below. 

## Example run
`python3 server.py --port 8000 --tickers AAPL TSLA NVDA --freq 5`

`python3 client.py --port 8000`

\>data TIME<br>
give information specified by TIME
If report.csv doesn't have information BEFORE TIME, try and recalculate.
If recalculation is successful, OVERWRITE the report.csv file with this new (old) data.

\> add V<br>
Adds V to the report.csv -> Adds the most recent data, doesn't adhere to the same time frame
stored in report.csv

\> delete AAPL<br>
Deletes all information regarding AAPL from report.csv. Doesn't touch any other data.

\>data TIME<br>
give information specified by TIME
- same rules as above run for `data` apply
- might return very stale data if TIME >> maximum index in report.csv -> IN this case, need to run report to get fresher data

\> report
recalculates all information using the latest information.

...

### Assumptions:
* Network is safe and doesn't fail.
* Server doesn't fail.
* CLI arguments to both the server and client will be right.
* Any and all clients are started AFTER server.
* There is a global dataset maintained by the server - not one dataset per client.
* The frequency of data is specified once in CLI. This won't change after that.

### Design decisions (including behavior of client functions):
* Given that the server doesn't fail (asusmption), we can store information (state) at the server
  to improve performance.
* Whenever a client asks to create a new `report`, get all the data regarding the assets
  and calculate the returns, momentum signal, as well as the PnL.
* Whenever a client asks for `data`, we try and get the latest data from rerport.csv. If the time requested
  if smaller than any data available in csv, we try query for new data. If the time requested is greater
  than any data available, we just find the closest data. So, in order to get up to date information, it might make sense
  to re-run report to restore the csv file and then get the latest data using `report`.
* When client wants to `add` ticker, and if the ticker doesn't already exist, information about that ticker is queried
  for the latest date range (date-range for the other assets in report.csv can be different).
* When client wants to `delete` ticker, the ticker is deleted from report.csv. Rest of the data is not touched

### Advantages of this design:
* easy to implement.
* Only gets new data when needed.

### Disadvantages / Restrictions of this design:
* A lot of calculations will happen again and again -> inefficient. Can using caching to improve performance.
  Example, one client wants to remove a ticker while another client wants data for that ticker. If both of them
  keep requesting addition / deletion, we will have to recalclate data everytime.
