import pandas as pd

file_path = r"D:\candles\snp 5min.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Verify column names
print("Column names:", df.columns)

# Calculate 9-day Simple Moving Average (SMA)
position = 0  # 0 = no position, 1 = long, -1 = short
n = 9
try:
    df['SMA'] = df['close'].rolling(window=n).mean()
except KeyError:
    print("Column 'close' not found in the data. Please check the file.")
    exit()

# Initialize variables
trend_data = []  # To store trend information

# Iterate through the rows of the dataframe
for i in range(n + 3, len(df)):  # Start after ensuring enough SMA values
    try:
        # Extract consecutive SMA values
        sma_t4 = round(df['SMA'].iloc[i - 3], 2)
        sma_t3 = round(df['SMA'].iloc[i - 2], 2)
        sma_t2 = round(df['SMA'].iloc[i - 1], 2)
        sma_t1 = round(df['SMA'].iloc[i], 2)

        # Extract corresponding close prices at SMA levels
        close_t4 = df['close'].iloc[i - 3]
        close_t3 = df['close'].iloc[i - 2]
        close_t2 = df['close'].iloc[i - 1]
        close_t1 = df['close'].iloc[i]

        # Extract current date and time
        date_time = df['Date (GMT)'].iloc[i]

        # Determine the trend
        if sma_t4 < sma_t3 < sma_t2 < sma_t1 and position == 0:  # Bullish trend
            entry_price = close_t1  # Close price at SMA_t1
            entry_time = date_time
            position = 1  # Long position
            print("\033[32m<------ LONG ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f"  Entry Date = {entry_time}")
            print(f" SMA at entry = {sma_t1}")
            print("-----------------------------------------")
            sma_trend_status = "Ultimate Bullish, ↗️ , ↑ , 📈 ,[4 < 3 < 2 < 1]"

        elif close_t4 < close_t3 and position == 1:  # Bearish reversal (Exit long position)
            exit_price = close_t3  # Close price at SMA_t3
            exit_time = date_time
            position = 0  # Exit long position
            print("\033[32m<------ LONG EXIT ------>\033[0m")
            print(f"    EXIT PRICE = {exit_price}")
            print(f"     Exit time = {exit_time}")
            print(f" SMA at exit = {sma_t2}")
            print("-----------------------------------------")

        elif sma_t4 > sma_t3 > sma_t2 > sma_t1 and position == 0:  # Bearish trend
            entry_price = close_t4  # Close price at SMA_t4
            entry_time = date_time
            position = -1  # Short position
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")
            print(f" ENTRY PRICE = {entry_price}")
            print(f"  Entry Date = {entry_time}")
            print(f" SMA at entry = {sma_t4}")
            print("------------------------------------------")
            sma_trend_status = "Ultimate Bearish, ↘️ , ↓ , 📉 ,[4 > 3 > 2 > 1]"

        elif close_t4 > close_t3 and position == -1:  # Bullish reversal (Exit short position)
            exit_price = close_t4  # Close price at SMA_t4
            exit_time = date_time
            position = 0  # Exit short position
            print("\033[31m<------ SHORT EXIT ------>\033[0m")
            print(f"    EXIT PRICE = {exit_price}")
            print(f"     Exit time = {exit_time}")
            print(f" SMA at exit = {sma_t3}")
            print("-----------------------------------------")

        # Append the trend data for visualization or analysis
        trend_data.append((date_time, sma_trend_status))

        # Print the trend
        print(f"Date: {date_time} -- SMA Trend: {sma_trend_status}")
        print(f"SMA 1: {sma_t1}")
        print(f"SMA 2: {sma_t2}")
        print(f"SMA 3: {sma_t3}")
        print(f"SMA 4: {sma_t4}")
        print("-----------------------------")

    except Exception as e:
        print(f"Error at index {i}: {e}")
