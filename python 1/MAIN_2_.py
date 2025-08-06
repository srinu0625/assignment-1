import pandas as pd
import math
import time

file_path1 = r"C:\Users\lenovo\Downloads\NYMEX_CL1!, 15_5c0b5.csv"
file_path2 = r"C:\Users\lenovo\Downloads\ICEEUR_DLY_BRN1!, 15_08646.csv"
# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date(GMT)'

# Trade stats and settings
contract_size = 50
tick_val = 1
max_num_lots = 5
risk = 450

# Initializing variables
number_of_positions = 0
num_of_trades = 0
entry_price = 0
exit_price = 0
TOTAL_P_L = 0
total_long_pnl = 0
total_short_pnl = 0
positive_pnl = 0
negative_pnl = 0
num_of_lots = 0
max_loss = 0
max_profit = 0
max_drawdown = 0
max_runup = 0
peak_pnl = 0
trough_pnl = 0
total_positive_trades = 0
total_negative_trades = 0

bull = False
bear = False
flag = False

# Temp storage for local highs/lows
temp_high = 0
temp_low = 0
local_high1 = 0
local_low1 = 0
local_high2 = 0
local_low2 = 0

for index1, row1 in data1.iterrows():
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        current_date1 = row1[time_column_name].split()[0]

        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]

                if current_date2 == current_date1:
                    try:
                        # Current and previous values
                        current_time1 = row1[time_column_name].split()[1]
                        current_high1 = float(row1[high_column_name])
                        current_low1 = float(row1[low_column_name])
                        previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else current_high1
                        previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else current_low1
                        
                        current_time2 = row2[time_column_name].split()[1]
                        current_high2 = float(row2[high_column_name])
                        current_low2 = float(row2[low_column_name])
                        previous_high2 = float(data2.at[index2 - 1, high_column_name]) if index2 > 0 else current_high2
                        previous_low2 = float(data2.at[index2 - 1, low_column_name]) if index2 > 0 else current_low2

                        # Update local high/low for daily
                        if current_high2 > previous_high2:
                            temp_high = current_high2
                            local_high2 = temp_high
                        if current_low2 < previous_low2:
                            temp_low = current_low2
                            local_low2 = temp_low

                        #Printing data for data2

                        print("DAILY Time:", current_time2)
                        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2, " temp_high2 :", temp_high)
                        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2, " temp_low2 :", temp_low)
                        print("   ")
                        time.sleep(1.5)

                        # Update local high/low for 240min
                        if current_high1 > previous_high1:
                            temp_high = current_high1
                            local_high1 = temp_high
                        if current_low1 < previous_low1:
                            temp_low = current_low1
                            local_low1 = temp_low

                        # Printing data for data1

                        print("HOURLY Time:", current_time1)
                        print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1, " temp_high1 :", temp_high)
                        print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1, " temp_low1 :", temp_low)
                        time.sleep(1.5)
                        print("-------------------------------------------------------------------------------------------")
                        
                        # updating exit price----------------------------------
                        if(bull and current_low1 < exit_price):
                           L_exit_price = current_low1

                        if(bear and current_high1 > exit_price):
                           S_exit_price = current_high1
            

                        # LONG ENTRY CONDITION
                        max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                        if current_high1 > local_high1 and local_low1 > local_high2 and all([local_high1, local_low1, local_high2, local_low2]) and not bear and not flag:
                            if max_loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = math.floor(risk / max_loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = max_num_lots
                            entry_price = local_high1 + (tick_val * 2)
                            print("\033[32m<------ LONG ENTRY ------> (CH1 > LH1 and LL1 > LH2)\033[0m")  # ANSI escape codes for this color coding to work
                            print("       ENTRY PRICE  = ", entry_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ",round(num_of_lots))
                            print(" max_loss_for_trade = ",round(max_loss_for_trade))
                            print("---------------------------------------------")
                            bull = True
                            flag = True
                            number_of_positions += 1
                            continue

                        # LONG EXIT
                        if current_low1 < local_low1 and bull and flag:
                            exit_price = local_low1 - (tick_val * 2)
                            pnl = (exit_price - entry_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_long_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            peak_pnl = max(peak_pnl, TOTAL_P_L)
                            trough_pnl = min(trough_pnl, TOTAL_P_L)
                            if pnl >= 0:
                                total_positive_trades += 1
                                positive_pnl += pnl
                            else:
                                total_negative_trades += 1
                                negative_pnl += pnl
                            num_of_trades += 1
                            number_of_positions -= 1
                            print("\033[32m<------ LONG EXIT ------> (CL1 < LL1)\033[0m")  # ANSI escape codes for this color coding to work
                            print("         EXIT PRICE = ", exit_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ", round(-1 * num_of_lots))
                            print("      num_of_trades = ", num_of_trades)
                            bull = False
                            flag = False
                            continue

                        # SHORT ENTRY CONDITION
                        max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                        if current_low1 < local_low1 and local_high1 < local_high2 and all([local_high1, local_low1, local_high2, local_low2]) and not bull and not flag:
                            if max_loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = math.floor(risk / max_loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = max_num_lots
                            entry_price = local_low1 - (tick_val * 2)
                            print("\033[31m<------ SHORT ENTRY ------> (CL1 < LL1 and LH1 < LH2)\033[0m")  # ANSI escape codes for this color coding to work
                            print("        ENTRY PRICE = ", entry_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ",round(num_of_lots))
                            print(" max_loss_for_trade = ",round(max_loss_for_trade))
                            print("------------------------------------------------")
                            bear = True
                            flag = True
                            number_of_positions += 1
                            continue

                        # SHORT EXIT
                        if current_high1 > local_high1 and bear and flag:
                            exit_price = local_high1 + (tick_val * 2)
                            pnl = (entry_price - exit_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_short_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            peak_pnl = max(peak_pnl, TOTAL_P_L)
                            trough_pnl = min(trough_pnl, TOTAL_P_L)
                            if pnl >= 0:
                                total_positive_trades += 1
                                positive_pnl += pnl
                            else:
                                total_negative_trades += 1
                                negative_pnl += pnl
                            num_of_trades += 1
                            number_of_positions -= 1
                            print("\033[31m<------ SHORT EXIT ------> (CH1 > LH1)\033[0m")  # ANSI escape codes for this color coding to work
                            print("         EXIT PRICE = ", exit_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ", round(-1 * num_of_lots))
                            print("      num_of_trades = ", num_of_trades)
                            bear = False
                            flag = False
                            continue

                    except Exception as e:
                        print("Error:", e)

# Final metrics
TradeCost = num_of_trades * 3
Net = TOTAL_P_L - TradeCost
max_drawdown = peak_pnl - trough_pnl if TOTAL_P_L < peak_pnl else 0
max_runup = peak_pnl
success_rate = (total_positive_trades / num_of_trades) * 100 if num_of_trades else 0
failure_rate = 100 - success_rate


print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")  
print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
print(f" Total Long PnL = \033[94m{total_long_pnl:.2f}\033[0m")
print(f"Total Short PnL = \033[94m{total_short_pnl:.2f}\033[0m")
print(f"          Gross = {TOTAL_P_L:.2f}")
print(f"     Trade Cost = {TradeCost:.2f}")
print(f"            Net = {Net:.2f}")
print(f"   Max Drawdown = {max_drawdown:.2f}")
print(f"     Max Run-up = {max_runup:.2f}")
print(f"Positive Trades = \033[92m{total_positive_trades}\033[0m")
print(f"Negative Trades = \033[91m{total_negative_trades}\033[0m")
print(f"   Total Trades = {num_of_trades}")
print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")