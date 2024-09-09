import pandas as pd
import math
import time

file_path1 = r"D:\candles\nq contracts\NQ U 240.csv"
file_path2 = r"D:\candles\nq contracts\NQ U day.csv"

output_file_path_long =  r"D:\Output_TradeBooks\NQ U LONG TRADES.csv"
output_file_path_short =  r"D:\Output_TradeBooks\NQ U SHORT TRADES.csv"


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
temp_high1 = temp_low1 = temp_high2 = temp_low2  = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2  = 0
current_high1 = 0
current_low1 = 0
current_high2 = 0
current_low2 = 0

previous_high2 = 0
previous_low2 = 0

# prev local high and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0
# for positive and negative trades
total_positive_trades = 0
total_negative_trades = 0

# Trading flags
bull = bear = flag = False

# Trading parameters
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
contract_size = 2
tick_val = 0.25
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Initialize list to store trade entries
trade_entries_long = []
trade_entries_short = []
# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the daily data
        current_date1 = row1[time_column_name].split()[0]

        # Iterate over each row of the hourly DataFrame (data2)
        for index2, row2 in data2.iterrows():
            # Check if the row has valid data
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                # Extract the current date from the hourly data
                current_date2 = row2[time_column_name].split()[0]

                # If the hourly data date matches the daily data date
                if current_date2 == current_date1:
                    try:
                         # Extracting current and previous values for high and low from data1
                        current_time1 = row1[time_column_name]
                        high1 = float(row1[high_column_name])
                        low1 = float(row1[low_column_name])
                        if (high1 > current_high1) or (low1 < current_low1):
                            previous_high1 = current_high1
                            previous_low1 = current_low1
                            current_high1 = high1
                            current_low1 = low1

                        # Extracting current and previous values for high and low from data2
                        current_time2 = (data2.at[index2 - 1, time_column_name])
                        high2 = float(row2[high_column_name])
                        low2 = float(row2[low_column_name])
                        if (high2 > current_high2) or(low2 < current_low2):
                            previous_high2 = current_high2
                            previous_low2 = current_low2
                            current_high2 = high2
                            current_low2 = low2

                        # Case 1 for data1
                        if current_high1 > previous_high1:
                            temp_high1 = current_high1
                            local_low1 = temp_low1

                        if current_low1 < previous_low1:
                            temp_low1 = current_low1
                            local_high1 = temp_high1

                        if current_high1 > previous_high1 and current_low1 < previous_low1:
                            local_high1 = temp_high1
                            local_low1 = temp_low1
                            # Printing data for data2
                        print("----240 MIN:----", current_time1)
                        print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :",
                                  local_high1)
                        print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :",
                                  local_low1)
                        print("   ")
                        time.sleep(0)

                            # case 1 for data2
                        if current_high2 > previous_high2:
                                temp_high2 = current_high2
                                local_low2 = temp_low2

                        if current_low2 < previous_low2:
                                temp_low2 = current_low2
                                local_high2 = temp_high2

                        if current_high2 > previous_high2 and current_low2 < previous_low2:
                                local_high2 = temp_high2
                                local_low2 = temp_low2

                            # Printing data for data2
                        print("----DAILY :----", current_time2)
                        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :",
                                  local_high2)
                        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :",
                                  local_low2)
                        print("   ")
                        time.sleep(0)
                        # Capture data for data1
                        data1_log = {
                            'Type': 'N/A',
                            'Time': current_time1,
                            'Current High1': current_high1,
                            'Previous High1': previous_high1,
                            'Local High1': local_high1,
                            'Current Low1': current_low1,
                            'Previous Low1': previous_low1,
                            'Local Low1': local_low1
                        }

                        # Capture data for data2
                        data2_log = {
                            'Type': 'N/A',
                            'Time': current_time2,
                            'Current High2': current_high2,
                            'Previous High2': previous_high2,
                            'Local High2': local_high2,
                            'Current Low2': current_low2,
                            'Previous Low2': previous_low2,
                            'Local Low2': local_low2
                        }

                        # Bullish entry
                        if local_high1 > 0:
                            if (current_high1 > local_high1) and  not bear and not flag:
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

                                    # Record the trade entry
                                    trade_entries_long.append({
                                        'Type': 'Long',
                                        'Entry Time': current_time1,
                                        'Entry Price': entry_price,
                                        'Local High': local_high1,
                                        'Local Low': local_low1,
                                        'Prev  High': previous_high1,
                                        'Prev  Low': previous_low1,
                                        'Current High': current_high1,
                                        'Current Low': current_low1,
                                        'local_high2':local_high2
                                        
                                    })

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

                            # Declaring max loss and max profit
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

                            # Record the trade exit
                            trade_entries_long.append({
                                'Type': 'Long Exit',
                                'Entry Time': current_time1,
                                'Exit Time': current_time1,
                                'Entry Price': entry_price,
                                'Exit Price': exit_price,
                                'Local High': local_high1,
                                'Local Low': local_low1,
                                'Prev  High': previous_high1,
                                'Prev  Low': previous_low1,
                                'Current High': current_high1,
                                'Current Low': current_low1,
                                'local_high2':local_high2,
                                'num_of_lots':round(num_of_lots),
                                'P&L': pnl
                               
                            })

                            continue

                        # Bearish entry
                        if local_low1 > 0:
                            if (current_low1 < local_low1) and not bull and not flag:
                                loss_for_trade = abs(local_low1 - current_high1 + ( tick_val * 4)) * contract_size
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

                                        # Record the trade entry
                                    trade_entries_short.append({
                                        'Type': 'Short',
                                        'Entry Time': current_time1,
                                        'Entry Price': entry_price,
                                        'Local High': local_high1,
                                        'Local Low': local_low1,
                                        'Prev  High': previous_high1,
                                        'Prev  Low': previous_low1,
                                        'Current High': current_high1,
                                        'Current Low': current_low1,
                                        'local_high2':local_high2
                                        
                                    })

                                    continue

                        # Updating exit price
                        if bear and current_high1 < exit_price:
                            exit_price = current_high1

                        # Bearish Exit
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

                            # Declaring max loss and max profit
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
                            print("       P&L_of_trade = ", pnl_color, round(integer_pnl, 2), "\033[0m")
                            print("------------------------------------------------")

                            # Record the trade exit
                            trade_entries_short.append({
                                'Type': 'Short Exit',
                                'Entry Time': current_time1,
                                'Exit Time': current_time1,
                                'Entry Price': entry_price,
                                'Exit Price': exit_price,
                                'Local High': local_high1,
                                'Local Low': local_low1,
                                'Prev  High': previous_high1,
                                'Prev  Low': previous_low1,
                                'Current High': current_high1,
                                'Current Low': current_low1,
                                'local_high2':local_high2,
                                'num_of_lots':round(num_of_lots),
                                'P&L': pnl
                               
                            })

                            continue

                    except Exception as e:
                        print("Error:", e)

                    finally:
                        print("------------------------------------------End of iteration---------------------------------------------")

# Save trade entries to a CSV file
trade_entries_long_df = pd.DataFrame(trade_entries_long)
trade_entries_long_df.to_csv(output_file_path_long, index=False)
trade_entries_short_df = pd.DataFrame(trade_entries_short)
trade_entries_short_df.to_csv(output_file_path_short, index=False)

# Print final statistics
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

# Prepare summary statistics
summary_stats_long = {
    'Type': 'Summary',
    'Entry Time': '',
    'Exit Time': '',
    'Entry Price': '',
    'Exit Price': '',
    'Local High': '',
    'Local Low': '',
    'Prev  High': '',
    'Prev  Low': '',
    'Current High': '',
    'Current Low': '',
    'local_high2': '',
    'num_of_lots': '',
    'P&L': '',

    'max_profit': round(max_profit, 2),
    'max_loss': round(max_loss, 2),
    'positive_pnl': round(positive_pnl, 2),
    'negative_pnl': round(negative_pnl, 2),
    'total_long_pnl': round(total_long_pnl, 2),
    'total_short_pnl': round(total_short_pnl, 2),
    'TOTAL_P_L': round(TOTAL_P_L, 2),
    'num_of_trades': num_of_trades,
    'total_positive_trades': total_positive_trades,
    'total_negative_trades': total_negative_trades
}

summary_stats_short = summary_stats_long.copy()

# Append the summary statistics to the DataFrames
trade_entries_long.append(summary_stats_long)
trade_entries_short.append(summary_stats_short)

# Save the trade entries along with summary statistics to CSV files
trade_entries_long_df = pd.DataFrame(trade_entries_long)
trade_entries_long_df.to_csv(output_file_path_long, index=False)

trade_entries_short_df = pd.DataFrame(trade_entries_short)
trade_entries_short_df.to_csv(output_file_path_short, index=False)
