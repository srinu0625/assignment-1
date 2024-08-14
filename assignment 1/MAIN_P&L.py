import pandas as pd
import os

# Initialize variables
Buy_value = 0
Sell_value = 0
Buy_Quantity = 0
Sell_Quantity = 0

# File paths
input_file_path = r"C:\Users\lenovo\Downloads\A2 SIM 13-08-24 .xlsx"
output_file_path = r"D:\........   A2 sim  .........xlsx"

# Ensure the output directory exists
output_directory = os.path.dirname(output_file_path)
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Read the Excel file into a pandas DataFrame
df = pd.read_excel(input_file_path)

# Reverse the DataFrame if needed
df = df.iloc[::-1]

# List of columns to delete
columns_to_delete = ['OrderID']
# Drop the specified columns
df.drop(columns=columns_to_delete, inplace=True)

# Write the modified DataFrame to a new Excel file
new_file_path = r"D:\\Modified_Pra.xlsx"
df.to_excel(new_file_path, index=False)

try:
    data = pd.read_excel(new_file_path)
except Exception as e:
    print("Error loading data from Excel file:", e)
    exit()

# Get unique symbols in the data
symbols = data['Symbol'].unique()

# Check if the 'P&L' column already exists
if 'P&L' not in data.columns:
    data['P&L'] = None

# Iterate over each symbol
for symbol in symbols:
    # Reset variables for each symbol
    Buy_value = 0
    Sell_value = 0
    Buy_Quantity = 0
    Sell_Quantity = 0
    
    # Iterate over rows for the current symbol
    for index, row in data.iterrows():
        if row['Symbol'] == symbol:
            if row['B/S'] == 'Buy':
                Buy_Quantity += row['Qty']
                Buy_value += row['Qty'] * row['Price']
            elif row['B/S'] == 'Sell':
                Sell_Quantity += row['Qty']
                Sell_value += row['Qty'] * row['Price']

            if Buy_Quantity == Sell_Quantity:
                if symbol[0:2] == "YM":
                    current_position = (Sell_value - Buy_value)*5
                elif symbol [0:2] == "ES" :
                    current_position = (Sell_value - Buy_value)*50
                elif symbol [0:2] == "NQ" :
                    current_position = (Sell_value - Buy_value)*20
                elif symbol [0:3] == "MES" :
                    current_position = (Sell_value - Buy_value)*5
                elif symbol [0:3] == "MNQ" :
                    current_position = (Sell_value - Buy_value)*2
                elif symbol [0:3] == "MYM" :
                    current_position = (Sell_value - Buy_value)*0.5
                elif symbol [0:3] == "MCL" :
                    current_position = (Sell_value - Buy_value)*100
                elif symbol [0:3] == "MBT" :
                    current_position = (Sell_value - Buy_value)*0.1
                elif symbol [0:3] == "MGC" :
                    current_position = (Sell_value - Buy_value)*10

                # new products of surya sir
                elif symbol [0:3] == "SIU" :
                    current_position = (Sell_value - Buy_value)*5000
                elif symbol [0:3] == "HGU" :
                    current_position = (Sell_value - Buy_value)*25000
                elif symbol [0:3] == "ZSX" :
                    current_position = (Sell_value - Buy_value)*50
                elif symbol [0:3] == "ZMZ" :
                    current_position = (Sell_value - Buy_value)*100
                elif symbol [0:3] == "ZCZ" :
                    current_position = (Sell_value - Buy_value)*50
                elif symbol [0:3] == "ZLZ" :
                    current_position = (Sell_value - Buy_value)*600
                elif symbol [0:3] == "ZWZ" :
                    current_position = (Sell_value - Buy_value)*50
                
                data.at[index, 'P&L'] = current_position
                Buy_Quantity = 0
                Buy_value = 0
                Sell_value = 0
                Sell_Quantity = 0

# Write the modified DataFrame to the new Excel file
data.to_excel(output_file_path, index=False)

# Re-open the Excel file in append mode to add each symbol's data to a separate sheet
with pd.ExcelWriter(output_file_path, mode='a', engine='openpyxl') as writer:
    for symbol in symbols:
        sheet_name = str(symbol)
        symbol_data = data[data['Symbol'] == symbol]

        # Append the data to the existing sheet or create a new sheet
        symbol_data.to_excel(writer, index=False, sheet_name=sheet_name, startrow=writer.sheets[sheet_name].max_row if sheet_name in writer.sheets else 0)
       
print("Data has been written to the Excel file and saved to----- D:disk.")
