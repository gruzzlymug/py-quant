import configparser
import numpy as np
import pandas as pd
import requests
import json
import csv
import quandl as q
import matplotlib.pyplot as plt

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

def calculate_drawdown(stock_df):
    window = 252

    plt.clf()
    stock_df['Adj_Close'].plot()
    rolling_max = stock_df['Adj_Close'].rolling(window, min_periods=1).max()
    rolling_max.plot()
    # notebook formula for max dd
    dd = stock_df['Adj_Close']/rolling_max - 1
    (dd*100+10).plot()
    # investopedia formula
    # https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp
    mdd = (stock_df['Adj_Close'] - rolling_max) / rolling_max
    (mdd*100).plot()
    plt.savefig('images/dd.png')

config = configparser.ConfigParser()
config.read('data.ini')
iex_key = config['DEFAULT']['svc_key_iex']
quandl_api_key = config['DEFAULT']['svc_key_quandl_course']

#create_iex_csv(iex_key)
create_quandl_csv(quandl_api_key)

df = pd.read_csv('data/apple_stock_eod_prices.csv', index_col=0, header=0, parse_dates=True)
#print(df.head)
#print(df.index)
#print(df.columns)
#print(list(df.columns))
#print(df.info)
#print(df.loc[pd.Timestamp('2014-11-01'):pd.Timestamp('2014-12-31')].head())
#print(df.sample(20))

df['diff'] = df.Open - df.Close
#print(df['diff'])

daily_close = df[['Adj_Close']]
#daily_close.plot()
#plt.savefig('images/daily_close.png', bbox_inches='tight')
#print(daily_close)

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

# Moving Window Computation
adj_close_px = df['Adj_Close']
#df['x40'] = adj_close_px.ewm(com=5).mean()
df['max'] = adj_close_px.rolling(window=40).max()
df['40'] = adj_close_px.rolling(window=40).mean()
df['252'] = adj_close_px.rolling(window=252).mean()
min_periods = 75
df['vol'] = daily_pct_c.rolling(window=min_periods).std() * np.sqrt(min_periods) * 100
df[['Adj_Close', '40', '252', 'vol', 'max']].plot(grid=True)
plt.savefig('images/baz.png')

# Strategy
short_window = 40
long_window = 252

signals = pd.DataFrame(index=df.index)
signals['signal'] = 0.0
signals['short_mavg'] = df['Adj_Close'].rolling(window=short_window, min_periods=1, center=False).mean()
signals['long_mavg'] = df['Adj_Close'].rolling(window=long_window, min_periods=1, center=False).mean()
signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:]
        > signals['long_mavg'][short_window:], 1.0, 0.0)
signals['positions'] = signals['signal'].diff()
#signals.plot()
fig = plt.figure()
ax1 = fig.add_subplot(111, ylabel='Price in $')
df['Adj_Close'].plot(ax=ax1, color='k', lw=1.0)
signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.0, grid=True)
# buys
ax1.plot(signals.loc[signals.positions == 1.0].index,
        signals.short_mavg[signals.positions == 1.0],
        '^', markersize=10, color='g')
# sells
ax1.plot(signals.loc[signals.positions == -1.0].index,
        signals.short_mavg[signals.positions == -1.0],
        'v', markersize=10, color='r')

plt.savefig('images/sig2.png')

calculate_drawdown(df)

# Backtest the Strategy
capital = float(100000.0)
positions = pd.DataFrame(index=signals.index).fillna(0.0)
positions['AAPL'] = 100*signals['signal']
portfolio = positions.multiply(df['Adj_Close'], axis=0)
pos_diff = positions.diff()
portfolio['holdings'] = (positions.multiply(df['Adj_Close'], axis=0)).sum(axis=1)
portfolio['cash'] = capital - (pos_diff.multiply(df['Adj_Close'], axis=0)).sum(axis=1).cumsum()
portfolio['total'] = portfolio['cash'] + portfolio['holdings']
portfolio['returns'] = portfolio['total'].pct_change()
print(portfolio.tail(5))
portfolio.plot()
plt.savefig('images/returns.png')

# Sharpe Ratio (Annualized)
returns = portfolio['returns']
sharpe_ratio = np.sqrt(252) * (returns.mean() / returns.std())
print(sharpe_ratio)
