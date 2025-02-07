import pandas as pd

file_path = r"D:\candles\snp 240min.csv"

# Load the data
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", df.columns)

# Calculate 9-day Simple Moving Average (SMA)
n = 10
df['SMA'] = df['close'].rolling(window=n).mean()

# Initialize variables
sma_trend_status = None  # To hold the current trend status
trend_data = []  # To store trend information

# Iterate through the rows of the dataframe
for i in range(n + 3, len(df)):  # Start after ensuring we have enough data for 4 SMA values
    try:
        # Extract consecutive SMA values
       
        sma_t4 = round(df['SMA'].iloc[i - 3], 2)
        sma_t3 = round(df['SMA'].iloc[i - 2], 2)
        sma_t2 = round(df['SMA'].iloc[i - 1], 2)
        sma_t1 = round(df['SMA'].iloc[i], 2)

        # Extract current date and time
        date_time = df['Date (GMT)'].iloc[i]

        # Determine the trend
        if sma_t4 < sma_t3 < sma_t2 < sma_t1:
            sma_trend_status = "Ultimate Bullish, ↗️ , ↑ , 📈 ,[4 < 3 < 2 < 1]"
        elif sma_t4 > sma_t3 > sma_t2 > sma_t1:
            sma_trend_status = "Ultimate Bearish, ↘️ , ↓ , 📉 ,[4 > 3 > 2 > 1]"
        else:
            sma_trend_status = "== Neutral ==,"

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



