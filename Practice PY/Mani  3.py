import pandas as pd

file_path = r"D:\es daily.csv"

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
tick_value = 0.25
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
    if pd.notna(row[time_column_name]) and pd.notna(row[high_column_name]) and pd.notna(row[low_column_name]):
        try:
            # Extracting current and previous values for high and low
            current_time = row[time_column_name]
            current_high = float(row[high_column_name])
            previous_high = float(data.at[index - 1, high_column_name] )
            current_low = float(row[low_column_name])
            previous_low = float(data.at[index - 1, low_column_name] )

             # case 1-----------------------------------------------------------------------------------
            if current_high > previous_high:
                temp_high = current_high

            if current_low < previous_low:
                temp_low = current_low
            # case 2------------------------------------------------------------------------------------
            if current_high > previous_high:
                local_low = temp_low

            if current_low < previous_low:
                local_high = temp_high

            # Printing data
            print("Time:", current_time)
            print("Current High :", current_high, "Previous High :", previous_high, "local_high :", local_high
                  , " temp_high :", temp_high)
            print("Current Low :", current_low, "Previous Low :", previous_low, "local_low :", local_low
                  , " temp_low :", temp_low)
            #time.sleep(2)

            # bullish candle---------------------------------------------------------------------------
            max_loss_for_trade = (local_high - local_low) * contract_size
            if current_high > local_high and local_high!=0 and local_low!=0  and not bear and not flag:
                number_of_positions +=1
                entry_price = local_high +(tick_value * 2)
                print("\033[32m--SNP500 LONG ENTRY-- (CH > LH)\033[0m") # ANSI escape codes for this color coding to work
                print("current_high = ",current_high),print("local_high = ",local_high)
                print("number_of_positions = ",number_of_positions)
                print("   long_entry_price = ",entry_price)
                print("max_loss_for_trade =",max_loss_for_trade)
                bull = True
                flag = True
                continue

            if current_low < local_low and bull and flag:
                number_of_positions -=1
                num_of_trades+=1
                exit_price = local_low -(tick_value * 2)
                print("\033[32m--SNP500 LONG EXIT-- (CL < LL)\033[0m") # ANSI escape codes for this color coding to work
                print("current_low :",current_low),print("local_low :",local_low)
                print("number_of_positions = ",number_of_positions),print("num_of_trades = ",num_of_trades)
                print( "    long_exit_pric =",exit_price)
                
                print(exit_price-entry_price)
                bull = False
                flag = False

            # Calculate P&L
                pnl = (exit_price - entry_price) * 1 *contract_size
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

                print("P&L for this trade = ",pnl_color, integer_pnl,"\033[0m")
                print("        max_profit = ",max_profit)
                print("          max_loss = ",max_loss)
                continue

            # bearish candle-------------------------------------------------------------------------
            if current_low < local_low and local_high!=0 and local_low!=0  and not bull and not flag:
                number_of_positions +=1
                entry_price=local_low-(tick_value * 2)
                print("\033[31m--SNP500 SHORT ENTRY-- (CL < LL)\033[0m") # ANSI escape codes for this color coding to work
                print("current_low :",current_low),print("local_low :",local_low)
                print("number_of_positions =",number_of_positions)
                print("  short_entry_price = ",entry_price)
                print("max_loss_for_trade =",max_loss_for_trade)
                bear = True
                flag = True
                continue

            if current_high > local_high and bear and flag:
                number_of_positions -=1
                num_of_trades +=1  
                exit_price=local_high + (tick_value * 2) 
                print("\033[31m--SNP500 SHORT EXIT-- (CH > LH)\033[0m") #  ANSI escape codes for this color coding to work 
                print("current_high :",current_high), print("local_high :",local_high),
                print("number_of_positions = ",number_of_positions),print("num_of_trades = ",num_of_trades)
                print("   short_exit_price = ",exit_price)
                print(entry_price-exit_price)
                bear = False
                flag = False

            # Calculate P&L
                pnl = (entry_price - exit_price) * 1 *contract_size
                TOTAL_P_L +=pnl
                total_short_pnl+=pnl
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
                print("P&L for this trade = ",pnl_color, integer_pnl,"\033[0m")
                print("        max_profit = ",max_profit)
                print("          max_loss = ",max_loss)
                continue

        except Exception as e:
            print("Error:", e)

        finally:
            print("-----------------------------End of iteration---------------------------------")

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
