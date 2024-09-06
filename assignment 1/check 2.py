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

## Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2 = 0

# prev local high and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0

# for positive and negative trades
total_positive_trades = 0
total_negative_trades = 0

current_high1 = 0
current_low1 = 0
current_high2 = 0
current_low2 = 0

previous_high2 = 0
previous_low2 = 0

# Trading flags
bull = bear = flag = False

# Trading parameters
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
contract_size = 5
tick_val = 0.25
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Weekly data accumulation
weekly_high1 = weekly_low1 = None
weekly_high2 = weekly_low2 = None
weekly_start_date = None

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the daily data
        current_date1 = row1[time_column_name].split()[0]

        # Determine the start of the week from the current date
        current_date1_dt = pd.to_datetime(current_date1)
        start_of_week = current_date1_dt - pd.to_timedelta(current_date1_dt.weekday(), unit='d')
        end_of_week = start_of_week + pd.DateOffset(days=6)

        # Reset weekly data if new week is detected
        if weekly_start_date is None:
            weekly_start_date = start_of_week
        elif current_date1_dt > end_of_week:
            # Print previous week data
            print(f"----WEEKLY DATA ({weekly_start_date.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')})----")
            print(f"Weekly High1: {weekly_high1}")
            print(f"Weekly Low1: {weekly_low1}")
            print(f"Weekly High2: {weekly_high2}")
            print(f"Weekly Low2: {weekly_low2}")
            print("-----------------------------------------------------------")

            # Update weekly start and end dates
            weekly_start_date = start_of_week
            end_of_week = start_of_week + pd.DateOffset(days=6)

            # Reset weekly data
            weekly_high1 = weekly_low1 = None
            weekly_high2 = weekly_low2 = None

        # Extracting current values for high and low from data1
        high1 = float(row1[high_column_name])
        low1 = float(row1[low_column_name])
        if weekly_high1 is None or high1 > weekly_high1:
            weekly_high1 = high1
        if weekly_low1 is None or low1 < weekly_low1:
            weekly_low1 = low1

        # Iterate over each row of the hourly DataFrame (data2)
        for index2, row2 in data2.iterrows():
            # Check if the row has valid data
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                # Extract the current date from the hourly data
                current_date2 = row2[time_column_name].split()[0]

                # If the hourly data date matches the daily data date
                if current_date2 == current_date1:
                    try:
                        # Extracting current and previous values for high and low from data2
                        current_time2 = data2.at[index2 - 1, time_column_name]
                        high2 = float(row2[high_column_name])
                        low2 = float(row2[low_column_name])
                        if weekly_high2 is None or high2 > weekly_high2:
                            weekly_high2 = high2
                        if weekly_low2 is None or low2 < weekly_low2:
                            weekly_low2 = low2

                        # Printing data for data2
                        print("----WEEKLY :----", current_time2)
                        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2)
                        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2)
                        print("   ")
                        time.sleep(1.5)

                        # Bullish entry
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
                                    print("       ENTRY PRICE  = ", entry_price)
                                    print("        num_of_lots = ", round(num_of_lots))
                                    print("     loss_for_trade = ", round(loss_for_trade))
                                    print("----------------------------------------------------------")
                                    bull = True
                                    flag = True
                                    continue

                        # updating exit price
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
                            print("         EXIT PRICE = ", exit_price)
                            print("        num_of_lots = ", round(num_of_lots))
                            print("      num_of_trades = ", num_of_trades)
                            print("         max_profit = ", round(max_profit, 2))
                            print("           max_loss = ", round(max_loss, 2))
                            print("       P&L_Of_trade = ", pnl_color, round(integer_pnl, 2), "\033[0m")
                            print("---------------------------------------------------------")
                            continue

                        # Bearish entry----------------------------------------------------------------------------
                        if local_low1 > 0:
                            if (current_low1 < local_low1) and (local_high1 <= local_high2) and not bull and not flag:
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
                                    print("        ENTRY PRICE = ", entry_price)
                                    print("        num_of_lots = ", round(num_of_lots))
                                    print("     loss_for_trade = ", round(loss_for_trade))
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
                            print("         EXIT PRICE = ", exit_price)
                            print("        num_of_lots = ", round(num_of_lots))
                            print("      num_of_trades = ", num_of_trades)
                            print("         max_profit = ", round(max_profit, 2))
                            print("           max_loss = ", round(max_loss, 2))
                            print("       P&L_of_trade = ", pnl_color, round(integer_pnl), "\033[0m")
                            print("------------------------------------------------")
                            continue

                    except Exception as e:
                        print("Error:", e)

                    finally:
                        print("-----------------------------------End of iteration-------------------------------------")

# Print data for the last week
if weekly_start_date:
    print(f"----WEEKLY DATA ({weekly_start_date.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')})----")
    print(f"Weekly High1: {weekly_high1}")
    print(f"Weekly Low1: {weekly_low1}")
    print(f"Weekly High2: {weekly_high2}")
    print(f"Weekly Low2: {weekly_low2}")
    print("-----------------------------------------------------------")

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
