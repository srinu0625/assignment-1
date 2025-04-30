import pandas as pd
import os
import re
import time

# File Path
file_path = r"C:\Users\lenovo\Desktop\Data\ES Jun25_daily.csv"

# Load Data
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    exit()

# Column Definitions
high_column_name = 'High'
low_column_name = 'Low'
close_column_name = 'Close'
time_column_name = 'Date(GMT)'

# Indicator Calculations
df['Previous_Close'] = df[close_column_name].shift(1)
df['High-Low'] = df[high_column_name] - df[low_column_name]
df['High-PC'] = abs(df[high_column_name] - df['Previous_Close'])
df['Low-PC'] = abs(df[low_column_name] - df['Previous_Close'])
df['TR'] = df[['High-Low', 'High-PC', 'Low-PC']].max(axis=1)
df['ATR_3'] = df['TR'].rolling(window=3).mean()
df['2DH'] = df[high_column_name].rolling(window=2).max()
df['2DL'] = df[low_column_name].rolling(window=2).min()

# Strategy Parameters
contract_size = 5
num_of_lots = 1
trade_cost = 1.30
stop_loss_atr = 1.0
take_profit_atr = 2.0

# Trade State Tracking
position = 0
entry_price = Entry_time = 0
total_pnl = 0
trade_list = []
positive_trades = negative_trades = num_of_trades = 0

# Additional Metrics
max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = negative_pnl = 0
total_long_pnl = total_short_pnl = 0
total_positive_trades = total_negative_trades = 0
cumulative_pnl_curve = []
max_drawdown = 0
max_runup = 0

# Backtest Loop
for i in range(5, len(df)):
    try:
        Close = df[close_column_name].iloc[i]
        High = df[high_column_name].iloc[i]
        Low = df[low_column_name].iloc[i]
        date = df[time_column_name].iloc[i]

        atr = df['ATR_3'].iloc[i]
        two_DH = df['2DH'].iloc[i]
        two_DL = df['2DL'].iloc[i]

        buy_rate = two_DH + 0.1 * atr
        sell_rate = two_DH - 0.1 * atr

        # 🔹 Print candle data and indicators
        print(f"{date} | High: {High:.2f}, Low: {Low:.2f}, Close: {Close:.2f}")
        print(f"ATR: {atr:.2f}, 2DH: {two_DH:.2f}, 2DL: {two_DL:.2f}")
        print(f"Buy Rate: {buy_rate:.2f}, Sell Rate: {sell_rate:.2f}")
        print("-" * 50)
        time.sleep(0.5)

        # Long Entry
        if position == 0 and Close > buy_rate:
            entry_price = Close
            Entry_time = date
            position = 1
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time  : {Entry_time}")
            print(f" Entry Price : {entry_price}")
            print("================================\n")
            time.sleep(0.5)

        # Long Exit
        elif position == 1:
            stop_loss = entry_price - stop_loss_atr * atr
            take_profit = entry_price + take_profit_atr * atr
            if Close <= stop_loss or Close < sell_rate or Close >= take_profit:
                exit_price = Close
                pnl = (exit_price - entry_price) * contract_size * num_of_lots - trade_cost
                total_pnl += pnl
                trade_list.append(pnl)
                num_of_trades += 1
                positive_trades += pnl > 0
                negative_trades += pnl <= 0

                # Metrics
                max_profit = max(max_profit, pnl)
                max_loss = min(max_loss, pnl)
                total_long_pnl += pnl
                if pnl > 0:
                    positive_pnl += pnl
                    total_positive_trades += 1
                else:
                    negative_pnl += pnl
                    total_negative_trades += 1

                cumulative_pnl_curve.append(total_pnl)
                if len(cumulative_pnl_curve) > 1:
                    peak = max(cumulative_pnl_curve[:-1])
                    max_drawdown = min(max_drawdown, total_pnl - peak)
                    trough = min(cumulative_pnl_curve[:-1])
                    max_runup = max(max_runup, total_pnl - trough)

                position = 0
                print("\033[1;32m========== LONG EXIT =========\033[0m")
                print(f" Exit Time   : {date}")
                print(f" Exit Price  : {exit_price}")
                print(f" Trade P&L   : {pnl:.2f}")
                print(f" Cumulative P&L : {total_pnl:.2f}")
                print("================================\n")
                time.sleep(0.5)

        # Short Entry
        if position == 0 and Close < sell_rate:
            entry_price = Close
            Entry_time = date
            position = -1
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time  : {Entry_time}")
            print(f" Entry Price : {entry_price}")
            print("================================\n")
            time.sleep(0.5)

        # Short Exit
        elif position == -1:
            stop_loss = entry_price + stop_loss_atr * atr
            take_profit = entry_price - take_profit_atr * atr
            if Close >= stop_loss or Close > buy_rate or Close <= take_profit:
                exit_price = Close
                pnl = (entry_price - exit_price) * contract_size * num_of_lots - trade_cost
                total_pnl += pnl
                trade_list.append(pnl)
                num_of_trades += 1
                positive_trades += pnl > 0
                negative_trades += pnl <= 0

                # Metrics
                max_profit = max(max_profit, pnl)
                max_loss = min(max_loss, pnl)
                total_short_pnl += pnl
                if pnl > 0:
                    positive_pnl += pnl
                    total_positive_trades += 1
                else:
                    negative_pnl += pnl
                    total_negative_trades += 1

                cumulative_pnl_curve.append(total_pnl)
                if len(cumulative_pnl_curve) > 1:
                    peak = max(cumulative_pnl_curve[:-1])
                    max_drawdown = min(max_drawdown, total_pnl - peak)
                    trough = min(cumulative_pnl_curve[:-1])
                    max_runup = max(max_runup, total_pnl - trough)

                position = 0
                print("\033[1;31m========== SHORT EXIT =========\033[0m")
                print(f" Exit Time   : {date}")
                print(f" Exit Price  : {exit_price}")
                print(f" Trade P&L   : {pnl:.2f}")
                print(f" Cumulative P&L : {total_pnl:.2f}")
                print("================================\n")
                time.sleep(0.5)

    except Exception as e:
        print(f"Error at index {i}: {e}")

# Summary Metrics
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

# File Meta Info
file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+\w+_(\d+min)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(2)
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} ATR Breakout:\033[0m")
else:
    print("\n\033[1mTrading Performance Summary:\033[0m")

# Final Summary Output
print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl:.2f}\033[0m")
print(f"          Gross = {total_pnl:.2f}")
print(f"     Trade Cost = {TradeCost:.2f}")
print(f"            Net = {Net:.2f}")
print(f"   Max Drawdown = \033[91m{max_drawdown:.2f}\033[0m")
print(f"     Max Run-up = \033[92m{max_runup:.2f}\033[0m")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")
