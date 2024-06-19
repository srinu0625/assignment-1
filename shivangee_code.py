import pandas as pd
import math 

file_path = r"D:\nq daily.csv"

# Load the data
try:
    data = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Print column names to verify
print("Column names:", data.columns)
print("Column names:", data.columns[1])
print("1st row", data.iloc[0].tolist())

# Assuming the column names for high and low are 'High' and 'Low'
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'
# temp column names
temp_high = 0
temp_low = 0
# local column names
local_high = temp_high
local_low = temp_low
# flag 
bull = False
bear = False
flag = False
# num of positions 
number_of_positions=0

# num of trades
num_of_trades=0

# P&L calculation
entry_price = 0
exit_price = 0
contract_size = 50
tick_val = 0.25
risk = 5000
max_num_lots = 5
# maxloss maxprofit
max_loss=0 
max_profit=0 
# total p&l
TOTAL_P_L=0

# total long and short pnl
total_long_pnl=0
total_short_pnl=0
positive_pnl=0
negative_pnl=0

# Iterate over each row of the DataFrame
for index, row in data.iterrows():
    # adding a check point  to not process the balck or nan values in excel
    if pd.notna(row[time_column_name]) and pd.notna(row[high_column_name]) and pd.notna(row[low_column_name]):
        try:
            # Extracting current and previous values for high and low
            current_time = row[time_column_name]
            current_high = float(row[high_column_name])
            previous_high = float(data.at[index - 1, high_column_name] )
            current_low = float(row[low_column_name])
            previous_low = float(data.at[index - 1, low_column_name] )

            # case 1------------------------------------------------------------------------------------
            if current_high > previous_high:
                temp_high = current_high

            if current_low < previous_low:
                temp_low = current_low

             # case 3-----------------------------------------------------------------------------------
            if(bull and previous_low > exit_price):
               exit_price = previous_low
           
            if(bear and previous_high < exit_price):
               exit_price = previous_high

            

            # Printing data
            print("Time:", current_time)
            print("Current High :", current_high, "Previous High :", previous_high)
            print("Current Low :", current_low, "Previous Low :", previous_low)
        

            # bullish candle---------------------------------------------------------------------------
            max_loss_for_trade = (previous_high - previous_low + (tick_val * 4)) * contract_size
            if current_high > previous_high and previous_high != 0 and previous_low != 0 and not bear and not flag:
                if max_loss_for_trade > risk:
                   num_of_lots = 1
                   continue 
                else:
                    max_loss_for_trade <= risk
                    num_of_lots = math.floor(risk / max_loss_for_trade )
                    number_of_positions += 1
                    if num_of_lots >=max_num_lots:
                       num_of_lots = 1
                entry_price = previous_high + (tick_val * 2)
                print("\033[32m<------ LONG ENTRY ------> (CH > LH)\033[0m")  # ANSI escape codes for this color coding to work
                print("       ENTRY PRICE  = ", entry_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ",round(num_of_lots))
                print(" max_loss_for_trade = ",round(max_loss_for_trade))
                bull = True
                flag = True
                continue
            # bullish exit---
            if current_low < exit_price and bull and flag:
                exit_price = exit_price - (tick_val * 2)
                number_of_positions -=1
                num_of_trades+=1
                print("\033[32m<------ LONG EXIT ------> (CL < LL)\033[0m")  # ANSI escape codes for this color coding to work
                print("         EXIT PRICE = ", exit_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ", round(-1 * num_of_lots))
                print("      num_of_trades = ", num_of_trades)
                bull = False
                flag = False

                # Calculate P&L
                pnl = (exit_price - entry_price) * num_of_lots * contract_size
                TOTAL_P_L+=pnl
                total_long_pnl+=pnl
                integer_pnl = float(pnl)  # Extract the integer part of the P&L

                # declaring maxloss and maxprofit
                max_profit=max(max_profit,pnl)
                max_loss=min(max_loss,pnl)

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

                print("        max_profit = ", round(max_profit,2))
                print("          max_loss = ", round(max_loss,2))
                print("      P&L_Of_trade = ", pnl_color, round(integer_pnl,2),"\033[0m")
                
                # updating the prevoius low
                previous_low = current_low

            # bearish candle-------------------------------------------------------------------------
            max_loss_for_trade = (previous_high - previous_low + ( tick_val * 4)) * contract_size
            if current_low < previous_low and previous_high != 0 and previous_low != 0 and not bull and not flag:
                if max_loss_for_trade > risk:
                   num_of_lots = 1
                   continue  # Skip this trade
                else:
                    ( max_loss_for_trade <=risk)
                    num_of_lots = math.floor( risk / max_loss_for_trade)
                    number_of_positions += 1
                    if num_of_lots >=max_num_lots:
                       num_of_lots = max_num_lots
                    entry_price = previous_low - (tick_val * 2)
                    print("\033[31m--SNP500 SHORT ENTRY-- (CL < PL)\033[0m",file_path) # ANSI escape codes for this color coding to work
                    print("current_low :",current_low),print("previous_low :",previous_low)
                    print("number_of_positions = ",number_of_positions)
                    print("  short_entry_price = ",entry_price)
                    bear = True
                    flag = True
                    continue
            # bearish exit------
            if current_high > exit_price and bear and flag:
                exit_price = exit_price + (tick_val * 2)
                number_of_positions -= 1
                num_of_trades += 1
                print("\033[31m<------ SHORT EXIT ------> (CH > LH)\033[0m")  # ANSI escape codes for this color coding to work
                print("         EXIT PRICE = ", exit_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ", round(-1 * num_of_lots))
                print("      num_of_trades = ", num_of_trades)
                bear = False
                flag = False

            # Calculate P&L
                pnl = (entry_price - exit_price) * 1 *contract_size
                TOTAL_P_L +=pnl
                total_short_pnl+=pnl
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

                print("P&L for this trade = ", pnl_color, integer_pnl, "\033[0m")
                print("        max_profit = ", max_profit)
                print("          max_loss =", max_loss)

                # Update previous high
                prevoius_high = current_high
            
        except Exception as e:
            print("Error processing row:", e)
        finally:
            print("---------------------------End of iteration--------------------------")
# colour coding the end  values
max_loss_color="\033[31m"if max_loss < 0 else "\033[32m"
max_profit_color="\033[31m"if max_profit < 0 else "\033[32m"
positive_pnl_color="\033[31m"if positive_pnl < 0 else "\033[32m"
negative_pnl_color="\033[31m"if negative_pnl < 0 else "\033[32m"
total_long_pnl_color="\033[31m"if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color="\033[31m"if total_short_pnl < 0 else "\033[32m"
TOTAL_P_L_colour="\033[31m"if TOTAL_P_L < 0 else "\033[32m"

print("        max_profit = ",max_profit_color, max_profit, "\033[0m")
print("          max_loss = ",max_loss_color, max_loss, "\033[0m")
print("      positive_pnl = ",positive_pnl_color,positive_pnl,"\033[0m")
print("      negative_pnl = ",negative_pnl_color,negative_pnl,"\033[0m")
print("   total_long_pnl  = ",total_long_pnl_color,total_long_pnl,"\033[0m")
print("  total_short_pnl  = ",total_short_pnl_color,total_short_pnl,"\033[0m")
print("         TOTAL_P_L = ",TOTAL_P_L_colour,TOTAL_P_L,"\033[0m")
print("     num of trades = ",num_of_trades)
                 
