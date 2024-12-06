import pandas as pd
import logging
import math

# Configure logging to both console and 'screenlog.txt'
logger = logging.getLogger('screenlog')
logger.setLevel(logging.INFO)  # Set the log level

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Terminal output handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# File output handler (writing to 'screenlog.txt')
file_handler = logging.FileHandler('screenlog.txt')  # Changed from 'screen.log' to 'screenlog.txt'
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# File paths
file_path1 = r"D:\data\bt 240.csv"
file_path2 = r"D:\data\bt d.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
except Exception as e:
    logger.error(f"Error loading data: {e}")
    exit()

# Initialize variables
contract_size = 0.1
tick_val = 5
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows
temp_high1 = temp_low1 = temp_high2 = temp_low2 = 0

# Local highs and lows
local_high1 = local_low1 = local_high2 = local_low2 = 0

# Previous local highs and lows
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = 0

# Trading parameters
total_positive_trades = total_negative_trades = 0
current_high1 = current_low1 = current_high2 = current_low2 = 0
previous_high1 = previous_low1 = previous_high2 = previous_low2 = 0
bull = bear = flag = False
number_of_positions = num_of_trades = 0
entry_price = exit_price = 0
max_loss = max_profit = loss_for_trade = 0
TOTAL_P_L = total_long_pnl = total_short_pnl = positive_pnl = negative_pnl = 0
num_of_lots = 0
max_num_lots = 20
risk = 720

# Iterate over each row of the daily DataFrame (data1)
for index1, row1 in data1.iterrows():
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        current_date1 = row1[time_column_name].split()[0]

        # Iterate over each row of the hourly DataFrame (data2)
        for index2, row2 in data2.iterrows():
            if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
                current_date2 = row2[time_column_name].split()[0]

                if current_date2 == current_date1:
                    try:
                        # Extract data from the row
                        current_time1 = row1[time_column_name]
                        high1 = float(row1[high_column_name])
                        low1 = float(row1[low_column_name])

                        # Update high and low tracking
                        previous_high1, previous_low1 = current_high1, current_low1
                        current_high1, current_low1 = high1, low1

                        # Update temp highs and lows
                        if current_high1 > previous_high1:
                            temp_high1 = current_high1
                        if current_low1 < previous_low1:
                            temp_low1 = current_low1

                        # Update local highs and lows
                        if current_high1 > previous_high1:
                            prev_local_low1 = local_low1
                            local_low1 = temp_low1
                        if current_low1 < previous_low1:
                            prev_local_high1 = local_high1
                            local_high1 = temp_high1

                        # Bullish entry logic
                        if local_high1 > 0:
                            if (current_high1 > local_high1) and (local_low1 >= local_low2) and not bear and not flag:
                                loss_for_trade = abs(local_high1 - current_low1 + (tick_val * 4)) * contract_size
                                num_of_lots = 1 if loss_for_trade > risk else min(math.floor(risk / loss_for_trade), max_num_lots)
                                entry_price = local_high1 + (tick_val * 2)
                                exit_price = current_low1 - (tick_val * 2)
                                
                                logger.info("<------ LONG ENTRY ------>")
                                logger.info(f"ENTRY PRICE = {entry_price}, num_of_lots = {round(num_of_lots)}, loss_for_trade = {round(loss_for_trade)}")
                                
                                bull = True
                                flag = True
                                continue

                        # Update exit price for bullish trade
                        if bull and current_low1 > exit_price:
                            exit_price = current_low1 

                        # Bullish exit logic
                        if current_low1 < exit_price and bull and flag:
                            num_of_trades += 1
                            bull = flag = False

                            pnl = (exit_price - entry_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_long_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            if pnl >= 0:
                                positive_pnl += pnl
                                total_positive_trades += 1
                            else:
                                negative_pnl += pnl
                                total_negative_trades += 1

                            logger.info("<------ LONG EXIT ------>")
                            logger.info(f"EXIT PRICE = {exit_price}, num_of_lots = {round(num_of_lots)}, P&L = {round(pnl, 2)}")
                            continue

                        # Bearish entry logic
                        if local_low1 > 0:
                            if (current_low1 < local_low1) and (local_high1 <= local_high2) and not bull and not flag:
                                loss_for_trade = abs(local_low1 - current_high1 + (tick_val * 4)) * contract_size
                                num_of_lots = 1 if loss_for_trade > risk else min(math.floor(risk / loss_for_trade), max_num_lots)
                                entry_price = local_low1 - (tick_val * 2)
                                exit_price = current_high1 + (tick_val * 2)

                                logger.info("<------ SHORT ENTRY ------>")
                                logger.info(f"ENTRY PRICE = {entry_price}, num_of_lots = {round(num_of_lots)}, loss_for_trade = {round(loss_for_trade)}")

                                bear = True
                                flag = True
                                continue

                        # Update exit price for bearish trade
                        if bear and current_high1 < exit_price:
                            exit_price = current_high1

                        # Bearish exit logic
                        if current_high1 > exit_price and bear and flag:
                            num_of_trades += 1
                            bear = flag = False

                            pnl = (entry_price - exit_price) * num_of_lots * contract_size
                            TOTAL_P_L += pnl
                            total_short_pnl += pnl
                            max_profit = max(max_profit, pnl)
                            max_loss = min(max_loss, pnl)
                            if pnl >= 0:
                                positive_pnl += pnl
                                total_positive_trades += 1
                            else:
                                negative_pnl += pnl
                                total_negative_trades += 1

                            logger.info("<------ SHORT EXIT ------>")
                            logger.info(f"EXIT PRICE = {exit_price}, num_of_lots = {round(num_of_lots)}, P&L = {round(pnl, 2)}")
                            continue

                    except Exception as e:
                        logger.error(f"Error during iteration: {e}")
                    finally:
                        logger.inf
                        o("End of iteration")

# Summary logging
logger.info("-------- Backtesting Summary --------")
logger.info(f"Total P&L: {round(TOTAL_P_L, 2)}, Number of trades: {num_of_trades}")
logger.info(f"Total Positive Trades: {total_positive_trades}, Total Negative Trades: {total_negative_trades}")
logger.info(f"Max Profit: {round(max_profit, 2)}, Max Loss: {round(max_loss, 2)}")
