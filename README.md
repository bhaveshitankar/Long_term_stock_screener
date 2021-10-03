# Long_term_stock_screener

Run extract_indicators.py to get the bse, nse, sp500. investment indicators.

# set up needs :

1] clone the repo & open command where extract_indicators.py is present.

2] Run "pip install pandas, yahoo_fin, pandas_datareader, requests, urllib3, contextlib, warnings"

# outpu:

ScreenOutput_.xlsx -- contains stoks with more then 70% RS Value in 500 National Stock listed(NSE)

ScreenOutput_nse.xlsx -- contains stoks with more then 70% RS Value in Nifty50(NSE)

ScreenOutput_bse.xlsx -- contains stoks with more then 70% RS Value in 30 listings of Bombay Stock Exchange(BSE)

# Indicators avilable:

RS_Rating, 50 Days Moving avarage, 150 Days MA, 200 Day MA, 52 weeks High and 52 weeks Low

