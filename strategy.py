import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class Strategy(object):
    def __init__(self, bars, short_window, long_window):
        self.bars = bars
        self.short_window = short_window
        self.long_window = long_window

    def _plot_signals(self, signals):
        plt.clf()
        fig = plt.figure(figsize=(12,8))
        ax1 = fig.add_subplot(111, ylabel='Price in $')
        self.bars['Close'].plot(ax=ax1, color='k', lw=1.0)
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.0, grid=True)
        # buys
        marker = '^'
        #marker = '|'
        ax1.plot(signals.loc[signals.positions == 1.0].index,
                signals.short_mavg[signals.positions == 1.0],
                marker, markersize=10, color='#00aa33')
        # sells
        marker = 'v'
        #marker = '|'
        ax1.plot(signals.loc[signals.positions == -1.0].index,
                signals.short_mavg[signals.positions == -1.0],
                marker, markersize=10, color='r')
        plt.savefig('images/signals.png', bbox_inches='tight')

    def generate_signals(self):
        """ This Bot's Strategy """

        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0
        signals['short_mavg'] = self.bars['Close'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = self.bars['Close'].rolling(window=self.long_window, min_periods=1, center=False).mean()
        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:]
                > signals['long_mavg'][self.short_window:], 1.0, 0.0)
        signals['positions'] = signals['signal'].diff()
        self._plot_signals(signals)
        return signals
