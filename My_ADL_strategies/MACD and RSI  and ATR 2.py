import pandas as pd
import os
import re
import time

# ==================== CONFIG ====================
file_path      = r"D:\Data\NQ Jun25_15min.csv"   # <--- change this
time_col       = 'Date(GMT)'
open_col       = 'Open'
high_col       = 'High'
low_col        = 'Low'
close_col      = 'Close'

rsi_period     = 14
atr_period     = 14
atr            = 1.5          # SL = 1.5 * ATR
contract_size  = 20
num_of_lots    = 1
trade_cost     = 1.30         # per round-trip (change if per side)
export_trades_csv = False     # set True to save trades to CSV
trades_csv_path   = "trades_macd_rsi_atr.csv"

# ==================== LOAD ====================
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    raise SystemExit

# ==================== INDICATORS ====================
def wilder_atr(df, high_col, low_col, close_col, period=14):
    high = df[high_col]
    low  = df[low_col]
    close = df[close_col]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return tr, atr

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, 1e-10))
    return 100 - (100 / (1 + rs))

def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

# Compute indicators
df['RSI'] = compute_rsi(df[close_col], rsi_period)
df['MACD'], df['Signal'] = compute_macd(df[close_col], 12, 26, 9)
df['TR'], df['ATR'] = wilder_atr(df, high_col, low_col, close_col, period=atr_period)

# Drop rows until indicators are valid
warmup = max(rsi_period, atr_period, 26)
df = df.reset_index(drop=True)

# ==================== BACKTEST ====================
position = 0   # 0 = flat, 1 = long, -1 = short
entry_price = 0.0
entry_time  = None
entry_index = None

total_pnl = total_long_pnl = total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')
highest_equity = None
lowest_equity  = None
max_drawdown = 0.0
max_runup = 0.0
equity_curve = []

trade_log = []
first_trade_done = False# EMA filters
df['ema'] = df[close_col].ewm(span=14, adjust=False).mean()

for i in range(warmup, len(df)):
    try:
        date    = df[time_col].iloc[i]
        close   = df[close_col].iloc[i]
        high    = df[high_col].iloc[i]
        low     = df[low_col].iloc[i]
        rsi     = df['RSI'].iloc[i]
        macd    = df['MACD'].iloc[i]
        signal  = df['Signal'].iloc[i]
        atr     = df['ATR'].iloc[i]
        ema     = df['ema'].iloc[i]

        macd_prev   = df['MACD'].iloc[i-1]
        signal_prev = df['Signal'].iloc[i-1]
        macd_cross_up = (macd_prev <= signal_prev) and (macd > signal)
        macd_cross_dn = (macd_prev >= signal_prev) and (macd < signal)
        

        # ------------- LONG ENTRY -------------
        if position == 0 and (macd > signal) and (ema(rsi) < 50):
            position = 1
            entry_price = close
            entry_time  = date
            entry_index = i
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" RSI          : {rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print("================================\n")
            continue
        time.sleep(0.5)
  
        # ------------- LONG EXIT -------------
        if position == 1:
            stop_loss     = entry_price + (2 * atr)
            target_profit = entry_price - (3 * atr)
            if close >= target_profit or (close <= stop_loss):
                exit_price = close
                pnl = (exit_price - entry_price) * num_of_lots * contract_size - trade_cost
                total_pnl += pnl
                total_long_pnl += pnl
                equity_curve.append(total_pnl)

                if not first_trade_done:
                    highest_equity = total_pnl
                    lowest_equity = total_pnl
                    first_trade_done = True

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

                # Log trade
                trade_log.append({
                    'side': 'long',
                    'entry_time': entry_time,
                    'entry_idx': entry_index,
                    'entry_price': entry_price,
                    'exit_time': date,
                    'exit_idx': i,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'bars_held': i - entry_index,
                    'exit_reason': 'MACD_cross' if macd_cross_dn else 'ATR_SL',
                    'rsi_exit': rsi,
                    'macd_exit': macd,
                    'signal_exit': signal,
                    'atr_exit': atr
                })

                print("\033[1;32m========== LONG EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" RSI          : {rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}    | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep(0.5)

                position = 0
                entry_price = entry_time = entry_index = None
                continue

        # ------------- SHORT ENTRY -------------
        if position == 0 and (macd < signal) and (ema(rsi) > 50):
            position = -1
            entry_price = close
            entry_time  = date
            entry_index = i
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" RSI          : {rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print("================================\n")
            time.sleep(0.5)
            continue

        # ------------- SHORT EXIT -------------
        if position == -1:
            stop_loss     = entry_price + (2 * atr)
            target_profit = entry_price - (3 * atr)
            if close <= target_profit or (close >= stop_loss):
                exit_price = close
                pnl = (entry_price - exit_price) * num_of_lots * contract_size - trade_cost
                total_pnl += pnl
                total_short_pnl += pnl
                equity_curve.append(total_pnl)

                if not first_trade_done:
                    highest_equity = total_pnl
                    lowest_equity = total_pnl
                    first_trade_done = True

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

                # Log trade
                trade_log.append({
                    'side': 'short',
                    'entry_time': entry_time,
                    'entry_idx': entry_index,
                    'entry_price': entry_price,
                    'exit_time': date,
                    'exit_idx': i,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'bars_held': i - entry_index,
                    'exit_reason': 'MACD_cross' if macd_cross_up else 'ATR_SL',
                    'rsi_exit': rsi,
                    'macd_exit': macd,
                    'signal_exit': signal,
                    'atr_exit': atr
                })

                print("\033[1;31m========== SHORT EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" RSI          : {rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}    | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep(0.5)

                position = 0
                entry_price = entry_time = entry_index = None
                continue

    except Exception as e:
        print(f"Error at index {i}: {e}")

# ==================== SUMMARY ====================
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+\w+_(\d+min)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(2)
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} (MACD+RSI+ATR 1.5x with crossover exits & intrabar SL):\033[0m")
else:
    print("\n\033[1mTrading Performance Summary (MACD+RSI+ATR 1.5x with crossover exits & intrabar SL):\033[0m")

print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl:.2f}\033[0m")
print(f"          Gross = {total_pnl:.2f}")
print(f"     Trade Cost = {TradeCost:.2f}")
print(f"            Net = {Net:.2f}")
print(f"   Max Drawdown = {max_drawdown:.2f}")
print(f"     Max Run-up = {max_runup:.2f}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")
time.sleep(0.5)

# Raw values (if you need to parse programmatically)
print(f"\033[92m{max_profit}\033[0m")
print(f"\033[91m{max_loss}\033[0m")
print(f"\033[92m{positive_pnl}\033[0m")
print(f"\033[91m{negative_pnl}\033[0m")
print(f"\033[94m{total_long_pnl}\033[0m")
print(f"\033[94m{total_short_pnl}\033[0m")
print(f"{total_pnl}")
print(f"{round(TradeCost,2)}")
print(f"{Net}")
print(f"{max_drawdown}")
print(f"{max_runup}")
print(f"\033[92m{total_positive_trades}\033[0m")
print(f"\033[91m{total_negative_trades}\033[0m")
print(f"{num_of_trades}")
print(f"\033[92m{success_rate:.2f}%\033[0m")
print(f"\033[91m{failure_rate:.2f}%\033[0m")
time.sleep(0.5)

# ==================== TRADE LOG ====================
if trade_log:
    trades_df = pd.DataFrame(trade_log)
    print("\nLast 10 trades:")
    print(trades_df.tail(10))

    if export_trades_csv:
        trades_df.to_csv(trades_csv_path, index=False)
        print(f"\nTrade log exported to: {trades_csv_path}")
else:
    print("\nNo trades generated.")
