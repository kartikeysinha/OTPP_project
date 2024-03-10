# Project 1 description

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

### Inital design decisions:
* Given that the server doesn't fail (asusmption), we can store information (state) at the server
  to improve performance.
* Let the server maintain the list of assets that the client wants.
* Whenever a client asks to create a new `report`, get all the data regarding the assets
  and calculate the returns, momentum signal, as well as the PnL.

### Advantages of this design:
* easy to implement.
* Only gets new data when needed.

### Disadvantage of this design:
* A lot of calculations will happen again and again -> inefficient.
