import pandas as pd
import math
import time

file_path1 = r"D:\candles\es 60 min.csv"
file_path2 = r"D:\candles\es 240 min.csv"
file_path3 = r"D:\candles\es daily.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1, dtype={time_column_name: str})
    data2 = pd.read_csv(file_path2, dtype={time_column_name: str})
    data3 = pd.read_csv(file_path3, dtype={time_column_name: str})
except Exception as e:
    print("Error loading data:", e)
    exit()

# Assuming the column names for high and low are 'High' and 'Low'
time_column_name = 'Date (GMT)'
high_column_name = 'High'
low_column_name  = 'Low'

# temp column names
temp_high1 = 0
temp_low1  = 0
temp_high2 = 0
temp_low2  = 0
temp_high3 = 0
temp_low3  = 0

# local high and local low 
current_high1 = 0
current_low1  = 0
local_high1 = temp_high1
local_low1 = temp_low1
local_high2 = temp_high2
local_low2 = temp_low2
local_high3 = temp_high3
local_low3 = temp_low3
prev_local_high1 = 0 
prev_local_low1  = 0
prev_local_high2 = 0 
prev_local_low2  = 0
prev_local_high3 = 0 
prev_local_low3  = 0

# flag 
bull = False
bear = False
flag = False

# num of positions 
number_of_positions = 0

# num of trades
num_of_trades = 0

# P&L calculation
entry_price = 0
exit_price  = 0
contract_size = 5
# defining tick size
tick_val = 0.25

# maxloss maxprofit
max_loss   = 0  
max_profit = 0 
max_loss_for_trade = 0

# total p&l
TOTAL_P_L = 0

# total long and short pnl
total_long_pnl = 0
total_short_pnl = 0
positive_pnl = 0
negative_pnl = 0
num_of_lots  = 0
max_num_lots = 20
risk = 360

#total rows in sheets
rows_count_240_mins = 0
rows_count_daily = 0
current_hours_count = 1
date_flag = False

previous_date = data1.loc[0, time_column_name].split()[0]

current_time2 = data2.loc[rows_count_240_mins, time_column_name]
current_high2 = float(data2.loc[rows_count_240_mins, high_column_name])
previous_high2 = float(data2.loc[rows_count_240_mins-1, high_column_name]) if rows_count_240_mins > 0 else 0
current_low2 = float(data2.loc[rows_count_240_mins, low_column_name])
previous_low2 = float(data2.loc[rows_count_240_mins-1, low_column_name]) if rows_count_240_mins > 0 else 0

current_time3 = data3.loc[rows_count_daily, time_column_name]
current_high3 = float(data3.loc[rows_count_daily, high_column_name])
previous_high3 = float(data3.loc[rows_count_daily-1, high_column_name]) if rows_count_daily > 0 else 0
current_low3 = float(data3.loc[rows_count_daily, low_column_name])
previous_low3 = float(data3.loc[rows_count_daily-1, low_column_name]) if rows_count_daily > 0 else 0
current_date3 = data3.loc[rows_count_daily, time_column_name].split()[0]

# Iterate over each row of the daily DataFrame (data3)
for index1, row1 in data1.iterrows():
    current_date = row1[time_column_name].split()[0]
    if previous_date != current_date:
        date_flag = True

    try:
        # Extracting current and previous values for high and low from data1
        current_time1 = row1[time_column_name]
        current_high1 = float(row1[high_column_name])
        previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else 0
        current_low1 = float(row1[low_column_name])
        previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else 0

        # Extracting current and previous values for high and low from data2
        if current_hours_count == 5 or date_flag:
            rows_count_240_mins += 1
            print("Assigned Row number:", rows_count_240_mins)
            current_time2 = data2.loc[rows_count_240_mins, time_column_name]
            current_high2 = float(data2.loc[rows_count_240_mins, high_column_name])
            previous_high2 = float(data2.loc[rows_count_240_mins-1, high_column_name]) if rows_count_240_mins > 0 else 0
            current_low2 = float(data2.loc[rows_count_240_mins, low_column_name])
            previous_low2 = float(data2.loc[rows_count_240_mins-1, low_column_name]) if rows_count_240_mins > 0 else 0
            current_hours_count = 1

        # Extracting current and previous values for high and low from data3
        if date_flag:
            rows_count_daily += 1
            current_date3 = data3.loc[rows_count_daily, time_column_name].split()[0]
            current_time3 = data3.loc[rows_count_daily, time_column_name]
            current_high3 = float(data3.loc[rows_count_daily, high_column_name])
            previous_high3 = float(data3.loc[rows_count_daily-1, high_column_name]) if rows_count_daily > 0 else 0
            current_low3 = float(data3.loc[rows_count_daily, low_column_name])
            previous_low3 = float(data3.loc[rows_count_daily-1, low_column_name]) if rows_count_daily > 0 else 0

        # Case 1 for data1
        if current_high1 > previous_high1:
            temp_high1 = current_high1

        if current_low1 < previous_low1:
            temp_low1 = current_low1
        
        # Case 2 for data1
        if current_high1 > previous_high1:
            prev_local_low1 = local_low1
            local_low1 = temp_low1

        if current_low1 < previous_low1:
            prev_local_high1 = local_high1
            local_high1 = temp_high1

        # Printing data for data1
        print("---60 MIN---:", current_time1)
        print("Current High1:", current_high1, "Previous High1:", previous_high1, "local_high1:", local_high1, "prev_local_high1:", prev_local_high1)
        print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "local_low1:", local_low1, "prev_local_low1:", prev_local_low1)
        print("   ")
        time.sleep(0.5)

        # Case 1 for data2
        if current_high2 > previous_high2:
            temp_high2 = current_high2

        if current_low2 < previous_low2:
            temp_low2 = current_low2
        
        # Case 2 for data2
        if current_high2 > previous_high2:
            prev_local_low2 = local_low2
            local_low2 = temp_low2

        if current_low2 < previous_low2:
            prev_local_high2 = local_high2
            local_high2 = temp_high2
        
        # Printing data for data2
        print("---240 MIN---:", current_time2)
        print("Current High2:", current_high2, "Previous High2:", previous_high2, "local_high2:", local_high2, "prev_local_high2:", prev_local_high2)
        print("Current Low2:", current_low2, "Previous Low2:", previous_low2, "local_low2:", local_low2, "prev_local_low2:", prev_local_low2)
        print("   ")
        time.sleep(0.5)

        # Case 1 for data3
        if current_high3 > previous_high3:
            temp_high3 = current_high3

        if current_low3 < previous_low3:
            temp_low3 = current_low3
        
        # Case 2 for data3
        if current_high3 > previous_high3:
            prev_local_low3 = local_low3
            local_low3 = temp_low3

        if current_low3 < previous_low3:
            prev_local_high3 = local_high3
            local_high3 = temp_high3

        # Printing data for data3
        print("---DAILY---:", current_time3)
        print("Current High3:", current_high3, "Previous High3:", previous_high3, "local_high3:", local_high3, "prev_local_high3:", prev_local_high3)
        print("Current Low3:", current_low3, "Previous Low3:", previous_low3, "local_low3:", local_low3, "prev_local_low3:", prev_local_low3)
        print("   ")
        time.sleep(0.5)
        
        current_hours_count += 1
        date_flag = False
        previous_date = current_date

    except Exception as e:
        print("Error processing row:", e)
        continue
