import pandas as pd

Buy_value = 0
Sell_value = 0
Buy_Quantity = 0
Sell_Quantity = 0
file_path = r"C:\Users\srinu\Downloads\Trade_Book_Export-20240415_23.41.52.xlsx"

try:
    data = pd.read_excel(file_path, sheet_name='MYMM4')
except Exception as e:
    print("Error loading data from Sheet2:", e)
    exit()

# Check if the 'P&L' column already exists
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

# Overwrite the existing sheet 'MYMM4' in the Excel file
try:
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='MYMM4')
    print("P&L calculated and saved to the Excel file.")


except Exception as e:
    print("Error writing data to Excel file:", e)
