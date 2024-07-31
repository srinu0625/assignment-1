import backtrader as bt
import numpy as np

class CrudeOilStrategy(bt.Strategy):
    params = (
        ('ema_period', 21),
        ('sd_factor', 3.5),
        ('long_tp_factor', 3),
        ('long_sl_factor', 6),
        ('short_tp_factor', 3),
        ('short_sl_factor', 6),
    )

    def __init__(self):
        self.ema21 = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_period)
        self.deviation = self.data.close - self.ema21
        self.sd = bt.indicators.StandardDeviation(self.deviation, period=self.params.ema_period)
        self.usd = self.ema21 + (self.params.sd_factor * self.sd)
        self.lsd = self.ema21 - (self.params.sd_factor * self.sd)

    def next(self):
        if self.data.low[0] <= self.lsd[0]:
            long_tp = self.ema21[0] + (self.params.long_tp_factor * self.sd[0])
            long_sl = self.ema21[0] - (self.params.long_sl_factor * self.sd[0])
            self.buy_bracket(limitprice=long_tp, stopprice=long_sl)
        
        if self.data.close[0] >= self.usd[0]:
            short_tp = self.ema21[0] - (self.params.short_tp_factor * self.sd[0])
            short_sl = self.ema21[0] + (self.params.short_sl_factor * self.sd[0])
            self.sell_bracket(limitprice=short_tp, stopprice=short_sl)

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CrudeOilStrategy)
    
    # Add your data feed here
    data = bt.feeds.YahooFinanceData(dataname='CL=F', fromdate=datetime(2020, 1, 1), todate=datetime(2021, 1, 1))
    cerebro.adddata(data)
    
    cerebro.run()
    cerebro.plot()
