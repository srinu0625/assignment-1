import pandas as pd
import time
import os
import re
file_path   = r"D:\candles\BR daily.csv"                
output_path = r"C:\Users\lenovo\Desktop\Trade Logs\ES daily_trades.xlsx"    

time_col   = 'date'
open_col   = 'open'
high_col   = 'high'
low_col    = 'low'
close_col  = 'close'

rsi_period    = 14
atr_period    = 14
atr_mult_sl   = 1.5   # 1.5 * ATR for stop-loss
contract_size = 50  # e.g., for CL futures
num_of_lots   = 1
trade_cost    = 1.30

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# -------------------- Load --------------------
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    raise SystemExit

# Calculate EMA


n = 50
df['ema50'] = df[close_col].ewm(span=n, adjust=False).mean()


# -------------------- Indicators --------------------
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

# RSI
delta = df[close_col].diff()
gain = delta.where(delta > 0, 0.0)
loss = -delta.where(delta < 0, 0.0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
rs = avg_gain / (avg_loss.replace(0, 1e-10))  # Avoid div by zero
df['RSI'] = 100 - (100 / (1 + rs))

# MACD
ema_fast = df[close_col].ewm(span=12, adjust=False).mean()
ema_slow = df[close_col].ewm(span=26, adjust=False).mean()
df['MACD'] = ema_fast - ema_slow
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# ATR
df['TR'], df['ATR'] = wilder_atr(df, high_col, low_col, close_col, period=atr_period)

# -------------------- Backtest --------------------
position = 0   # 0 = flat, 1 = long, -1 = short
entry_price = entry_time = None
entry_index = None
entry_side  = None

total_pnl = total_long_pnl = total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')
highest_equity = 0.0
lowest_equity  = 0.0
max_drawdown = 0.0
max_runup = 0.0
equity_curve = []

# one-row-per-trade, in execution order
trade_log = []

for i in range(max(atr_period, 26), len(df)):
    try:
        date   = df[time_col].iloc[i]
        close  = df[close_col].iloc[i]
        high   = df[high_col].iloc[i]
        low    = df[low_col].iloc[i]
        rsi    = df['RSI'].iloc[i]
        macd   = df['MACD'].iloc[i]
        signal = df['Signal'].iloc[i]
        atr    = df['ATR'].iloc[i]
        ema    = df['ema50'].iloc[i]

        # ---------------- Long Entry ----------------
        if position == 0 and (macd > signal) and (rsi < 50) and (close > df['ema50'].iloc[i]):
            position = 1
            entry_price = close
            entry_time  = date
            entry_index = i
            entry_side  = 'LONG'

            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" RSI          : {rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print(f" EMA50        : {ema:.2f}")
            print("================================\n")
            continue
            time.sleep(1)  # to avoid too fast execution in real-time scenarios

        # ---------------- Long Exit ----------------
        if position == 1:
            stop_loss = entry_price - atr_mult_sl * atr
            if (macd < signal) or (close <= stop_loss):
                exit_price = close
                pnl = (exit_price - entry_price) * num_of_lots * contract_size - trade_cost
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

                if len(equity_curve) == 1:
                    highest_equity = lowest_equity = total_pnl
                else:
                    highest_equity = max(highest_equity, total_pnl)
                    lowest_equity  = min(lowest_equity, total_pnl)

                drawdown = highest_equity - total_pnl
                runup    = total_pnl - lowest_equity
                max_drawdown = max(max_drawdown, drawdown)
                max_runup    = max(max_runup, runup)

                print("\033[1;32m========== LONG EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" RSI          : {rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" EMA50        : {ema:.2f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}    | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep( 1)

                # append one row for this full trade
                trade_log.append({
                    "Side": entry_side,
                    "Entry Time": entry_time,
                    "Entry Index": entry_index,
                    "Entry Price": entry_price,
                    "Exit Time": date,
                    "Exit Index": i,
                    "Exit Price": exit_price,
                    "P&L": pnl,
                    "Cum_PnL": total_pnl,
                    "Bars_Held": i - entry_index if entry_index is not None else None,
                    "Entry MACD": df['MACD'].iloc[entry_index],
                    "Entry Signal": df['Signal'].iloc[entry_index],
                    "Entry RSI": df['RSI'].iloc[entry_index],
                    "Exit MACD": macd,
                    "Exit Signal": signal,
                    "Exit RSI": rsi,
                    "ATR Exit": atr,
                    "Drawdown": drawdown,
                    "Max_Drawdown": max_drawdown,
                    "Runup": runup,
                    "Max_Runup": max_runup
                })

                # reset
                position = 0
                entry_price = entry_time = entry_index = entry_side = None
                continue

        # ---------------- Short Entry ----------------
        if position == 0 and (macd < signal) and (rsi > 50) and (close < df['ema50'].iloc[i]):
            position = -1
            entry_price = close
            entry_time  = date
            entry_index = i
            entry_side  = 'SHORT'

            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" Entry Time   : {entry_time}")
            print(f" Entry Price  : {entry_price}")
            print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
            print(f" EMA50        : {ema:.2f}")
            print(f" RSI          : {rsi:.2f}")
            print(f" ATR          : {atr:.4f}")
            print("================================\n")
            time.sleep(1)
            continue

        # ---------------- Short Exit ----------------
        if position == -1:
            stop_loss = entry_price + atr_mult_sl * atr
            if (macd > signal) or (close >= stop_loss):
                exit_price = close
                pnl = (entry_price - exit_price) * num_of_lots * contract_size - trade_cost
                total_pnl += pnl
                total_short_pnl += pnl
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

                if len(equity_curve) == 1:
                    highest_equity = lowest_equity = total_pnl
                else:
                    highest_equity = max(highest_equity, total_pnl)
                    lowest_equity  = min(lowest_equity, total_pnl)

                drawdown = highest_equity - total_pnl
                runup    = total_pnl - lowest_equity
                max_drawdown = max(max_drawdown, drawdown)
                max_runup    = max(max_runup, runup)

                print("\033[1;31m========== SHORT EXIT =========\033[0m")
                print(f" Exit Time    : {date}")
                print(f" Exit Price   : {exit_price}")
                print(f" MACD / Sig   : {macd:.4f} / {signal:.4f}")
                print(f" RSI          : {rsi:.2f}")
                print(f" ATR          : {atr:.4f}")
                print(f" EMA50        : {ema:.2f}")
                print(f" Trade P&L    : {pnl:.2f}")
                print(f" Cum. P&L     : {total_pnl:.2f}")
                print(f" Drawdown     : {drawdown:.2f} | Max DD: {max_drawdown:.2f}")
                print(f" Run-up       : {runup:.2f}    | Max RU: {max_runup:.2f}")
                print("================================\n")
                time.sleep(1)

                # append one row for this full trade
                trade_log.append({
                    "Side": entry_side,
                    "Entry Time": entry_time,
                    "Entry Index": entry_index,
                    "Entry Price": entry_price,
                    "Exit Time": date,
                    "Exit Index": i,
                    "Exit Price": exit_price,
                    "P&L": pnl,
                    "Cum_PnL": total_pnl,
                    "Bars_Held": i - entry_index if entry_index is not None else None,
                    "Entry MACD": df['MACD'].iloc[entry_index],
                    "Entry Signal": df['Signal'].iloc[entry_index],
                    "Entry RSI": df['RSI'].iloc[entry_index],
                    "Exit MACD": macd,
                    "Exit Signal": signal,
                    "Exit RSI": rsi,
                    "ATR Exit": atr,
                    "Drawdown": drawdown,
                    "Max_Drawdown": max_drawdown,
                    "Runup": runup,
                    "Max_Runup": max_runup
                })

                # reset
                position = 0
                entry_price = entry_time = entry_index = entry_side = None
                continue

    except Exception as e:
        print(f"Error at index {i}: {e}")

# -------------------- Summary --------------------
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+\w+_(\d+min)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(2)
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} (MACD+RSI+ATR 1.5x):\033[0m")
else:
    print("\n\033[1mTrading Performance Summary (MACD+RSI+ATR 1.5x):\033[0m")

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
time.sleep(1)


# -------------------- Save trades to Excel (chronological, mixed long/short) --------------------
if trade_log:
    trades_df = pd.DataFrame(trade_log)
    try:
        trades_df.to_excel(output_path, index=False)
        print(f"\nTrades saved (in execution order) to: {output_path}")
    except Exception as e:
        print(f"\nFailed to save trades to Excel: {e}")
else:
    print("\nNo trades to save.")
