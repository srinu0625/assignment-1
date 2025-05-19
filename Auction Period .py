import pandas as pd
import os
import re

# File path
file_path = r"C:\Users\lenovo\Desktop\Data\BR Jun25_30min.csv"

# Load data
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    exit()

# Constants
tick_size = 0.05  # Change this according to the instrument
contract_size = 5
num_of_lots = 1
trade_cost = 1.30

# State variables
position = 0
entry_price = Entry_time = 0
total_pnl = 0
trade_list = []
positive_trades = negative_trades = num_of_trades = 0
max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = negative_pnl = 0
total_long_pnl = total_short_pnl = 0
total_positive_trades = total_negative_trades = 0
cumulative_pnl_curve = []
max_drawdown = 0
max_runup = 0

# Loop
for i in range(1, len(df)):
    try:
        row = df.iloc[i]
        prev_close = df['Close'].iloc[i - 1]
        ltp = row['Close']
        ask_qty = row['Ask Quantity']
        bid_qty = row['Bid Quantity']
        date = row['Date(GMT)']

        # Long Entry
        if position == 0 and (ltp > prev_close + 10 * tick_size) and (ask_qty > 100):
            entry_price = ltp
            Entry_time = date
            position = 1
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time  : {Entry_time}")
            print(f" Entry Price : {entry_price:.2f}")
            print("================================\n")

        # Long Exit
        elif position == 1:
            if (ltp >= entry_price + 10 * tick_size) or \
               (ltp <= entry_price - 4 * tick_size) or \
               (bid_qty < 50):
                exit_price = ltp
                pnl = (exit_price - entry_price) * contract_size * num_of_lots - trade_cost
                total_pnl += pnl
                trade_list.append(pnl)
                num_of_trades += 1
                positive_trades += pnl > 0
                negative_trades += pnl <= 0
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
                print(f" Exit Price  : {exit_price:.2f}")
                print(f" Trade P&L   : {pnl:.2f}")
                print(f" Cumulative P&L : {total_pnl:.2f}")
                print("================================\n")

        # Short Entry
        if position == 0 and (ltp < prev_close - 10 * tick_size) and (bid_qty > 100):
            entry_price = ltp
            Entry_time = date
            position = -1
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time  : {Entry_time}")
            print(f" Entry Price : {entry_price:.2f}")
            print("================================\n")

        # Short Exit
        elif position == -1:
            if (ltp <= entry_price - 10 * tick_size) or \
               (ltp >= entry_price + 4 * tick_size) or \
               (ask_qty < 50):
                exit_price = ltp
                pnl = (entry_price - exit_price) * contract_size * num_of_lots - trade_cost
                total_pnl += pnl
                trade_list.append(pnl)
                num_of_trades += 1
                positive_trades += pnl > 0
                negative_trades += pnl <= 0
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
                print(f" Exit Price  : {exit_price:.2f}")
                print(f" Trade P&L   : {pnl:.2f}")
                print(f" Cumulative P&L : {total_pnl:.2f}")
                print("================================\n")

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
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} Auction Logic:\033[0m")
else:
    print("\n\033[1mTrading Performance Summary:\033[0m")

# Final Output
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
