import pandas as pd

# Load the dataset
file_path = r"C:\Users\manoh\Desktop\SRINU\snp 10 min 2000 candles.csv"
df = pd.read_csv(file_path)

# Print the column names to verify them
print(df.columns)

# Initialize an empty DataFrame to store trades
trades_df = pd.DataFrame(
    columns=['Entry Date', 'Open', 'High', 'Low', 'Close', 'Stop Loss', 'Take Profit', 'P&L', 'Lots'])


# Define the conditions for bullish entries
def is_bullish_entry(row):
    open_price = row['Open']
    high_price = row['High']
    low_price = row['Low']
    close_price = row['Last']

    if close_price > open_price:
        open_low_ratio = (open_price - low_price) / (high_price - low_price)
        close_open_ratio = (close_price - open_price) / (high_price - low_price)
        high_close_ratio = (high_price - close_price) / (high_price - low_price)

        if (0.4 <= open_low_ratio <= 0.6 and 0.4 <= close_open_ratio <= 0.6 and high_close_ratio <= 0.12):
            return True
    return False


# Initialize variables for trade tracking
total_pl = 0

# Iterate through the dataframe to execute trades
for index, row in df.iterrows():
    if is_bullish_entry(row):
        # Take long entry at current close
        entry_price = row['Last']
        stop_loss = row['Low']
        take_profit = entry_price + (row['High'] - row['Low'])

        # Calculate P&L based on the assumption of taking one lot
        pnl = (row['Last'] - entry_price) * 1 * 50 if index > 0 else 0

        # Update total P&L
        total_pl += pnl

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
        print("Bullish entry at", row['Date (GMT)'])
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
                pnl = (current_price - entry_price) * 1 * 50
                total_pl += pnl
                trades_df.loc[index, 'Take Profit'] = current_price
                trades_df.loc[index, 'P&L'] = pnl
                print("Take profit hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('-------------------------------------------------')
                break
            elif current_price <= stop_loss:
                pnl = (stop_loss - entry_price) * 1 * 50
                total_pl += pnl
                trades_df.loc[index, 'Stop Loss'] = stop_loss
                trades_df.loc[index, 'P&L'] = pnl
                print("Stop loss hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('----------------------------                        ---------------------')
                break

# Save trades to a file
trades_df.to_csv(r'C:\Users\manoh\Desktop\SRINU\bullish_trades.csv', index=False)

# Print total P&L
print("Total P&L:", total_pl)
