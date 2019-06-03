import configparser
import numpy as np
import pandas as pd
import requests
import json
import csv
import quandl as q
import matplotlib.pyplot as plt

from portfolio import Portfolio
from strategy import Strategy

def write_json_to_file(text, filename):
    text_file = open(filename, "w")
    text_file.write(text)
    text_file.close()

def convert_json_to_csv(json_filename, csv_filename):
    text_file = open(json_filename, "r")
    contents = text_file.read()
    text_file.close()
    parsed_json = json.loads(contents)
    data_file = open(csv_filename, "w")
    csv_writer = csv.writer(data_file)
    count = 0
    for row in parsed_json:
        if count == 0:
            header = row.keys()
            csv_writer.writerow(header)
            count += 1
        csv_writer.writerow(row.values())
    data_file.close()

def create_quandl_csv(api_key):
    q.ApiConfig.api_key = api_key
    apple_data = q.get("EOD/AAPL", start_date="2012-01-01", end_date="2019-12-31")
    apple_data.to_csv('./data/apple_stock_eod_prices.csv', index=True)

def create_iex_csv(iex_token):
    #url = f'https://cloud.iexapis.com/stable/stock/aapl/batch?types=quote,chart&range=5y&token={iex_token}'
    url = f"https://cloud.iexapis.com/stable/stock/aapl/chart/5y?token={iex_token}"
    response = requests.get(url)
    if response.status_code == 200:
        write_json_to_file(response.text, "data/aapl.txt")
        convert_json_to_csv("data/aapl.txt", "data/aapl.csv")
    else:
        print("failed: " + response.status_code)

def read_stock_data(filename):
    df = pd.read_csv(filename, index_col=0, header=0, parse_dates=True)
    #print(df.head)
    #print(df.index)
    #print(df.columns)
    #print(list(df.columns))
    #print(df.info)
    #print(df.loc[pd.Timestamp('2014-11-01'):pd.Timestamp('2014-12-31')].head())
    #print(df.sample(20))
    return df

def plot_crossover(short, long, adj_close_px):
    plt.clf()
    short_label = f'Short ({short})'
    long_label = f'Long ({long})'
    df[short_label] = adj_close_px.rolling(window=short).mean()
    df[long_label] = adj_close_px.rolling(window=long).mean()
    min_periods = 75
    df[['Adj_Close', short_label, long_label]].plot(grid=True)
    plt.savefig('images/crossover.png', bbox_inches='tight')

def calculate_drawdown(stock_df):
    window = 252

    plt.clf()
    stock_df['Adj_Close'].plot()
    rolling_max = stock_df['Adj_Close'].rolling(window, min_periods=1).max()
    rolling_max.plot()
    # notebook formula for max dd
    dd = stock_df['Adj_Close']/rolling_max - 1
    # multiply by 100 so it shows up in graph
    (dd*100).plot(grid=True)
    # investopedia formula
    # https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp
    #mdd = (stock_df['Adj_Close'] - rolling_max) / rolling_max
    #(mdd*100).plot()
    plt.savefig('images/drawdown.png', bbox_inches='tight')

def plot_volatility(df, daily_pct_c):
    min_periods = 75
    plt.clf()
    df['vol'] = daily_pct_c.rolling(window=min_periods).std() * np.sqrt(min_periods)
    df[['vol']].plot(grid=True)
    plt.savefig('images/vol.png', bbox_inches='tight')


config = configparser.ConfigParser()
config.read('data.ini')
iex_key = config['DEFAULT']['svc_key_iex']
quandl_api_key = config['DEFAULT']['svc_key_quandl_course']

#create_iex_csv(iex_key)
#create_quandl_csv(quandl_api_key)

df = read_stock_data('data/apple_stock_eod_prices.csv')

df['diff'] = df.Open - df.Close
#print(df['diff'])

daily_close = df[['Adj_Close']]
daily_pct_c = daily_close.pct_change()
daily_pct_c.fillna(0, inplace=True)
print(daily_pct_c.head())
#print(df.loc['2016-07'])
#print(df.iloc[20:43])
#print(df.describe())
cum_daily_return = (daily_pct_c+1).cumprod()
print(cum_daily_return.head())
cum_daily_return.plot(figsize=(12,8),grid=True)
plt.savefig('images/cum_dly_ret.png', bbox_inches='tight')
cum_monthly_return = cum_daily_return.resample("M").mean()

plot_volatility(df, daily_pct_c)

# Moving Window Computation
short_window = 30
long_window = 252

adj_close_px = df['Adj_Close']
#df['x40'] = adj_close_px.ewm(com=5).mean()
#df['max'] = adj_close_px.rolling(window=40).max()
plot_crossover(short_window, long_window, adj_close_px)

bars = pd.DataFrame(index=df.index)
bars['Close'] = df['Adj_Close']
strategy = Strategy(bars, short_window, long_window)
signals = strategy.generate_signals()

pp = Portfolio()
portfolio = pp.backtest(bars, signals)

#portfolio = backtest(signals, df)
print(portfolio[short_window:short_window+5:])
print(portfolio.tail(5))

# RISK ASSESSMENT METRICS
# 1. Sharpe Ratio (Annualized)
returns = portfolio['returns']
sharpe_ratio = np.sqrt(252) * (returns.mean() / returns.std())
print(f"{'Sharpe Ratio:':<14} {sharpe_ratio:>12}")

# 2. Maximum Drawdown
calculate_drawdown(df)

# 3. Compound Annual Growth Rate
days = (df.index[-1] - df.index[0]).days
cagr = ((((df['Adj_Close'][-1]) / df['Adj_Close'][1])) ** (365.0/days)) - 1
print(f"{'CAGR:':<14} {cagr:>12}")
