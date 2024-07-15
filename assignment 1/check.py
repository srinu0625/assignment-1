import pandas as pd
import math
import time

file_path1 = r"D:\New folder\es 60 min.csv"
file_path2 = r"D:\New folder\es 240 min.csv"
file_path3 = r"D:\New folder\es day.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
    data3 = pd.read_csv(file_path3)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Assuming the column names for high and low are 'High' and 'Low'
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# temp column names
temp_high1 = temp_low1 = temp_high2 = temp_low2 = temp_high3 = temp_low3 = 0

# local high and local low
local_high1 = local_low1 = local_high2 = local_low2 = local_high3 = local_low3 = 0

# flags
bull = bear = flag = False

# num of positions
number_of_positions = 0

# num of trades
num_of_trades = 0

# P&L calculation
entry_price = exit_price = 0
contract_size = 5
# defining tick size
tick_val = 0.25

# max loss max profit
max_loss = max_profit = max_loss_for_trade = 0

# total P&L
TOTAL_P_L = 0

# total long and short pnl
total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 360

# total rows in sheets
rows_count_240_mins = rows_count_daily = 0
current_hours_count = 1
date_flag = False

previous_date = data1.loc[0, time_column_name].split()[0]

current_time2 = data2.loc[rows_count_240_mins, time_column_name]
current_high2 = float(data2.loc[rows_count_240_mins, high_column_name])
previous_high2 = float(data2.loc[rows_count_240_mins - 1, high_column_name]) if rows_count_240_mins > 0 else 0
current_low2 = float(data2.loc[rows_count_240_mins, low_column_name])
previous_low2 = float(data2.loc[rows_count_240_mins - 1, low_column_name]) if rows_count_240_mins > 0 else 0

current_time3 = data3.loc[rows_count_daily, time_column_name]
current_high3 = float(data3.loc[rows_count_daily, high_column_name])
previous_high3 = float(data3.loc[rows_count_daily - 1, high_column_name]) if rows_count_daily > 0 else 0
current_low3 = float(data3.loc[rows_count_daily, low_column_name])
previous_low3 = float(data3.loc[rows_count_daily - 1, low_column_name]) if rows_count_daily > 0 else 0
current_date3 = data3.loc[rows_count_daily, time_column_name].split()[0]

# Iterate over each row of the 60-minute DataFrame (data1)
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
            previous_high2 = float(data2.loc[rows_count_240_mins - 1, high_column_name]) if rows_count_240_mins > 0 else 0
            current_low2 = float(data2.loc[rows_count_240_mins, low_column_name])
            previous_low2 = float(data2.loc[rows_count_240_mins - 1, low_column_name]) if rows_count_240_mins > 0 else 0
            current_hours_count = 1

        # Extracting current and previous values for high and low from data3
        if date_flag:
            rows_count_daily += 1
            current_date3 = data3.loc[rows_count_daily, time_column_name].split()[0]
            current_time3 = data3.loc[rows_count_daily, time_column_name]
            current_high3 = float(data3.loc[rows_count_daily, high_column_name])
            previous_high3 = float(data3.loc[rows_count_daily - 1, high_column_name]) if rows_count_daily > 0 else 0
            current_low3 = float(data3.loc[rows_count_daily, low_column_name])
            previous_low3 = float(data3.loc[rows_count_daily - 1, low_column_name]) if rows_count_daily > 0 else 0

        # case 1 for data1
        if current_high1 > previous_high1:
            temp_high1 = current_high1
        if current_low1 < previous_low1:
            temp_low1 = current_low1

        # case 2 for data1
        if current_high1 > previous_high1:
            local_low1 = temp_low1
        if current_low1 < previous_low1:
            local_high1 = temp_high1

        # Printing data for data1
        print("---60 MIN---:", current_time1)
        print("Current High1:", current_high1, "Previous High1:", previous_high1, "local_high1:", local_high1)
        print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "local_low1:", local_low1)
        print("   ")

        # case 1 for data2
        if current_high2 > previous_high2:
            temp_high2 = current_high2
        if current_low2 < previous_low2:
            temp_low2 = current_low2

        # case 2 for data2
        if current_high2 > previous_high2:
            local_low2 = temp_low2
        if current_low2 < previous_low2:
            local_high2 = temp_high2

        # Printing data for data2
        print("---240 MIN---:", current_time2)
        print("Current High2:", current_high2, "Previous High2:", previous_high2, "local_high2:", local_high2)
        print("Current Low2:", current_low2, "Previous Low2:", previous_low2, "local_low2:", local_low2)
        print("   ")

        # case 1 for data3
        if current_high3 > previous_high3:
            temp_high3 = current_high3
        if current_low3 < previous_low3:
            temp_low3 = current_low3

        # case 2 for data3
        if current_high3 > previous_high3:
            local_low3 = temp_low3
        if current_low3 < previous_low3:
            local_high3 = temp_high3

        # Printing data for data3
        print("----DAILY----:", current_time3)
        print("Current High3:", current_high3, "Previous High3:", previous_high3, "local_high3:", local_high3)
        print("Current Low3:", current_low3, "Previous Low3:", previous_low3, "local_low3:", local_low3)
        print("   ")

        # Updating exit price
        if bull and local_low1 > exit_price:
            exit_price = local_low1
        if bear and local_high1 < exit_price:
            exit_price = local_high1

        # Bullish candle
        max_loss_for_trade = (local_high1 - current_low1 + (tick_val * 4)) * contract_size
        if (current_high1 > local_high1) and ((local_high1 > local_high2) or (local_high1 > current_high2)) and ((local_low1 > local_low2) and (local_low1 > local_low3) and (local_low1 > current_low3)) and local_low1 != 0 and local_high2 != 0 and local_low2 != 0 and not bear and not flag:
            if max_loss_for_trade > risk:
                num_of_lots = 1
                print("num of lots:", num_of_lots)
                continue  # Skip this trade
            else:
                num_of_lots = math.floor(risk / max_loss_for_trade)
                if num_of_lots >= max
                                print("num of lots:", num_of_lots)

                entry_price = local_low1
                flag = True
                bull = True

                max_loss = max_loss_for_trade
                max_profit = (local_high1 - current_low1 + (tick_val * 4)) * contract_size
                continue

        # Bearish candle
        max_loss_for_trade = (current_high1 - local_low1 + (tick_val * 4)) * contract_size
        if (current_low1 < local_low1) and ((local_high1 < local_high2) or (local_high1 < current_high2)) and ((local_low1 < local_low2) and (local_low1 < current_low3)) and local_low1 != 0 and local_high2 != 0 and local_low2 != 0 and not bull and not flag:
            if max_loss_for_trade > risk:
                num_of_lots = 1
                print("num of lots:", num_of_lots)
                continue  # Skip this trade
            else:
                num_of_lots = math.floor(risk / max_loss_for_trade)
                if num_of_lots >= max_num_lots:
                    print("num of lots:", num_of_lots)
                    continue

                entry_price = local_high1
                flag = True
                bear = True

                max_loss = max_loss_for_trade
                max_profit = (current_high1 - local_low1 + (tick_val * 4)) * contract_size
                continue

        # Exiting the trade
        if bull and local_high1 > exit_price:
            TOTAL_P_L += (local_high1 - entry_price + (tick_val * 4)) * contract_size
            if (local_high1 - entry_price + (tick_val * 4)) * contract_size > positive_pnl:
                positive_pnl = (local_high1 - entry_price + (tick_val * 4)) * contract_size
                print("Positive PnL:", positive_pnl)
                print("positive pnl:", positive_pnl)
            if (local_high1 - entry_price + (tick_val * 4)) * contract_size < negative_pnl:
                negative_pnl = (local_high1 - entry_price + (tick_val * 4)) * contract_size
                print("Negative PnL:", negative_pnl)
                print("negative pnl:", negative_pnl)
                number_of_positions = index1

            flag = False
            bull = False

        if bear and local_low1 < exit_price:
            TOTAL_P_L += (entry_price - local_low1 + (tick_val * 4)) * contract_size
            if (entry_price - local_low1 + (tick_val * 4)) * contract_size > positive_pnl:
                positive_pnl = (entry_price - local_low1 + (tick_val * 4)) * contract_size
                print("Positive PnL:", positive_pnl)
                print("positive pnl:", positive_pnl)
            if (entry_price - local_low1 + (tick_val * 4)) * contract_size < negative_pnl:
                negative_pnl = (entry_price - local_low1 + (tick_val * 4)) * contract_size
                print("Negative PnL:", negative_pnl)
                print("negative pnl:", negative_pnl)
                number_of_positions = index1

            flag = False
            bear = False

        # Printing out total  pnl, positve pnl, and negative pnl.
        print("Total PnL:", TOTAL_P_L)
        print("Positive PnL:", positive_pnl)
        print("Negative PnL:", negative_pnl)
        print("Max Loss:", max_loss)
        print("Max Profit:", max_profit)
        print("Assigned Row number:", number_of_positions)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        print("Assigned Row number:", index1)
        print("Error in iteration:", index1)
        continue

    # Handle errors in the loop
    except Exception as e:
        print(f"Error in iteration {index1}: {e}")
        continue

# Final output after loop completion
print("Total PnL:", TOTAL_P_L)
print("Positive PnL:", positive_pnl)
print("Negative PnL:", negative_pnl)
print("Max Loss:", max_loss)
print("Max Profit:", max_profit)
print("Assigned Row number:", number_of_positions)


