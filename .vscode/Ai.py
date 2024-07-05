import pandas as pd

# Load the dataset
file_path = r"D:\data\New folder\5 MIN.csv"
df = pd.read_csv(file_path)

# Print the column names to verify them
print(df.columns)

# Initialize an empty DataFrame to store trades
trades_df = pd.DataFrame(
    columns=['Entry Date', 'Open', 'High', 'Low', 'Close', 'Stop Loss', 'Take Profit', 'P&L', 'Lots'])

# Define the conditions for bearish entries
def is_bearish_entry(df, index):
    if index < 4:
        return False
    
    high1 = df.at[index, 'High']
    high2 = df.at[index-3, 'High']
    high3 = df.at[index-2, 'High']
    high4 = df.at[index-1, 'High']
    close1 = df.at[index, 'Last']
    open1 = df.at[index, 'Open']
    open4 = df.at[index-1, 'Open']
    low1 = df.at[index, 'Low']
    low2 = df.at[index-3, 'Low']
    
    condition = close1 > open1

    # Condition 1
    condition1 = high1 >= high4 >= high3 >= high2
    
    # Condition 2
    condition2 = close1 >= open4
    
    # Condition 3
    # condition3 = low1 <= low2
    
    return condition and condition1 and condition2 

# Initialize variables for trade tracking
total_positive_pnl = 0
total_positive_trades = 0
total_negative_pnl = 0
total_negative_trades = 0
tick_value = 12.5
pnl = 0
# Iterate through the dataframe to execute trades
for index, row in df.iterrows():
    if is_bearish_entry(df, index):
        # Take entry at current close
        entry_price = row['Last']
        take_profit = entry_price + row['High'] - row['Low']
        stop_loss = row['Low'] - 2 * tick_value
        
        # Calculate P&L based on the assumption of taking one lot
        #pnl = (row['Last'] - entry_price) * 1 * 50 if index > 0 else 0

        # Add trade details to the DataFrame
        trades_df = trades_df._append({
            'Entry Date': row['Date (GMT)'],
            'Open': row['Open'],
            'High': row['High'],
            'Low': row['Low'],
            'Close': row['Last'],
            'Stop Loss': stop_loss,
            'Take Profit': take_profit,
            'P&L': pnl,
            'Lots': 1
        }, ignore_index=True)

        # Print trade details
        print("bearish entry at", row['Date (GMT)'])
        print(" Open:", row['Open'], " High:", row['High'])
        print(" Low:", row['Low'], " Close:", row['Last'])
        print(" Stop Loss:", stop_loss)
        print(" Take Profit:", take_profit)
        print(" P&L:", pnl)
        print('-------------------------------------------------')

        # Check for take profit or stop loss conditions and execute them if met
        for i in range(index + 1, len(df)):
            current_price = df.at[i, 'Last']
            if current_price >= take_profit:
                pnl = (take_profit - entry_price) * 1 * 50
                total_positive_pnl += pnl
                total_positive_trades += 1
                trades_df.loc[index, 'Take Profit'] = take_profit
                trades_df.loc[index, 'P&L'] = pnl
                print("Entry Price:", entry_price)
                print("Take profit hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('-------------------------------------------------')
                break
            elif current_price <= stop_loss:
                pnl = (entry_price - stop_loss) * 1 * 50
                total_negative_pnl += pnl
                total_negative_trades += 1
                trades_df.loc[index, 'Stop Loss'] = stop_loss
                trades_df.loc[index, 'P&L'] = pnl
                print("Stop loss hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('-------------------------------------------------')
                break

# Save trades to a file
trades_df.to_csv(r'D:\data\4Candles_5min.csv', index=False)

# Print total P&L and trade statistics
print("   Total Positive P&L:", total_positive_pnl)
print("Total Positive Trades:", total_positive_trades)
print("   Total Negative P&L:", total_negative_pnl)
print("Total Negative Trades:", total_negative_trades)
