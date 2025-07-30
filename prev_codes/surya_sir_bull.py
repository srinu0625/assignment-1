import pandas as pd

# Load the dataset
file_path = r"C:\Users\lenovo\Downloads\10 MIN .csv"
df = pd.read_csv(file_path)

# Print the column names to verify them
print(df.columns)

# Initialize an empty DataFrame to store trades
trades_df = pd.DataFrame(
    columns=['Entry Date', 'Open', 'High', 'Low', 'Close', 'Stop Loss', 'Take Profit 1', 'Take Profit 2', 'P&L 1',
             'P&L 2', 'Total P&L', 'Lots'])


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

        if (0.42<= open_low_ratio <= 0.62 and 0.42 <= close_open_ratio <= 0.62 and high_close_ratio <= 0.12):
            return True
    return False


# Initialize variables for trade tracking
total_positive_pnl = 0
total_positive_trades = 0
total_negative_pnl = 0
total_negative_trades = 0

# Iterate through the dataframe to execute trades
for index, row in df.iterrows():
    if is_bullish_entry(row):
        # Take long entry at current close with 2 lots
        entry_price = row['Last']
        stop_loss = row['Low']
        take_profit_1 = entry_price + 0.5 * (row['High'] - row['Low'])
        take_profit_2 = entry_price + (row['High'] - row['Low'])

        print("Entry Price:", entry_price)

        # Initialize P&L for both lots
        pnl_1 = 0
        pnl_2 = 0
        total_pnl = 0
        hit_tp_1 = False
        hit_tp_2 = False

        # Add trade details to the DataFrame
        trades_df = trades_df._append({
            'Entry Date': row['Date (GMT)'],
            'Open': row['Open'],
            'High': row['High'],
            'Low': row['Low'],
            'Close': row['Last'],
            'Stop Loss': stop_loss,
            'Take Profit 1': take_profit_1,
            'Take Profit 2': take_profit_2,
            'P&L 1': 0,
            'P&L 2': 0,
            'Total P&L': 0,
            'Lots': 2
        }, ignore_index=True)

        # Print trade details
        print("Bullish entry at", row['Date (GMT)'])
        print(" Open:", row['Open'], " High:", row['High'])
        print(" Low:", row['Low'], " Close:", row['Last'])
        print(" Stop Loss:", stop_loss)
        print(" Take Profit 1:", take_profit_1)
        print(" Take Profit 2:", take_profit_2)
        print('-------------------------------------------------')

        # Check for take profit or stop loss conditions and execute them if met
        for i in range(index + 1, len(df)):
            current_price = df.at[i, 'Last']
            if not hit_tp_1 and current_price >= take_profit_1:
                pnl_1 = (take_profit_1 - entry_price) * 1 * 50
                total_pnl += pnl_1
                total_positive_pnl += pnl_1
                total_positive_trades += 1
                trades_df.loc[index, 'Take Profit 1'] = take_profit_1
                trades_df.loc[index, 'P&L 1'] = pnl_1
                hit_tp_1 = True
                print("Take profit 1 hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L 1:", pnl_1)
                print('-------------------------------------------------')
            if not hit_tp_2 and current_price >= take_profit_2:
                pnl_2 = (take_profit_2 - entry_price) * 1 * 50
                total_pnl += pnl_2
                total_positive_pnl += pnl_2
                total_positive_trades += 1
                trades_df.loc[index, 'Take Profit 2'] = take_profit_2
                trades_df.loc[index, 'P&L 2'] = pnl_2
                hit_tp_2 = True
                print("Take profit 2 hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L 2:", pnl_2)
                print('-------------------------------------------------')

            # If both take profit targets are hit, break out of the loop
            if hit_tp_1 and hit_tp_2:
                break

            # If stop loss is hit before both TPs are hit, execute stop loss for remaining lots
            if current_price <= stop_loss:
                if not hit_tp_1:
                    pnl_1 = (stop_loss - entry_price) * 1 * 50
                    total_negative_pnl += pnl_1
                    total_negative_trades += 1
                    trades_df.loc[index, 'P&L 1'] = pnl_1
                if not hit_tp_2:
                    pnl_2 = (stop_loss - entry_price) * 1 * 50
                    total_negative_pnl += pnl_2
                    total_negative_trades += 1
                    trades_df.loc[index, 'P&L 2'] = pnl_2
                total_pnl += pnl_1 + pnl_2
                print("Stop loss hit at", df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L 1:", pnl_1)
                print("P&L 2:", pnl_2)
                print('-------------------------------------------------')
                break

        trades_df.loc[index, 'Total P&L'] = total_pnl

# Save trades to a file
#trades_df.to_csv(r'C:\Users\manoh\Desktop\SRINU\Candles\2lots\240_min_bullish_trades.csv', index=False)

# Print total P&L and trade statistics
print("   Total Positive P&L:", total_positive_pnl)
print("Total Positive Trades:", total_positive_trades)
print("   Total Negative P&L:", total_negative_pnl)
print("Total Negative Trades:", total_negative_trades)
