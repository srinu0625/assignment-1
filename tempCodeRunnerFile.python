import pandas as pd
import math
import time

file_path1 = r"D:\New folder\snp 60 min.csv"
file_path2 = r"D:\New folder\snp 240 min.csv"
file_path3 = r"D:\New folder\snp day.csv"

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
low_column_name  = 'Low'
time_column_name = 'Date (GMT)'

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
tick_val = 1

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
max_num_lots = 5
risk = 450

# Iterate over each row of the 60-minute DataFrame (data1)
for index1, row1 in data1.iterrows():
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        current_date1 = row1[time_column_name].split()[0]
        current_time1 = row1[time_column_name]

        # Iterate over each row of the 240-minute DataFrame (data2)
        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]
                current_time2 = row2[time_column_name]

                if current_date1 == current_date2:
                    # Iterate over each row of the daily DataFrame (data3)
                    for index3, row3 in data3.iterrows():
                        if pd.notna(row3[time_column_name]) and pd.notna(row3[high_column_name]) and pd.notna(row3[low_column_name]):
                            current_date3 = row3[time_column_name].split()[0]
                            current_time3 = row3[time_column_name]

                            if current_date2 == current_date3:
                                try:
                                    # Extracting current and previous values for high and low from data1
                                    current_high1 = float(row1[high_column_name])
                                    previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else 0
                                    current_low1 = float(row1[low_column_name])
                                    previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else 0

                                    # Extracting current and previous values for high and low from data2
                                    current_high2 = float(row2[high_column_name])
                                    previous_high2 = float(data2.at[index2 - 1, high_column_name]) if index2 > 0 else 0
                                    current_low2 = float(row2[low_column_name])
                                    previous_low2 = float(data2.at[index2 - 1, low_column_name]) if index2 > 0 else 0

                                    # Extracting current and previous values for high and low from data3
                                    current_high3 = float(row3[high_column_name])
                                    previous_high3 = float(data3.at[index3 - 1, high_column_name]) if index3 > 0 else 0
                                    current_low3 = float(row3[low_column_name])
                                    previous_low3 = float(data3.at[index3 - 1, low_column_name]) if index3 > 0 else 0

                                    # Update temp and local highs/lows for 60-minute data
                                    if current_high1 > previous_high1:
                                        temp_high1 = current_high1
                                    if current_low1 < previous_low1:
                                        temp_low1 = current_low1
                                    if current_high1 > previous_high1:
                                        local_low1 = temp_low1
                                    if current_low1 < previous_low1:
                                        local_high1 = temp_high1

                                    # Print 60-minute data
                                    print("---60 MIN---:", current_time1)
                                    print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1, " temp_high1 :", temp_high1)
                                    print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1, " temp_low1 :", temp_low1)
                                    print("   ")

                                    # Update temp and local highs/lows for 240-minute data
                                    if current_high2 > previous_high2:
                                        temp_high2 = current_high2
                                    if current_low2 < previous_low2:
                                        temp_low2 = current_low2
                                    if current_high2 > previous_high2:
                                        local_low2 = temp_low2
                                    if current_low2 < previous_low2:
                                        local_high2 = temp_high2

                                    # Print 240-minute data
                                    print("---240 MIN---:", current_time2)
                                    print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2, " temp_high2 :", temp_high2)
                                    print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2, " temp_low2 :", temp_low2)
                                    print("   ")

                                    # Update temp and local highs/lows for daily data
                                    if current_high3 > previous_high3:
                                        temp_high3 = current_high3
                                    if current_low3 < previous_low3:
                                        temp_low3 = current_low3
                                    if current_high3 > previous_high3:
                                        local_low3 = temp_low3
                                    if current_low3 < previous_low3:
                                        local_high3 = temp_high3

                                    # Print daily data
                                    print("----DAILY----:", current_time3)
                                    print("Current High3 :", current_high3, "Previous High3 :", previous_high3, "local_high3 :", local_high3, " temp_high3 :", temp_high3)
                                    print("Current Low3 :", current_low3, "Previous Low3 :", previous_low3, "local_low3 :", local_low3, " temp_low3 :", temp_low3)
                                    print("   ")
                                    print("------------------------------------------------------------------------------------------------------------------------------------------------")

                                    # Update exit price
                                    if bull and local_low1 > exit_price:
                                        exit_price = local_low1
                                    if bear and local_high1 < exit_price:
                                        exit_price = local_high1

                                    max_loss_for_trade = (local_high1 - current_low1 + (tick_val * 4)) * contract_size
                                    if current_high1 > local_high1 and local_low1 > local_high2 and local_high1 != 0 and local_low1 != 0 and local_high2 != 0 and local_low2 != 0 and not bear and not flag:
                                        if max_loss_for_trade > risk:
                                            num_of_lots = math.floor(risk / max_loss_for_trade)
                                            if num_of_lots == 0:
                                                continue  # Skip this trade if even 1 lot exceeds the risk
                                        else:
                                            num_of_lots = math.floor(risk / max_loss_for_trade)

                                        number_of_positions += 1
                                        if num_of_lots >= max_num_lots:
                                            num_of_lots = max_num_lots
                                        entry_price = local_high1 + (tick_val * 2)
                                        print("\033[32m<------ LONG ENTRY ------> (CH1 > LH1 and LL1 > LH2)\033[0m")
                                        print("       ENTRY PRICE  = ", entry_price)
                                        print("   num_of_positions = ", number_of_positions)
                                        print("        num_of_lots = ", round(num_of_lots))
                                        print(" max_loss_for_trade = ", round(max_loss_for_trade))
                                        print("---------------------------------------------------")
                                        bull = True
                                        flag = True
                                        continue

                                    # Bullish Exit
                                    if current_low1 <= local_low1 and bull and flag:
                                        exit_price = current_low1 - (tick_val * 2)
                                        number_of_positions -= 1
                                        num_of_trades += 1
                                        TOTAL_P_L = (exit_price - entry_price) * contract_size
                                        total_long_pnl += TOTAL_P_L
                                        if TOTAL_P_L > 0:
                                            positive_pnl += TOTAL_P_L
                                        else:
                                            negative_pnl += TOTAL_P_L

                                        print("\033[31m<------ LONG EXIT ------> (CL1 <= LL1 and Bull)\033[0m")
                                        print("     EXIT PRICE = ", exit_price)
                                        print("    TOTAL P&L   = ", TOTAL_P_L)
                                        print("    num_of_positions = ", number_of_positions)
                                        print("    total_long_pnl   = ", total_long_pnl)
                                        print("    num_of_trades    = ", num_of_trades)
                                        print("---------------------------------------------------")
                                        bull = False
                                        flag = False
                                        entry_price = 0
                                        exit_price = 0
                                        time.sleep(0.05)

                                    max_loss_for_trade = (current_high1 - local_low1 + (tick_val * 4)) * contract_size
                                    if current_low1 < local_low1 and local_high1 < local_low2 and local_high1 != 0 and local_low1 != 0 and local_high2 != 0 and local_low2 != 0 and not bull and not flag:
                                        if max_loss_for_trade > risk:
                                            num_of_lots = math.floor(risk / max_loss_for_trade)
                                            if num_of_lots == 0:
                                                continue  # Skip this trade if even 1 lot exceeds the risk
                                        else:
                                            num_of_lots = math.floor(risk / max_loss_for_trade)

                                        number_of_positions += 1
                                        if num_of_lots >= max_num_lots:
                                            num_of_lots = max_num_lots
                                        entry_price = local_low1 - (tick_val * 2)
                                        print("\033[32m<------ SHORT ENTRY ------> (CL1 < LL1 and LH1 < LL2)\033[0m")
                                        print("       ENTRY PRICE  = ", entry_price)
                                        print("   num_of_positions = ", number_of_positions)
                                        print("        num_of_lots = ", round(num_of_lots))
                                        print(" max_loss_for_trade = ", round(max_loss_for_trade))
                                        print("---------------------------------------------------")
                                        bear = True
                                        flag = True
                                        continue

                                    # Bearish Exit
                                    if current_high1 >= local_high1 and bear and flag:
                                        exit_price = current_high1 + (tick_val * 2)
                                        number_of_positions -= 1
                                        num_of_trades += 1
                                        TOTAL_P_L = (entry_price - exit_price) * contract_size
                                        total_short_pnl += TOTAL_P_L
                                        if TOTAL_P_L > 0:
                                            positive_pnl += TOTAL_P_L
                                        else:
                                            negative_pnl += TOTAL_P_L

                                        print("\033[31m<------ SHORT EXIT ------> (CH1 >= LH1 and Bear)\033[0m")
                                        print("     EXIT PRICE = ", exit_price)
                                        print("    TOTAL P&L   = ", TOTAL_P_L)
                                        print("    num_of_positions = ", number_of_positions)
                                        print("    total_short_pnl  = ", total_short_pnl)
                                        print("    num_of_trades    = ", num_of_trades)
                                        print("---------------------------------------------------")
                                        bear = False
                                        flag = False
                                        entry_price = 0
                                        exit_price = 0
                                        time.sleep(0.05)

                                    # Print the local_high and local_low
                                    print("       Local High1  :", local_high1)
                                    print("       Local Low1   :", local_low1)
                                    print("       Local High2  :", local_high2)
                                    print("       Local Low2   :", local_low2)
                                    print("       Local High3  :", local_high3)
                                    print("       Local Low3   :", local_low3)
                                    print("==========================================")

                                except ValueError as ve:
                                    print(f"Value error for date {current_date1}: {ve}")
                                except KeyError as ke:
                                    print(f"Key error for date {current_date1}: {ke}")
                                except Exception as e:
                                    print(f"Unexpected error for date {current_date1}: {e}")
