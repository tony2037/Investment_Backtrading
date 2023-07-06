import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
import yfinance as yf
import math
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

INIT_CASH = 1000000

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

class StableRatio(bt.Strategy):
    def __init__(self):
        self.etf = self.datas[0]
        self.target_ratio = 7 / 3

    def next(self):
        total_value = self.broker.getvalue() # the total portfolio value
        cash_value = self.broker.getcash()  # cash
        etf_position = self.broker.getposition(self.etf).size
        etf_value = self.etf.close[0] * etf_position # calcualte etf value
        ROI = (total_value - INIT_CASH) * 100 / INIT_CASH # unit: %
        date = self.etf.datetime.date(0)

        # calculate the ratio
        current_ratio = etf_value / cash_value if cash_value > 0 else 0

        if current_ratio < self.target_ratio:
            """
            buy in
            x + a / y - a = c
            cy - ca = x + a
            a = (cy - x) / (1 + c)
            """
            amount_to_buy = (self.target_ratio * cash_value - etf_value) / (1 + self.target_ratio)
            # FIXME: buy in with open price
            self.buy(self.etf, size=amount_to_buy / self.etf.close[0])
            print('Buy')

        elif current_ratio > self.target_ratio and etf_position > 0:
            """
            sell
            x - a / y + a = c
            cy + ca = x - a
            a = (x - cy) / (1 + c)
            """
            amount_to_sell = (etf_value - self.target_ratio * cash_value) / (1 + self.target_ratio)
            self.sell(self.etf, size=amount_to_sell / self.etf.open[0])
            print('SELL')

        print('[date:{}] Total: {}; Cash: {}; ROI: {:.2f}%'.format(date, total_value, cash_value, ROI))


# get date from yahoo
data = bt.feeds.PandasData(dataname=yf.download('0050.TW', '2018-01-01', '2023-01-01'))
"""
data = btfeeds.YahooFinanceData(dataname='etf',
                                fromdate=datetime.datetime(2019, 1, 1),
                                todate=datetime.datetime(2019, 12, 31))
"""

strategies = [SmaCross, StableRatio]
cerebro = bt.Cerebro()
cerebro.broker.setcash(INIT_CASH)
cerebro.adddata(data, name='0000')
cerebro.addstrategy(strategies[1])
cerebro.run()

b = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())
cerebro.plot(b)
