import matplotlib.pyplot as plt
import pandas as pd

class Portfolio(object):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def _plot_returns(self, portfolio):
        portfolio.plot()
        plt.savefig('images/returns.png')

    def generate_positions(self):
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        positions[self.symbol] = 100*self.signals['signal']
        return positions

    def backtest_portfolio(self):
        portfolio = self.positions.multiply(self.bars['Close'], axis=0)
        pos_diff = self.positions.diff()

        portfolio['holdings'] = (self.positions.multiply(self.bars['Close'], axis=0)).sum(axis=1)
        portfolio['cash'] = self.initial_capital - (pos_diff.multiply(self.bars['Close'], axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()
        self._plot_returns(portfolio)
        return portfolio

class MarketOnOpenPortfolio(Portfolio):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = initial_capital
        self.positions = self.generate_positions()

    def generate_positions(self):
        positions = pd.DataFrame(index=signals.index).fillna(0.0)
        ###
        return positions

    def backtest_portfolio(self):
        pass
