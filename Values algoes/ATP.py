import pandas as pd
import datetime

# Initialize tm_struct as the current datetime
tm_struct = datetime.datetime.now()


file_path = r"D:\surya sir.csv"

# Load the data
try:
    data = pd.read_csv(file_path)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Assuming the column names
Date_Time_ = 'DateTime'
Price_name = 'Price'
Volume_name = 'Volume'
ExchTime_price = 'ExchTime'

# Initialize variables
avg_trade_price =0
current_minute = None
total_volume = 0
num_of_lines = 0
Date_Time=0
newPrice=0
curr_high = float('-inf')  
curr_low = float('inf')  
tm_struct = 0  
timeSlot = 0  
flagg = False  
curr_open = 0  
curr_close = 0  
timeSlot = 15  # Assuming time slot is 15 minutes



# Iterate over each row of the DataFrame
for index, row in data.iterrows():
    try:
        # Extracting values
        Price = row[Price_name]
        Volume = row[Volume_name]
        ExchTime = row[ExchTime_price]
        Date_Time = row[Date_Time_]

        # Split ExchTime into hours, minutes, and seconds
        hour, minute, second = map(int, ExchTime.split('.'))

        # Convert time to seconds
        total_seconds = hour * 18600 + minute * 310 + second
        

        # Check if it's a new minute
        if minute != current_minute:
            # Calculate average trade price for the previous minute
            if current_minute is not None:
                if total_volume != 0:
                    avg_trade_price = (total_trade_value / total_volume)
                    avg_trade_price_rounded = round(avg_trade_price, 2)
                    print(f"Avg_trade_price : {current_minute}: {avg_trade_price_rounded}")
                    print('----------------------------')
                else:
                    print(f"No trades occurred in minute {current_minute}")

            if avg_trade_price > curr_high:
               curr_high = avg_trade_price
               print("curr_high :",curr_high)
            if avg_trade_price < curr_low:
               curr_low = avg_trade_price
               print("curr_Low :",curr_low)

            tm_struct = datetime.datetime.now()
            

            if tm_struct.minute % timeSlot == 0 and flagg:
               curr_close = avg_trade_price
               print("curr_close :", curr_close)

            # Reset variables for the new minute
            current_minute = minute
            total_trade_value = 0
            total_volume = 0
        
        # Accumulate trade value and volume
        total_trade_value += Price * Volume
        total_volume += Volume
        num_of_lines +=1
        print('        Time:', ExchTime)
        print('       Price:', Price)           
        print('      Volume:', Volume)
        print('    ExchTime:', ExchTime)
        print('num_of_lines:', num_of_lines)
        print('----------------------------------------------------------------')

    except Exception as e:
        print("Error:", e)

