# Buy-side only MACD + RSI Logic WITH entry/exit-style rows saved to Excel
import pandas as pd
import numpy as np
import time
import os
import re

# --------- PATHS (edit these) ----------
file_path   = r"D:\Data\BR Jun25_15min.csv"
output_path = r"D:\trade logs\MACD and RSI\hg_copper_trades_30min.xlsx"

# Ensure directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# --------- LOAD ---------
df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# --------- PARAMETERS ---------
rsi_period     = 14
contract_size  = 0.01
num_of_lots    = 1
trade_cost     = 1.30

# --------- INDICATORS ---------
# RSI
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
rs = avg_gain / (avg_loss.replace(0, 1e-12))
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].round(2)

# MACD
ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
df['macd'] = ema_fast - ema_slow
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

# --------- BACKTEST STATE ---------
position = 0
Entry_price = Entry_time = Exit_price = Exit_time = None
Entry_idx = None

# Performance Metrics
total_pnl = total_long_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = num_of_trades = 0
max_profit = float('-inf')
max_loss = float('inf')
highest_equity = lowest_equity = max_drawdown = max_runup = 0.0
equity_curve = []

# This will store rows that mirror the print output
trade_log_rows = []

# --------- LOOP ---------
for i in range(26, len(df)):  # MACD slow EMA needs 26 bars
    try:
        close_today = df['Close'].iloc[i]
        date_time   = df['Date(GMT)'].iloc[i]
        high        = df['High'].iloc[i]
        low         = df['Low'].iloc[i]
        rsi         = df['rsi'].iloc[i]
        macd        = df['macd'].iloc[i]
        signal      = df['macd_signal'].iloc[i]

        # SHORT ENTRY
        if position == 0 and (macd < signal) and (rsi < 80):
            Entry_price = close_today
            Entry_time  = date_time
            Entry_idx   = i
            position = 1

            # Print
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time      : {Entry_time}")
            print(f" Entry Price     : {Entry_price}")
            print(f" MACD / Signal   : {macd:.2f} / {signal:.2f}")
            print(f" RSI             : {rsi}")
            print(f" High / Low      : {high} / {low}")
            print("================================\n")
            time.sleep(0.5)

            # Log row (ENTRY)
            trade_log_rows.append({
                "Type": "ENTRY",
                "Side": "Long",
                "Time": Entry_time,
                "Price": Entry_price,
                "MACD": macd,
                "Signal": signal,
                "RSI": rsi,
                "High": high,
                "Low": low,
                "P&L": np.nan,
                "Cum_PnL": np.nan,
                "Drawdown": np.nan,
                "Max_Drawdown": np.nan,
                "Runup": np.nan,
                "Max_Runup": np.nan,
                "Bars_Held": np.nan
            })

        # SHORT EXIT
        elif position == 1 and (macd > signal) and (rsi > 40):
            Exit_price = close_today
            Exit_time  = date_time
            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl
            equity_curve.append(total_pnl)

            max_profit = max(max_profit, pnl)
            max_loss   = min(max_loss, pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1

            highest_equity = max(highest_equity, total_pnl)
            lowest_equity  = min(lowest_equity, total_pnl)
            drawdown = highest_equity - total_pnl
            runup    = total_pnl - lowest_equity
            max_drawdown = max(max_drawdown, drawdown)
            max_runup    = max(max_runup, runup)

            # Print
            print("\033[1;31m========== SHORT EXIT =========\033[0m")
            print(f" Exit Time       : {Exit_time}")
            print(f" Exit Price      : {Exit_price}")
            print(f" MACD / Signal   : {macd:.2f} / {signal:.2f}")
            print(f" RSI             : {rsi}")
            print(f" High / Low      : {high} / {low}")
            print(f" Trade P&L       : {pnl:.2f}")
            print(f" Cumulative P&L  : {total_pnl:.2f}")
            print(f" Drawdown        : {drawdown:.2f}, Max Drawdown: {max_drawdown:.2f}")
            print(f" Run-up          : {runup:.2f}, Max Run-up: {max_runup:.2f}")
            print("================================\n")
            time.sleep(0.5)  # Simulate processing time

            # Log row (EXIT)
            trade_log_rows.append({
                "Type": "EXIT",
                "Side": "Long",
                "Time": Exit_time,
                "Price": Exit_price,
                "MACD": macd,
                "Signal": signal,
                "RSI": rsi,
                "High": high,
                "Low": low,
                "P&L": pnl,
                "Cum_PnL": total_pnl,
                "Drawdown": drawdown,
                "Max_Drawdown": max_drawdown,
                "Runup": runup,
                "Max_Runup": max_runup,
                "Bars_Held": i - Entry_idx if Entry_idx is not None else np.nan
            })

            position = 0
            Entry_price = Entry_time = Exit_price = Exit_time = None
            Entry_idx = None

    except Exception as e:
        print("Error:", e)

# --------- SUMMARY ---------
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

print(f"Max Profit per trade = \033[92m{max_profit:.2f}\033[0m")
print(f"  Max Loss per trade = \033[91m{max_loss:.2f}\033[0m")
print(f"        Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
print(f"        Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f"      Total Long PnL = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"               Gross = {total_pnl:.2f}")
print(f"          Trade Cost = {round(TradeCost, 2)}")
print(f"                 Net = {Net:.2f}")
print(f"        Max Drawdown = {max_drawdown:.2f}")
print(f"          Max Run-up = {max_runup:.2f}")
print(f"     Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"     Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"        Total Trades = {num_of_trades}")
print(f"        Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"        Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")

# --------- SAVE TO EXCEL ---------
if trade_log_rows:
    trades_df = pd.DataFrame(trade_log_rows)
    try:
        trades_df.to_excel(output_path, index=False)
        print(f"\nTrade log (entry & exit rows) saved to: {output_path}")
    except Exception as e:
        print(f"\nFailed to save trade log to Excel: {e}")
else:
    print("\nNo trades to save.")
