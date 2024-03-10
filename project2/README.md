# Project 2

## Data
You have been given the following data for two countries, United States and Canada. 

### United States 

Two tradeable assets (in asset prices.csv) 
* `ES1 Index`: Daily close price of S&P 500 Index Futures 
* `DXY Curncy`: US Dollar Index. Please treat this as a tradeable foreign exchange rate. It represents value of 1 US Dollar. The higher the value, the stronger US Dollar is relative to other currencies. 

Four economic data:
* `US GDP growth rate (%)` 
* `US Industrial Production` 
* `US Home Sales` 
* `US Unemployment Rate` 
 

### Canada 

Two tradeable assets (in asset prices.csv) 

* `PT 1 Index`: Daily close price of Toronto Stock Exchange Index Futures 
* `CADUSD Curncy`: Tradeable foreign exchange rate. Represents value of 1 Canadian Dollar. 

Four economic data:
* `Canada GDP growth rate (%)` 
* `Canada Industrial Production` 
* `Canada Home Sales` 
* `Canada Unemployment Rate` 

(* For the economic data, the data include both actual value and expected value. The actual values are the values released by government on the date listed in the file. The expected values represent market-expected (forecasted) value known prior to the release of the actual value. The expected value is the average of forecasts published by multiple independent forecasters and disseminated among the market participants some time (e.g., a few days – a couple of weeks) before the release date.) 

## Project Requirements
There are two parts to this project. 

### Part 1. 
Using the economic data, propose and implement an economic indicator that will be indicative of the growth and/or health of the respective economy and could be used as a basis for some trading strategies.  

Please use the notebook given. It has all the code to load the data, and a sample indicator. 

### Part 2. 
Create one or more trading signals using the indicator you created. Then, apply the trading signal to one or more tradeable assets to examine the profitability of your trading signal. 


## Other information
Generally, the growth and health of the country’s economy translates to the strength of the country’s stock market and the country’s currency. Thus, it may be possible to use your indicator as a trading signal for the stock and currency market. You could either use the indicator as-is (in which case your trading signal will be identical to your economic indicator, this is the example given in the notebook) or transform the indicator in some way to make it more suitable for trading.  

In the notebook given, we are proving the code you can use to apply your signal to the asset price data and calculate profit and loss of the trading signal. 

Your trading signal can be anything from a time-series signal (the signal for the country tells you when to buys/sells one or more assets for that country, without regards to other country), or cross-sectional signal (a signal to buy/sell Canadian assets based on US economic indicator)  

You don’t have to use all provided data to build this indicator and signal. You don’t have to use all past historical data. You don’t need to try to trade on all assets. We care primarily about your thought process, not the profitability of your trading signal. For example, your thought process could include 
* how you chose your indicators, 
* how you combined them together, etc. 
Please show 
* all your analysis, 
* investigative process, 
* assumptions you made and 
* the reasoning of choosing these indicators.  

Here are some questions that are designed to help you think about this problem. To be clear, we are not asking you to answer these questions in your submission. But thinking about these questions could guide your mind in the exploratory process. 

* Should you use the actual value or the expected value in building your indicator? Why? How about both? Why or why not? 
* How will you choose which assets to trade? 
* Do some assets perform better than others using your indicator? Why? 
* If your signal worked, why? 
* If your signal didn’t work, why? 
* If you trade more than one asset, is the performance dominated by one asset? If so, why? Is there any way to deal with that? 

