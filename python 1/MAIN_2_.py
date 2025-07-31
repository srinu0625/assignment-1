import pandas as pd
import math
import time

file_path1 = r"D:\Data\ES Jun25_240min.csv"
file_path2 = r"D:\Data\ES Jun25_daily.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Assuming the column names for high and low are 'High' and 'Low'
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date(GMT)'

# temp column names
temp_high = 0
temp_low = 0

# local high and low
current_high1 = 0
current_low1 = 0
local_high1 = temp_high
local_low1 = temp_low
local_high2 = temp_high
local_low2 = temp_low

# flags
bull = False
bear = False
flag = False

# trade stats
number_of_positions = 0
num_of_trades = 0
entry_price = 0
exit_price = 0
contract_size = 50
tick_val = 1
max_loss = 0
max_profit = 0
max_loss_for_trade = 0
TOTAL_P_L = 0
total_long_pnl = 0
total_short_pnl = 0
positive_pnl = 0
negative_pnl = 0
num_of_lots = 0
max_num_lots = 5
risk = 450

# additional tracking for performance metrics
total_positive_trades = 0
total_negative_trades = 0
max_drawdown = 0
max_runup = 0
peak_pnl = 0
trough_pnl = 0

for index1, row1 in data1.iterrows():
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        current_date1 = row1[time_column_name].split()[0]

        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]

                if current_date2 == current_date1:
                    try:
                        current_time1 = row1[time_column_name]
                        current_high1 = float(row1[high_column_name])
                        previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else 0
                        current_low1 = float(row1[low_column_name])
                        previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else 0

                        current_time2 = row2[time_column_name]
                        current_high2 = float(row2[high_column_name])
                        previous_high2 = float(data2.at[index2 - 1, high_column_name]) if index2 > 0 else 0
                        current_low2 = float(row2[low_column_name])
                        previous_low2 = float(data2.at[index2 - 1, low_column_name]) if index2 > 0 else 0

                        if current_high2 > previous_high2:
                            temp_high = current_high2
                        if current_high2 > previous_high2:
                            local_low2 = temp_low
                        if current_low2 < previous_low2:
                            temp_low = current_low2
                        if current_low2 < previous_low2:
                            local_high2 = temp_high

                        print("DAILY Time:", current_time2)
                        print("Current High2:", current_high2, "Previous High2:", previous_high2, "local_high2:", local_high2, "temp_high2:", temp_high)
                        print("Current Low2:", current_low2, "Previous Low2:", previous_low2, "local_low2:", local_low2, "temp_low2:", temp_low)
                        print("   ")
                        # time.sleep(1.5)

                        if current_high1 > previous_high1:
                            temp_high = current_high1
                        if current_low1 < previous_low1:
                            local_high1 = temp_high
                        if current_low1 < previous_low1:
                            temp_low = current_low1
                        if current_high1 > previous_high1:
                            local_low1 = temp_low

                        print("HOURLY Time:", current_time1)
                        print("Current High1:", current_high1, "Previous High1:", previous_high1, "local_high1:", local_high1, "temp_high1:", temp_high)
                        print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "local_low1:", local_low1, "temp_low1:", temp_low)
                        # time.sleep(1.5)
                        print("-------------------------------------------------------------------------------------------")

                        if bull and current_low1 < exit_price:
                            exit_price = current_low1
                        if bear and current_high1 > exit_price:
                            exit_price = current_high1

                        max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                        if current_high1 > local_high1 and local_low1 > local_high2 and all([local_high1, local_low1, local_high2, local_low2]) and not bear and not flag:
                            if max_loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = min(math.floor(risk / max_loss_for_trade), max_num_lots)
                                number_of_positions += 1
                                entry_price = local_high1 + (tick_val * 2)
                                print("\033[32m<------ LONG ENTRY ------> (CH1 > LH1 and LL1 > LH2)\033[0m")
                                print("       ENTRY PRICE  =", entry_price)
                                print("   num_of_positions =", number_of_positions)
                                print("        num_of_lots =", round(num_of_lots))
                                print(" max_loss_for_trade =", round(max_loss_for_trade))
                                print("---------------------------------------------")
                                bull = True
                                flag = True
                                continue

                        if current_low1 < local_low1 and bull and flag:
                            exit_price = local_low1 - (tick_val * 2)
                            number_of_positions -= 1
                            num_of_trades += 1
                            print("\033[32m<------ LONG EXIT ------> (CL1 < LL1)\033[0m")
                            print("         EXIT PRICE =", exit_price)
                            print("   num_of_positions =", number_of_positions)
                            print("        num_of_lots =", round(-1 * num_of_lots))
                            print("      num_of_trades =", num_of_trades)
                            pnl = (exit_price - entry_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_long_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            positive_pnl += pnl if pnl >= 0 else 0
                            negative_pnl += pnl if pnl < 0 else 0
                            pnl_color = "\033[32m" if pnl >= 0 else "\033[31m"
                            print("        max_profit =", round(max_profit, 2))
                            print("          max_loss =", round(max_loss, 2))
                            print("      P&L_Of_trade =", pnl_color, round(pnl, 2), "\033[0m")
                            print("---------------------------------------------------------")
                            bull = False
                            flag = False
                            continue

                        max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                        if current_low1 < local_low1 and local_high1 < local_high2 and all([local_high1, local_low1, local_high2, local_low2]) and not bull and not flag:
                            if max_loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = min(math.floor(risk / max_loss_for_trade), max_num_lots)
                                number_of_positions += 1
                                entry_price = local_low1 - (tick_val * 2)
                                print("\033[31m<------ SHORT ENTRY ------> (CL1 < LL1 and LH1 < LH2)\033[0m")
                                print("        ENTRY PRICE =", entry_price)
                                print("   num_of_positions =", number_of_positions)
                                print("        num_of_lots =", round(num_of_lots))
                                print(" max_loss_for_trade =", round(max_loss_for_trade))
                                print("------------------------------------------------")
                                bear = True
                                flag = True
                                continue

                        if current_high1 > local_high1 and bear and flag:
                            exit_price = local_high1 + (tick_val * 2)
                            number_of_positions -= 1
                            num_of_trades += 1
                            print("\033[31m<------ SHORT EXIT ------> (CH1 > LH1)\033[0m")
                            print("         EXIT PRICE =", exit_price)
                            print("   num_of_positions =", number_of_positions)
                            print("        num_of_lots =", round(-1 * num_of_lots))
                            print("      num_of_trades =", num_of_trades)
                            pnl = (entry_price - exit_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_short_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            positive_pnl += pnl if pnl >= 0 else 0
                            negative_pnl += pnl if pnl < 0 else 0
                            pnl_color = "\033[32m" if pnl >= 0 else "\033[31m"
                            print("        max_profit =", round(max_profit, 2))
                            print("          max_loss =", round(max_loss, 2))
                            print("      P&L_of_trade =", pnl_color, round(pnl, 2), "\033[0m")
                            print("------------------------------------------------")
                            bear = False
                            flag = False
                            continue

                    except Exception as e:
                        print("Error:", e)

print("-----------------------------------End of iteration-------------------------------------")

# Final stats
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

