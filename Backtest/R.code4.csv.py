import pandas as pd

file_path = r"C:\Users\lenovo\Downloads\ES 3.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", df.columns)

# Calculate 9-day Simple Moving Average (SMA)
df['SMA'] = df['Last'].rolling(window=9).mean()

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
Entry_price = Entry_time = Exit_price = Exit_time = 0
cumulative_pnl = total_long_pnl = total_short_pnl = TOTAL_P_L = 0
contract_size = 5  # Given contract size is 5
num_of_lots = 1  # Define number of lots (can be adjusted)

# Metrics for summary
num_of_trades = 0
total_positive_trades = 0
total_negative_trades = 0
max_profit = float('-inf')
max_loss = float('inf')

# Initialize list to store trades
trades = []

# Iterate over each row to simulate trades based on SMA
for i in range(9, len(df)):  # Start from 9 to ensure we have enough data for SMA calculation
    try:
        sma = round(df['SMA'].iloc[i], 2)  # Current day's SMA
        date_time = df['Date (GMT)'].iloc[i]  # Date and Time for the current row
        prev_sma = round(df['SMA'].iloc[i - 1], 2)  # Previous day's SMA

        # Print the current SMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - SMA: {sma}")

        # LONG ENTRY: Current price > SMA (buy signal)
        if df['High'].iloc[i] > sma and position == 0:
            Entry_price = df['High'].iloc[i]  # Entry at the high of the current candle (long)
            Entry_time = date_time
            position = 1  # Long position
            print(f"<------ LONG ENTRY ------>")
            print(f" ENTRY PRICE = {Entry_price}")
            print(f" Entry Date = {Entry_time}")
            print(f"SMA at entry: {sma}")

        # LONG EXIT: Current price < SMA (sell signal for long)
        elif df['Last'].iloc[i] < sma and position == 1:
            Exit_price = df['Last'].iloc[i]  # Exit at the last price of the current candle (long)
            Exit_time = date_time
            # Calculate P&L for long
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_long_pnl += pnl
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            num_of_trades += 1
            if pnl > 0:
                total_positive_trades += 1
            else:
                total_negative_trades += 1
            trades.append({
                'Type': 'LONG',
                'Entry': Entry_price,
                'Exit': Exit_price,
                'P&L': pnl,
                'Entry Time': Entry_time,
                'Exit Time': Exit_time
            })
            print(f"<------ LONG EXIT ------>")
            print(f" EXIT PRICE = {Exit_price}")
            print(f" Exit Date = {Exit_time}")
            print(f"SMA at exit: {sma}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {TOTAL_P_L}")
            print("-----------------------------------")
            position = 0  # Exit the long position

        # SHORT ENTRY: Current price < SMA (sell signal for short)
        elif df['Low'].iloc[i] < sma and position == 0:
            Entry_price = df['Low'].iloc[i]  # Entry at the low of the current candle (short)
            Entry_time = date_time
            position = 2  # Short position
            print(f"<------ SHORT ENTRY ------>")
            print(f" ENTRY PRICE = {Entry_price}")
            print(f" Entry Date = {Entry_time}")
            print(f"SMA at entry: {sma}")

        # SHORT EXIT: Current price > SMA (buy signal to exit short)
        elif df['High'].iloc[i] > sma and position == 2:
            Exit_price = df['High'].iloc[i]  # Exit at the high of the current candle (short)
            Exit_time = date_time
            # Calculate P&L for short
            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_short_pnl += pnl
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)
            num_of_trades += 1
            if pnl > 0:
                total_positive_trades += 1
            else:
                total_negative_trades += 1
            trades.append({
                'Type': 'SHORT',
                'Entry': Entry_price,
                'Exit': Exit_price,
                'P&L': pnl,
                'Entry Time': Entry_time,
                'Exit Time': Exit_time
            })
            print(f"<------ SHORT EXIT ------>")
            print(f" EXIT PRICE = {Exit_price}")
            print(f" Exit Date = {Exit_time}")
            print(f"SMA at exit: {sma}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {TOTAL_P_L}")
            print("-----------------------------------")
            position = 0  # Exit the short position

    except Exception as e:
        print("Error:", e)

# Adding colors for clarity
max_profit_color = '\033[92m'
max_loss_color = '\033[91m'
total_long_pnl_color = '\033[94m'
total_short_pnl_color = '\033[94m'
TOTAL_P_L_colour = '\033[95m'

# Print summary metrics
print("        max_profit = ", max_profit_color, round(max_profit, 2), "\033[0m")
print("          max_loss = ", max_loss_color, round(max_loss, 2), "\033[0m")
print("   total_long_pnl  = ", total_long_pnl_color, round(total_long_pnl, 2), "\033[0m")
print("  total_short_pnl  = ", total_short_pnl_color, round(total_short_pnl, 2), "\033[0m")
print("         TOTAL_P_L = ", TOTAL_P_L_colour, round(TOTAL_P_L, 2), "\033[0m")
print("     num of trades = ", num_of_trades)
print(" Total Positive Trades =", total_positive_trades)
print(" Total Negative Trades =", total_negative_trades)
