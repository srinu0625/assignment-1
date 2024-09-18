import pandas as pd
import os
from datetime import datetime, timedelta

# Initialize variables
Buy_value = 0
Sell_value = 0
Buy_Quantity = 0
Sell_Quantity = 0
current_date = datetime.now()
previous_day = current_date - timedelta(days=1)

# File paths
input_file_path = r"C:\Users\lenovo\Downloads\A8 bearish 18-09-24.xlsx"
output_file_path = r"D:\PNL output\PNL- A8 BEARISH 18-09-24 bear.xlsx"

# Ensure the output directory exists
output_directory = os.path.dirname(output_file_path)
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Read the Excel file into a pandas DataFrame
df = pd.read_excel(input_file_path)

# Sort the DataFrame by 'OrderID' in Ascending order
df.sort_values(by='OrderID', ascending=True, inplace=True)

# List of columns to delete (excluding 'OrderID')
columns_to_delete = ['OrderID']
# Drop the specified columns
df.drop(columns=columns_to_delete, inplace=True)

# Write the modified DataFrame to a new Excel file
new_file_path = r"D:\PNL output\TRADE BOOK-A8 BEARISH 18-09-24.xlsx"
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

# Dictionary to store summed P&L values and trade counts for each product
summed_pl = {}
positive_trades = {}
negative_trades = {}

# Iterate over each symbol
for symbol in symbols:
    # Reset variables for each symbol
    Buy_value = 0
    Sell_value = 0
    Buy_Quantity = 0
    Sell_Quantity = 0
    current_position = 0
    summed_pl[symbol] = 0
    positive_trades[symbol] = 0
    negative_trades[symbol] = 0

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
                    current_position = (Sell_value - Buy_value) * 5
                elif symbol[0:2] == "ES":
                    current_position = (Sell_value - Buy_value) * 50
                elif symbol[0:2] == "NQ":
                    current_position = (Sell_value - Buy_value) * 20
                elif symbol[0:3] == "MES":
                    current_position = (Sell_value - Buy_value) * 5
                elif symbol[0:3] == "MNQ":
                    current_position = (Sell_value - Buy_value) * 2
                elif symbol[0:3] == "MYM":
                    current_position = (Sell_value - Buy_value) * 0.5
                elif symbol[0:3] == "MCL":
                    current_position = (Sell_value - Buy_value) * 100
                elif symbol[0:3] == "MBT":
                    current_position = (Sell_value - Buy_value) * 0.1
                elif symbol[0:3] == "MGC":
                    current_position = (Sell_value - Buy_value) * 10

                # New products of Surya Sir
                elif symbol[0:3] == "SIZ":
                    current_position = (Sell_value - Buy_value) * 5000
                elif symbol[0:3] == "HGZ":
                    current_position = (Sell_value - Buy_value) * 25000
                elif symbol[0:3] == "ZSX":
                    current_position = (Sell_value - Buy_value) * 50
                elif symbol[0:3] == "ZMZ":
                    current_position = (Sell_value - Buy_value) * 100
                elif symbol[0:3] == "ZCZ":
                    current_position = (Sell_value - Buy_value) * 50
                elif symbol[0:3] == "ZLZ":
                    current_position = (Sell_value - Buy_value) * 600
                elif symbol[0:3] == "ZWZ":
                    current_position = (Sell_value - Buy_value) * 50
                elif symbol[0:3] == "6EU":
                    current_position = (Sell_value - Buy_value) * 1250
                elif symbol[0:3] == "6CU":
                    current_position = (Sell_value - Buy_value) * 1000
                elif symbol[0:3] == "6BU":
                    current_position = (Sell_value - Buy_value) * 625

                # Update the P&L column
                data.at[index, 'P&L'] = current_position
                summed_pl[symbol] += current_position

                # Count positive and negative trades
                if current_position > 0:
                    positive_trades[symbol] += 1
                elif current_position < 0:
                    negative_trades[symbol] += 1

                # Reset variables for the next trade
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
        symbol_data.to_excel(writer, index=False, sheet_name=sheet_name,
                             startrow=writer.sheets[sheet_name].max_row if sheet_name in writer.sheets else 0)

    # Add the new sheet for summed P&L values and trade counts
    summed_pl_df = pd.DataFrame({
        'Symbol': list(summed_pl.keys()),
        'Total P&L': list(summed_pl.values()),
        'Positive': [positive_trades[symbol] for symbol in symbols],
        'Negative': [negative_trades[symbol] for symbol in symbols]
    })

    # Insert the current date in the first row
    summed_pl_df.loc[-1] = [f"Date: {previous_day.strftime('%Y-%m-%d')}", '', '', '']
    summed_pl_df.index = summed_pl_df.index + 1
    summed_pl_df = summed_pl_df.sort_index()

    summed_pl_df.to_excel(writer, index=False, sheet_name='Summed_P&L')

print("Data has been written to the Excel file and saved to the specified location.")
