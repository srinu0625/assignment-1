import pandas as pd
import os
import time

# ---------------- CONFIG ----------------
file_path = r"D:\Data\ES Jun25_5min.csv"
output_path = r"C:\Users\lenovo\Desktop\Trade Logs\ES_daily_trades.xlsx"

time_col = 'Date(GMT)'
open_col = 'Open'
high_col = 'High'
low_col = 'Low'
close_col = 'Close'

atr_period = 14
rsi_period = 14
stop_atr_mult = 2
target_atr_mult = 3
contract_size = 50
lots = 1
trade_cost = 1.30

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# ---------------- LOAD DATA ----------------
df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# ---------------- INDICATORS ----------------
# RSI
delta = df[close_col].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
rs = avg_gain / avg_loss.replace(0, 1e-10)
df['RSI'] = 100 - (100 / (1 + rs))

# EMA(RSI)
df['EMA_RSI'] = df['RSI'].ewm(span=14, adjust=False).mean()

# MACD
ema_fast = df[close_col].ewm(span=12, adjust=False).mean()
ema_slow = df[close_col].ewm(span=26, adjust=False).mean()
df['MACD'] = ema_fast - ema_slow
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# ATR (Wilder)
high = df[high_col]
low = df[low_col]
close = df[close_col]
prev_close = close.shift(1)
tr = pd.concat([
    high - low,
    (high - prev_close).abs(),
    (low - prev_close).abs()
], axis=1).max(axis=1)
df['ATR'] = tr.ewm(alpha=1/atr_period, adjust=False).mean()

# ---------------- BACKTEST ----------------
position = 0
entry_price = entry_time = None
tp_price = sl_price = None
entry_side = None

total_pnl = 0
trade_log = []

for i in range(max(atr_period, 26), len(df)):
    date = df[time_col].iloc[i]
    close = df[close_col].iloc[i]
    macd = df['MACD'].iloc[i]
    signal = df['Signal'].iloc[i]
    ema_rsi = df['EMA_RSI'].iloc[i]
    atr = df['ATR'].iloc[i]

    macd_prev = df['MACD'].iloc[i - 1]
    signal_prev = df['Signal'].iloc[i - 1]

    # ENTRY CONDITIONS
    if position == 0:
        # Long Entry: MACD cross above signal & EMA(RSI) < 50
        if macd_prev < signal_prev and macd > signal and ema_rsi < 50:
            position = 1
            entry_price = close
            tp_price = entry_price + target_atr_mult * atr
            sl_price = entry_price - stop_atr_mult * atr
            entry_time = date
            entry_side = 'LONG'
            print(f"\033[92m[LONG ENTRY] {date} | Price: {entry_price:.2f} | TP: {tp_price:.2f} | SL: {sl_price:.2f}\033[0m")
            continue

        # Short Entry: MACD cross below signal & EMA(RSI) > 50
        if macd_prev > signal_prev and macd < signal and ema_rsi > 50:
            position = -1
            entry_price = close
            tp_price = entry_price - target_atr_mult * atr
            sl_price = entry_price + stop_atr_mult * atr
            entry_time = date
            entry_side = 'SHORT'
            print(f"\033[91m[SHORT ENTRY] {date} | Price: {entry_price:.2f} | TP: {tp_price:.2f} | SL: {sl_price:.2f}\033[0m")
            continue

    # EXIT CONDITIONS
    if position == 1:  # Long
        if close >= tp_price or close <= sl_price:
            pnl = (close - entry_price) * lots * contract_size - trade_cost
            total_pnl += pnl
            print(f"\033[92m[LONG EXIT] {date} | Price: {close:.2f} | PnL: {pnl:.2f} | CumPnL: {total_pnl:.2f}\033[0m")
            trade_log.append({
                "Side": entry_side, "Entry Time": entry_time, "Entry Price": entry_price,
                "Exit Time": date, "Exit Price": close, "P&L": pnl, "Cum_PnL": total_pnl
            })
            position = 0

    elif position == -1:  # Short
        if close <= tp_price or close >= sl_price:
            pnl = (entry_price - close) * lots * contract_size - trade_cost
            total_pnl += pnl
            print(f"\033[91m[SHORT EXIT] {date} | Price: {close:.2f} | PnL: {pnl:.2f} | CumPnl: {total_pnl:.2f}\033[0m")
            trade_log.append({
                "Side": entry_side, "Entry Time": entry_time, "Entry Price": entry_price,
                "Exit Time": date, "Exit Price": close, "P&L": pnl, "Cum_PnL": total_pnl
            })
            position = 0

# ---------------- SAVE TO EXCEL ----------------
if trade_log:
    pd.DataFrame(trade_log).to_excel(output_path, index=False)
    print(f"Saved trade log to: {output_path}")
else:
    print("No trades executed.")
