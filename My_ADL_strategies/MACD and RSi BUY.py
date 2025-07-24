# Buy-side only MACD + RSI Logic
import pandas as pd
import time
import os
import re

file_path = r"C:\Users\lenovo\Downloads\ES 15min.csv"  # Update with your file path

# Load CSV
df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# Calculate RSI
rsi_period = 14
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
rs = avg_gain / avg_loss
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].round(2)

# Calculate MACD
ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
df['macd'] = ema_fast - ema_slow
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

# Backtest Logic
position = 0
Entry_price = Entry_time = Exit_price = Exit_time = 0
contract_size = 50  # ES contract size
num_of_lots = 1
trade_cost = 1.30

# Performance Metrics
total_pnl = total_long_pnl = 0
positive_pnl = negative_pnl = 0
total_positive_trades = total_negative_trades = num_of_trades = 0
max_profit = float('-inf')
max_loss = float('inf')
highest_equity = lowest_equity = max_drawdown = max_runup = 0
equity_curve = []

for i in range(26, len(df)):
    try:
        close_today = df['Close'].iloc[i]
        date_time = df['Date(GMT)'].iloc[i]
        high = df['High'].iloc[i]
        low = df['Low'].iloc[i]
        rsi = df['rsi'].iloc[i]
        macd = df['macd'].iloc[i]
        signal = df['macd_signal'].iloc[i]

        # LONG ENTRY
        if macd > signal and rsi < 40 and position == 0:
            Entry_price = close_today
            Entry_time = date_time
            position = 1    
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time      : {Entry_time}")
            print(f" Entry Price     : {Entry_price}")
            print(f" MACD            : {macd:.2f}")
            print(f" Signal Line     : {signal:.2f}")
            print(f" RSI             : {rsi}")
            print(f" High / Low      : {high} / {low}")
            print("================================\n")

        # LONG EXIT
        elif position == 1 and macd < signal and rsi > 70:
            Exit_price = close_today
            Exit_time = date_time
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl
            equity_curve.append(total_pnl)
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1
            highest_equity = max(highest_equity, total_pnl)
            lowest_equity = min(lowest_equity, total_pnl)
            drawdown = highest_equity - total_pnl
            runup = total_pnl - lowest_equity
            max_drawdown = max(max_drawdown, drawdown)
            max_runup = max(max_runup, runup)
            print("\033[1;32m========== LONG EXIT =========\033[0m")
            print(f" Exit Time       : {Exit_time}")
            print(f" Exit Price      : {Exit_price}")
            print(f" MACD            : {macd:.2f}")
            print(f" Signal Line     : {signal:.2f}")
            print(f" RSI             : {rsi}")
            print(f" High / Low      : {high} / {low}")
            print(f" Trade P&L       : {pnl}")
            print(f" Cumulative P&L  : {total_pnl}")
            print(f" Drawdown        : {drawdown}, Max Drawdown: {max_drawdown}")
            print(f" Run-up          : {runup}, Max Run-up: {max_runup}")
            print("================================\n")
            position = 0

    except Exception as e:
        print("Error:", e)

# Final Summary
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0

file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+\w+_(\d+min)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(2)
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} (Buy-side Only):\033[0m")
else:
    print("\n\033[1mTrading Performance Summary (Buy-side Only):\033[0m")

print(f"     Max Profit = \033[92m{max_profit}\033[0m")
print(f"       Max Loss = \033[91m{max_loss}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl}\033[0m")
print(f"          Gross = {total_pnl}")
print(f"     Trade Cost = {round(TradeCost,2)}")
print(f"            Net = {Net}")
print(f"   Max Drawdown = {max_drawdown}")
print(f"     Max Run-up = {max_runup}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")
