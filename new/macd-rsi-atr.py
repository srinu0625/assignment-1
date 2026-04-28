import pandas as pd
import os
import time

# -------------------- Paths & Config --------------------
file_path   = r"D:\Data\BR daily.csv"
output_path = r"C:\Users\lenovo\Desktop\Trade Logs\BR_daily_trades.xlsx"

time_col   = 'Date(GMT)'
open_col   = 'Open'
high_col   = 'High'
low_col    = 'Low'
close_col  = 'Close'

rsi_period    = 14
ema_rsi_span  = 14   # span for EMA of RSI (kept 14 as before)
atr_period    = 14
Stop_atr      = 2     # Stop-loss multiplier
profit_atr    = 3     # Take-profit multiplier
contract_size = 1000
num_of_lots   = 1
trade_cost    = 1.30  # cost per trade (applied once per round-trip trade in summary)

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# -------------------- Load Data --------------------
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    raise SystemExit

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
rs = avg_gain / avg_loss.replace(0, 1e-10)
df['RSI'] = 100 - (100 / (1 + rs))

# EMA of RSI
df['EMA_RSI'] = df['RSI'].ewm(span=ema_rsi_span, adjust=False).mean()

# MACD
ema_fast = df[close_col].ewm(span=12, adjust=False).mean()
ema_slow = df[close_col].ewm(span=26, adjust=False).mean()
df['MACD'] = ema_fast - ema_slow
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# ATR
df['TR'], df['ATR'] = wilder_atr(df, high_col, low_col, close_col, period=atr_period)

# -------------------- Backtest --------------------
position = 0
entry_price = entry_time = entry_side = None
tp_price = sl_price = None

total_pnl = total_long_pnl = total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')
highest_equity = lowest_equity = 0.0
max_drawdown = max_runup = 0.0
equity_curve = []
trade_log = []

# start index: need at least ATR and ema slow (26) values
start_idx = max(atr_period, 26)

for i in range(start_idx, len(df)):
    try:
        date   = df[time_col].iloc[i]
        close  = df[close_col].iloc[i]
        atr    = df['ATR'].iloc[i]
        macd   = df['MACD'].iloc[i]
        signal = df['Signal'].iloc[i]
        ema_rsi = df['EMA_RSI'].iloc[i]

        # ---------------- Long Entry ----------------
        if position == 0:
            # changed: use only current MACD > Signal (no previous-bar check)
            if (macd > signal) and (ema_rsi < 45):
                position = 1
                entry_price = close
                tp_price = entry_price + profit_atr * atr
                sl_price = entry_price - Stop_atr * atr
                entry_time = date
                entry_side = 'LONG'

                print(f"\033[92m[LONG ENTRY]\033[0m")
                print(f"  Date       : {entry_time}")
                print(f"  Price      : {entry_price}")
                print(f"  Take Profit: {tp_price}")
                print(f"  Stop Loss  : {sl_price}")
                print("-----------------------------------")
                time.sleep(10)  # slight pause for readability
                continue

        # ---------------- Long Exit ----------------
        if position == 1:
            # changed: exit on TP/SL or current MACD < Signal (no prev check)
            if close >= tp_price or close <= sl_price or (macd < signal):
                exit_price = close
                pnl = (exit_price - entry_price) * num_of_lots * contract_size
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

                print("\033[92m[LONG EXIT]\033[0m")
                print(f"  Date       : {date}")
                print(f"  Side       : {entry_side}")
                print(f"  Entry Time : {entry_time}")
                print(f"  Entry Price: {entry_price}")
                print(f"  Exit Time  : {date}")
                print(f"  Exit Price : {exit_price}")
                print(f"  PnL        : {pnl:.2f}")
                print(f"  Cum PnL    : {total_pnl:.2f}")
                print("-----------------------------------")
                time.sleep(10)

                trade_log.append({
                    "Side": entry_side,
                    "Entry Time": entry_time,
                    "Entry Price": entry_price,
                    "Exit Time": date,
                    "Exit Price": exit_price,
                    "P&L": pnl,
                    "Cum_PnL": total_pnl
                })

                position = 0
                entry_price = entry_time = entry_side = None
                continue

        # ---------------- Short Entry ----------------
        if position == 0:
            # changed: use only current MACD < Signal (no previous-bar check)
            if (macd < signal) and (ema_rsi > 55):
                position = -1
                entry_price = close
                tp_price = entry_price - profit_atr * atr
                sl_price = entry_price + Stop_atr * atr
                entry_time = date
                entry_side = 'SHORT'

                print(f"\033[91m[SHORT ENTRY]\033[0m")
                print(f"  Date       : {entry_time}")
                print(f"  Price      : {entry_price}")
                print(f"  Take Profit: {tp_price}")
                print(f"  Stop Loss  : {sl_price}")
                print("-----------------------------------")
                time.sleep(10)
                continue

        # ---------------- Short Exit ----------------
        if position == -1:
            # changed: exit on TP/SL or current MACD > Signal (no prev check)
            if close <= tp_price or close >= sl_price or (macd > signal):
                exit_price = close
                pnl = (entry_price - exit_price) * num_of_lots * contract_size
                total_pnl += pnl
                total_short_pnl += pnl
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

                print("\033[91m[SHORT EXIT]\033[0m")
                print(f"  Date       : {date}")
                print(f"  Side       : {entry_side}")
                print(f"  Entry Time : {entry_time}")
                print(f"  Entry Price: {entry_price}")
                print(f"  Exit Time  : {date}")
                print(f"  Exit Price : {exit_price}")
                print(f"  PnL        : {pnl:.2f}")
                print(f"  Cum PnL    : {total_pnl:.2f}")
                print("-----------------------------------")
                time.sleep(10)

                trade_log.append({
                    "Side": entry_side,
                    "Entry Time": entry_time,
                    "Entry Price": entry_price,
                    "Exit Time": date,
                    "Exit Price": exit_price,
                    "P&L": pnl,
                    "Cum_PnL": total_pnl
                })

                position = 0
                entry_price = entry_time = entry_side = None
                continue

    except Exception as e:
        print(f"Error at index {i}: {e}")

# -------------------- Summary --------------------
# Trade cost applied once per trade here (not double-counted)
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

print("\n\033[1mTrading Performance Summary (MACD Cross + EMA_RSI):\033[0m")
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
print(f"   Failure Rate = \033[91m{failure_rate:.2f}\033[0m")

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
