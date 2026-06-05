# inside_bar_backtest.py
import pandas as pd
import os
import time
import re
from datetime import datetime

# ==================== CONFIG ====================
file_path         = r"D:\Data\CL 10min.csv"       # <- set your CSV path
output_path       = r"C:\Users\lenovo\Downloads\ES_insidebar_trades.xlsx"
time_col          = 'Date(GMT)'   # column name containing timestamp
open_col          = 'Open'
high_col          = 'High'
low_col           = 'Low'
close_col         = 'Close'

# Strategy inputs (mirror Pine input names)
m_percent         = 100    # Profit % multiplier (Pine 'm')
n_inside          = 8      # No_of_Candles (Pine 'n')
position_size     = 1.0    # contracts per trade
tick_size         = 0.25   # minimum tick (used to compute stop offsets)
contract_size     = 50     # contract multiplier (used for PnL calc)
trade_cost        = 1      # per-trade cost
export_trades_csv = True

# Backtest safety / warmup
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# ==================== LOAD DATA ====================
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    raise SystemExit

# Ensure datetime if possible
if time_col in df.columns:
    try:
        df[time_col] = pd.to_datetime(df[time_col])
    except Exception:
        pass

# ==================== STATE STORAGE (pattern arrays) ====================
# We replicate Pine arrays with Python lists. Each element across lists corresponds.
s_highs = []         # mother-candle highs
s_lows  = []         # mother-candle lows
counts  = []         # number of inside candles observed
trade_ids = []       # trade id assigned when executed ("" until executed)
trade_active = []    # boolean: pattern has active trade
target_prices = []   # TP associated with the pattern (when trade entered)
stop_prices   = []   # SL associated with the pattern (when trade entered)
start_indices = []   # start bar index of the pattern (for cleanup)

# ==================== TRADE / P&L TRACKING ====================
trade_log = []
equity_curve = []
total_pnl = 0.0
total_long_pnl = 0.0
total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')
first_trade_done = False
highest_equity = lowest_equity = None
max_drawdown = max_runup = 0.0

# Helper to generate unique trade id
def gen_trade_id(side, i, bar_index):
    return f"{side}_{i}_{bar_index}_{int(time.time()*1000)%100000}"

# ==================== MAIN LOOP ====================
for i in range(1, len(df)):  # start at 1 because we reference previous bar high/low
    try:
        date  = df[time_col].iloc[i] if time_col in df.columns else i
        o     = df[open_col].iloc[i]
        h     = df[high_col].iloc[i]
        l     = df[low_col].iloc[i]
        c     = df[close_col].iloc[i]

        prev_h = df[high_col].iloc[i-1]
        prev_l = df[low_col].iloc[i-1]

        # ----------------- Detect new inside-bar (current close inside previous bar) -----------------
        # Pine: if close <= high[1] and close >= low[1] -> record mother candle high/low
        if (c <= prev_h) and (c >= prev_l):
            s_highs.append(prev_h)
            s_lows.append(prev_l)
            counts.append(0)
            trade_ids.append("")         # empty until trade entered
            trade_active.append(False)
            target_prices.append(float('nan'))
            stop_prices.append(float('nan'))
            start_indices.append(i-1)    # mother candle index

        # ----------------- Process patterns backward to allow safe removals -----------------
        j = len(s_highs) - 1
        while j >= 0:
            # If pattern already had trade entered, skip counting/removal logic for it.
            if not trade_active[j]:
                # If current candle closed inside stored high/low -> increment count
                if (c <= s_highs[j]) and (c >= s_lows[j]):
                    counts[j] += 1
                else:
                    # Not inside anymore -> check for breakout entry if count >= n_inside
                    # For Long breakout: close > s_high (we'll require not broken below mother low in same candle)
                    breakout_up = (c > s_highs[j]) and (l > s_lows[j])
                    # For Short breakout: close < s_low and high < s_high (no simultaneous opposite breakout)
                    breakout_down = (c < s_lows[j]) and (h < s_highs[j])

                    if breakout_up and counts[j] >= n_inside:
                        # Enter long
                        tid = gen_trade_id("Long", j, i)
                        trade_ids[j] = tid
                        trade_active[j] = True
                        pattern_range = s_highs[j] - s_lows[j]
                        tp = s_highs[j] + (m_percent * 0.01 * pattern_range)
                        sl = s_lows[j] - 2 * tick_size
                        target_prices[j] = tp
                        stop_prices[j] = sl

                        entry_price = c
                        entry_time = date
                        entry_idx = i

                        # Register open trade in trade_log with partial info; will complete on exit
                        trade_log.append({
                            'trade_id': tid,
                            'side': 'long',
                            'entry_time': entry_time,
                            'entry_idx': entry_idx,
                            'entry_price': entry_price,
                            'tp': tp,
                            'sl': sl,
                            'exit_time': None,
                            'exit_idx': None,
                            'exit_price': None,
                            'pnl': None,
                            'bars_held': None,
                            'exit_reason': None
                        })

                        print("\033[1;32m========== LONG ENTRY =========\033[0m")
                        print(f" Entry Time   : {entry_time}")
                        print(f" Entry Price  : {entry_price}")
                        print(f" Mother High  : {s_highs[j]}  Mother Low: {s_lows[j]}")
                        print(f" TP           : {tp}  | SL: {sl}")
                        print("================================\n")
                        time.sleep(2)
                    elif breakout_down and counts[j] >= n_inside:
                        # Enter short
                        tid = gen_trade_id("Short", j, i)
                        trade_ids[j] = tid
                        trade_active[j] = True
                        pattern_range = s_highs[j] - s_lows[j]
                        tp = s_lows[j] - (m_percent * 0.01 * pattern_range)
                        sl = s_highs[j] + 2 * tick_size
                        target_prices[j] = tp
                        stop_prices[j] = sl

                        entry_price = c
                        entry_time = date
                        entry_idx = i

                        trade_log.append({
                            'trade_id': tid,
                            'side': 'short',
                            'entry_time': entry_time,
                            'entry_idx': entry_idx,
                            'entry_price': entry_price,
                            'tp': tp,
                            'sl': sl,
                            'exit_time': None,
                            'exit_idx': None,
                            'exit_price': None,
                            'pnl': None,
                            'bars_held': None,
                            'exit_reason': None
                        })

                        print("\033[1;31m========== SHORT ENTRY =========\033[0m")
                        print(f" Entry Time   : {entry_time}")
                        print(f" Entry Price  : {entry_price}")
                        print(f" Mother High  : {s_highs[j]}  Mother Low: {s_lows[j]}")
                        print(f" TP           : {tp}  | SL: {sl}")
                        print("================================\n")
                        time.sleep(2)
                    else:
                        # Pattern invalid / broken before reaching required inside count -> remove it
                        # Remove corresponding indices across all lists
                        del s_highs[j]
                        del s_lows[j]
                        del counts[j]
                        del trade_ids[j]
                        del trade_active[j]
                        del target_prices[j]
                        del stop_prices[j]
                        del start_indices[j]
            j -= 1

        # ----------------- Check active trades for exits (intrabar TP/SL or bar close-based) ---------------
        # We'll iterate over a copy of trade_log to update open trades
        for t in trade_log:
            if t['exit_time'] is not None:
                continue  # already closed

            tid = t['trade_id']
            side = t['side']
            entry_idx = t['entry_idx']
            entry_price = t['entry_price']
            # Find pattern index for this trade (should exist)
            # pattern index may have changed due to removals -> search in trade_ids
            try:
                pat_idx = trade_ids.index(tid)
                tp = target_prices[pat_idx]
                sl = stop_prices[pat_idx]
            except ValueError:
                # Pattern index not found (rare) -> we still have tp/sl in t entry
                tp = t.get('tp', float('nan'))
                sl = t.get('sl', float('nan'))

            exit_price = None
            exit_reason = None

            if side == 'long':
                # Intrabar checks: if high >= tp -> target hit; elif low <= sl -> stop hit
                if not pd.isna(tp) and h >= tp:
                    exit_price = tp
                    exit_reason = 'Target'
                elif not pd.isna(sl) and l <= sl:
                    exit_price = sl
                    exit_reason = 'Stop'
                else:
                    # Optional: exit if some other condition (none in Pine). We'll not force-close on any signal.
                    pass
                # You could also add bar-close signal exit if required.

                if exit_price is not None:
                    pnl = (exit_price - entry_price) * contract_size * position_size - trade_cost
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

                    # Update trade entry in log
                    t['exit_time'] = date
                    t['exit_idx'] = i
                    t['exit_price'] = exit_price
                    t['pnl'] = pnl
                    t['bars_held'] = i - entry_idx
                    t['exit_reason'] = exit_reason

                    print("\033[1;32m========== LONG EXIT =========\033[0m")
                    print(f" Exit Time    : {date}")
                    print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                    print(f" Trade P&L    : {pnl:.2f}")
                    print(f" Cum. P&L     : {total_pnl:.2f}")
                    print("================================\n")
                    time.sleep(2)

                    # mark that pattern is no longer active (if its pattern still exists)
                    if tid in trade_ids:
                        idx = trade_ids.index(tid)
                        trade_active[idx] = False
                        # remove the pattern arrays for cleanup (Pine removes trade arrays on closure)
                        del s_highs[idx]
                        del s_lows[idx]
                        del counts[idx]
                        del trade_ids[idx]
                        del trade_active[idx]
                        del target_prices[idx]
                        del stop_prices[idx]
                        del start_indices[idx]

            else:  # short side
                if not pd.isna(tp) and l <= tp:
                    exit_price = tp
                    exit_reason = 'Target'
                elif not pd.isna(sl) and h >= sl:
                    exit_price = sl
                    exit_reason = 'Stop'

                if exit_price is not None:
                    pnl = (entry_price - exit_price) * contract_size * position_size - trade_cost
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

                    t['exit_time'] = date
                    t['exit_idx'] = i
                    t['exit_price'] = exit_price
                    t['pnl'] = pnl
                    t['bars_held'] = i - entry_idx
                    t['exit_reason'] = exit_reason

                    print("\033[1;31m========== SHORT EXIT =========\033[0m")
                    print(f" Exit Time    : {date}")
                    print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                    print(f" Trade P&L    : {pnl:.2f}")
                    print(f" Cum. P&L     : {total_pnl:.2f}")
                    print("================================\n")
                    time.sleep(2)

                    if tid in trade_ids:
                        idx = trade_ids.index(tid)
                        trade_active[idx] = False
                        del s_highs[idx]
                        del s_lows[idx]
                        del counts[idx]
                        del trade_ids[idx]
                        del trade_active[idx]
                        del target_prices[idx]
                        del stop_prices[idx]
                        del start_indices[idx]

    except Exception as e:
        print(f"Error at index {i}: {e}")

# ==================== SUMMARY ====================
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

file_name = os.path.basename(file_path)
print("\n\033[1mTrading Performance Summary (Inside-Bar Breakout logic):\033[0m")
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
if trade_log and export_trades_csv:
    trades_df = pd.DataFrame(trade_log)
    try:
        trades_df.to_excel(output_path, index=False)
        print(f"\nTrade log saved to: {output_path}")
    except Exception as e:
        print(f"\nFailed to save trades to Excel: {e}")
else:
    print("\nNo trades to save.")
