import pandas as pd
import math
import time

file_path1 = r"C:\Users\lenovo\Desktop\snp 240.csv"
file_path2 = r"C:\Users\lenovo\Desktop\snp day.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    print("Error loading data:", e)
    exit()

contract_size = 5
tick_val = 0.25

# Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2 = 0

# Prev local high and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0

# Variables for positive and negative trades
total_positive_trades = 0
total_negative_trades = 0

current_high1 = 0
current_low1 = 0
current_high2 = 0
current_low2 = 0
previous_high1 = 0
previous_low1 = 0
previous_high2 = 0
previous_low2 = 0

# Trading flags
bull = bear = flag = False

# Trading parameters
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        current_date1 = row1[time_column_name].split()[0]

        # Iterate over each row of the hourly DataFrame (data2)
        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]

                if current_date2 == current_date1:
                    try:
                        current_time1 = row1[time_column_name]
                        high1 = float(row1[high_column_name])
                        low1 = float(row1[low_column_name])

                        # Track highs and lows
                        if high1 > current_high1 or low1 < current_low1:
                            previous_high1 = current_high1
                            previous_low1 = current_low1
                            current_high1 = high1
                            current_low1 = low1

                        if high1 > current_high1 and prev_local_low1 == local_low1:
                            local_low1 = temp_low1

                        if low1 < current_low1 and prev_local_high1 == local_high1:
                            local_high1 = temp_high1

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

                        # Printing data for data1
                        print("----240 MIN :----", current_time1)
                        print("Current High1:", current_high1, "Previous High1:", previous_high1, "temp_high:", temp_high1,
                              "local_high1:", local_high1, "prev_local_high1:", prev_local_high1)
                        print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "temp_low:", temp_low1,
                              "local_low1:", local_low1, "prev_local_low1:", prev_local_low1)
                        print("   ")

                        # Extract current and previous values for high and low from data2
                        current_time2 = row2[time_column_name]
                        high2 = float(row2[high_column_name])
                        low2 = float(row2[low_column_name])

                        if high2 > current_high2 or low2 < current_low2:
                            previous_high2 = current_high2
                            previous_low2 = current_low2
                            current_high2 = high2
                            current_low2 = low2

                        if high2 > current_high2 and prev_local_low2 == local_low2:
                            local_low2 = temp_low2

                        if low2 < current_low2 and prev_local_high2 == local_high2:
                            local_high2 = temp_high2

                        if current_high2 > previous_high2:
                            temp_high2 = current_high2
                        if current_low2 < previous_low2:
                            temp_low2 = current_low2

                        if current_high2 > previous_high2:
                            if temp_low2 != local_low2:
                                prev_local_low2 = local_low2
                            local_low2 = temp_low2

                        if current_low2 < previous_low2:
                            if temp_high2 != local_high2:
                                prev_local_high2 = local_high2
                            local_high2 = temp_high2

                        # Printing data for data2
                        print("---- DAILY :----", current_time2)
                        print("Current High2:", current_high2, "Previous High2:", previous_high2, "temp_high2:", temp_high2,
                              "local_high2:", local_high2, "prev_local_high2:", prev_local_high2)
                        print("Current Low2:", current_low2, "Previous Low2:", previous_low2, "temp_low2:", temp_low2,
                              "local_low2:", local_low2, "prev_local_low2:", prev_local_low2)
                        print("   ")

                        # Bullish entry logic
                 
