# Imports
from pandas_datareader import data as pdr
from yahoo_fin import stock_info as si
from pandas import ExcelWriter
import yfinance as yf
import pandas as pd
import datetime
from functools import partial
import common_utils
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

def update_data(tickers,stk=''):
    if stk == 'nse':
        f_name= r'data_nse\\'
    elif stk == 'bse':
        f_name = r'data_bse\\'
    else:
        f_name= r'temp\\'
    index_name = '^GSPC'
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    end_date = datetime.date.today()
    exportList = pd.DataFrame(columns=['Stock', "RS_Rating", "50 Day MA", "150 Day Ma", "200 Day MA", "52 Week Low", "52 week High"])
    # returns_multiples = []

    # Index Returns
    with common_utils.no_ssl_verification():
        index_df = pdr.get_data_yahoo(index_name, start_date, end_date)

    index_df['Percent Change'] = index_df['Adj Close'].pct_change()
    index_return = (index_df['Percent Change'] + 1).cumprod()[-1]

    # Find top 30% performing stocks (relative to the S&P 500)
    def data_maker(ticker,stk):
        global cnt, returns_multiples

        if stk == 'nse':
            tik_ext = '.NS'
            f_name= r'data_nse\\'
        elif stk == 'bse':
            tik_ext = '.BO'
            f_name = r'data_bse\\'
        else:
            tik_ext = ''
            f_name= r'temp\\'
        try:
            mutex.acquire()
            with common_utils.no_ssl_verification():
                df = pdr.get_data_yahoo(ticker+tik_ext, start_date, end_date)
            cnt = cnt+1
            print(cnt)
            mutex.release()
            df.to_csv(f'{f_name}{ticker}.csv')
            
            # Calculating returns relative to the market (returns multiple)
            df['Percent Change'] = df['Adj Close'].pct_change()
            stock_return = (df['Percent Change'] + 1).cumprod()[-1]
            
            returns_multiple = round((stock_return / index_return), 2)
            mutex.acquire()
            returns_multiples.extend([returns_multiple])
            mutex.release()
            print (f'Ticker: {ticker}; Returns Multiple against S&P 500: {returns_multiple}\n')
            # time.sleep(1)
        except:
            mutex.release()
            print(f"No data for {ticker}")

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(partial(data_maker, stk=stk),tickers)

    # Creating dataframe of only top 30%
    rs_df = pd.DataFrame(list(zip(tickers, returns_multiples)), columns=['Ticker', 'Returns_multiple'])
    rs_df['RS_Rating'] = rs_df.Returns_multiple.rank(pct=True) * 100
    rs_df = rs_df[rs_df.RS_Rating >= rs_df.RS_Rating.quantile(.70)]

    # Checking Minervini conditions of top 30% of stocks in given list
    rs_stocks = rs_df['Ticker']
    for stock in rs_stocks:    
        try:
            df = pd.read_csv(f'{f_name}{stock}.csv', index_col=0)
            sma = [50, 150, 200]
            for x in sma:
                df["SMA_"+str(x)] = round(df['Adj Close'].rolling(window=x).mean(), 2)
            
            # Storing required values 
            currentClose = df["Adj Close"][-1]
            moving_average_50 = df["SMA_50"][-1]
            moving_average_150 = df["SMA_150"][-1]
            moving_average_200 = df["SMA_200"][-1]
            low_of_52week = round(min(df["Low"][-260:]), 2)
            high_of_52week = round(max(df["High"][-260:]), 2)
            RS_Rating = round(rs_df[rs_df['Ticker']==stock].RS_Rating.tolist()[0])
            
            try:
                moving_average_200_20 = df["SMA_200"][-20]
            except Exception:
                moving_average_200_20 = 0

            # Condition 1: Current Price > 150 SMA and > 200 SMA
            condition_1 = currentClose > moving_average_150 > moving_average_200
            
            # Condition 2: 150 SMA and > 200 SMA
            condition_2 = moving_average_150 > moving_average_200

            # Condition 3: 200 SMA trending up for at least 1 month
            condition_3 = moving_average_200 > moving_average_200_20
            
            # Condition 4: 50 SMA> 150 SMA and 50 SMA> 200 SMA
            condition_4 = moving_average_50 > moving_average_150 > moving_average_200
            
            # Condition 5: Current Price > 50 SMA
            condition_5 = currentClose > moving_average_50
            
            # Condition 6: Current Price is at least 30% above 52 week low
            condition_6 = currentClose >= (1.3*low_of_52week)
            
            # Condition 7: Current Price is within 25% of 52 week high
            condition_7 = currentClose >= (.75*high_of_52week)
            
            # If all conditions above are true, add stock to exportList
            if(condition_1 and condition_2 and condition_3 and condition_4 and condition_5 and condition_6 and condition_7):
                exportList = exportList.append({'Stock': stock, "RS_Rating": RS_Rating ,"50 Day MA": moving_average_50, "150 Day Ma": moving_average_150, "200 Day MA": moving_average_200, "52 Week Low": low_of_52week, "52 week High": high_of_52week}, ignore_index=True)
                print (stock + " made the Minervini requirements")
        except Exception as e:
            print (e)
            print(f"Could not gather data on {stock}")

    exportList = exportList.sort_values(by='RS_Rating', ascending=False)
    print('\n', exportList)
    writer = ExcelWriter(f"ScreenOutput_{stk}.xlsx")
    exportList.to_excel(writer, "Sheet1")
    writer.save()

if __name__ == '__main__':
    mutex = Lock()
    yf.pdr_override()

    # Variables
    
    with common_utils.no_ssl_verification():
        tickers_ns = si.tickers_sp500(url='https://en.wikipedia.org/wiki/NIFTY_50')
        tickers_ns = [item.replace(".", "-") for item in tickers_ns]
        tickers_bo = si.tickers_sp500(url='https://en.wikipedia.org/wiki/List_of_BSE_SENSEX_companies',table_num=0)
        tickers_bo = [item.replace(".BO", "").replace('-BO','') for item in tickers_bo]
        tickers_sp500 = si.tickers_sp500(table_num=0)
        tickers_sp500 = [item.replace(".", "-") for item in tickers_sp500]

    cnt = 0
    returns_multiples = []
    update_data(tickers_ns,stk='nse')
    cnt = 0
    returns_multiples = []
    update_data(tickers_bo,stk='bse')
    cnt = 0
    returns_multiples = []
    update_data(tickers_sp500)