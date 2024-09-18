import pandas as pd
import math
import time

file_path1 = r"D:\data\ym hour.csv"
file_path2 = r"D:\data\ym daily.csv"

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
time_column_name = 'Date (GMT)'

# P&L parameters
contract_size = 5
tick_val = 1
risk_per_trade = 450

# Trading variables initialization
current_high1 = 0
current_low1 = 0
local_high1 = 0
local_low1 = 0
bull = False
bear = False
flag = False
number_of_positions = 0
num_of_trades = 0
max_loss = 0
max_profit = 0
TOTAL_P_L = 0
total_long_pnl = 0
total_short_pnl = 0
positive_pnl = 0
negative_pnl = 0
num_of_lots = 0
max_num_lots = 5

try:
    # Iterate over each row of the daily DataFrame (data1)
    for index1, row1 in data1.iterrows():
        if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
            current_date1 = row1[time_column_name].split()[0]

            # Iterate over each row of the hourly DataFrame (data2)
            for index2, row2 in data2.iterrows():
                if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                    current_date2 = row2[time_column_name].split()[0]

                    if current_date2 == current_date1:
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

                        # Logic for data1
                        if current_high1 > previous_high1:
                            local_high1 = current_high1
                            local_low1 = previous_low1  # Assuming local low is the previous low

                        if current_low1 < previous_low1:
                            local_low1 = current_low1
                            local_high1 = previous_high1  # Assuming local high is the previous high

                        # Logic for data2
                        if current_high2 > previous_high2:
                            local_high2 = current_high2
                            local_low2 = previous_low2  # Assuming local low is the previous low

                        if current_low2 < previous_low2:
                            local_low2 = current_low2
                            local_high2 = previous_high2  # Assuming local high is the previous high

                        # Entry conditions for long and short trades
                        if current_high1 > local_high1 and local_low1 > local_low2 and local_low1 > current_low2 and not bear and not flag:
                            max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                            if max_loss_for_trade <= risk_per_trade:
                                num_of_lots = math.floor(risk_per_trade / max_loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = max_num_lots
                                entry_price = local_high1 + (tick_val * 2)
                                print("<------ LONG ENTRY ------> (LL1 > LL2 and LL1 > CL2)")
                                print("       ENTRY PRICE  = ", entry_price)
                                print("   num_of_positions = ", number_of_positions)
                                print("        num_of_lots = ", round(num_of_lots))
                                print(" max_loss_for_trade = ", round(max_loss_for_trade))
                                print("---------------------------------------------")
                                bull = True
                                flag = True

                        elif current_low1 < local_low1 and local_high1 < local_high2 and local_high1 < current_high2 and not bull and not flag:
                            max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                            if max_loss_for_trade <= risk_per_trade:
                                num_of_lots = math.floor(risk_per_trade / max_loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = max_num_lots
                                entry_price = local_low1 - (tick_val * 2)
                                print("<------ SHORT ENTRY ------> (LH1 < LL2 and LH1 < CH2)")
                                print("        ENTRY PRICE = ", entry_price)
                                print("   num_of_positions = ", number_of_positions)
                                print("        num_of_lots = ", round(num_of_lots))
                                print(" max_loss_for_trade = ", round(max_loss_for_trade))
                                print("------------------------------------------------")
                                bear = True
                                flag = True

                        # Exit conditions
                        if current_low1 >= local_low1 and bull and flag:
                            exit_price = current_low1 - (tick_val * 2)
                            number_of_positions -= 1
                            num_of_trades += 1
                            print("<------ LONG EXIT ------> (CL1 < LL1)")
                            print("         EXIT PRICE = ", exit_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ", round(-1 * num_of_lots))
                            print("      num_of_trades = ", num_of_trades)

                            pnl = (exit_price - entry_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_long_pnl += pnl

                            bull = False
                            flag = False

                        elif current_high1 >= local_high1 and bear and flag:
                            exit_price = current_high1 + (tick_val * 2)
                            number_of_positions -= 1
                            num_of_trades += 1
                            print("<------ SHORT EXIT ------> (CH1 > LH1)")
                            print("         EXIT PRICE = ", exit_price)
                            print("   num_of_positions = ", number_of_positions)
                            print("        num_of_lots = ", round(-1 * num_of_lots))
                            print("      num_of_trades = ", num_of_trades)

                            pnl = (entry_price - exit_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_short_pnl += pnl

                            bear = False
                            flag = False

except Exception as e:
    print("Error:", e)

finally:
    print("-----------------------------------End of iteration-------------------------------------")

max_loss_color = "\033[31m" if max_loss < 0 else "\033[32m"
max_profit_color = "\033[31m" if max_profit < 0 else "\033[32m"
positive_pnl_color = "\033[31m" if positive_pnl < 0 else "\033[32m"
negative_pnl_color = "\033[31m" if negative_pnl < 0 else "\033[32m"
total_long_pnl_color = "\033[31m" if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color = "\033[31m" if total_short_pnl < 0 else "\033[32m"
TOTAL_P_L_colour = "\033[31m" if TOTAL_P_L < 0 else "\033[32m"

print("           max_profit = ", max_profit_color, round(max_profit, 2), "\033[0m")
print("             max_loss = ", max_loss_color, round(max_loss, 2), "\033[0m")
print("         positive_pnl = ", positive_pnl_color, round(positive_pnl, 2), "\033[0m")
print("         negative_pnl = ", negative_pnl_color, round(negative_pnl, 2), "\033[0m")
print("      total_long_pnl  = ", total_long_pnl_color, round(total_long_pnl, 2), "\033[0m")
print("     total_short_pnl  = ", total_short_pnl_color, round(total_short_pnl, 2), "\033[0m")
print("            TOTAL_P_L = ", TOTAL_P_L_colour, round(TOTAL_P_L, 2), "\033[0m")
print("        num of trades = ", num_of_trades)
print("Total Positive Trades =", total_positive_trades)
print("Total Negative Trades =", total_negative_trades)
