import matplotlib.pyplot as plt
import pandas as pd

class Portfolio(object):
    def __init__(self):
        pass

    def _plot_returns(self, portfolio):
        portfolio.plot()
        plt.savefig('images/returns.png')

    def backtest(self, bars, signals):
        """ Backtest the Strategy """
        capital = float(100000.0)
        positions = pd.DataFrame(index=signals.index).fillna(0.0)
        positions['AAPL'] = 100*signals['signal']
        portfolio = positions.multiply(bars['Close'], axis=0)
        pos_diff = positions.diff()
        portfolio['holdings'] = (positions.multiply(bars['Close'], axis=0)).sum(axis=1)
        portfolio['cash'] = capital - (pos_diff.multiply(bars['Close'], axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()
        self._plot_returns(portfolio)
        return portfolio

