import pandas as pd

file_path = r"C:\Users\lenovo\Downloads\ES 1 HOUR.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", df.columns)

# Calculate 9-day Simple Moving Average (SMA)
df['SMA'] = df['close'].rolling(window=9).mean()

# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
# Initialize variables
position = 0  # 0 = no position, 1 = in long position, 2 = in short position
Entry_price = Exit_time = Entry_time = Exit_price = 0
cumulative_pnl = total_long_pnl = total_short_pnl = TOTAL_P_L = 0
contract_size = 5  # Given contract size is 5
num_of_lots = 1  # Define number of lots (can be adjusted)
max_profit = float('-inf')
max_loss = float('inf')
positive_pnl = 0
negative_pnl = 0
total_positive_trades = 0
total_negative_trades = 0
num_of_trades = 0

# Initialize list to store trades
trades = []

# Iterate over each row to simulate trades based on SMA
for i in range(9, len(df)):  # Start from 9 to ensure we have enough data for SMA calculation
    try:
        sma = round(df['SMA'].iloc[i],2)  # Current day's SMA
        date_time = df['Date (GMT)'].iloc[i]  # Date and Time for the current row
        prev_sma = round(df['SMA'].iloc[i-1],2)  # Previous day's SMA

        # Print the current SMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - SMA: {sma}")

        # LONG ENTRY: Current price > SMA (buy signal)
        if df['High'].iloc[i] > sma and position == 0:
            Entry_price = df['High'].iloc[i]  # Entry at the high of the current candle (long)
            Entry_time = date_time
            position = 1  # Long position
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {Entry_price}")
            print(f" Entry Date = {Entry_time}")
            print(f"SMA at entry: {sma}")

        # LONG EXIT: Current price < SMA (sell signal for long)
        elif df['Low'].iloc[i] < sma and position == 1:
            Exit_price = df['Low'].iloc[i]  # Exit at the last price of the current candle (long)
            Exit_time = date_time
            # Calculate P&L for long
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_long_pnl += pnl
            integer_pnl = float(pnl)  # Extract the integer part of the P&L
           
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
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")
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
            integer_pnl = float(pnl)  # Extract the integer part of the P&L
           
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
            print(f" EXIT PRICE = {Exit_price}")
            print(f" Exit Date = {Exit_time}")
            print(f"SMA at exit: {sma}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {TOTAL_P_L}")
            print("-----------------------------------")
            position = 0  # Exit the short position

    except Exception as e:
        print("Error:", e)

print(f"Total Cumulative P&L: {TOTAL_P_L}")
print(f"Total Long P&L: {total_long_pnl}")
print(f"Total Short P&L: {total_short_pnl}")

# Additional summary statistics
max_profit_color = '\033[92m'  # Green color
max_loss_color = '\033[91m'    # Red color
positive_pnl_color = '\033[92m'  # Green color
negative_pnl_color = '\033[91m'  # Red color
total_long_pnl_color = '\033[94m'  # Blue color
total_short_pnl_color = '\033[94m'  # Blue color
TOTAL_P_L_colour = '\033[95m'  # Purple color

print("           max_profit = ", max_profit_color, round(max_profit, 2), "\033[0m")
print("             max_loss = ", max_loss_color, round(max_loss, 2), "\033[0m")
print("         positive_pnl = ", positive_pnl_color, round(positive_pnl, 2), "\033[0m")
print("         negative_pnl = ", negative_pnl_color, round(negative_pnl, 2), "\033[0m")
print("      total_long_pnl  = ", total_long_pnl_color, round(total_long_pnl, 2), "\033[0m")
print("     total_short_pnl  = ", total_short_pnl_color, round(total_short_pnl, 2), "\033[0m")
print("            TOTAL_P_L = ", TOTAL_P_L_colour, round(TOTAL_P_L, 2), "\033[0m")
print("        num of trades = ", num_of_trades)
print("Total Positive Trades =", total_positive_trades)
print("Total Negative Trades =", total_negative_trades)
