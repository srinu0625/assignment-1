import pandas as pd
import time
import os

# -------------------- Paths & Config --------------------
file_path   = r"D:\Data\ES Jun25_5min.csv"                 
output_path = r"C:\Users\lenovo\Desktop\Trade Logs\ES_daily_trades.xlsx"    

time_col   = 'Date(GMT)'
open_col   = 'Open'
high_col   = 'High'
low_col    = 'Low'
close_col  = 'Close'

rsi_period    = 14
atr_period    = 14
Stop_atr      = 1.5     # Stop-loss multiplier
profit_atr    = 1.5     # Take-profit multiplier
contract_size = 50
num_of_lots   = 1
trade_cost    = 1.30
macd_gap_min  = 0.05    # Minimum MACD gap for entry

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

# EMA filters
df['ema50'] = df[close_col].ewm(span=50, adjust=False).mean()
df['ema200'] = df[close_col].ewm(span=200, adjust=False).mean()

# RSI
delta = df[close_col].diff()
gain = delta.where(delta > 0, 0.0)
loss = -delta.where(delta < 0, 0.0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period, adjust=False).mean()
rs = avg_gain / (avg_loss.replace(0, 1e-10))
df['RSI'] = 100 - (100 / (1 + rs))

# MACD
ema_fast = df[close_col].ewm(span=12, adjust=False).mean()
ema_slow = df[close_col].ewm(span=26, adjust=False).mean()
df['MACD'] = ema_fast - ema_slow
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# ATR
df['TR'], df['ATR'] = wilder_atr(df, high_col, low_col, close_col, period=atr_period)
atr_median = df['ATR'].median()

# -------------------- Backtest --------------------
position = 0
entry_price = None
entry_time = None
entry_side  = None
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

for i in range(max(atr_period, 200), len(df)):
    try:
        date   = df[time_col].iloc[i]
        close  = df[close_col].iloc[i]
        high   = df[high_col].iloc[i]
        low    = df[low_col].iloc[i]
        rsi    = df['RSI'].iloc[i]
        macd   = df['MACD'].iloc[i]
        signal = df['Signal'].iloc[i]
        atr    = df['ATR'].iloc[i]
        ema50  = df['ema50'].iloc[i]
        ema200 = df['ema200'].iloc[i]

        # FLAT → Check Long/Short Entry
        if position == 0:
            # Long Entry
            if (macd > signal) and ((macd - signal) > macd_gap_min) and (rsi > 55) and (ema50 > ema200) and (close > ema50) and (atr > atr_median):
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
                continue
 
            # Short Entry
            if (macd < signal) and ((signal - macd) > macd_gap_min) and (rsi < 45) and (ema50 < ema200) and (close < ema50) and (atr > atr_median):
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
                time.sleep(1)
                continue

        # LONG → Check Exit
        elif position == 1:
            if close >= tp_price or close <= sl_price or (macd < signal):
                exit_price = close
                pnl = (exit_price - entry_price) * num_of_lots * contract_size - trade_cost
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
                time.sleep(1)

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

        # SHORT → Check Exit
        elif position == -1:
            if close <= tp_price or close >= sl_price or (macd > signal):
                exit_price = close
                pnl = (entry_price - exit_price) * num_of_lots * contract_size - trade_cost
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

                # Short exit
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
                time.sleep(1)

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

    except Exception as e:
        print(f"Error at index {i}: {e}")

# -------------------- Summary --------------------
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

print("\n\033[1mTrading Performance Summary (MACD+RSI+EMA+ATR Filters):\033[0m")
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
        print(f"Saved trades to: {output_path}")
    except Exception as e:
        print(f"\nFailed to save trades to Excel: {e}")
else:
    print("\nNo trades to save.")
