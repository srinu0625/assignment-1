import pandas as pd
import time
import turtle

file_path = r"C:\Users\srinu\Downloads\recent download\ES_BIG_DATA_10MIN (1).csv"

# Load the data
try:
    data = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()


# Print column names to verify
print("Column names:", data.columns)

# Assuming the column names for high and low are 'High' and 'Low'
high_column_name = float('High')
low_column_name = float('Low')
time_column_name = float('time')
# temp column names
temp_high=0
temp_low=0
# local column names
local_high=temp_high
local_low=temp_low

bull = False
bear = False

# Iterate over each row of the DataFrame
for index, row in data.iterrows():
    try:
        # Extracting current and previous values for high and low
        current_time = row[time_column_name]
        current_high = row[high_column_name]
        previous_high = data.at[index - 1, high_column_name] if index > 0 else None
        current_low = row[low_column_name]
        previous_low = data.at[index - 1, low_column_name] if index > 0 else None
        # bullish candle---------------------------------------------------------------------------
        if current_high > previous_high and not bear:
            temp_high = current_high
            print("snp500 long entry")
            bull = True

        if current_low < previous_low and bull:
            print("snp500 long exit")
            bull = False

        # bearish candle-------------------------------------------------------------------------
        if current_low < previous_low and not bull:
            print("snp500 short entry")
            bear = True

        if current_high > previous_high and bear:
            print("snp500 short exit")
            bear = False

        # case 1------------------------------------------------------------------------------------
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
        print("Current High :", current_high, "Previous High :", previous_high,"local_high :",local_high
              ,"temp_high :", temp_high)
        print("Current Low :", current_low,   "Previous Low :", previous_low,   "local_low :",local_low
              , "temp_low :", temp_low)

    except Exception as e:
        print("Error:", e)

    finally:
        print("End of iteration-------------------------------")
