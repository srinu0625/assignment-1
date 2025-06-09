import pandas as pd
import datetime
import time

# Initialize tm_struct as the current datetime
tm_struct = datetime.datetime.now()

file_path = r"C:\Users\lenovo\Music\es day.csv"

# Load the data
try:
    data = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Assuming the column names
Date_Time_ = 'DateTime'
Price_name = 'Price'
Volume_name = 'Volume'
ExchTime_price = 'ExchTime'

# Initialize variables
current_minute = None
total_volume = 0
num_of_lines = 0
Date_Time = 0
curr_high = float('-inf')
curr_low = float('inf')
curr_close = 0
total_trade_value =0 
timeSlot = 240  # Assuming time slot is 15 minutes

# Iterate over each row of the DataFrame
for index, row in data.iterrows():
    try:
        # Extracting values
        Price = row[Price_name]
        Volume = row[Volume_name]
        ExchTime = row[ExchTime_price]
        Date_Time = row[Date_Time_]

        # Split ExchTime into hours, minutes, and seconds
        hour, minute, second = map(int, ExchTime.split('.'))

        # Convert time to seconds
        total_seconds = hour * 3600 + minute * 60 + second

        # Check if it's a new minute
        if minute != current_minute:
            # Calculate average trade price for the previous minute
            if current_minute is not None:
                if total_volume != 0:
                    avg_trade_price = (total_trade_value / total_volume)
                    avg_trade_price_rounded = round(avg_trade_price, 2)
                    print(f"Avg_trade_price : {current_minute}: {avg_trade_price_rounded}")
                    print('----------------------------')
                else:
                    print(f"No trades occurred in minute {current_minute}")


        # Check if it's a new minute
        if minute != current_minute:
            # Print candlestick for the previous minute
            if current_minute is not None:
                print("Time:", tm_struct)
                print("Open:", curr_open)
                print("High:", curr_high)
                print("Low:", curr_low)
                print("Close:", curr_close)
                print('----------------------------')
                time.sleep(60)

            # Reset variables for the new minute
            current_minute = minute
            curr_open = Price
            curr_high = Price
            curr_low = Price
            curr_close = Price
            total_volume = 0

        # Update high and low prices
        if Price > curr_high:
            curr_high = Price
        if Price < curr_low:
            curr_low = Price

        # Check if it's the end of a candlestick interval
        if tm_struct.minute % timeSlot == 0 and tm_struct.minute != minute:
            curr_close = Price
            tm_struct = datetime.datetime.now()

    except Exception as e:
        print("Error:", e)
