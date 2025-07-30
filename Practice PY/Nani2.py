import pandas as pd

Buy_Quantity = 0
Buy_value = 0
Sell_value = 0
Sell_Quantity = 0

file_path = r"D:\\Pra.xlsx"

# Read the Excel file into a pandas DataFrame
df = pd.read_excel(file_path)

# Reverse the DataFrame
df = df.iloc[::-1]

# List of columns to delete
columns_to_delete = ['OrderID', 'User', 'TradeID']

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
print(symbols)

# Open the new Excel file in append mode
with pd.ExcelWriter(new_file_path, mode='a', engine='openpyxl') as writer:
    for symbol in symbols:
        sheet_name = str(symbol)
        symbol_data = data[data['Symbol'] == symbol]

        # Check if the sheet already exists in the Excel file
        if sheet_name in writer.book.sheetnames:
            # Append the data to the existing sheet
            with pd.ExcelWriter(new_file_path, engine='openpyxl', mode='a') as writer_append:
                writer_append.book = writer.book
                writer_append.sheets = {ws.title: ws for ws in writer.book.worksheets}
                symbol_data.to_excel(writer_append, index=False, sheet_name=sheet_name, startrow=-1, header=False)
        else:
            # Create a new sheet and add the data
            symbol_data.to_excel(writer, index=False, sheet_name=sheet_name)

print("Data has been written to the Excel file.")

with pd.ExcelWriter(new_file_path, mode='a', engine='openpyxl') as writer:
    # Iterate over each symbol
    for symbol in symbols:
       if 'P&L' not in data.columns:
        data['P&L'] = None

    for index, row in data.iterrows():
        if row['B/S'] == 'Buy':
            Buy_Quantity += row['Qty']
            Buy_value += row['Qty'] * row['Price']
        elif row['B/S'] == 'Sell':
            Sell_Quantity += row['Qty']
            Sell_value += row['Qty'] * row['Price']

        if Buy_Quantity == Sell_Quantity:
            current_position = (Sell_value - Buy_value) * 0.5
            data.at[index, 'P&L'] = current_position
            Buy_Quantity = 0
            Buy_value = 0
            Sell_value = 0
            Sell_Quantity = 0
        
        # Write the processed DataFrame to the corresponding sheet
        sheet_name = str(symbol)
        df_symbol.to_excel(writer, index=False, sheet_name=sheet_name)

print("Data has been written to the Excel file.")
