import pandas as pd
import os
import re
import time

# ==================== CONFIG ====================
file_path         = r"D:\Data\ES Jun25_5min.csv"
output_path       = r"C:\Users\lenovo\Desktop\Trade Logs\trade_log_ES_Jun25_5min.xlsx"
time_col          = 'Date(GMT)'
open_col          = 'Open'
high_col          = 'High'
low_col           = 'Low'
close_col         = 'Close'

rsi_period        = 14
long_threshold    = 50
short_threshold   = 50
contract_size     = 50
tick_size         = 0.25
max_loss_per_trade= 0
limit             = 450
atr_period        = 14
num_of_lots       = 1
trade_cost        = 1
export_trades_csv = False
os.makedirs(os.path.dirname(output_path), exist_ok=True)

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

    atr = tr.ewm(alpha=1/period, adjust=False).mean()  # Wilder smoothing
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

# Indicators
df['RSI']      = compute_rsi(df[close_col], rsi_period)
df['EMA_RSI']  = df['RSI'].ewm(span=14, adjust=False).mean()   # EMA(RSI,14)
df['MACD'], df['Signal'] = compute_macd(df[close_col], 12, 26, 9)
df['TR'], df['ATR']      = wilder_atr(df, high_col, low_col, close_col, period=atr_period)

# Warmup to avoid NaNs
warmup = max(rsi_period, atr_period, 26)
df = df.reset_index(drop=True)

# ==================== BACKTEST ====================
position = 0                  # 0 flat, 1 long, -1 short
entry_price = entry_time = entry_index = None
stop_loss = target_profit = None

total_pnl = total_long_pnl = total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')

highest_equity = lowest_equity = None
max_drawdown = max_runup = 0.0
equity_curve = []
trade_log = []
first_trade_done = False

for i in range(warmup, len(df)):
    try:
        date        = df[time_col].iloc[i]
        close       = df[close_col].iloc[i]
        high        = df[high_col].iloc[i]
        low         = df[low_col].iloc[i]
        rsi         = df['RSI'].iloc[i]
        ema_rsi     = df['EMA_RSI'].iloc[i]
        macd        = df['MACD'].iloc[i]
        signal      = df['Signal'].iloc[i]
        atr         = df['ATR'].iloc[i]
        macd_prev   = df['MACD'].iloc[i-1]
        signal_prev = df['Signal'].iloc[i-1]

        # ---------- LONG ENTRY ----------
        if position == 0 and macd > signal and ema_rsi < long_threshold:
            position = 1
            entry_price = close
            entry_time  = date
            entry_index = i
            stop_loss     = entry_price - (1.5 * atr)   # store for later bars
            target_profit = entry_price + (  2 * atr)   # store for later bars
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" EMA_RSI      : {ema_rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print("================================\n")
            time.sleep(0.5)
            continue

        if position == 1:
            exit_reason = None
            exit_price = None

            if high >= target_profit:  # hit target intrabar
                exit_price = target_profit
                exit_reason = 'Target'
            elif low <= stop_loss:  # hit stop intrabar
                exit_price = stop_loss
                exit_reason = 'Stop'
            elif close <= signal:  # hit signal
                exit_price = close
                exit_reason = 'Signal'

            if exit_price is not None:
            #  Now safe to calculate max_loss_per_trade
                max_loss_per_trade = (entry_price - exit_price) * contract_size * num_of_lots
                if max_loss_per_trade >= limit:
                    exit_price = entry_price - (tick_size * 2)
                    exit_reason = "Max Loss"

            # p&l calculation-------------
            if exit_price is not None:
                pnl = (exit_price - entry_price) * num_of_lots * contract_size - trade_cost
                total_pnl += pnl
                total_long_pnl += pnl
                equity_curve.append(total_pnl)

                if not first_trade_done:
                    highest_equity = lowest_equity = total_pnl
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
                    'exit_reason': exit_reason
                })

                print("\033[1;32m========== LONG EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" EMA_RSI      : {ema_rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" max_loss     : {max_loss_per_trade:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}  | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep(0.5)
                position = 0
                entry_price = entry_time = entry_index = None
                stop_loss = target_profit = None
                continue

        # ---------- SHORT ENTRY ----------
        if position == 0 and macd < signal and ema_rsi > short_threshold:
            position = -1
            entry_price = close
            entry_time  = date
            entry_index = i
            stop_loss     = entry_price + (1.5 * atr)   # store for later bars
            target_profit = entry_price - (2 * atr)   # store for later bars
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" EMA_RSI      : {ema_rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print("================================\n")
            time.sleep(0.5)
            continue

        if position == -1:
            exit_reason = None
            exit_price = None

            if low <= target_profit:  # hit target intrabar
                exit_price = target_profit
                exit_reason = 'Target'
            elif high >= stop_loss:  # hit stop intrabar
                exit_price = stop_loss
                exit_reason = 'Stop'
            elif close >= signal:  # hit signal
                exit_price = close
                exit_reason = "Signal"

            if exit_price is not None:
            #  Now safe to calculate max_loss_per_trade
                max_loss_per_trade = (exit_price - entry_price) * contract_size * num_of_lots
                if max_loss_per_trade >= limit:
                    exit_price = entry_price + (tick_size * 2)
                    exit_reason = "Max Loss"

            # p&l calculation
            if exit_price is not None:
                pnl = (entry_price - exit_price) * num_of_lots * contract_size - trade_cost
                total_pnl += pnl
                total_short_pnl += pnl
                equity_curve.append(total_pnl)

                if not first_trade_done:
                    highest_equity = lowest_equity = total_pnl
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
                    'exit_reason': exit_reason
                })

                print("\033[1;31m========== SHORT EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" EMA_RSI      : {ema_rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" max_loss     : {max_loss_per_trade:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}  | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep(0.5)
                position = 0
                entry_price = entry_time = entry_index = None
                stop_loss = target_profit = None
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
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} (MACD crossover + EMA(RSI,14) filter + ATR(14) TP/SL):\033[0m")
else:
    print("\n\033[1mTrading Performance Summary (MACD crossover + EMA(RSI,14) filter + ATR(14) TP/SL):\033[0m")

print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL = {total_long_pnl:.2f}")
print(f"Total Short PnL = {total_short_pnl:.2f}")
print(f"          Gross = {total_pnl:.2f}")
print(f"     Trade Cost = {TradeCost:.2f}")
print(f"            Net = {Net:.2f}")
print(f"   Max Drawdown = {max_drawdown:.2f}")
print(f"     Max Run-up = {max_runup:.2f}")
print(f"Positive Trades = {total_positive_trades}")
print(f"Negative Trades = {total_negative_trades}")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")

# -------------------- Save to Excel --------------------
if trade_log:
    trades_df = pd.DataFrame(trade_log)
    try:
        trades_df.to_excel(output_path, index=False)
        print(f"Trade log saved to: {output_path}")
    except Exception as e:
        print(f"\nFailed to save trades to Excel: {e}")
else:
    print("\nNo trades to save.")