import pandas as pd
import time

# File paths
file_path1 = r"C:\Users\lenovo\Desktop\ES 240..csv"


# Load the data
try:
    data1 = pd.read_csv(file_path1)
   
except Exception as e:
    print("Error loading data:", e)
    exit()

## Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temporary variables for tracking highs and lows for all datasets
temp_high1 = temp_low1 = temp_high2 = temp_low2 = temp_high3 = temp_low3 = 0
temp_high4 = temp_low4 = temp_high5 = temp_low5 = temp_high6 = temp_low6 = 0

# Local highs and lows for all datasets
local_high1 = local_low1 = local_high2 = local_low2 = local_high3 = local_low3 = 0
local_high4 = local_low4 = local_high5 = local_low5 = local_high6 = local_low6 = 0

# Current highs and lows for all datasets
current_high1 = current_low1 = current_high2 = current_low2 = current_high3 = current_low3 = 0
current_high4 = current_low4 = current_high5 = current_low5 = current_high6 = current_low6 = 0

# Previous highs and lows for all datasets
previous_high1 = previous_low1 = previous_high2 = previous_low2 = previous_high3 = previous_low3 = 0
previous_high4 = previous_low4 = previous_high5 = previous_low5 = previous_high6 = previous_low6 = 0

# Previous local highs and lows for all datasets
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = prev_local_high3 = prev_local_low3 = 0
prev_local_high4 = prev_local_low4 = prev_local_high5 = prev_local_low5 = prev_local_high6 = prev_local_low6 = 0

# Iterate through the data for all datasets (data1 to data6)
for index1, row1 in data1.iterrows():
    # Process dataset 1
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        try:
            current_time1 = row1[time_column_name]
            high1 = float(row1[high_column_name])
            low1 = float(row1[low_column_name])
            
            if (high1 > current_high1) or (low1 < current_low1):
                previous_high1 = current_high1
                previous_low1 = current_low1
                current_high1 = high1
                current_low1 = low1
            
            if current_high1 > previous_high1:
                temp_high1 = current_high1
            if current_low1 < previous_low1:
                temp_low1 = current_low1
            
            if current_high1 > previous_high1:
                if temp_low1 != local_low1:
                    prev_local_low1 = local_low1
                local_low1 = temp_low1
            
            if current_low1 < previous_low1:
                if temp_high1 != local_high1:
                    prev_local_high1 = local_high1
                local_high1 = temp_high1

            print("----240 MIN :----", current_time1)
            print("Current High1 :", current_high1, "Previous High1 :", previous_high1,"temp_high",temp_high1, "local_high1 :", local_high1,"prev_local_high :",prev_local_high1)
            print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1,"temp_low",temp_low1 ,"local_low1 :", local_low1,"prev_local_low1 :",prev_local_low1)
            print("   ")
            print("---------------------------------------------------------------------------")
            time.sleep(0)

        except Exception as e:
            print("Error in Dataset 1:", e)
            