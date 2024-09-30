import pandas as pd
import time

# File paths
file_path1 = r"D:\CANDLES 2\ES 240.csv"
file_path2 = r"D:\CANDLES 2\NQ 240.csv"
file_path3 = r"D:\CANDLES 2\YM 240.csv"
file_path4 = r"D:\CANDLES 2\CL 240.csv"
file_path5 = r"D:\CANDLES 2\BT 240.csv"
file_path6 = r"D:\CANDLES 2\GC 240.csv"

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
    data3 = pd.read_csv(file_path3)
    data4 = pd.read_csv(file_path4)
    data5 = pd.read_csv(file_path5)
    data6 = pd.read_csv(file_path6)
except Exception as e:
    print("Error loading data:", e)
    exit()

## Column names
high_column_name = 'High'
low_column_name = 'Low'
time_column_name = 'Date (GMT)'

# Temporary variables for tracking highs and lows for all datasets
temp_high1 = temp_low1 = temp_high2 = temp_low2 = temp_high3 = temp_low3 = 0
temp_high4 = temp_low4 = temp_high5 = temp_low5 = temp_high6 = temp_low6 = 0

# Local highs and lows for all datasets
local_high1 = local_low1 = local_high2 = local_low2 = local_high3 = local_low3 = 0
local_high4 = local_low4 = local_high5 = local_low5 = local_high6 = local_low6 = 0

# Current highs and lows for all datasets
current_high1 = current_low1 = current_high2 = current_low2 = current_high3 = current_low3 = 0
current_high4 = current_low4 = current_high5 = current_low5 = current_high6 = current_low6 = 0

# Previous highs and lows for all datasets
previous_high1 = previous_low1 = previous_high2 = previous_low2 = previous_high3 = previous_low3 = 0
previous_high4 = previous_low4 = previous_high5 = previous_low5 = previous_high6 = previous_low6 = 0

# Previous local highs and lows for all datasets
prev_local_high1 = prev_local_low1 = prev_local_high2 = prev_local_low2 = prev_local_high3 = prev_local_low3 = 0
prev_local_high4 = prev_local_low4 = prev_local_high5 = prev_local_low5 = prev_local_high6 = prev_local_low6 = 0

# Iterate through the data for all datasets (data1 to data6)
for index1, row1 in data1.iterrows():
    # Process dataset 1
    if pd.notna(row1[time_column_name]) and pd.notna(row1[high_column_name]) and pd.notna(row1[low_column_name]):
        try:
            current_time1 = row1[time_column_name]
            high1 = float(row1[high_column_name])
            low1 = float(row1[low_column_name])
            
            if (high1 > current_high1) or (low1 < current_low1):
                previous_high1 = current_high1
                previous_low1 = current_low1
                current_high1 = high1
                current_low1 = low1
            
            if current_high1 > previous_high1:
                temp_high1 = current_high1
            if current_low1 < previous_low1:
                temp_low1 = current_low1
            
            if current_high1 > previous_high1:
                if temp_low1 != local_low1:
                    prev_local_low1 = local_low1
                local_low1 = temp_low1
            
            if current_low1 < previous_low1:
                if temp_high1 != local_high1:
                    prev_local_high1 = local_high1
                local_high1 = temp_high1

            print(f"----240 min: {current_time1} ----")
            print(f"1,c,MESZ4,{current_high1},{current_low1},{previous_high1},{previous_low1},{temp_high1},{temp_low1},{local_high1},{local_low1},{prev_local_high1},{prev_local_low1}")
            print("   ")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 1:", e)
            
# Dataset 2
for index2, row2 in data2.iterrows():
    if pd.notna(row2[time_column_name]) and pd.notna(row2[high_column_name]) and pd.notna(row2[low_column_name]):
        try:
            current_time2 = row2[time_column_name]
            high2 = float(row2[high_column_name])
            low2 = float(row2[low_column_name])
            
            if (high2 > current_high2) or (low2 < current_low2):
                previous_high2 = current_high2
                previous_low2 = current_low2
                current_high2 = high2
                current_low2 = low2
            
            if current_high2 > previous_high2:
                temp_high2 = current_high2
            if current_low2 < previous_low2:
                temp_low2 = current_low2
            
            if current_high2 > previous_high2:
                if temp_low2 != local_low2:
                    prev_local_low2 = local_low2
                local_low2 = temp_low2
            
            if current_low2 < previous_low2:
                if temp_high2 != local_high2:
                    prev_local_high2 = local_high2
                local_high2 = temp_high2

            print(f"----240 min: {current_time2} ----")
            print(f"1,c,MNQZ4,{current_high2},{current_low2},{previous_high2},{previous_low2},{temp_high2},{temp_low2},{local_high2},{local_low2},{prev_local_high2},{prev_local_low2}")
            print("   ")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 2", e)

# Dataset 3
for index3, row3 in data3.iterrows():
    if pd.notna(row3[time_column_name]) and pd.notna(row3[high_column_name]) and pd.notna(row3[low_column_name]):
        try:
            current_time3 = row3[time_column_name]
            high3 = float(row3[high_column_name])
            low3 = float(row3[low_column_name])
            
            if (high3 > current_high3) or (low3 < current_low3):
                previous_high3 = current_high3
                previous_low3 = current_low3
                current_high3 = high3
                current_low3 = low3
            
            if current_high3 > previous_high3:
                temp_high3 = current_high3
            if current_low3 < previous_low3:
                temp_low3 = current_low3
            
            if current_high3 > previous_high3:
                if temp_low3 != local_low3:
                    prev_local_low3 = local_low3
                local_low3 = temp_low3
            
            if current_low3 < previous_low3:
                if temp_high3 != local_high3:
                    prev_local_high3 = local_high3
                local_high3 = temp_high3

            print(f"----240 min: {current_time3} ----")
            print(f"1,c,MYMZ4,{current_high3},{current_low3},{previous_high3},{previous_low3},{temp_high3},{temp_low3},{local_high3},{local_low3},{prev_local_high3},{prev_local_low3}")
            print("   ")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 3:", e)
        
# Process data for dataset 4
for index4, row4 in data4.iterrows():
    if pd.notna(row4[time_column_name]) and pd.notna(row4[high_column_name]) and pd.notna(row4[low_column_name]):
        try:
            current_time4 = row4[time_column_name]
            high4 = float(row4[high_column_name])
            low4 = float(row4[low_column_name])

            if (high4 > current_high4) or (low4 < current_low4):
                previous_high4 = current_high4
                previous_low4 = current_low4
                current_high4 = high4
                current_low4 = low4

            if current_high4 > previous_high4:
                temp_high4 = current_high4
            if current_low4 < previous_low4:
                temp_low4 = current_low4

            if current_high4 > previous_high4:
                if temp_low4 != local_low4:
                    prev_local_low4 = local_low4
                local_low4 = temp_low4

            if current_low4 < previous_low4:
                if temp_high4 != local_high4:
                    prev_local_high4 = local_high4
                local_high4 = temp_high4

            print(f"----240 min: {current_time4} ----")
            print(f"1,c,MCLX4,{current_high4},{current_low4},{previous_high4},{previous_low4},{temp_high4},{temp_low4},{local_high4},{local_low4},{prev_local_high4},{prev_local_low4}")
            print("   ")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 4:", e)

# Process data for dataset 5
for index5, row5 in data5.iterrows():
    if pd.notna(row5[time_column_name]) and pd.notna(row5[high_column_name]) and pd.notna(row5[low_column_name]):
        try:
            current_time5 = row5[time_column_name]
            high5 = float(row5[high_column_name])
            low5 = float(row5[low_column_name])

            if (high5 > current_high5) or (low5 < current_low5):
                previous_high5 = current_high5
                previous_low5 = current_low5
                current_high5 = high5
                current_low5 = low5

            if current_high5 > previous_high5:
                temp_high5 = current_high5
            if current_low5 < previous_low5:
                temp_low5 = current_low5

            if current_high5 > previous_high5:
                if temp_low5 != local_low5:
                    prev_local_low5 = local_low5
                local_low5 = temp_low5

            if current_low5 < previous_low5:
                if temp_high5 != local_high5:
                    prev_local_high5 = local_high5
                local_high5 = temp_high5

            print(f"----240 min: {current_time5} ----")
            print(f"1,c,MBTV4,{current_high5},{current_low5},{previous_high5},{previous_low5},{temp_high5},{temp_low5},{local_high5},{local_low5},{prev_local_high5},{prev_local_low5}")
            print("   ")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 5:", e)

# Process data for dataset 6
for index6, row6 in data6.iterrows():
    if pd.notna(row6[time_column_name]) and pd.notna(row6[high_column_name]) and pd.notna(row6[low_column_name]):
        try:
            current_time6 = row6[time_column_name]
            high6 = float(row6[high_column_name])
            low6 = float(row6[low_column_name])

            if (high6 > current_high6) or (low6 < current_low6):
                previous_high6 = current_high6
                previous_low6 = current_low6
                current_high6 = high6
                current_low6 = low6

            if current_high6 > previous_high6:
                temp_high6 = current_high6
            if current_low6 < previous_low6:
                temp_low6 = current_low6

            if current_high6 > previous_high6:
                if temp_low6 != local_low6:
                    prev_local_low6 = local_low6
                local_low6 = temp_low6

            if current_low6 < previous_low6:
                if temp_high6 != local_high6:
                    prev_local_high6 = local_high6
                local_high6 = temp_high6

            print(f"----240 min: {current_time6} ----")
            print(f"1,c,MGCZ4,{current_high6},{current_low6},{previous_high6},{previous_low6},{temp_high6},{temp_low6},{local_high6},{local_low6},{prev_local_high6},{prev_local_low6}")
            print("   ")
            print("====================================================================================================================================")
            time.sleep(1)

        except Exception as e:
            print("Error in Dataset 5:", e)

       
            
       


        

        

       

       

       

        



                                                                                                                                                                            

        