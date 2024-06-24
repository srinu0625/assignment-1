import pandas as pd
import math

file_path1 = r"D:\data\snp hour.csv"
file_path2 = r"D:\data\snp daily.csv"

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

# Initialize variables
contract_size = 50
tick_val = 2
max_loss = 0
max_profit = 0
TOTAL_P_L = 0
total_long_pnl = 0
total_short_pnl = 0
num_of_trades = 0
max_num_lots = 5
risk = 450

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the daily data
        current_date1 = row1[time_column_name].split()[0]

        # Reset flags and variables for each daily iteration
        bull = False
        bear = False
        flag = False
        entry_price = 0
        num_of_lots = 0

        # Initialize local highs and lows
        local_high1 = 0
        local_low1 = 0
        local_high2 = 0
        local_low2 = 0

        # Iterate over each row of the hourly DataFrame (data2)
        for index2, row2 in data2.iterrows():
            # Check if the row has valid data
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                # Extract the current date from the hourly data
                current_date2 = row2[time_column_name].split()[0]

                # If the hourly data date matches the daily data date
                if current_date2 == current_date1:
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

                    # Update local highs and lows for data1
                    if current_high1 > previous_high1:
                        local_high1 = current_high1
                    if current_low1 < previous_low1:
                        local_low1 = current_low1

                    # Update local highs and lows for data2
                    if current_high2 > previous_high2:
                        local_high2 = current_high2
                    if current_low2 < previous_low2:
                        local_low2 = current_low2

                    # Print data for debugging
                    print("DAILY Time:", row1[time_column_name])
                    print("Current High1:", current_high1, "Previous High1:", previous_high1, "Local High1:", local_high1)
                    print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "Local Low1:", local_low1)
                    print(" ")
                    print("HOURLY Time:", row2[time_column_name])
                    print("Current High2:", current_high2, "Previous High2:", previous_high2, "Local High2:", local_high2)
                    print("Current Low2:", current_low2, "Previous Low2:", previous_low2, "Local Low2:", local_low2)
                    print("-------------------------------------------------------------------------------------------")

                    # Evaluate bullish condition and execute trades
                    # Evaluate bullish condition and execute trades
                    max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                    if (local_low1 > local_low2) and (local_low1 > current_low2) and (local_high1 != 0 and local_low1 != 0 and local_high2 != 0 and local_low2 != 0) and (not bear and not flag):
                       if max_loss_for_trade > risk:
                          num_of_lots = 1
                          continue
                    num_of_lots = math.floor(risk / max_loss_for_trade)

                    # Execute long entry
                    entry_price = local_high1 + (tick_val * 2)
                    print("\033[32m<------ LONG ENTRY ------>\033[0m")
                    print("ENTRY PRICE  = ", entry_price)
                    print("num_of_lots = ", round(num_of_lots))
                    print("max_loss_for_trade = ", round(max_loss_for_trade))
                    print("---------------------------------------------")
                    bull = True
                    flag = True

                    # Set exit condition for long trade
                    if current_low1 <= entry_price - 2 * tick_val:
                        exit_price = current_low1
                        num_of_trades += 1
                        print("\033[32m<------ LONG EXIT ------>\033[0m")
                        print("EXIT PRICE = ", exit_price)
                        print("num_of_lots = ", round(-1 * num_of_lots))
                        print("num_of_trades = ", num_of_trades)
                        bull = False
                        flag = False

                        # Calculate P&L
                        pnl = (exit_price - entry_price) * num_of_lots * contract_size
                        TOTAL_P_L += pnl
                        total_long_pnl += pnl
                        integer_pnl = float(pnl)  # Extract the integer part of the P&L

                        # Update max profit and max loss
                        max_profit = max(max_profit, pnl)
                        max_loss = min(max_loss, pnl)

                        # Print P&L details
                        print("max_profit = ", round(max_profit, 2))
                        print("max_loss = ", round(max_loss, 2))
                        print("P&L_Of_trade = ", "\033[32m" if pnl >= 0 else "\033[31m", round(integer_pnl, 2), "\033[0m")
                        print("---------------------------------------------------------")
                        continue

                    # Evaluate bearish condition and execute trades
                    max_loss_for_trade = (local_high1 - local_low1 + (tick_val * 4)) * contract_size
                    if (local_high1 < local_high2) and (local_high1 < current_high2) and (local_high1 != 0 and local_low1 != 0 and local_high2 != 0 and local_low2 != 0) and (not bull and not flag):
                        if max_loss_for_trade > risk:
                            num_of_lots = 1
                            continue
                        num_of_lots = math.floor(risk / max_loss_for_trade)

                        # Execute short entry
                        entry_price = local_low1 - (tick_val * 2)
                        print("\033[31m<------ SHORT ENTRY ------>\033[0m")
                        print("ENTRY PRICE = ", entry_price)
                        print("num_of_lots = ", round(num_of_lots))
                        print("max_loss_for_trade = ", round(max_loss_for_trade))
                        print("------------------------------------------------")
                        bear = True
                        flag = True

                        # Set exit condition for short trade
                        if current_high1 >= entry_price + 2 * tick_val:
                            exit_price = current_high1 - (tick_val * 2)
                            num_of_trades += 1
                            print("\033[31m<------ SHORT EXIT ------>\033[0m")
                            print("EXIT PRICE = ", exit_price)
                            print("num_of_lots = ", round(-1 * num_of_lots))
                            print("num_of_trades = ", num_of_trades)
                            bear = False
                            flag = False

                            # Calculate P&L
                            pnl = (entry_price - exit_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_short_pnl += pnl
                            integer_pnl = float(pnl)  # Extract the integer part of the P&L

                            # Update max profit and max loss
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)

                            # Print P&L details
                            print("max_profit = ", round(max_profit, 2))
                            print("max_loss = ", round(max_loss, 2))
                            print("P&L_Of_trade = ", "\033[32m" if pnl >= 0 else "\033[31m", round(integer_pnl, 2), "\033[0m")
                            print("---------------------------------------------------------")
                            continue

# Formatting output colors based on P&L results
max_loss_color = "\033[31m" if max_loss < 0 else "\033[32m"
max_profit_color = "\033[31m" if max_profit < 0 else "\033[32m"
positive_pnl_color = "\033[31m" if TOTAL_P_L < 0 else "\033[32m"
negative_pnl_color = "\033[31m" if TOTAL_P_L < 0 else "\033[32m"
total_long_pnl_color = "\033[31m" if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color = "\033[31m" if total_short_pnl < 0 else "\033[32m"

# Printing final P&L results
print("     max_profit = ", max_profit_color, round(max_profit, 2), "\033[0m")
print("       max_loss = ", max_loss_color, round(max_loss, 2), "\033[0m")
print("   total_long_pnl = ", total_long_pnl_color, round(total_long_pnl, 2), "\033[0m")
print("   total_short_pnl = ", total_short_pnl_color, round(total_short_pnl, 2), "\033[0m")
print("      TOTAL_P_L = ", "\033[32m" if TOTAL_P_L >= 0 else "\033[31m", round(TOTAL_P_L, 2), "\033[0m")
print("  num_of_trades = ", num_of_trades)
