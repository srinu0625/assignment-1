import pandas as pd
import time

file_path1 = r"D:\CANDLES 2\NQ DAY.csv"

# Load the data
try:
    data2 = pd.read_csv(file_path1)
except Exception as e:
    print("Error loading data:", e)
    exit()

## Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2  = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2  = 0

# current high and current lows
current_high1 = current_low1 = current_high2 = current_low2 = previous_high2 = previous_low2 = 0

# prev local high and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0

# Iterate over each row of the hourly DataFrame (data2)
for index1, row1 in data2.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the hourly data
        current_date2 = row1[time_column_name].split()[0]

        # If the hourly data date matches the daily data date
        try:
            # Extracting current and previous values for high and low from data1
            current_time1 = row1[time_column_name]
            high1 = float(row1[high_column_name])
            low1 = float(row1[low_column_name])
            if (high1 > current_high1) or (low1 < current_low1):
                previous_high1 = current_high1
                previous_low1 = current_low1
                current_high1 = high1
                current_low1 = low1

            # case 1 for data1-----------------------------------------------------------------------------------
            if(current_high1 > previous_high1):
                temp_high1 = current_high1
                
            if(current_low1 < previous_low1):
                temp_low1 = current_low1
            # case 2 for data2-----------------------------------------------------------------------------------
            if current_high1 > previous_high1:
                if temp_low1 != local_low1:
                    prev_local_low1 = local_low1
                local_low1 = temp_low1

            if current_low1 < previous_low1:
                if temp_high1 != local_high1:
                    prev_local_high1 = local_high1
                local_high1 = temp_high1
                
            # Printing data for data1
            print("----WEEKLY:----", current_time1)
            print("1,C,MGCZ4," + str(current_high1) + "," + str(current_low1) + "," + str(previous_high1) + "," + str(previous_low1) + "," + str(temp_high1) + "," + str(temp_low1) + "," + str(local_high1) + "," + str(local_low1) + "," + str(prev_local_high1) + "," + str(prev_local_low1))
            print("   ")
            time.sleep(0)

        except Exception as e:
            print("Error:", e)

        finally:
            print("-----------------------------------End of iteration-------------------------------------")