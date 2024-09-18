import pandas as pd
import math
import time
from datetime import datetime

file_path1 = r"C:\Users\lenovo\Music\es 240.csv"
file_path2 = r"C:\Users\lenovo\Music\es day.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Set contract size and tick value based on the symbol in the file path
def set_contract_tick_values(file_path):
    if "es" in file_path:
        return 5, 0.25
    elif "nq" in file_path:
        return 2, 0.25
    elif "ym" in file_path:
        return 0.5, 1
    elif "cl" in file_path:
        return 100, 0.01
    elif "bt" in file_path:
        return 0.1, 5
    elif "gc" in file_path:
        return 10, 0.1
    else:
        return None, None

contract_size, tick_val = set_contract_tick_values(file_path1)

# Check if valid contract size and tick value were set
if contract_size is None or tick_val is None:
    print("Unknown symbol in file path. Exiting.")
    exit()

## Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Trading time restrictions (example: stop trading between 14:00 and 16:00)
restricted_times = [("14:00")]

# Days when trading is restricted (e.g., weekends, holidays, or specific dates)
restricted_days = ["Thursday"]  # Example: stop trading on weekends

# Add specific dates if required
restricted_dates = ['2024-09-12']  # Example: stop trading on Christmas and New Year's

# Function to check if the current time falls within restricted hours
def is_time_restricted(current_time):
    current_time_obj = datetime.strptime(current_time.split()[1], "%H:%M")
    for start_time, end_time in restricted_times:
        start_time_obj = datetime.strptime(start_time, "%H:%M")
        end_time_obj = datetime.strptime(end_time, "%H:%M")
        if start_time_obj <= current_time_obj <= end_time_obj:
            return True
    return False

# Function to check if the current day is restricted
def is_day_restricted(current_date):
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    day_name = date_obj.strftime("%A")  # Get the day name (e.g., Monday, Tuesday)
    
    # Check if the day of the week is restricted
    if day_name in restricted_days:
        return True
    
    # Check if the specific date is restricted
    if current_date in restricted_dates:
        return True
    
    return False

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2 = 0

# prev local high and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0

# for positive and negative trades
total_positive_trades = total_negative_trades = 0
current_high1 = current_low1 = current_high2 = current_low2 = 0
previous_high2 = previous_low2 = 0

# Trading flags
bull = bear = flag = False

# Trading parameters
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    # Check if the row has valid data
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        # Extract the current date from the daily data
        current_date1 = row1[time_column_name].split()[0]
        current_time1 = row1[time_column_name]

        # Check for restricted days and skip trading if on restricted day
        if is_day_restricted(current_date1):
            print("Skipping trades due to restricted day: ", current_date1)
            continue  # Skip trading on restricted days

        # Check for restricted times and skip trading if in restricted period
        if is_time_restricted(current_time1):
            print("Skipping trades due to restricted time: ", current_time1)
            continue  # Skip trading during restricted time

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
                        high1 = float(row1[high_column_name])
                        low1 = float(row1[low_column_name])
                        if (high1 > current_high1) or (low1 < current_low1):
                            previous_high1 = current_high1
                            previous_low1 = current_low1
                            current_high1 = high1
                            current_low1 = low1

                        # Update temp highs/lows and local highs/lows
                        if current_high1 > previous_high1:
                            temp_high1 = current_high1
                            local_low1 = temp_low1

                        if current_low1 < previous_low1:
                            temp_low1 = current_low1
                            local_high1 = temp_high1

                        # Print data for data1
                        print("----240 MIN :----", current_time1)
                        print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1)
                        print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1)
                        print("   ")
                        
                        # Extracting current and previous values for high and low from data2
                        current_time2 = data2.at[index2 - 1, time_column_name]
                        high2 = float(row2[high_column_name])
                        low2 = float(row2[low_column_name])
                        if (high2 > current_high2) or (low2 < current_low2):
                            previous_high2 = current_high2
                            previous_low2 = current_low2
                            current_high2 = high2
                            current_low2 = low2

                        # Print data for data2
                        print("---- DAILY :----", current_time2)
                        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2)
                        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2)
                        print("   ")

                        # Perform trade checks and logic here (bullish, bearish, etc.)

                    except Exception as e:
                        print("Error:", e)
                    finally:
                        print("-----------------------------------End of iteration-------------------------------------")

# Final summary
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
print("       total_long_pnl = ", total_long_pnl_color, round(total_long_pnl, 2), "\033[0m")
print("      total_short_pnl = ", total_short_pnl_color, round(total_short_pnl, 2), "\033[0m")
print("               TOTAL_P_L = ", TOTAL_P_L_colour, round(TOTAL_P_L, 2), "\033[0m")
