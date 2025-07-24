import pandas as pd
import os
import time
import re
import matplotlib.pyplot as plt

file_path = r"D:\Data\ES jun25_5min.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

print("Column names:", df.columns)

# EMA Parameters
n = 20
df['ema'] = df['Close'].ewm(span=n, adjust=False).mean()

# RSI Parameters
rsi_period = 14
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
rs = avg_gain / avg_loss
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].round(2)

# RSI % Change (5d)
df['rsi_pct_change_5d'] = df['rsi'].pct_change(periods=5) * 100
df['rsi_pct_change_5d'] = df['rsi_pct_change_5d'].round(2)

# Strategy Variables
position = 0
Entry_price = Exit_time = Entry_time = Exit_price = 0
total_long_pnl = total_short_pnl = total_pnl = 0
contract_size = 50
num_of_lots = 1
trade_cost = 1.30

max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = negative_pnl = 0
total_positive_trades = total_negative_trades = num_of_trades = 0
equity_curve = []
highest_equity = 0
lowest_equity = 0
max_drawdown = 0
max_runup = 0
rsi_value     = 55
rsi_pct_value = 5

stop_loss     = 20  # in points
take_profit   = 30  # in points

trades = []

# MAIN LOOP
for i in range(max(n, rsi_period, 5), len(df)):
    try:
        close_today = df['Close'].iloc[i]
        ema = df['ema'].iloc[i]
        high = df['High'].iloc[i]
        low = df['Low'].iloc[i]
        open_today = df['Open'].iloc[i]
        rsi = df['rsi'].iloc[i]
        rsi_pct = df['rsi_pct_change_5d'].iloc[i]
        date_time = df['Date(GMT)'].iloc[i]

        # LONG ENTRY
        if close_today > ema and (rsi >= rsi_value or rsi_pct > rsi_pct_value) and position == 0:
            Entry_price = close_today
            Entry_time = date_time
            position = 1
            print("\033[1;32m========== LONG ENTRY =========\033[0m")
            print(f" entry PRICE     = {Entry_price}")
            print(f" entry Date      = {Entry_time}")
            print(f" EMA at entry    = {ema}")
            print(f" RSI at entry    = {rsi} (+{rsi_pct}%)")
            print(f" High = {high}, Low = {low}")
            print("================================")
            time.sleep(0.2)
# 

        # LONG EXIT
        elif position == 1 and (
                close_today < ema or
                close_today <= Entry_price - stop_loss or
                close_today >= Entry_price + take_profit or
                rsi <= rsi_value or
                rsi_pct < rsi_pct_value
            ):
            
            Exit_price = close_today
            Exit_time = date_time

            # Determine reason
            if close_today >= Entry_price + take_profit:
                exit_reason = "TP"
            elif close_today <= Entry_price - stop_loss:
                exit_reason = "SL"
            else:
                exit_reason = "ExitCond"

            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
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

            # Print
            print("\033[1;32m========== LONG EXIT =========\033[0m")
            print(f" exit PRICE      = {Exit_price}")
            print(f" exit Date       = {Exit_time}")
            print(f" Exit Reason     = {exit_reason}")
            print(f" RSI at exit     = {rsi} ({rsi_pct}%)")
            print(f" High = {high}, Low = {low}")
            print(f" Trade P&L       = {pnl},    Cumulative P&L = {total_pnl}")
            print(f" Drawdown        = {drawdown}, Max Drawdown = {max_drawdown}")
            print(f" Run-up          = {runup},   Max Run-up    = {max_runup}")
            print("================================")
            time.sleep(0.2)

            # Save trade
            # trades.append({
            #     "Type": "Long",
            #     "EntryTime": Entry_time,
            #     "EntryPrice": Entry_price,
            #     "ExitTime": Exit_time,
            #     "ExitPrice": Exit_price,
            #     "P&L": pnl,
            #     "Reason": exit_reason
            # })

            position = 0


        # SHORT ENTRY
        elif close_today < ema and (rsi <= rsi_value or rsi_pct < rsi_pct_value) and position == 0:
            Entry_price = close_today
            Entry_time = date_time
            position = 2
            print("\033[1;31m========== SHORT ENTRY =========\033[0m")
            print(f" entry PRICE     = {Entry_price}")
            print(f" entry Date      = {Entry_time}")
            print(f" EMA at entry    = {ema}")
            print(f" RSI at entry    = {rsi} ({rsi_pct}%)")
            print(f" High = {high}, Low = {low}")
            print("================================")
            time.sleep(0.2)


        # SHORT EXIT
        elif position == 2 and (
                close_today > ema or
                close_today >= Entry_price + stop_loss or
                close_today <= Entry_price - take_profit or
                rsi >= rsi_value or
                rsi_pct > rsi_pct_value
            ):

            
            Exit_price = close_today
            Exit_time = date_time

            # Determine reason
            if close_today <= Entry_price - take_profit:
                exit_reason = "TP"
            elif close_today >= Entry_price + stop_loss:
                exit_reason = "SL"
            else:
                exit_reason = "ExitCond"

            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
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

            # Print
            print("\033[1;31m========== SHORT EXIT =========\033[0m")
            print(f" exit PRICE      = {Exit_price}")
            print(f" exit Date       = {Exit_time}")
            print(f" Exit Reason     = {exit_reason}")
            print(f" RSI at exit     = {rsi} ({rsi_pct}%)")
            print(f" High = {high}, Low = {low}")
            print(f" Trade P&L       = {pnl},    Cumulative P&L = {total_pnl}")
            print(f" Drawdown        = {drawdown}, Max Drawdown = {max_drawdown}")
            print(f" Run-up          = {runup},   Max Run-up    = {max_runup}")
            print("================================")
            time.sleep(0.2)

            # Save trade
            # trades.append({
            #     "Type": "Short",
            #     "EntryTime": Entry_time,
            #     "EntryPrice": Entry_price,
            #     "ExitTime": Exit_time,
            #     "ExitPrice": Exit_price,
            #     "P&L": pnl,
            #     "Reason": exit_reason
            # })

            position = 0


    except Exception as e:
        print("Error:", e)

# Summary
Net = total_pnl - num_of_trades * trade_cost
TradeCost = num_of_trades * trade_cost
success_rate = round((total_positive_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0
failure_rate = round((total_negative_trades / num_of_trades) * 100, 2) if num_of_trades > 0 else 0

file_name = os.path.basename(file_path)
match = re.search(r'([A-Z]+)\s+(\w+)_([a-zA-Z0-9]+)', file_name)
if match:
    product = match.group(1)
    timeframe = match.group(3)
    print(f"\n\033[1mTrading Performance Summary for {product} {timeframe} EMA + RSI % Change:\033[0m")
else:
    print("\n\033[1mTrading Performance Summary:\033[0m")

print(f"     Max Profit = \033[92m{max_profit}\033[0m")
print(f"       Max Loss = \033[91m{max_loss}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl}\033[0m")
print(f"          Gross = {total_pnl}")
print(f"     Trade Cost = {round(TradeCost,2)}")
print(f"            Net = {Net}")
print(f"   Max Drawdown = {max_drawdown}")
print(f"     Max Run-up = {max_runup}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")

# Save trade log to CSV
trades_df = pd.DataFrame(trades)
trades_df.to_csv("trades_log.csv", index=False)

# Plot Equity Curve
plt.plot(equity_curve)
plt.title("Equity Curve")
plt.xlabel("Trade Number")
plt.ylabel("Cumulative P&L")
plt.grid(True)
plt.show()
