import pandas as pd
import math

file_path1 = r"C:\Users\lenovo\Music\es 1 240.csv"
file_path2 = r"C:\Users\lenovo\Music\es 1 day.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Ensure the date columns are in datetime format
data1['Date (GMT)'] = pd.to_datetime(data1['Date (GMT)'])
data2['Date (GMT)'] = pd.to_datetime(data2['Date (GMT)'])

# Merge the datasets on the date column
merged_data = pd.merge(data1, data2, on='Date (GMT)', suffixes=('_240', '_daily'))

# Column names
high_240 = 'High_240'
low_240 = 'Low_240'
high_daily = 'High_daily'
low_daily = 'Low_daily'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2 = 0

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
risk = 900

# Iterate over each row of the merged DataFrame
for index, row in merged_data.iterrows():
    try:
        # Extract current and previous values for high and low
        current_time = row[time_column_name]
        
        current_high1 = row[high_240]
        current_low1 = row[low_240]
        current_high2 = row[high_daily]
        current_low2 = row[low_daily]
        
        previous_high1 = merged_data.at[index - 1, high_240] if index > 0 else 0
        previous_low1 = merged_data.at[index - 1, low_240] if index > 0 else 0
        previous_high2 = merged_data.at[index - 1, high_daily] if index > 1 else 0
        previous_low2 = merged_data.at[index - 1, low_daily] if index > 1 else 0

        # Update temp highs and lows for data1 (240 min)
        if current_high1 > previous_high1:
            temp_high1 = current_high1
            local_low1 = temp_low1

        if current_low1 < previous_low1:
            temp_low1 = current_low1
            local_high1 = temp_high1

        # Update temp highs and lows for data2 (daily)
        if current_high2 > previous_high2:
            temp_high2 = current_high2
            local_low2 = temp_low2

        if current_low2 < previous_low2:
            temp_low2 = current_low2
            local_high2 = temp_high2

        # Updating exit price
        if bull and current_low1 > exit_price:
            exit_price = current_low1

        if bear and current_high1 < exit_price:
            exit_price = current_high1

        # Bullish trade logic
        if (current_high1 > local_high1) and (local_low1 >= local_low2) and not bear and not flag:
            entry_price = local_high1 + (tick_val * 2)
            loss_for_trade = (local_high1 - current_low1 + (tick_val * 4)) * contract_size
            num_of_lots = 1 if loss_for_trade > risk else min(math.floor(risk / loss_for_trade), max_num_lots)

            print("\033[32m<------ LONG ENTRY ------>(CH1 > LH1) AND (LL1 >= LL2)\033[0m")
            print(f"       ENTRY PRICE  = {entry_price}")
            print(f"        num_of_lots = {round(num_of_lots)}")
            print(f"     loss_for_trade = {round(loss_for_trade)}")
            print("--------------------------------------------------")
            bull = True
            flag = True
            continue

        # Bullish exit logic
        if current_low1 < exit_price and bull and flag:
            exit_price = current_low1 - (tick_val * 2)
            number_of_positions -= 1
            num_of_trades += 1
            bull = False
            flag = False

            pnl = (exit_price - entry_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_long_pnl += pnl

            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)

            pnl_color = "\033[32m" if pnl >= 0 else "\033[31m"
            positive_pnl += pnl if pnl >= 0 else 0
            negative_pnl += pnl if pnl < 0 else 0

            print("\033[32m<------ LONG EXIT ------>(LL1 >\033[0m")
            print(f"         EXIT PRICE = {exit_price}")
            print(f"        num_of_lots = {round(num_of_lots)}")
            print(f"      num_of_trades = {num_of_trades}")
            print(f"         max_profit = {round(max_profit, 2)}")
            print(f"           max_loss = {round(max_loss, 2)}")
            print(f"       P&L_Of_trade = {pnl_color}{round(pnl, 2)}\033[0m")
            print("---------------------------------------------------------")
            continue

        # Bearish trade logic
        if (current_low1 < local_low1) and (local_high1 <= local_high2) and not bull and not flag:
            entry_price = local_low1 - (tick_val * 2)
            loss_for_trade = (local_low1 - current_high1 + (tick_val * 4)) * contract_size
            num_of_lots = 1 if loss_for_trade > risk else min(math.floor(risk / loss_for_trade), max_num_lots)

            print("\033[31m<------ SHORT ENTRY ------> (CH1 < LL1) AND (LH1 <= LH2)\033[0m")
            print(f"        ENTRY PRICE = {entry_price}")
            print(f"        num_of_lots = {round(num_of_lots)}")
            print(f"     loss_for_trade = {round(loss_for_trade)}")
            print("------------------------------------------------")
            bear = True
            flag = True
            continue

        # Bearish exit logic
        if current_high1 > exit_price and bear and flag:
            exit_price = current_high1 + (tick_val * 2)
            number_of_positions -= 1
            num_of_trades += 1

            bear = False
            flag = False

            pnl = (entry_price - exit_price) * num_of_lots * contract_size
            TOTAL_P_L += pnl
            total_short_pnl += pnl

            max_profit = max(max_profit, pnl)
            max_loss = min(max_loss, pnl)

            pnl_color = "\033[32m" if pnl >= 0 else "\033[31m"
            positive_pnl += pnl if pnl >= 0 else 0
            negative_pnl += pnl if pnl < 0 else 0

            print("\033[31m<------ SHORT EXIT ------>(LH1 >)\033[0m")
            print(f"         EXIT PRICE = {exit_price}")
            print(f"        num_of_lots = {round(num_of_lots)}")
            print(f"      num_of_trades = {num_of_trades}")
            print(f"         max_profit = {round(max_profit, 2)}")
            print(f"           max_loss = {round(max_loss, 2)}")
            print(f"       P&L_of_trade = {pnl_color}{round(pnl, 2)}\033[0m")
            print("------------------------------------------------")
            continue

    except Exception as e:
        print("Error:", e)

    finally:
        print("------------------------------------------End of iteration---------------------------------------------")

# Final summary
max_loss_color = "\033[31m" if max_loss < 0 else "\033[32m"
max_profit_color = "\033[31m" if max_profit < 0 else "\033[32m"
positive_pnl_color = "\033[31m" if positive_pnl < 0 else "\033[32m"
negative_pnl_color = "\033[31m" if negative_pnl < 0 else "\033[32m"
total_long_pnl_color = "\033[31m" if total_long_pnl < 0 else "\033[32m"
total_short_pnl_color = "\033[31m" if total_short_pnl < 0 else "\033[32m"
TOTAL_P_L_colour = "\033[31m" if TOTAL_P_L < 0 else "\033[32m"

print(f"        max_profit = {max_profit_color}{round(max_profit, 2)}\033[0m")
print(f"          max_loss = {max_loss_color}{round(max_loss, 2)}\033[0m")
print(f"      positive_pnl = {positive_pnl_color}{round(positive_pnl, 2)}\033[0m")
print(f"      negative_pnl = {negative_pnl_color}{round(negative_pnl, 2)}\033[0m")
print(f"   total_long_pnl  = {total_long_pnl_color}{round(total_long_pnl, 2)}\033[0m")
print(f"  total_short_pnl  = {total_short_pnl_color}{round(total_short_pnl, 2)}\033[0m")
print(f"         TOTAL_P_L = {TOTAL_P_L_colour}{round(TOTAL_P_L, 2)}\033[0m")
print(f"     num of trades = {num_of_trades}")
