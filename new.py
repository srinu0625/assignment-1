import pandas as pd


class BullishTradingStrategy:
    def __init__(self, data):
        self.df = data
        self.trades_df = pd.DataFrame(
            columns=['Entry Date', 'Open', 'High', 'Low', 'Close', 'Stop Loss', 'Take Profit', 'P&L', 'Lots'])
        self.total_positive_pnl = 0
        self.total_positive_trades = 0
        self.total_negative_pnl = 0
        self.total_negative_trades = 0

    def is_bullish_entry(self, row):
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

    def execute_trades(self):
        for index, row in self.df.iterrows():
            if self.is_bullish_entry(row):
                self.enter_trade(index, row)

        self.save_trades()
        self.print_summary()

    def enter_trade(self, index, row):
        entry_price = row['Last']
        stop_loss = row['Low']
        take_profit = entry_price + (row['High'] - row['Low'])

        pnl = 0

        self.trades_df = self.trades_df._append({
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

        print("Bullish entry at", row['Date (GMT)'])
        print(" Open:", row['Open'], " High:", row['High'])
        print(" Low:", row['Low'], " Close:", row['Last'])
        print(" Stop Loss:", stop_loss)
        print(" Take Profit:", take_profit)
        print(" P&L:", pnl)
        print('-------------------------------------------------')

        self.monitor_trade(index, entry_price, stop_loss, take_profit)

    def monitor_trade(self, index, entry_price, stop_loss, take_profit):
        for i in range(index + 1, len(self.df)):
            current_price = self.df.at[i, 'Last']
            if current_price >= take_profit:
                pnl = (current_price - entry_price) * 1 * 50
                self.total_positive_pnl += pnl
                self.total_positive_trades += 1
                self.trades_df.loc[index, 'Take Profit'] = current_price
                self.trades_df.loc[index, 'P&L'] = pnl
                print("Take profit hit at", self.df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('-------------------------------------------------')
                break
            elif current_price <= stop_loss:
                pnl = (stop_loss - entry_price) * 1 * 50
                self.total_negative_pnl += pnl
                self.total_negative_trades += 1
                self.trades_df.loc[index, 'Stop Loss'] = stop_loss
                self.trades_df.loc[index, 'P&L'] = pnl
                print("Stop loss hit at", self.df.at[i, 'Date (GMT)'])
                print("Close price:", current_price)
                print("P&L:", pnl)
                print('-------------------------------------------------')
                break

    def save_trades(self):
        self.trades_df.to_csv(r'C:\Users\manoh\Desktop\SRINU\bullish_trades.csv', index=False)

    def print_summary(self):
        print("   Total Positive P&L:", self.total_positive_pnl)
        print("Total Positive Trades:", self.total_positive_trades)
        print("   Total Negative P&L:", self.total_negative_pnl)
        print("Total Negative Trades:", self.total_negative_trades)


# Load the dataset
file_path = r"C:\Users\manoh\Desktop\SRINU\snp 5 min 2000 candles.csv"
df = pd.read_csv(file_path)

# Initialize and execute the strategy
strategy = BullishTradingStrategy(df)
strategy.execute_trades()
