import pandas as pd

file_path = r"D:\candles\snp 1W.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", df.columns)

# Calculate 100-day Simple Moving Average (SMA)
n = 9
df['SMA'] = df['close'].rolling(window=n).mean()

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
Entry_price = Exit_time = Entry_time = Exit_price = 0
cumulative_pnl = total_long_pnl = total_short_pnl = total_pnl = 0
Gross = trade_cost = 0
Trade_cost = 1.30
contract_size = 5 # Given contract size is 5
num_of_lots = 1  # Define number of lots (can be adjusted)

max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = 0
negative_pnl = 0
total_positive_trades = 0
total_negative_trades = 0
num_of_trades = 0

# Max Drawdown variables
equity_curve = []  # Track cumulative P&L for each trade
max_runup = 0
max_drawdown = 0
peak_equity = 0

# Initialize list to store trades
trades = []

# Iterate over each row to simulate trades based on SMA
for i in range(n, len(df)):  # Start from 5 to ensure we have enough data for SMA calculation
    try:
        sma = round(df['SMA'].iloc[i], 2)  # Current day's SMA
        date_time = df['Date (GMT)'].iloc[i]  # Date and Time for the current row
        prev_sma = round(df['SMA'].iloc[i], 2)  # Previous day's SMA

        # Print the current SMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - SMA: {sma}")

        # LONG ENTRY: Current price > SMA (buy signal)
        if df['close'].iloc[i] > sma and position == 0:
            entry_price = df['close'].iloc[i]
            entry_time = date_time
            position = 1
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f"  Entry Date = {entry_time}")
            print(f"SMA at entry ={sma}")
            print("----------------------------------------------")

        # LONG EXIT: Current price < SMA (sell signal for long)
        elif df['close'].iloc[i] < sma and position == 1:
            exit_price = df['close'].iloc[i]
            exit_time = date_time
            pnl = (exit_price - entry_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl
            equity_curve.append(total_pnl)  # Update equity curve


            # Update max profit, max loss, positive/negative PnL
            if pnl > max_profit:
                max_profit = pnl
            if pnl < max_loss:
                max_loss = pnl
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1

            # Calculate Drawdown
            peak_equity = max(peak_equity, total_pnl)
            drawdown = peak_equity - total_pnl
            max_drawdown = max(max_drawdown, drawdown)

            print("\033[32m<------ LONG EXIT ------>\033[0m")
            print(f"        EXIT PRICE = {exit_price}")
            print(f"         Exit Date = {exit_time}")
            print(f"      SMA at entry = {sma}")
            print(f"P&L for this trade = {pnl}, Cumulative P&L: {total_pnl}")
            print(f"  Current Drawdown = {pnl}, Max Drawdown: {max_drawdown}")
            print("-----------------------------------")
            position = 0

        # SHORT ENTRY: Current price < SMA (sell signal for short)
        elif df['close'].iloc[i] < sma and position == 0:
            entry_price = df['close'].iloc[i]
            entry_time = date_time
            position = 2
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f"  Entry Date = {entry_time}")
            print(f"SMA at entry = {sma}")
            print("----------------------------------------------")

        # SHORT EXIT: Current price > SMA (buy signal to exit short)
        elif df['close'].iloc[i] > sma and position == 2:
            exit_price = df['close'].iloc[i]
            exit_time = date_time
            pnl = (entry_price - exit_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_short_pnl += pnl
            equity_curve.append(total_pnl)  # Update equity curve

            # Update max profit, max loss, positive/negative PnL
            if pnl > max_profit:
                max_profit = pnl
            if pnl < max_loss:
                max_loss = pnl
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1

            # Update max run-up and drawdown
            peak_equity = max(peak_equity, cumulative_pnl)  # Update peak equity
            drawdown = peak_equity - cumulative_pnl  # Calculate drawdown
            runup = cumulative_pnl - peak_equity  # Calculate run-up

            max_drawdown = max(max_drawdown, drawdown)
            max_runup = max(max_runup, runup)

            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f"        EXIT PRICE  = {exit_price}")
            print(f"         Exit Date  = {exit_time}")
            print(f"       SMA at exit  = {sma}")
            print(f" P&L for this trade = {pnl}, Cumulative P&L: {total_pnl}")
            print(f"   Current Drawdown = {pnl}, Max Drawdown: {max_drawdown}")
            print("-----------------------------------")
            position = 0

    except Exception as e:
        print("Error:", e)

# Calculate success rate and failure rate
if num_of_trades > 0:  # To avoid division by zero
    success_rate = (total_positive_trades / num_of_trades) * 100
    failure_rate = (total_negative_trades / num_of_trades) * 100
else:
    success_rate = 0
    failure_rate = 0

# Additional summary statistics
print("\nTrading Performance Summary:")
print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl:.2f}\033[0m")
print(f"          Gross = {total_pnl}")
print(f"     trade_cost = {num_of_trades * 1.30}")
print(f"            Net = {total_pnl - num_of_trades * 1.30}")
print(f"   Max Drawdown = {max_drawdown}")
print(f"     Max run_up = {max_runup}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")
