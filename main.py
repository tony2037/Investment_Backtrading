import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
import yfinance as yf
import math
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

# sma cross strategy
class SmaCross(bt.Strategy):
    # trade log
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    # arguments
    params = dict(
        ma_period_short=5,
        ma_period_long=10
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.ma_period_short)
        sma2 = bt.ind.SMA(period=self.p.ma_period_long)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

        # all in
        self.setsizer(sizer())

        # buy in with open price
        self.dataopen = self.datas[0].open

    def next(self):
        # empty
        if not self.position:
            if self.crossover > 0:
                # log trade date and price
                self.log('BUY ' + ', Price: ' + str(self.dataopen[0]))
                # use open price as target
                self.buy(price=self.dataopen[0])
        elif self.crossover < 0:
            # log trade date and price
            self.log('SELL ' + ', Price: ' + str(self.dataopen[0]))
            # open price as target
            self.close(price=self.dataopen[0])

class sizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            return math.floor(cash/data[1])
        else:
            return self.broker.getposition(data)

# get date from yahoo
data = bt.feeds.PandasData(dataname=yf.download('TSLA', '2018-01-01', '2019-01-01'))
"""
data = btfeeds.YahooFinanceData(dataname='SPY',
                                fromdate=datetime.datetime(2019, 1, 1),
                                todate=datetime.datetime(2019, 12, 31))
"""

cerebro = bt.Cerebro()
cerebro.adddata(data, name='0000')
cerebro.addstrategy(SmaCross)
cerebro.run()

b = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())
cerebro.plot(b)
