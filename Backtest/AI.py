import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import resample_apply
import numpy as np

# Load and prepare data (replace with correct file paths)
file_path1 = r"D:\data\es 240.csv"  # 240-min data
file_path2 = r"D:\data\es d.csv"    # Daily data

data1 = pd.read_csv(file_path1, parse_dates=True, index_col=0)
data2 = pd.read_csv(file_path2, parse_dates=True, index_col=0)

# Ensure data columns match expectations
data1.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
data2.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

class CustomHighLowStrategy(Strategy):
    risk = 720  # Max risk per trade
    max_num_lots = 20
    contract_size = 5
    tick_val = 0.25
    
    def init(self):
        # Store high and low series for easier access
        self.high = self.data.High
        self.low = self.data.Low

        # Daily resampling for comparison
        self.daily_high = resample_apply('D', np.max, self.data.High)
        self.daily_low = resample_apply('D', np.min, self.data.Low)

    def next(self):
        price = self.data.Close[-1]
        
        # Calculate local high and low based on rolling window
        local_high = self.high[-5:].max()
        local_low = self.low[-5:].min()

        # Entry logic (example)
        if price > local_high and not self.position:
            risk_per_trade = abs(local_high - local_low) * self.contract_size
            num_of_lots = min(self.risk // risk_per_trade, self.max_num_lots)
            
            # Entry with calculated risk and stop-loss
            self.buy(size=num_of_lots, sl=local_low)
        
        # Exit logic (example)
        if self.position and price < local_low:
            self.position.close()

# Run the backtest
bt = Backtest(data1, CustomHighLowStrategy, cash=10_000, commission=0.002)
results = bt.run()

# Print results and plot
print(results)
bt.plot()
