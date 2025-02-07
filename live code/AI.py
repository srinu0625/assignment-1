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
time_interval = '60min'  # Change to '5min', '15min', '30min', etc.

# Resample the data dynamically
df_resampled = df.resample(time_interval).agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
}).dropna()

# Calculate SMA for the resampled data
n = 9  # SMA period
df_resampled['sma'] = df_resampled['close'].rolling(window=n).mean()

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
entry_price = exit_time = entry_time = exit_price = 0
cumulative_pnl = total_long_pnl = total_short_pnl = total_pnl = 0 
Trade_cost = 1.30
contract_size = 5
num_of_lots = 1
max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = 0
negative_pnl = 0
total_positive_trades = 0
total_negative_trades = 0
num_of_trades = 0

# Max Drawdown variables
equity_curve = []  # Track cumulative P&L for each trade
max_drawdown = 0
peak_equity = 0

# Iterate over each row in the resampled data
for i in range(n, len(df_resampled)):
    try:
        sma = round(df_resampled['sma'].iloc[i], 2)
        date_time = df_resampled.index[i]  # Date and time for the current row

        # LONG ENTRY: Current price > SMA (buy signal)
        if df_resampled['close'].iloc[i] > sma and position == 0:
            entry_price = df_resampled['close'].iloc[i]
            entry_time = date_time
            position = 1
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f" Entry Date = {entry_time}")

        # LONG EXIT: Current price < SMA (sell signal for long)
        elif df_resampled['close'].iloc[i] < sma and position == 1:
            exit_price = df_resampled['close'].iloc[i]
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
            print(f" EXIT PRICE = {exit_price}")
            print(f" Exit Date = {exit_time}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {total_pnl}")
            print(f"Current Drawdown: {drawdown}, Max Drawdown: {max_drawdown}")
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

        # SHORT EXIT: Current price > SMA (buy signal to exit short)
        elif df_resampled['close'].iloc[i] > sma and position == 2:
            exit_price = df_resampled['close'].iloc[i]
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

            # Calculate Drawdown
            peak_equity = max(peak_equity, total_pnl)
            drawdown = peak_equity - total_pnl
            max_drawdown = max(max_drawdown, drawdown)

            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f" EXIT PRICE = {exit_price}")
            print(f" Exit Date = {exit_time}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {total_pnl}")
            print(f"Current Drawdown: {drawdown}, Max Drawdown: {max_drawdown}")
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
print(f"     Max Profit: {max_profit}")
print(f"       Max Loss: {max_loss}")
print(f"   Positive PnL: {positive_pnl}")
print(f"   Negative PnL: {negative_pnl}")
print(f" Total Long PnL: {total_long_pnl}")
print(f"Total Short PnL: {total_short_pnl}")
print(f"          Gross: {total_pnl}")
print(f"     trade_cost: {num_of_trades * Trade_cost}")
print(f"            Net: {total_pnl - num_of_trades * Trade_cost}")
print(f"Positive Trades: {total_positive_trades}")
print(f"Negative Trades: {total_negative_trades}")
print(f"   Total Trades: {num_of_trades}")
print(f"   Success Rate: {success_rate}%")
print(f"   Failure Rate: {failure_rate}%")
print(f"Max Drawdown: {max_drawdown}")
