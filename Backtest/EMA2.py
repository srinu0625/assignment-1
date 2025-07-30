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

# Calculate EMA
n = 9  # Period for EMA
multiplier = 2 / (n + 1)
# Initialize the first EMA value using SMA
# Formula for calculating EMA
def calculate_ema(price_today, ema_yesterday, time_period):
    multiplier = 2 / (1 + time_period)
    ema = (price_today * multiplier) + (ema_yesterday * (1 - multiplier))
    return ema


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

# Iterate over each row to simulate trades based on EMA
for i in range(n, len(df)):  # Start from n to ensure EMA is available
    try:
        close_today = df['close'].iloc[i]  # Today's close price
        ema_yesterday = df['ema'].iloc[i-1]  # Yesterday's EMA
        ema = (close_today * multiplier) + (ema_yesterday * (1 - multiplier))  # EMA formula
        df.at[i, 'ema'] = ema  # Update the EMA for today (use .at to avoid warnings)
        
        ema = round(ema, 2)  # Current day's EMA
        date_time = df['Date (GMT)'].iloc[i]  # Date and Time for the current row

        # Print the current EMA along with the Date and Time at each index
        print(f"Index {i} - Date: {date_time} - EMA: {ema}")

        # LONG ENTRY: Current price > EMA (buy signal)
        if df['close'].iloc[i] > ema and position == 0:
            Entry_price = df['close'].iloc[i]  # Entry at the close of the current candle (long)
            Entry_time = date_time
            position = 1  # Long position
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {Entry_price}")
            print(f" Entry Date = {Entry_time}")
            print(f"EMA at entry: {ema}")

        # LONG EXIT: Current price < EMA (sell signal for long)
        elif df['close'].iloc[i] < ema and position == 1:
            Exit_price = df['close'].iloc[i]  # Exit at the close price of the current candle (long)
            Exit_time = date_time
            # Calculate P&L for long
            pnl = (Exit_price - Entry_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_long_pnl += pnl

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

            print("\033[32m<------ LONG EXIT ------>\033[0m")
            print(f" EXIT PRICE = {Exit_price}")
            print(f" Exit Date = {Exit_time}")
            print(f"EMA at exit: {ema}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {TOTAL_P_L}")
            print("-----------------------------------")
            position = 0  # Exit the long position

        # SHORT ENTRY: Current price < EMA (sell signal for short)
        elif df['close'].iloc[i] < ema and position == 0:
            Entry_price = df['close'].iloc[i]  # Entry at the close of the current candle (short)
            Entry_time = date_time
            position = 2  # Short position
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {Entry_price}")
            print(f" Entry Date = {Entry_time}")
            print(f"EMA at entry: {ema}")

        # SHORT EXIT: Current price > EMA (buy signal to exit short)
        elif df['close'].iloc[i] > ema and position == 2:
            Exit_price = df['close'].iloc[i]  # Exit at the close of the current candle (short)
            Exit_time = date_time
            # Calculate P&L for short
            pnl = (Entry_price - Exit_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
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

            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f" EXIT PRICE = {Exit_price}")
            print(f" Exit Date = {Exit_time}")
            print(f"EMA at exit: {ema}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {TOTAL_P_L}")
            print("-----------------------------------")
            position = 0  # Exit the short position

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
print(f"     Max Profit: \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss: \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL: \033[92m{positive_pnl:.2f}\033[0m")
print(f"   Negative PnL: \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL: \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL: \033[94m{total_short_pnl:.2f}\033[0m")
print(f"      Total P&L: \033[95m{TOTAL_P_L:.2f}\033[0m")
print(f"Positive Trades: \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades: \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades: {num_of_trades}")
print(f"   Success Rate: \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate: \033[91m{failure_rate:.2f}%\033[0m")
