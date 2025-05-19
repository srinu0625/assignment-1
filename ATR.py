import time
import pandas as pd
import os

# Load CSV
file_path = r"D:\Data\ES Jun25_Daily.csv"
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    exit()

# Columns
high_col = 'High'
low_col = 'Low'
close_col = 'Close'
date_col = 'Date(GMT)'
window = 3

# Indicators
df['Prev_Close'] = df[close_col].shift(1)
df['High_Low'] = df[high_col] - df[low_col]
df['High_PC'] = abs(df[high_col] - df['Prev_Close'])
df['Low_PC'] = abs(df[low_col] - df['Prev_Close'])
df['TR'] = df[['High_Low', 'High_PC', 'Low_PC']].max(axis=1)
df['ATR_5'] = df['TR'].rolling(window).mean()
df['2DH'] = df[high_col].rolling(window).max().shift(1)
df['2DL'] = df[low_col].rolling(window).min().shift(1)

# Strategy Settings
contract_size = 50
lots = 1
trade_cost = 1.30
points = 1.5

# State Tracking
position = 0
entry_price = 0
entry_time = ''
total_pnl = 0
trade_list = []
positive_trades = negative_trades = total_trades = 0
positive_pnl = negative_pnl = 0
total_long_pnl = total_short_pnl = 0
max_profit = float('-inf')
max_loss = float('inf')
cumulative_pnl = []
max_drawdown = max_runup = 0

# Backtest Loop
for i in range(window, len(df)):
    try:
        date = df[date_col].iloc[i]
        close = df[close_col].iloc[i]
        high = df[high_col].iloc[i]
        low = df[low_col].iloc[i]
        atr = df['ATR_5'].iloc[i]
        two_dh = df['2DH'].iloc[i]
        two_dl = df['2DL'].iloc[i]

        # Skip if indicator values are NaN
        if pd.isna(atr) or pd.isna(two_dh) or pd.isna(two_dl):
            continue

        buy_rate = two_dh + points * atr
        sell_rate = two_dl - points * atr

        print(f"{date} | High: {high:.2f}, Low: {low:.2f}, Close: {close:.2f}")
        print(f"ATR: {atr:.2f}, 2DH: {two_dh:.2f}, 2DL: {two_dl:.2f}")
        print(f"Buy Rate: {buy_rate:.2f}, Sell Rate: {sell_rate:.2f}")
        print("-" * 60)
        # time.sleep(1)

        # Long Entry (Breakout above 2DH + buffer)
        if position == 0 and high > buy_rate:
            entry_price = close
            entry_time = date
            position = 1
            print(f"\n\033[1;32m[LONG ENTRY]\033[0m")
            print(f"Date        : {entry_time}")
            print(f"Entry Price : {entry_price:.2f}")
            print("=====================================")
            time.sleep(1)


        # Long Exit (Breakdown below 2DL - buffer)
        elif position == 1 and low < sell_rate:
            exit_price = close
            pnl = (exit_price - entry_price) * contract_size * lots - trade_cost
            total_pnl += pnl
            position = 0

            trade_list.append(pnl)
            total_trades += 1
            if pnl > 0:
                positive_trades += 1
                positive_pnl += pnl
                total_long_pnl += pnl
            else:
                negative_trades += 1
                negative_pnl += pnl
                total_long_pnl += pnl

            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            cumulative_pnl.append(total_pnl)

            if len(cumulative_pnl) > 1:
                peak = max(cumulative_pnl[:-1])
                trough = min(cumulative_pnl[:-1])
                max_drawdown = min(max_drawdown, total_pnl - peak)
                max_runup = max(max_runup, total_pnl - trough)

            print(f"\n\033[1;32m[LONG EXIT]\033[0m")
            print(f"Date        : {date}")
            print(f"Exit Price  : {exit_price:.2f}")
            print(f"PnL         : {pnl:.2f}")
            print(f"Cumulative  : {total_pnl:.2f}")
            print("=====================================")
            # time.sleep(1)


        # Short Entry (Breakdown below 2DL - buffer)
        if position == 0 and low < sell_rate:
            entry_price = close
            entry_time = date
            position = -1
            print(f"\033[1;31m[SHORT ENTRY]\033[0m")
            print(f"Date        : {entry_time}")
            print(f"Entry Price : {entry_price:.2f}")
            print("=====================================")
            # time.sleep(1)

        # Short Exit (Reversal above 2DH + buffer)
        elif position == -1 and high > buy_rate:
            exit_price = close
            pnl = (entry_price - exit_price) * contract_size * lots - trade_cost
            total_pnl += pnl
            position = 0

            trade_list.append(pnl)
            total_trades += 1
            if pnl > 0:
                positive_trades += 1
                positive_pnl += pnl
                total_short_pnl += pnl
            else:
                negative_trades += 1
                negative_pnl += pnl
                total_short_pnl += pnl

            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            cumulative_pnl.append(total_pnl)

            if len(cumulative_pnl) > 1:
                peak = max(cumulative_pnl[:-1])
                trough = min(cumulative_pnl[:-1])
                max_drawdown = min(max_drawdown, total_pnl - peak)
                max_runup = max(max_runup, total_pnl - trough)

            print(f"\033[1;31m[SHORT EXIT]\033[0m")
            print(f"Date        : {date}")
            print(f"Entry Price : {exit_price:.2f}")
            print(f"PnL         : {pnl:.2f}")
            print(f"Cumulative  : {total_pnl:.2f}")
            print("=====================================")
            # time.sleep(1)

    except Exception as e:
        print(f"Error on index {i}: {e}")

# Summary
success_rate = (positive_trades / total_trades) * 100 if total_trades else 0
failure_rate = (negative_trades / total_trades) * 100 if total_trades else 0

# Clean file name parsing
file_name = os.path.basename(file_path)
product = os.path.splitext(file_name)[0].replace("_", " ")

print(f"\n\033[1mPerformance Summary for {product} ATR Breakout:\033[0m")
print(f"     Max Profit  = \033[92m{max_profit:.2f}\033[0m")
print(f"      Max Loss   = \033[91m{max_loss:.2f}\033[0m")
print(f" Positive PnL    = \033[92m{positive_pnl:.2f}\033[0m")
print(f" Negative PnL    = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL  = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL  = \033[94m{total_short_pnl:.2f}\033[0m")
print(f"        Net PnL  = {total_pnl:.2f}")
print(f" Max Drawdown    = \033[91m{max_drawdown:.2f}\033[0m")
print(f"   Max Run-up    = \033[92m{max_runup:.2f}\033[0m")
print(f"  Total Trades   = {total_trades}")
print(f"Success Rate     = \033[92m{success_rate:.2f}%\033[0m")
print(f"Failure Rate     = \033[91m{failure_rate:.2f}%\033[0m")
# time.sleep(1)
