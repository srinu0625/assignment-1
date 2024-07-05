import pandas as pd
import math
import time

file_path1 = r"D:\es 60 min .csv"
file_path2 = r"D:\es 240 min.csv"
file_path3 = r"D:\es daily .csv"

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

# Iterate over each row of the daily DataFrame (data3)
for index3, row3 in data3.iterrows():
    if pd.notna(row3[time_column_name]) and pd.notna(row3[high_column_name]) and pd.notna(row3[low_column_name]):
        current_date3 = row3[time_column_name].split()[0]

        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]

                if current_date2 == current_date3:

                    for index1, row1 in data1.iterrows():
                        if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
                            current_date1 = row1[time_column_name].split()[0]

                            if current_date1 == current_date2 == current_date3:
                                try:
                                    # Extracting current and previous values for high and low from data1
                                    current_time1 = row1[time_column_name]
                                    current_high1 = float(row1[high_column_name])
                                    previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else 0
                                    current_low1 = float(row1[low_column_name])
                                    previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else 0

                                    # Extracting current and previous values for high and low from data2
                                    current_time2 = row2[time_column_name]
                                    current_high2 = float(row2[high_column_name])
                                    previous_high2 = float(data2.at[index2 - 1, high_column_name]) if index2 > 0 else 0
                                    current_low2 = float(row2[low_column_name])
                                    previous_low2 = float(data2.at[index2 - 1, low_column_name]) if index2 > 0 else 0

                                    # Extracting current and previous values for high and low from data3
                                    current_time3 = row3[time_column_name]
                                    current_high3 = float(row3[high_column_name])
                                    previous_high3 = float(data3.at[index3 - 1, high_column_name]) if index3 > 0 else 0
                                    current_low3 = float(row3[low_column_name])
                                    previous_low3 = float(data3.at[index3 - 1, low_column_name]) if index3 > 0 else 0

                                    # case 1 for data1
                                    if current_high1 > previous_high1:
                                        temp_high1 = current_high1

                                    if current_low1 < previous_low1:
                                        temp_low1 = current_low1
                                    # case 2 for data1
                                    if current_high1 > previous_high1:
                                        local_low1 = temp_low1
                                        prev_local_low1 = local_low1

                                    if current_low1 < previous_low1:
                                        local_high1 = temp_high1
                                        prev_local_high1 = local_high1

                                    # Printing data for data1
                                    print("---60 MIN---:", current_time1)
                                    print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1, " temp_high1 :", temp_high1)
                                    print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1, " temp_low1 :", temp_low1)
                                    print("   ")
                                    time.sleep(0.5)

                                    # case 1 for data2
                                    if current_high2 > previous_high2:
                                        temp_high2 = current_high2

                                    if current_low2 < previous_low2:
                                        temp_low2 = current_low2
                                    # case 2 for data2
                                    if current_high2 > previous_high2:
                                        local_low2 = temp_low2
                                        prev_local_low2 = local_low2

                                    if current_low2 < previous_high2:
                                        local_high2 = temp_high2
                                        prev_local_high2 = local_high2

                                    # Printing data for data2
                                    print("---240 MIN---:", current_time2)
                                    print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2, " temp_high2 :", temp_high2)
                                    print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2, " temp_low2 :", temp_low2)
                                    print("   ")
                                    time.sleep(0.5)

                                    # case 1 for data3
                                    if current_high3 > previous_high3:
                                        temp_high3 = current_high3

                                    if current_low3 < previous_low3:
                                        temp_low3 = current_low3
                                    # case 2 for data3
                                    if current_high3 > previous_high3:
                                        local_low3 = temp_low3
                                        prev_local_low3 = local_low3

                                    if current_low3 < previous_high3:
                                        local_high3 = temp_high3
                                        prev_local_high3 = local_high3

                                    # Printing data for data3
                                    print("----DAILY----:", current_time3)
                                    print("Current High3 :", current_high3, "Previous High3 :", previous_high3, "local_high3 :", local_high3, " temp_high3 :", temp_high3)
                                    print("Current Low3 :", current_low3, "Previous Low3 :", previous_low3, "local_low3 :", local_low3, " temp_low3 :", temp_low3)
                                    print("   ")
                                    time.sleep(0.5)
                                    print("--------------------------------------------------------------------------------------------------------------------------------------------")

                                    # updating exit price
                                    if bull and local_low1 > exit_price:
                                        exit_price = local_low1
                    
                                    if bear and local_high1 < exit_price:
                                        exit_price = local_high1
                            
                                    # bullish candle
                                    max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size 
                                    if current_high1 > local_high1 and local_low1 > local_high2 and local_high1 != 0 and local_low1 != 0  and local_high2 != 0 and local_low2 != 0 and not bear and not flag:
                                        print("1 = hourly","2 = daily")
                                        print("CH1 =",current_high1,"LH1 =",local_high1,"and","LL1 =",local_low1,"LH2 =",local_high2)
                                        if max_loss_for_trade > risk:
                                            num_of_lots = 1
                                            continue  # Skip this trade
                                        else:
                                            num_of_lots = math.floor(risk / max_loss_for_trade )
                                            number_of_positions += 1
                                            if num_of_lots >= max_num_lots:
                                                num_of_lots = max_num_lots
                                            entry_price = local_high1 + (tick_val * 2)
                                            print("\033[32m<------ LONG ENTRY ------> (CH1 > LH1 and LL1 > LH2)\033[0m")  # ANSI escape codes for this color coding to work
                                            print("       ENTRY PRICE  :",entry_price)
                                            print("       NO OF LOTS :",num_of_lots)
                                            print("   ")
                                            bull = True
                                            bear = False
                                            flag = True
                                            temp_high1 = 0
                                            temp_low1 = 0

                                    # bearish candle
                                    if current_low1 < local_low1 and local_high1 < local_low2 and local_high1 != 0 and local_low1 != 0  and local_high2 != 0 and local_low2 != 0 and not bull and not flag:
                                        print("1 = hourly","2 = daily")
                                        print("CL1 =",current_low1,"LL1 =",local_low1,"and","LH1 =",local_high1,"LL2 =",local_low2)
                                        if max_loss_for_trade > risk:
                                            num_of_lots = 1
                                            continue  # Skip this trade
                                        else:
                                            num_of_lots = math.floor(risk / max_loss_for_trade )
                                            number_of_positions += 1
                                            if num_of_lots >= max_num_lots:
                                                num_of_lots = max_num_lots
                                            entry_price = local_low1 - (tick_val * 2)
                                            print("\033[31m<------ SHORT ENTRY ------> (CL1 < LL1 and LH1 < LL2)\033[0m")
                                            print("       ENTRY PRICE  :",entry_price)
                                            print("       NO OF LOTS :",num_of_lots)
                                            print("   ")
                                            bull = False
                                            bear = True
                                            flag = True
                                            temp_high1 = 0
                                            temp_low1 = 0

                                    if bull and local_low1 <= local_high1 - (tick_val * 4):
                                        num_of_trades += 1
                                        exit_price = local_low1 - (tick_val * 2)
                                        current_pnl = (exit_price - entry_price) * num_of_lots
                                        total_long_pnl += current_pnl
                                        TOTAL_P_L += current_pnl
                                        print("\033[32m<------ LONG EXIT ------> (SL=2PT)\033[0m")
                                        print("       EXIT PRICE  :", exit_price)
                                        print("       P&L :", current_pnl)
                                        print("       TOTAL P&L :", TOTAL_P_L)
                                        print("       NO OF LOTS :",num_of_lots)
                                        print("   ")
                                        bull = False
                                        bear = False
                                        flag = False
                                        temp_high1 = 0
                                        temp_low1 = 0

                                    if bear and local_high1 >= local_low1 + (tick_val * 4):
                                        num_of_trades += 1
                                        exit_price = local_high1 + (tick_val * 2)
                                        current_pnl = (entry_price - exit_price) * num_of_lots
                                        total_short_pnl += current_pnl
                                        TOTAL_P_L += current_pnl
                                        print("\033[31m<------ SHORT EXIT ------> (SL=2PT)\033[0m")
                                        print("       EXIT PRICE  :", exit_price)
                                        print("       P&L :", current_pnl)
                                        print("       TOTAL P&L :", TOTAL_P_L)
                                        print("       NO OF LOTS :",num_of_lots)
                                        print("   ")
                                        bull = False
                                        bear = False
                                        flag = False
                                        temp_high1 = 0
                                        temp_low1 = 0
                                except Exception as e:
                                    print("Error processing row:", e)
                            else:
                                continue
                    else:
                        continue
                else:
                    continue
    else:
        continue

# Performance Summary
print("\033[1mPERFORMANCE SUMMARY\033[0m")
print("TOTAL NO OF POSITIONS :",number_of_positions)
print("TOTAL NO OF TRADES  :",num_of_trades)
print("TOTAL P&L :",TOTAL_P_L)
print("TOTAL LONG P&L :",total_long_pnl)
print("TOTAL SHORT P&L :",total_short_pnl)
print("MAX LOSS :",max_loss)
print("MAX PROFIT :",max_profit)
print("POSITIVE P&L :",positive_pnl)
print("NEGATIVE P&L :",negative_pnl)
print(" ")
