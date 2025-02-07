import pandas as pd

file_path = r"D:\candles\snp daily.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", df.columns)

# Calculate EMA
n = 100  # Period for EMA
multiplier = 2 / (n + 1)
# Initialize the first EMA value using SMA
df['ema'] = df['close'].rolling(window=n).mean()  # Initial SMA for first n periods

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
Entry_price = Exit_time = Entry_time = Exit_price = 0
cumulative_pnl = total_long_pnl = total_short_pnl = total_pnl = 0
contract_size = 5  # Given contract size is 5
num_of_lots = 1  # Define number of lots (can be adjusted)
trade_cost = 1.30

max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = negative_pnl = 0
total_positive_trades = total_negative_trades = num_of_trades = 0

# Max Drawdown and Run-up variables
equity_curve = []  # Track cumulative P&L for each trade
highest_equity = 0  # Tracks the highest equity value so far
lowest_equity = 0  # Tracks the lowest equity value so far
max_drawdown = 0
max_runup = 0

# Iterate over each row to simulate trades based on EMA
for i in range(n, len(df)):  # Start from n to ensure EMA is available
    try:
        close_today = df['close'].iloc[i]  # Today's close price
        ema_yesterday = df['ema'].iloc[i-1]  # Yesterday's EMA
        ema = (close_today * multiplier) + (ema_yesterday * (1 - multiplier))  # EMA formula
        df.at[i, 'ema'] = ema  # Update the EMA for today (use .at to avoid warnings)
        
        ema = round(ema,2)  # Current day's EMA
        date_time = df['Date (GMT)'].iloc[i]  # Date and Time for the current row

        # Print the current EMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - EMA: {ema}")

        # LONG entry: Current price > EMA (buy signal)
        if df['close'].iloc[i] > ema and position == 0:
            Entry_price = df['close'].iloc[i]  # entry at the close of the current candle (long)
            Entry_time = date_time
            position = 1  # Long position
            print("\033[32m<------ LONG entry ------>\033[0m")
            print(f" entry PRICE = {Entry_price}")
            print(f"  entry Date = {Entry_time}")
            print(f"EMA at entry = {ema}")
            print("-----------------------------------------")

        # LONG exit: Current price < EMA (sell signal for long)
        elif df['Low'].iloc[i] < ema and position == 1:
            Exit_price = df['close'].iloc[i]  # exit at the close price of the current candle (long)
            Exit_time = date_time
            # Calculate P&L for long
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl
            equity_curve.append(total_pnl)  # Update equity curve

            # Update max profit, max loss, positive/negative PnL
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1

            # Update Peak Equity and Trough Equity
            highest_equity = max(highest_equity, total_pnl)  # Update peak equity
            lowest_equity = min(lowest_equity, total_pnl)  # Update trough equity

            # Calculate Drawdown and Run-up
            drawdown = highest_equity - total_pnl
            runup = total_pnl - lowest_equity
            max_drawdown = max(max_drawdown, drawdown)
            max_runup = max(max_runup, runup)

            print("\033[32m<------ LONG exit ------>\033[0m")
            print(f" exit PRICE = {Exit_price}")
            print(f" exit Date = {Exit_time}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {total_pnl}")
            print(f"Current Drawdown: {drawdown}, Max Drawdown: {max_drawdown}")
            print(f"Current Run-up: {runup}, Max Run-up: {max_runup}")
            print("-------------------------------------------------")
            position = 0

        # SHORT entry: Current price < EMA (sell signal for short)
        elif df['close'].iloc[i] < ema and position == 0:
            Entry_price = df['close'].iloc[i]  # entry at the close of the current candle (short)
            Entry_time = date_time
            position = 2  # Short position
            print("\033[31m<------ SHORT entry ------>\033[0m")
            print(f" entry PRICE = {Entry_price}")
            print(f" entry Date = {Entry_time}")
            print(f"EMA at entry: {ema}")

        # SHORT exit: Current price > EMA (buy signal to exit short)
        elif df['High'].iloc[i] > ema and position == 2:
            Exit_price = df['close'].iloc[i]  # exit at the close of the current candle (short)
            Exit_time = date_time
            # Calculate P&L for short
            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_short_pnl += pnl

            # Update max profit, max loss, positive/negative PnL
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            if pnl > 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1
            num_of_trades += 1

            # Update Peak Equity and Trough Equity
            highest_equity = max(highest_equity, total_pnl)  # Update peak equity
            lowest_equity = min(lowest_equity, total_pnl)  # Update trough equity

            # Calculate Drawdown and Run-up
            drawdown = highest_equity - total_pnl
            runup = total_pnl - lowest_equity
            max_drawdown = max(max_drawdown, drawdown)
            max_runup = max(max_runup, runup)

            print("\033[31m<------ SHORT exit ------>\033[0m")
            print(f"        exit PRICE = {Exit_price}")
            print(f"         exit Date = {Exit_time}")
            print(f"P&L for this trade = {pnl}, Cumulative P&L = {total_pnl}")
            print(f"  Current Drawdown = {drawdown}, Max Drawdown = {max_drawdown}")
            print(f"    Current Run-up = {runup}, Max Run-up = {max_runup}")
            print("-------------------------------------------------------")
            position = 0
    except Exception as e:
        print("Error:", e)

# Calculate success rate and failure rate

Net = total_pnl - num_of_trades * trade_cost
TradeCost = num_of_trades * trade_cost
if num_of_trades > 0:  # To avoid division by zero
    success_rate = round((total_positive_trades / num_of_trades) * 100, 2)
    failure_rate = round((total_negative_trades / num_of_trades) * 100, 2)
else:
    success_rate = 0
    failure_rate = 0

#  Additional summary statistics
print("\nTrading Performance Summary:")
print(f"     Max Profit = \033[92m{max_profit}\033[0m")
print(f"       Max Loss = \033[91m{max_loss}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl}\033[0m")
print(f"   Negative PnL = \033[91m{negative_pnl}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl}\033[0m")
print(f"          Gross = {total_pnl}")
print(f"     Trade Cost = {TradeCost}")
print(f"            Net = {Net}")
print(f"   Max Drawdown = {max_drawdown}")
print(f"     Max Run-up = {max_runup}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")



#  Additional summary statistics
print("\nTrading Performance Summary:")

print(f"{max_profit}")
print(f"{max_loss}")
print(f"{positive_pnl}")
print(f"{negative_pnl}")
print(f"{total_long_pnl}")
print(f"{total_short_pnl}")
print(f"{total_pnl}")
print(f"{TradeCost}")
print(f"{Net}")
print(f"{max_drawdown}")
print(f"{max_runup}")
print(f"{total_positive_trades}")
print(f"{total_negative_trades}")
print(f"{num_of_trades}")
print(f"{success_rate}%")
print(f"{failure_rate}%")

print("------------")