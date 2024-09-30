import pandas as pd
import time

# File paths
file_paths = [
    r"D:\CANDLES 2\ES DAY.csv",
    r"D:\CANDLES 2\NQ DAY.csv",
    r"D:\CANDLES 2\YM DAY.csv",
    r"D:\CANDLES 2\CL DAY.csv",
    r"D:\CANDLES 2\BT DAY.csv",
    r"D:\CANDLES 2\GC DAY.csv"
]

# Load the data from all file paths
data_frames = []
for path in file_paths:
    try:
        df = pd.read_csv(path)
        data_frames.append(df)
    except Exception as e:
        print(f"Error loading data from {path}: {e}")
        exit()

# Column names (assuming all files have the same structure)
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temp variables for tracking highs and lows for each dataset
temp_high = [0] * 6
temp_low = [0] * 6
local_high = [0] * 6
local_low = [0] * 6
current_high = [0] * 6
current_low = [0] * 6
previous_high = [0] * 6
previous_low = [0] * 6
prev_local_high = [0] * 6
prev_local_low = [0] * 6

# Iterate over all dataframes simultaneously
for rows in zip(*[df.iterrows() for df in data_frames]):
    for i, (index, row) in enumerate(rows):
        # Check if the row has valid data
        if pd.notna(row[time_column_name]) and pd.notna(row[high_column_name]) and pd.notna(row[low_column_name]):
            try:
                # Extract current time and high/low values
                current_time = row[time_column_name]
                high = float(row[high_column_name])
                low = float(row[low_column_name])

                # Update current and previous high/low
                if high > current_high[i] or low < current_low[i]:
                    previous_high[i] = current_high[i]
                    previous_low[i] = current_low[i]
                    current_high[i] = high
                    current_low[i] = low

                # Case 1: Update temporary highs and lows
                if current_high[i] > previous_high[i]:
                    temp_high[i] = current_high[i]
                if current_low[i] < previous_low[i]:
                    temp_low[i] = current_low[i]

                # Case 2: Update local highs and lows
                if current_high[i] > previous_high[i]:
                    if temp_low[i] != local_low[i]:
                        prev_local_low[i] = local_low[i]
                    local_low[i] = temp_low[i]
                if current_low[i] < previous_high[i]:
                    if temp_high[i] != local_high[i]:
                        prev_local_high[i] = local_high[i]
                    local_high[i] = temp_high[i]

                # Print data for each file (data1, data2, etc.)
                print(f"----File {i + 1}:---- {current_time}")
                print(f"1,c,MGCZ4,{current_high[i]},{current_low[i]},{previous_high[i]},{previous_low[i]},{temp_high[i]},{temp_low[i]},{local_high[i]},{local_low[i]},{prev_local_high[i]},{prev_local_low[i]}")
                print("   ")

            except Exception as e:
                print(f"Error in file {i + 1}: {e}")

            finally:
                print(f"-----------------------------------End of iteration for file {i + 1}-------------------------------------")

    time.sleep(0)
