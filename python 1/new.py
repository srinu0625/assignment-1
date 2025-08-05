import pandas as pd
import math

file_path = r"D:\Data\ES Jun25_60min.csv" 

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
low_column_name  = 'Low'
time_column_name = 'Date(GMT)'

# temp column names
temp_high = 0
temp_low  = 0

# local high and local low 
local_high = temp_high
local_low  = temp_low

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
exit_price = 0
contract_size = 50
# defining tick size
tick_val = 1

# maxloss maxprofit
max_loss   = 0  
max_profit = 0 
max_loss_for_trade=0

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

# additional tracking for performance metrics
total_positive_trades = 0
total_negative_trades = 0
max_drawdown = 0
max_runup = 0
peak_pnl = 0
trough_pnl = 0

# Iterate over each row of the DataFrame
for index, row in data.iterrows():
    # adding a check point  to not process the balck or nan values in excel
    if pd.notna(row[time_column_name]) and pd.notna(row[high_column_name]) and pd.notna(row[low_column_name]):
        try:
            # Extracting current and previous values for high and low
            current_time = row[time_column_name]
            current_high = float(row[high_column_name])
            previous_high = float(data.at[index - 1, high_column_name])
            current_low = float(row[low_column_name])
            previous_low = float(data.at[index - 1, low_column_name])

            # case 1-----------------------------------------------------------------------------------
            if (current_high > previous_high):
                temp_high = current_high

            if (current_low < previous_low):
                temp_low = current_low
            # case 2-----------------------------------------------------------------------------------
            if (current_high > previous_high):
                local_low = temp_low

            if (current_low < previous_low):
                local_high = temp_high

            

            # Printing data
            print("Time:", current_time)
            print("Current High :", current_high, "Previous High :", previous_high, "local_high :", local_high, " temp_high :", temp_high)
            print("Current Low :", current_low, "Previous Low :", previous_low, "local_low :", local_low, " temp_low :", temp_low)

            # bullish candle---------------------------------------------------------------------------
            max_loss_for_trade = (local_high - local_low + (tick_val * 4)) * contract_size
            if current_high > local_high and local_high != 0 and local_low != 0 and not bear and not flag:
                num_of_lots = 1
                entry_price = local_high + (tick_val * 2)
                print("\033[32m<------ LONG ENTRY ------> (CH > LH)\033[0m")  # ANSI escape codes for this color coding to work
                print("       ENTRY PRICE  = ", entry_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ", round(num_of_lots))
                print(" max_loss_for_trade = ", round(max_loss_for_trade))
                bull = True
                flag = True
                continue
            # Bullish Exit
            if current_low < local_low and bull and flag:
                exit_price = current_low - (tick_val * 2)
                number_of_positions -= 1
                num_of_trades += 1
                print("\033[32m<------ LONG EXIT ------> (CL < LL)\033[0m")  # ANSI escape codes for this color coding to work
                print("         EXIT PRICE = ", exit_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ", round(-1 * num_of_lots))
                print("      num_of_trades = ", num_of_trades)
                bull = False
                flag = False

                # Calculate P&L
                pnl = (exit_price - entry_price) * num_of_lots * contract_size
                TOTAL_P_L += pnl
                total_long_pnl += pnl
                integer_pnl = float(pnl)  # Extract the integer part of the P&L

                # declaring maxloss and maxprofit
                max_profit = max(max_profit, pnl)
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
                continue

            # bearish candle-------------------------------------------------------------------------
            max_loss_for_trade = (local_high - local_low + ( tick_val * 4)) * contract_size
            if current_low < local_low and local_high != 0 and local_low != 0 and not bull and not flag:
                num_of_lots = 1
                entry_price = local_low - (tick_val * 2)
                print("\033[31m<------ SHORT ENTRY ------> (CL < LL)\033[0m")  # ANSI escape codes for this color coding to work
                print("        ENTRY PRICE = ", entry_price)
                print("   num_of_positions = ", number_of_positions)
                print("        num_of_lots = ", round(num_of_lots))
                print(" max_loss_for_trade = ", round(max_loss_for_trade))
                bear = True
                flag = True
                continue
            # bearish exit
            if current_high > local_high and bear and flag:
                exit_price = current_high + (tick_val * 2)
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

                print("        max_profit = ", round(max_profit,2))  
                print("          max_loss = ", round( max_loss,2))
                print("      P&L_of_trade = ", pnl_color, round(integer_pnl,2),"\033[0m")
                continue

        except Exception as e:
            print("Error:", e)

        finally:
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
