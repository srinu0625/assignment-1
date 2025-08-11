import pandas as pd
import time
import os
import re

# === Load Data ===
file_path = r"D:\Data\NQ_1min.csv"  # CHANGE THIS TO YOUR FILE PATH

try:
    df = pd.read_csv(file_path)
except Exception as e:
    raise RuntimeError(f"Error loading data: {e}")

# === Parameters ===
ema_period = 20
bb_period = 20
rsi_period = 14
contract_size = 1000
num_of_lots = 1
trade_cost = 1.30

# === Indicators ===
df['ema'] = df['Close'].rolling(window=ema_period).mean()
multiplier = 2 / (ema_period + 1)

delta = df['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.ewm(alpha=1 / rsi_period, min_periods=rsi_period).mean()
avg_loss = loss.ewm(alpha=1 / rsi_period, min_periods=rsi_period).mean()
rs = avg_gain / avg_loss
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].round(2)

df['rsi_pct_change_5d'] = df['rsi'].pct_change(periods=5) * 100
df['rsi_pct_change_5d'] = df['rsi_pct_change_5d'].round(2)

df['sma'] = df['Close'].rolling(window=bb_period).mean()
df['stddev'] = df['Close'].rolling(window=bb_period).std()
df['bb_upper'] = df['sma'] + (2 * df['stddev'])
df['bb_lower'] = df['sma'] - (2 * df['stddev'])

# === Strategy Vars ===
position = 0
Entry_price = Exit_price = Entry_time = Exit_time = 0
total_pnl = total_long_pnl = total_short_pnl = 0
positive_pnl = negative_pnl = 0
total_positive_trades = total_negative_trades = num_of_trades = 0
equity_curve = []
highest_equity = 0
lowest_equity = 0
max_drawdown = 0
max_runup = 0

# === Strategy Logic Loop ===
for i in range(max(ema_period, rsi_period, 5, bb_period), len(df)):
    try:
        Close = df['Close'].iloc[i]
        ema_yesterday = df['ema'].iloc[i - 1]
        ema = (Close * multiplier) + (ema_yesterday * (1 - multiplier))
        df.at[i, 'ema'] = ema
        ema = round(ema, 2)
        rsi = df['rsi'].iloc[i]
        rsi_pct = df['rsi_pct_change_5d'].iloc[i]
        date_time = df['Date(GMT)'].iloc[i]
        bb_upper = df['bb_upper'].iloc[i]
        bb_lower = df['bb_lower'].iloc[i]
        bb_median = df['sma'].iloc[i]

        if pd.isna(bb_upper) or pd.isna(bb_lower) or pd.isna(bb_median):
            continue

        # === LONG ENTRY ===
        if (Close > ema and rsi > 55 and rsi_pct > 10 and Close > bb_lower and position == 0):
            Entry_price = Close
            Entry_time = date_time
            position = 1
            print(f"\n\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Date & Time      : {Entry_time}")
            print(f" Entry Price      : {Entry_price}")
            print(f" EMA20            : {ema}")
            print(f" RSI (14)         : {rsi}")
            print(f" RSI% (5 candles) : {rsi_pct:.2f}%")
            print(f" BB Lower (20)    : {bb_lower}")
            print(f" Close Price      : {Close}")
            print(" Entry Conditions Met: Close > EMA20 AND RSI > 55 AND RSI% > 10 AND Close > BB Lower")
            print("=============================================")
            time.sleep(1)  # Simulate delay for real-time trading
        # === LONG EXIT ===
        elif position == 1 and (Close < ema or rsi < 50 or rsi_pct < 0 or Close < bb_median):
            Exit_price = Close
            Exit_time = date_time
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl
            equity_curve.append(total_pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1
            position = 0
            print(f"\n\033[1;32m========== LONG EXIT =========\033[0m")
            print(f" Date & Time      : {Exit_time}")
            print(f" Exit Price       : {Exit_price}")
            print(f" EMA20            : {ema}")
            print(f" RSI (14)         : {rsi}")
            print(f" RSI% (5 candles) : {rsi_pct:.2f}%")
            print(f" BB Median (20)   : {bb_median}")
            print(f" Close Price      : {Close}")
            print(f" Trade PnL        : {pnl:.2f}")
            print(" Exit Conditions Met: Close < EMA20 OR RSI < 50 OR RSI% < 0 OR Close < BB Mid")
            print("=============================================")
            time.sleep(1)  # Simulate delay for real-time trading

        # === SHORT ENTRY ===
        elif (Close < ema and rsi < 45 and rsi_pct < -10 and Close < bb_upper and position == 0):
            Entry_price = Close
            Entry_time = date_time
            position = 2
            print(f"\n\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Date & Time      : {Entry_time}")
            print(f" Entry Price      : {Entry_price}")
            print(f" EMA20            : {ema}")
            print(f" RSI (14)         : {rsi}")
            print(f" RSI% (5 candles) : {rsi_pct:.2f}%")
            print(f" BB Upper (20)    : {bb_upper}")
            print(f" Close Price      : {Close}")
            print(" Entry Conditions Met: Close < EMA20 AND RSI < 45 AND RSI% < -10 AND Close < BB Upper")
            print("=============================================")
            time.sleep(1)  # Simulate delay for real-time trading

        # === SHORT EXIT ===
        elif position == 2 and (Close > ema or rsi > 50 or rsi_pct > 0 or Close > bb_median):
            Exit_price = Close
            Exit_time = date_time
            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_short_pnl += pnl
            equity_curve.append(total_pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1
            position = 0
            print(f"\n\033[1;31m========== SHORT EXIT =========\033[0m")
            print(f" Date & Time      : {Exit_time}")
            print(f" Exit Price       : {Exit_price}")
            print(f" EMA20            : {ema}")
            print(f" RSI (14)         : {rsi}")
            print(f" RSI% (5 candles) : {rsi_pct:.2f}%")
            print(f" BB Median (20)   : {bb_median}")
            print(f" Close Price      : {Close}")
            print(f" Trade PnL        : {pnl:.2f}")
            print(" Exit Conditions Met: Close > EMA20 OR RSI > 50 OR RSI% > 0 OR Close > BB Mid")
            print("=============================================")
            time.sleep(1)  # Simulate delay for real-time trading

    except Exception as e:
        print("Error:", e)

# === Final Summary ===
Net = total_pnl - num_of_trades * trade_cost
TradeCost = num_of_trades * trade_cost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0

file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+(\w+)_([a-zA-Z0-9]+)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(3)
    print(f"\n=== Summary for {product} {timeframe} ===")
else:
    print("\n=== Trading Performance Summary ===")

print(f"Total PnL        : {total_pnl:.2f}")
print(f"Net PnL          : {Net:.2f}")
print(f"Total Trades     : {num_of_trades}")
print(f"Trade Cost       : {TradeCost:.2f}")
print(f"Success Rate     : {success_rate:.2f}%")
print(f"Failure Rate     : {failure_rate:.2f}%")
print(f"Positive Trades  : {total_positive_trades}")
print(f"Negative Trades  : {total_negative_trades}")
print(f"Total Long PnL   : {total_long_pnl:.2f}")
print(f"Total Short PnL  : {total_short_pnl:.2f}")
