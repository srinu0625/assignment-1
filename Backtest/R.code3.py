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

# Generate 'Signal' column based on simple logic:
# Buy signal when 'Last' price goes up compared to previous row, Sell signal when it goes down
df['Signal'] = 0  # Initialize with no signal (0)
df['Signal'][df['Last'].pct_change() > 0] = 1  # Buy signal when price increases
df['Signal'][df['Last'].pct_change() < 0] = -1  # Sell signal when price decreases

# Initialize variables
position = 0  # 0 = no position, 1 = in position
buy_price = 0
sell_price = 0
buy_time = None
sell_time = None
cumulative_pnl = 0
trades = []

# Define number of lots (for example purposes, we can set it to a fixed number or calculate based on available capital)
num_of_lots = 2  # Adjust this value according to your strategy

# Iterate over each row in the DataFrame
for i in range(1, len(df)):  # Start from 1 to avoid out-of-bounds error
    try:
        # Check if Signal is 1 (Buy) and we are not already in a position
        if df['Signal'].iloc[i] == 1 and position == 0:  # Buy
            buy_price = df['Last'].iloc[i]
            buy_time = df['Date (GMT)'].iloc[i]  # Record buy timestamp
            position = 1
            print("\033[32m<------ ENTRY ------>\033[0m")
            print(f" PRICE  =  {buy_price}")
            print(f"num_of_lots =  {num_of_lots}")
            print(f"Buying at {buy_price} on {buy_time}")
        
        # Check if Signal is -1 (Sell) and we are in a position
        elif df['Signal'].iloc[i] == -1 and position == 1:  # Sell
            sell_price = df['Last'].iloc[i]
            sell_time = df['Date (GMT)'].iloc[i]  # Record sell timestamp
            pnl = sell_price - buy_price  # Calculate P&L
            cumulative_pnl += pnl
            trades.append({
                'Buy Time': buy_time,
                'Buy Price': buy_price,
                'Sell Time': sell_time,
                'Sell Price': sell_price,
                'P&L': pnl,
                'Cumulative P&L': cumulative_pnl
            })
            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f" EXIT PRICE  =  {sell_price}")
            print(f"num_of_lots =  {num_of_lots}")
            print(f"Selling at {sell_price} on {sell_time}")
            print(f"P&L for this trade: {pnl}, Cumulative P&L: {cumulative_pnl}")
            print("-----------------------------------")
            position = 0  # Exit the position

    except Exception as e:
        print("Error:", e)

# After iterating through the rows, print the final results
print("\nSummary of trades:")
for trade in trades:
    print(trade)

print(f"Total Cumulative P&L: {cumulative_pnl}")
