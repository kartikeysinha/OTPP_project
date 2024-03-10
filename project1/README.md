# Project 1 description

Note that Alpha Vantage has a revised API limit of 25 calls / day. Hence, I've decided to
use YahooFinance to get the data. One problem with YahooFinance is that for higher frequency,
there is not much histroical data available.

Due to a very strict limit of 25 calls / day, I will initially focus on mkaing sure the solution
works with YahooFinance. Once that's done and I have time left, I will try make the solution
resiliant (and more flexible) to include Alpha Vantage as well.

# Setup

All the requirements are specified in the requirements.txt file in the root directory.

## Handling API Keys
Create a .env file in the root directory which contains the API keys to both Alpha Vantage 
& Finnhub. Name them as follows:
```
ALPHA_VANTAGE_API_KEY=""
FINNHUB_API_KEY=""
``` 

# Development Notes
I've documented my development process below. 

## Iteration 1

### Initial assumptions:
* Network is safe and doesn't fail.
* Server doesn't fail.
* There is only one client
* CLI arguments to both the server and client will be right.
* Any and all clients are started AFTER server.
* There is a global dataset maintained by the server - not one dataset per client.
* The frequency of data is specified once either in CLI or by first client request. This won't change after that.
* If a client requests for daa at some time which is not available (due to different frequencies), server will
  return the latest data available as of the time specified (that is, the last data point before this time).

### Inital design decisions:
* Given that the server doesn't fail (asusmption), we can store information (state) at the server
  to improve performance.
* I'm having the client register with the server. This is not needed for the specific set of assumptions in Iteration 1.
  However, doing so will help scale the solution later to where we might want to server different clients with different
  dtasets (i.e. one dataset per client).
* Whenever a client asks to create a new `report`, get all the data regarding the assets
  and calculate the returns, momentum signal, as well as the PnL.
* Whenever a client asks for `data`, do NOT query new data from DataGrabber. Work with the report.csv to find the 
  lastest data available. If no data exists, handle appropriately.
* When client wants to add ticker, and if the ticker doesn't already exist, information about that ticker is queried
  for the same date-range as the report.csv.
* When client wants to delete ticker, the ticker is deleted from report.csv.

### Advantages of this design:
* easy to implement.
* Only gets new data when needed.

### Disadvantages / Restrictions of this design:
* A lot of calculations will happen again and again -> inefficient. Can using caching to improve performance.
  Example, one client wants to remove a ticker while another client wants data for that ticker. If both of them
  keep requesting addition / deletion, we will have to recalclate data everytime.
* As of now, only the latest available data will be served by server. Will not be able to query data for more than a month ago.
