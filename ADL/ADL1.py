import backtrader as bt
import pandas as pd

class ADLStrategy(bt.Strategy):
    params = (
        ('contract_size', 50),
        ('tick_value', 0.25),
    )
    
    def __init__(self):
        self.local_high = None
        self.local_low = None
        self.bull = False
        self.bear = False
        self.flag = False
        
    def next(self):
        current_high = self.data.high[0]
        current_low = self.data.low[0]
        
        # Define local high and low
        if not self.local_high or current_high > self.local_high:
            self.local_high = current_high
        if not self.local_low or current_low < self.local_low:
            self.local_low = current_low

        # Bullish Entry
        if current_high > self.local_high and not self.bear and not self.flag:
            self.buy(price=self.local_high + (self.p.tick_value * 2))
            self.bull = True
            self.flag = True

        # Bullish Exit
        elif current_low < self.local_low and self.bull and self.flag:
            self.close()
            self.bull = False
            self.flag = False
        
        # Bearish Entry
        elif current_low < self.local_low and not self.bull and not self.flag:
            self.sell(price=self.local_low - (self.p.tick_value * 2))
            self.bear = True
            self.flag = True

        # Bearish Exit
        elif current_high > self.local_high and self.bear and self.flag:
            self.close()
            self.bear = False
            self.flag = False

# Load Data
data = pd.read_csv("D:\\candles\\bt daily.csv", parse_dates=True, index_col='Date (GMT)')
data_feed = bt.feeds.PandasData(dataname=data)

# Initialize Backtest
cerebro = bt.Cerebro()
cerebro.addstrategy(ADLStrategy)
cerebro.adddata(data_feed)
cerebro.broker.set_cash(10000)
cerebro.broker.setcommission(commission=0.001)

# Run Backtest
cerebro.run()

# Plot Results
cerebro.plot()
