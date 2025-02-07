import pandas as pd

# Load CSV data
file_path = r"D:\candles\snp 5min.csv"  # Replace with your file path

try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Inspect and print column names
print("Column names :", df.columns)

# Convert the 'Date (GMT)' column to datetime
try:
    df['Date (GMT)'] = pd.to_datetime(df['Date (GMT)'], format='%d-%m-%Y %H:%M', dayfirst=True)
except Exception as e:
    print("Error parsing dates:", e)
    exit()

# Set 'Date (GMT)' as the index
df.set_index('Date (GMT)', inplace=True)

# Rename columns to lowercase (optional for consistency)
df.columns = df.columns.str.lower()

# Dynamic time interval for resampling (set it here)
time_interval = '120min'  # Change to '5min', '15min', '30min', etc.

# Resample the data dynamically
df_resampled = df.resample(time_interval).agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
}).dropna()

# Calculate SMA for the resampled data
n = 20 # SMA period
df_resampled['sma'] = df_resampled['close'].rolling(window=n).mean()

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
Gross = trade_cost = 0
entry_price = exit_time = entry_time = exit_price = 0
cumulative_pnl = total_long_pnl = total_short_pnl = total_pnl = 0 
Trade_cost = 1.30
contract_size = 5
num_of_lots = 1

Net = Gross - trade_cost
max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = 0
negative_pnl = 0
total_positive_trades = 0
total_negative_trades = 0
num_of_trades = 0

# Iterate over each row in the resampled data
for i in range(n, len(df_resampled)):
    try:
        sma = round(df_resampled['sma'].iloc[i], 2)
        date_time = df_resampled.index[i]  # Date and time for the current row

        # Print the current SMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - SMA: {sma}")

        # LONG ENTRY: Current price > SMA (buy signal)
        if df_resampled['close'].iloc[i] > sma and position == 0:
            entry_price = df_resampled['close'].iloc[i]
            entry_time = date_time
            position = 1
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f" Entry Date = {entry_time}")
            print(f"SMA at entry: {sma}")

        # LONG EXIT: Current price < SMA (sell signal for long)
        elif df_resampled['close'].iloc[i] < sma and position == 1:
            exit_price = df_resampled['close'].iloc[i]
            exit_time = date_time
            pnl = (exit_price - entry_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_long_pnl += pnl

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

            print("\033[32m<------ LONG EXIT ------>\033[0m")
            print(f" EXIT PRICE = {exit_price}")
            print(f" Exit Date = {exit_time}")
            print(f"SMA at exit: {sma}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {total_pnl}")
            print("-----------------------------------")
            position = 0

        # SHORT ENTRY: Current price < SMA (sell signal for short)
        elif df_resampled['close'].iloc[i] < sma and position == 0:
            entry_price = df_resampled['close'].iloc[i]
            entry_time = date_time
            position = 2
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f" Entry Date = {entry_time}")
            print(f"SMA at entry: {sma}")

        # SHORT EXIT: Current price > SMA (buy signal to exit short)
        elif df_resampled['close'].iloc[i] > sma and position == 2:
            exit_price = df_resampled['close'].iloc[i]
            exit_time = date_time
            pnl = (entry_price - exit_price) * num_of_lots * contract_size
            total_pnl += pnl
            total_short_pnl += pnl

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

            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f" EXIT PRICE = {exit_price}")
            print(f" Exit Date = {exit_time}")
            print(f"SMA at exit: {sma}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {total_pnl}")
            print("-----------------------------------")
            position = 0

    except Exception as e:
        print("Error:", e)

# Summary statistics
if num_of_trades > 0:
    success_rate = (total_positive_trades / num_of_trades) * 100 if num_of_trades > 0 else 0
    failure_rate = (total_negative_trades / num_of_trades) * 100 if num_of_trades > 0 else 0
else:
    success_rate = 0
    failure_rate = 0
print("\nTrading Performance Summary:")
# Additional summary statistics
print("\nTrading Performance Summary:")
print(f"     Max Profit: \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss: \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL: \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL: \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL: \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL: \033[94m{total_short_pnl:.2f}\033[0m")
print(f"          Gross: {total_pnl}")
print(f"     trade_cost: {num_of_trades * 1.30}")
print(f"            Net: {total_pnl - num_of_trades * 1.30}")
print(f"Positive Trades: \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades: \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades: {num_of_trades}")
print(f"   Success Rate: \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate: \033[91m{failure_rate:.2f}%\033[0m")
