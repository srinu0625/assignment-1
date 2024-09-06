import pandas as pd
import math
import time

file_path1 = r"C:\Users\lenovo\Desktop\ES D.csv"
file_path2 = r"C:\Users\lenovo\Desktop\ES W.csv"

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
time_column_name = 'Date (GMT)'

# Convert dates to datetime for better manipulation
data1[time_column_name] = pd.to_datetime(data1[time_column_name])
data2[time_column_name] = pd.to_datetime(data2[time_column_name])

# Sort weekly data by date
data2 = data2.sort_values(by=time_column_name).reset_index(drop=True)

# Initialize variables for tracking daily and weekly high/low

# for positive and negative trades
total_positive_trades = 0
total_negative_trades = 0
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0
local_high1 = local_low1 = local_high2 = local_low2 = 0
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0
current_high1 = current_low1 = 0
current_high2 = current_low2 = 0
previous_high2 = previous_low2 = 0
bull = bear = flag = False
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
contract_size = 5
tick_val = 0.25
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Track weekly data
current_week = None
weekly_info_printed = False

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the daily data
        current_date1 = row1[time_column_name].date()
        week_start = current_date1 - pd.DateOffset(days=current_date1.weekday())
        
        # Determine current week
        if current_week != week_start:
            # Update weekly information if the week has changed
            weekly_data = data2[data2[time_column_name].dt.date == week_start]
            if not weekly_data.empty:
                weekly_row = weekly_data.iloc[0]
                current_high2 = float(weekly_row[high_column_name])
                current_low2 = float(weekly_row[low_column_name])
                previous_high2 = current_high2
                previous_low2 = current_low2
                
                temp_high2 = current_high2
                temp_low2 = current_low2
                local_high2 = temp_high2
                local_low2 = temp_low2

                weekly_info_printed = False
                print(f"----WEEKLY :---- {week_start}")
                print(f"Current High2: {current_high2}, Previous High2: {previous_high2}, Local High2: {local_high2}")
                print(f"Current Low2: {current_low2}, Previous Low2: {previous_low2}, Local Low2: {local_low2}")
                print(" ------------------------------------------------------------------------------------------------")
            
            current_week = week_start
        
        # Daily data processing
        current_time1 = row1[time_column_name]
        high1 = float(row1[high_column_name])
        low1 = float(row1[low_column_name])
        
        if (high1 > current_high1) or (low1 < current_low1):
            previous_high1 = current_high1
            previous_low1 = current_low1
            current_high1 = high1
            current_low1 = low1

        # case 1 for data1
        if current_high1 > previous_high1:
            temp_high1 = current_high1
            local_low1 = temp_low1

        if current_low1 < previous_low1:
            temp_low1 = current_low1
            local_high1 = temp_high1

        if current_high1 > previous_high1 and current_low1 < previous_low1:
            local_high1 = temp_high1
            local_low1 = temp_low1
        
        # Printing data for data1
        print("----DAILY :----", current_time1.date())
        print("Current High1:", current_high1, "Previous High1:", previous_high1, "Local High1:", local_high1)
        print("Current Low1:", current_low1, "Previous Low1:", previous_low1, "Local Low1:", local_low1)
        print("   ")
        time.sleep(1.5)

        # Bullish entry and exit
        if local_high1 > 0:
            if (current_high1 > local_high1) and (local_low1 >= local_low2) and not bear and not flag:
                loss_for_trade = abs(local_high1 - current_low1 + (tick_val * 4)) * contract_size
                if loss_for_trade > risk:
                    num_of_lots = 1
                    continue
                else:
                    num_of_lots = math.floor(risk / loss_for_trade)
                    if num_of_lots >= max_num_lots:
                        num_of_lots = 5
                    entry_price = local_high1 + (tick_val * 2)
                    exit_price = current_low1 - (tick_val * 2)
                    print("\033[32m<------ LONG ENTRY ------>(CH1 > LH1) AND (LL1 >= LL2)\033[0m")
                    print("       ENTRY PRICE  =", entry_price)
                    print("        num_of_lots =", round(num_of_lots))
                    print("     loss_for_trade =", round(loss_for_trade))
                    print("----------------------------------------------------------")
                    bull = True
                    flag = True
                    continue
        
        # Updating exit price
        if bull and current_low1 > exit_price:
            exit_price = current_low1 

        # Bullish Exit
        if current_low1 < exit_price and bull and flag:
            num_of_trades += 1
            bull = False
            flag = False

            # Calculate P&L
            pnl = (exit_price - entry_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_long_pnl += pnl
            integer_pnl = float(pnl)  # Extract the integer part of the P&L

            # declaring maxloss and maxprofit
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)

            # Check if integer part of P&L is positive or negative and set color accordingly
            if integer_pnl >= 0:
                pnl_color = "\033[32m"  # Green color
            else:
                pnl_color = "\033[31m"  # Red color

            # Add to total positive or negative P&L based on the result
            if pnl >= 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1

            print("\033[32m<------ LONG EXIT ------>(LL1 >\033[0m")
            print("         EXIT PRICE =", exit_price)
            print("        num_of_lots =", round(num_of_lots))
            print("      num_of_trades =", num_of_trades)
            print("         max_profit =", round(max_profit, 2))
            print("           max_loss =", round(max_loss, 2))
            print("       P&L_Of_trade =", pnl_color, round(integer_pnl, 2), "\033[0m")
            print("---------------------------------------------------------")
            continue

        # Bearish entry
        if local_low1 > 0:
            if (current_low1 < local_low1) and (current_high1 <= current_high2) and not bull and not flag:
                loss_for_trade = abs(current_high1 - local_low1 + (tick_val * 4)) * contract_size
                if loss_for_trade > risk:
                    num_of_lots = 1
                    continue
                else:
                    num_of_lots = math.floor(risk / loss_for_trade)
                    if num_of_lots >= max_num_lots:
                        num_of_lots = 5
                    entry_price = local_low1 - (tick_val * 2)
                    exit_price = current_high1 + (tick_val * 2)
                    print("\033[31m<------ SHORT ENTRY ------> (CL1 < LL1) AND (LH1 <= LH2)\033[0m")
                    print("        ENTRY PRICE =", entry_price)
                    print("        num_of_lots =", round(num_of_lots))
                    print("     loss_for_trade =", round(loss_for_trade))
                    print("------------------------------------------------")
                    bear = True
                    flag = True
                    continue

        if bear and current_high1 < exit_price:
            exit_price = current_high1

        # Bearish exit
        if current_high1 > exit_price and bear and flag:
            number_of_positions -= 1
            num_of_trades += 1
            bear = False
            flag = False

            # Calculate P&L
            pnl = (entry_price - exit_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_short_pnl += pnl
            integer_pnl = float(pnl)  # Extract the integer part of the P&L

            # declaring maxloss and maxprofit
            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)

            # Check if integer part of P&L is positive or negative and set color accordingly
            if integer_pnl >= 0:
                pnl_color = "\033[32m"  # Green color
            else:
                pnl_color = "\033[31m"  # Red color

            # Add to total positive or negative P&L based on the result
            if pnl >= 0:
                positive_pnl += pnl
                total_positive_trades += 1
            else:
                negative_pnl += pnl
                total_negative_trades += 1

            print("\033[31m<------ SHORT EXIT ------>(LH1 >)\033[0m")
            print("         EXIT PRICE =", exit_price)
            print("        num_of_lots =", round(num_of_lots))
            print("      num_of_trades =", num_of_trades)
            print("         max_profit =", round(max_profit, 2))
            print("           max_loss =", round(max_loss, 2))
            print("       P&L_of_trade =", pnl_color, round(integer_pnl), "\033[0m")
            print("------------------------------------------------")
            continue

        # Set weekly info print flag
        weekly_info_printed = True

   
        print("------------------------------------------End of iteration---------------------------------------------")

# Final summary
max_loss_color = "\033[31m" if max_loss < 0 else "\033[32m"
max_profit_color = "\033[31m" if max_profit < 0 else "\033[32m"
positive_pnl_color = "\033[31m" if positive_pnl < 0 else "\033[32m"
negative_pnl_color = "\033[31m" if negative_pnl < 0 else "\033[32m"
total_long_pnl_color = "\033[31m" if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color = "\033[31m" if total_short_pnl < 0 else "\033[32m"
