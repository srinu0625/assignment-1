import pandas as pd
import math
import time
file_path1 = r"D:\candles\es monthly data\es feb 60 min.csv"
file_path2 = r"D:\candles\es monthly data\es feb 240 min.csv"
file_path3 = r"D:\candles\es monthly data\es feb daily.csv"

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
tick_val = 0.25

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
max_num_lots = 20
risk = 360

#total rows in sheets
rows_count_240_mins=0
rows_count_daily=0
current_hours_count=1
date_flag = False

previous_date = data1.loc[0,time_column_name].split()[0]

current_time2 = data2.loc[rows_count_240_mins, time_column_name]
current_high2 = float(data2.loc[rows_count_240_mins,high_column_name])
previous_high2 = float(data2.loc[rows_count_240_mins-1,high_column_name]) if rows_count_240_mins > 0 else 0
current_low2 = float(data2.loc[rows_count_240_mins,low_column_name])
previous_low2 = float(data2.loc[rows_count_240_mins-1,low_column_name]) if rows_count_240_mins > 0 else 0

current_time3 = data3.loc[rows_count_daily, time_column_name]
current_high3 = float(data3.loc[rows_count_daily,high_column_name])
previous_high3 = float(data3.loc[rows_count_daily-1,high_column_name]) if rows_count_daily > 0 else 0
current_low3 = float(data3.loc[rows_count_daily,low_column_name])
previous_low3 = float(data3.loc[rows_count_daily-1,low_column_name]) if rows_count_daily > 0 else 0
current_date3 = data3.loc[rows_count_daily,time_column_name].split()[0]

# Iterate over each row of the daily DataFrame (data3)
for index1, row1 in data1.iterrows():
    current_date = row1[time_column_name].split()[0]
    if(previous_date != current_date):
        date_flag = True

    try:
        # Extracting current and previous values for high and low from data1
        current_time1 = row1[time_column_name]
        current_high1 = float(row1[high_column_name])
        previous_high1 = float(data1.at[index1 - 1, high_column_name]) if index1 > 0 else 0
        current_low1 = float(row1[low_column_name])
        previous_low1 = float(data1.at[index1 - 1, low_column_name]) if index1 > 0 else 0

        # Extracting current and previous values for high and low from data2
        if(current_hours_count==5 or date_flag):
            rows_count_240_mins=rows_count_240_mins+1
            print("Assigned Row number:", rows_count_240_mins)
            current_time2 = data2.loc[rows_count_240_mins, time_column_name]
            current_high2 = float(data2.loc[rows_count_240_mins,high_column_name])
            previous_high2 = float(data2.loc[rows_count_240_mins-1,high_column_name]) if rows_count_240_mins > 0 else 0
            current_low2 = float(data2.loc[rows_count_240_mins,low_column_name])
            previous_low2 = float(data2.loc[rows_count_240_mins-1,low_column_name]) if rows_count_240_mins > 0 else 0
            current_hours_count=1

        # Extracting current and previous values for high and low from data3
        print(date_flag)
        if date_flag:
            rows_count_daily=rows_count_daily+1
            current_date3 = data3.loc[rows_count_daily,time_column_name].split()[0]
            current_time3 = data3.loc[rows_count_daily, time_column_name]
            current_high3 = float(data3.loc[rows_count_daily,high_column_name])
            previous_high3 = float(data3.loc[rows_count_daily-1,high_column_name]) if rows_count_daily > 0 else 0
            current_low3 = float(data3.loc[rows_count_daily,low_column_name])
            previous_low3 = float(data3.loc[rows_count_daily-1,low_column_name]) if rows_count_daily > 0 else 0

        # case 1 for data1-----------------------------------------------------------------------------------
        if(current_high1 > previous_high1):
            temp_high1 = current_high1
            

        if(current_low1 < previous_low1):
            temp_low1 = current_low1
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high1 > previous_high1):
            local_low1 = temp_low1

        if(current_low1 < previous_low1):
            local_high1 = temp_high1
        

        # Printing data for data1

        print("---60 MIN---:", current_time1)
        print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1)
        print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1)
        print("   ")
        time.sleep(0)

    # case 1 for data2-----------------------------------------------------------------------------------
        if (current_high2 > previous_high2):
            temp_high2 = current_high2

        if (current_low2 < previous_low2):
            temp_low2 = current_low2
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high2 > previous_high2):
            local_low2 = temp_low2

        if(current_low2 < previous_low2):
            local_high2 = temp_high2
        
        # Printing data for data2

        print("---240 MIN---:", current_time2)
        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2)
        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2)
        print("   ")
        time.sleep(0)

        # case 1 for data3-----------------------------------------------------------------------------------
        if (current_high3 > previous_high3):
            temp_high3 = current_high3

        if (current_low3 < previous_low3):
            temp_low3 = current_low3
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high3 > previous_high3):
            local_low3 = temp_low3

        if(current_low3 < previous_low3):
            local_high3 = temp_high3

        # Printing data for data3

        print("----DAILY----:", current_time3)
        print("Current High3 :", current_high3, "Previous High3 :", previous_high3, "local_high3 :", local_high3)
        print("Current Low3 :", current_low3, "Previous Low3 :", previous_low3, "local_low3 :", local_low3)
        time.sleep(0)
        print("   ")

       # updating exit price----------------------------------
        if(bull and current_low1 > exit_price):
            exit_price = current_low1

        if(bear and current_high1 < exit_price):
            exit_price = current_high1

        # bullish candle   
        max_loss_for_trade = (max(current_high1, local_high1) - current_low1 + ( tick_val * 4)) * contract_size  
        if (current_high1 > local_high1) and ((local_high1 > local_high2) or (local_high1 > local_high3) or (local_high1 > current_high3)) and ((local_low1 > local_low2) and (local_low1 > local_low3) and (local_low1 > current_low3)) and local_high1 != 0 and local_low1 != 0  and local_high2 != 0 and local_low2 != 0 and not bear and not flag :
            if max_loss_for_trade > risk:
                   num_of_lots = 5
                   continue 
            else:
                max_loss_for_trade <= risk
                num_of_lots = math.floor(risk / max_loss_for_trade )
                if num_of_lots >=max_num_lots:
                    num_of_lots = 10
            entry_price = (max(local_high1,current_high1)) + (tick_val * 2)
            exit_price = current_low1 - (tick_val * 2)
            print("\033[32m<------ LONG ENTRY ------>\033[0m")  # ANSI escape codes for this color coding to work
            print("       ENTRY PRICE  = ", entry_price)
            print("   num_of_positions = ", number_of_positions)
            print("        num_of_lots = ", round(num_of_lots))
            print(" max_loss_for_trade = ", round(max_loss_for_trade))
            print("---------------------------------------------------")
            bull = True
            flag = True
            continue

        # Bullish Exit
        if current_low1 < exit_price and bull and flag:
            number_of_positions -= 1
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
            max_loss = min(max_loss,pnl)

            # Check if integer part of P&L is positive or negative and set color accordingly
            if integer_pnl >= 0:
                pnl_color = "\033[32m"  # Green color
            else:
                pnl_color = "\033[31m"  # Red color

            # Add to total positive or negative P&L based on the result
            if pnl >= 0:
                positive_pnl += pnl
            else:
                negative_pnl += pnl
            
            print("\033[32m<------ LONG EXIT ------> \033[0m")  # ANSI escape codes for this color coding to work
            print("         EXIT PRICE = ", exit_price)
            print("   num_of_positions = ", number_of_positions)
            print("        num_of_lots = ", round(-1 * num_of_lots))
            print("      num_of_trades = ", num_of_trades)
            print("         max_profit = ", round(max_profit,2))
            print("           max_loss = ", round(max_loss,2))
            print("       P&L_Of_trade = ", pnl_color, round(integer_pnl,2),"\033[0m")
            print("-------------------------------------------------------------------")
            continue
                    
        # bearish candle-------------------------------------------------------------------------
        max_loss_for_trade = (min(local_low1,current_low1) - current_high1 + ( tick_val * 4)) * contract_size
        if (current_low1 < local_low1) and ((local_low1 < local_low2) or (local_low1 < local_low3) or (local_low1 < current_low3)) and ((local_high1 < local_high2) and (local_high1 < local_high3) and (local_high1 < current_high3)) and local_high1 != 0 and local_low1 != 0  and local_high2 != 0 and local_low2 != 0  and not bull and not flag:
            if max_loss_for_trade > risk:
                num_of_lots = 5
                continue  
            else:
                max_loss_for_trade <= risk
                num_of_lots = math.floor(risk / max_loss_for_trade )
                number_of_positions += 1
                if num_of_lots >=max_num_lots:
                    num_of_lots = 10
            entry_price = min(local_low1,current_low1) - (tick_val * 2)
            exit_price = current_high1 + (tick_val * 2)
            print("\033[31m<------ SHORT ENTRY ------>\033[0m")  # ANSI escape codes for this color coding to work
            print("        ENTRY PRICE = ", entry_price)
            print("   num_of_positions = ", number_of_positions)
            print("        num_of_lots = ", round(num_of_lots))
            print(" max_loss_for_trade = ", round(max_loss_for_trade))
            print("----------------------------------------------------")
            bear = True
            flag = True
            continue

        # bearish exit        
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
            max_profit = max(max_profit,pnl)
            max_loss   = min(max_loss,pnl)

            # Check if integer part of P&L is positive or negative and set color accordingly
            if integer_pnl >= 0:
                pnl_color = "\033[32m"  # Green color
            else:
                pnl_color = "\033[31m"  # Red color

            # Add to total positive or negative P&L based on the result
            if pnl >= 0:
                positive_pnl += pnl
            else:
                negative_pnl += pnl
            print("\033[31m<------ SHORT EXIT ------> \033[0m")  # ANSI escape codes for this color coding to work
            print("         EXIT PRICE = ", exit_price)
            print("   num_of_positions = ", number_of_positions)
            print("        num_of_lots = ", round(-1 * num_of_lots))
            print("      num_of_trades = ", num_of_trades)
            print("         max_profit = ", round(max_profit,2))  
            print("           max_loss = ", round( max_loss,2))
            print("       P&L_of_trade = ", pnl_color, round(integer_pnl,2),"\033[0m")
            print("-----------------------------------------------------------------------")
            continue
    except Exception as e:
        print("Error:", e)

    finally:
        print("-----------------------------------End of iteration-------------------------------------")
        current_hours_count=current_hours_count+1
        previous_date = data1.loc[index1,time_column_name].split()[0]
        date_flag = False
        print("current_hours_count: ",current_hours_count)

max_loss_color = "\033[31m" if max_loss < 0 else "\033[32m"
max_profit_color = "\033[31m" if max_profit < 0 else "\033[32m"
positive_pnl_color = "\033[31m" if positive_pnl < 0 else "\033[32m"
negative_pnl_color = "\033[31m" if negative_pnl < 0 else "\033[32m"
total_long_pnl_color = "\033[31m" if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color = "\033[31m" if total_short_pnl < 0 else "\033[32m"
TOTAL_P_L_colour = "\033[31m" if TOTAL_P_L < 0 else "\033[32m"

print("        max_profit = ", max_profit_color,round(max_profit,2),"\033[0m")
print("          max_loss = ", max_loss_color, round(max_loss,2),"\033[0m")
print("      positive_pnl = ", positive_pnl_color,round(positive_pnl,2),"\033[0m")
print("      negative_pnl = ", negative_pnl_color, round(negative_pnl,2),"\033[0m")
print("   total_long_pnl  = ", total_long_pnl_color,round(total_long_pnl,2),"\033[0m")
print("  total_short_pnl  = ", total_short_pnl_color, round(total_short_pnl,2),"\033[0m")
print("         TOTAL_P_L = ", TOTAL_P_L_colour, round(TOTAL_P_L,2),"\033[0m")
print("     num of trades = ", num_of_trades)
