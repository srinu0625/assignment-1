# inside_bar_backtest_clean.py
import pandas as pd
import time

# ==================== CONFIG ====================
file_path         = r"D:\Data\BR 10min.csv"       # <- set your CSV path
time_col          = 'Date(GMT)'   # column name containing timestamp
open_col          = 'Open'
high_col          = 'High'
low_col           = 'Low'
close_col         = 'Close'

# Strategy inputs
m_percent         = 100    # Profit % multiplier
n_inside          = 8      # No_of_Candles
position_size     = 1.0    # contracts per trade
tick_size         = 0.25   # minimum tick
contract_size     = 20    # contract multiplier
trade_cost        = 1      # per-trade cost

# ==================== LOAD DATA ====================
try:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
except Exception as e:
    print("Error loading data:", e)
    raise SystemExit

if time_col in df.columns:
    try:
        df[time_col] = pd.to_datetime(df[time_col])
    except Exception:
        pass

# ==================== STATE STORAGE ====================
mother_highs, mother_lows, inside_counts = [], [], []
trade_ids, trade_active = [], []
target_prices, stop_prices, start_indices = [], [], []

# ==================== TRADE / P&L TRACKING ====================
total_pnl = total_long_pnl = total_short_pnl = 0.0
positive_pnl = negative_pnl = 0.0
total_positive_trades = total_negative_trades = 0
num_of_trades = 0
max_profit = float('-inf')
max_loss   = float('inf')

def gen_trade_id(side, bar_index):
    return f"{side}_{bar_index}_{int(time.time()*1000)%100000}"

# ==================== MAIN LOOP ====================
for i in range(1, len(df)):
    try:
        current_time   = df[time_col].iloc[i] if time_col in df.columns else i
        current_open   = df[open_col].iloc[i]
        current_high   = df[high_col].iloc[i]
        current_low    = df[low_col].iloc[i]
        current_close  = df[close_col].iloc[i]

        prev_high  = df[high_col].iloc[i-1]
        prev_low   = df[low_col].iloc[i-1]

        # --- Detect new inside bar ---
        if (current_close <= prev_high) and (current_close >= prev_low):
            mother_highs.append(prev_high)
            mother_lows.append(prev_low)
            inside_counts.append(0)
            trade_ids.append("")
            trade_active.append(False)
            target_prices.append(float('nan'))
            stop_prices.append(float('nan'))
            start_indices.append(i-1)

        # --- Process patterns ---
        j = len(mother_highs) - 1
        while j >= 0:
            if not trade_active[j]:
                if (current_close <= mother_highs[j]) and (current_close >= mother_lows[j]):
                    inside_counts[j] += 1
                else:
                    breakout_up   = (current_close > mother_highs[j]) and (current_low > mother_lows[j])
                    breakout_down = (current_close < mother_lows[j]) and (current_high < mother_highs[j])

                    if breakout_up and inside_counts[j] >= n_inside:
                        trade_id = gen_trade_id("Long", i)
                        trade_ids[j] = trade_id
                        trade_active[j] = True
                        pattern_range = mother_highs[j] - mother_lows[j]
                        take_profit = mother_highs[j] + (m_percent * 0.01 * pattern_range)
                        stop_loss   = mother_lows[j] - 2 * tick_size
                        target_prices[j], stop_prices[j] = take_profit, stop_loss

                        entry_price = current_close
                        print("\033[1;32m========== LONG ENTRY =========\033[0m")
                        print(f"      OHLC: Open={current_open:.2f}   High={current_high:.2f}   Low={current_low:.2f}   Close={current_close:.2f}")
                        print(f"      Time: {current_time}")
                        print(f"     Entry: {entry_price:.2f}")
                        print(f" BASE High: {mother_highs[j]} | BASE Low: {mother_lows[j]}")
                        print(f"        TP: {take_profit:.2f} | SL: {stop_loss:.2f}")
                        print("================================\n")
                        time.sleep(0.5)  # slight delay for readability in console

                    elif breakout_down and inside_counts[j] >= n_inside:
                        trade_id = gen_trade_id("Short", i)
                        trade_ids[j] = trade_id
                        trade_active[j] = True
                        pattern_range = mother_highs[j] - mother_lows[j]
                        take_profit = mother_lows[j] - (m_percent * 0.01 * pattern_range)
                        stop_loss   = mother_highs[j] + 2 * tick_size
                        target_prices[j], stop_prices[j] = take_profit, stop_loss

                        entry_price = current_close
                        print("\033[1;31m========== SHORT ENTRY =========\033[0m")
                        print(f"      OHLC: Open={current_open:.2f}   High={current_high:.2f}   Low={current_low:.2f}   Close={current_close:.2f}")
                        print(f"      Time: {current_time}")
                        print(f"     Entry: {entry_price:.2f}")
                        print(f" BASE High: {mother_highs[j]} | BASE Low: {mother_lows[j]}")
                        print(f"        TP: {take_profit:.2f} | SL: {stop_loss:.2f}")
                        print("================================\n")
                        time.sleep(0.5)  # slight delay for readability in console
                    else:
                        for arr in [mother_highs, mother_lows, inside_counts, trade_ids,
                                    trade_active, target_prices, stop_prices, start_indices]:
                            del arr[j]
            j -= 1

        # --- Check exits for active trades ---
               # --- Check exits for active trades ---
        idx = 0
        while idx < len(trade_ids):
            if not trade_active[idx]:
                idx += 1
                continue

            trade_side = "long" if trade_ids[idx].startswith("Long") else "short"
            take_profit, stop_loss = target_prices[idx], stop_prices[idx]
            exit_price, exit_reason = None, None

            if trade_side == "long":
                if current_high >= take_profit:
                    exit_price, exit_reason = take_profit, "Target"
                elif current_low <= stop_loss:
                    exit_price, exit_reason = stop_loss, "Stop"
                if exit_price:
                    pnl = (exit_price - entry_price) * contract_size * position_size - trade_cost
                    total_pnl += pnl
                    total_long_pnl += pnl

                    max_profit = max(max_profit, pnl)
                    max_loss   = min(max_loss, pnl)
                    if pnl > 0:
                        positive_pnl += pnl
                        total_positive_trades += 1
                    else:
                        negative_pnl += pnl
                        total_negative_trades += 1
                    num_of_trades += 1

                    print("\033[1;32m========== LONG EXIT =========\033[0m")
                    print(f"    OHLC      : Open={current_open:.2f}   High={current_high:.2f}   Low={current_low:.2f}   Close={current_close:.2f}")
                    print(f" Exit Time    : {current_time}")
                    print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                    print(f" Trade P&L    : {pnl:.2f}")
                    print(f" Cum. P&L     : {total_pnl:.2f}")
                    print("====================================================================\n")
                    time.sleep(0.5)  # slight delay for readability in console

                    for arr in [mother_highs, mother_lows, inside_counts, trade_ids,
                                trade_active, target_prices, stop_prices, start_indices]:
                        del arr[idx]
                    continue  # skip idx++ because we deleted
            else:  # short
                if current_low <= take_profit:
                    exit_price, exit_reason = take_profit, "Target"
                elif current_high >= stop_loss:
                    exit_price, exit_reason = stop_loss, "Stop"
                if exit_price:
                    pnl = (entry_price - exit_price) * contract_size * position_size - trade_cost
                    total_pnl += pnl
                    total_short_pnl += pnl

                    max_profit = max(max_profit, pnl)
                    max_loss   = min(max_loss, pnl)
                    if pnl > 0:
                        positive_pnl += pnl
                        total_positive_trades += 1
                    else:
                        negative_pnl += pnl
                        total_negative_trades += 1
                    num_of_trades += 1

                    print("\033[1;31m========== SHORT EXIT =========\033[0m")
                    print(f"  OHLC       : Open={current_open:.2f}   High={current_high:.2f}   Low={current_low:.2f}   Close={current_close:.2f}")
                    print(f" Exit Time    : {current_time}")
                    print(f" Exit Price   : {exit_price:.2f} | Reason: {exit_reason}")
                    print(f" Trade P&L    : {pnl:.2f}")
                    print(f" Cum. P&L     : {total_pnl:.2f}")
                    print("====================================================================\n")
                    time.sleep(0.5)  # slight delay for readability in console

                    for arr in [mother_highs, mother_lows, inside_counts, trade_ids,
                                trade_active, target_prices, stop_prices, start_indices]:
                        del arr[idx]
                    continue  # skip idx++ because we deleted

            idx += 1


    except Exception as e:
        print(f"Error at index {i}: {e}")

# ==================== SUMMARY ====================
TradeCost = num_of_trades * trade_cost
Net = total_pnl - TradeCost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades else 0

print("\n\033[1mTrading Performance Summary (Inside-Bar Breakout):\033[0m")
print(f"     Max Profit = {max_profit:.2f}")
print(f"       Max Loss = {max_loss:.2f}")
print(f"   Positive PnL = {positive_pnl:.2f}")
print(f"   Negative PnL = {negative_pnl:.2f}")
print(f" Total Long PnL = {total_long_pnl:.2f}")
print(f"Total Short PnL = {total_short_pnl:.2f}")
print(f"          Gross = {total_pnl:.2f}")
print(f"     Trade Cost = {TradeCost:.2f}")
print(f"            Net = {Net:.2f}")
print(f"Positive Trades = {total_positive_trades}")
print(f"Negative Trades = {total_negative_trades}")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = {success_rate:.2f}%")
print(f"   Failure Rate = {failure_rate:.2f}%")
