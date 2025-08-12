import pandas as pd
import matplotlib.pyplot as plt
import time

# ==== File paths ====
file1 = r"D:\Data\GC Jun25_15min.csv"
file2 = r"C:\Users\lenovo\Documents\si 15min.csv"

# ==== Contract sizes for each product ====
contract_size_es = 5  # E-mini S&P 500 Futures (si)
contract_size_nq = 5  # E-mini NASDAQ-100 Futures (cp)

# ==== Load and clean data ====
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# Parse datetime
df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1.set_index('Date(GMT)', inplace=True)
df2.set_index('Date(GMT)', inplace=True)

# Keep only Close price
df1 = df1[['Close']].rename(columns={'Close': 'si'})
df2 = df2[['Close']].rename(columns={'Close': 'cp'})

# Merge datasets
df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')


# Calculate spread and z-score
df['spread'] = df['si'] - df['cp']
df['mean'] = df['spread'].rolling(30)
df['std'] = df['spread'].rolling(30).std()
df['zscore'] = (df['spread'] - df['mean']) / df['std']

# ==== Backtest Parameters ====
entry_thresh = 2.5
exit_thresh = 0
stop_thresh = 4
position = 0  # 0 = no position, 1 = long si / short cp, -1 = short si / long cp
entry_si = entry_cp = 0
total_pnl = 0
pnl_list = []

# Track PnL for plotting
df['position'] = 0
df['trade_pnl'] = 0
df['cum_pnl'] = 0

# ==== Backtest Loop ====
for i in range(30, len(df)):
    z = df['zscore'].iloc[i]
    si = df['si'].iloc[i]
    cp = df['cp'].iloc[i]
    t = df.index[i]

    if position == 0:
        if z > entry_thresh:
            position = -1  # Short si, Long cp
            entry_si = si
            entry_cp = cp
            print(f"\033[91m{t} | SHORT ENTRY | Z = {z:.2f} | si = {si:.2f}, cp = {cp:.2f}\033[0m")
            # time.sleep(1)  # Simulate processing delay
        elif z < -entry_thresh:
            position = 1  # Long si, Short cp
            entry_si = si
            entry_cp = cp
            print(f"\033[92m{t} | LONG ENTRY  | Z = {z:.2f} | si = {si:.2f}, cp = {cp:.2f}\033[0m")
            # time.sleep(1)  # Simulate processing delay

    elif position == 1:  # Long si, Short cp
        if z >= exit_thresh or z <= -stop_thresh:
            pnl_si = (si - entry_si) * contract_size_es
            pnl_cp = -(cp - entry_cp) * contract_size_nq
            pnl = pnl_si + pnl_cp

            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | LONG EXIT   | Z = {z:.2f} | "
                  f"PnL = {pnl_color}{pnl:.2f}\033[0m | "
                  f"Entry si: {entry_si:.2f}, Exit si: {si:.2f} | "
                  f"Entry cp: {entry_cp:.2f}, Exit cp: {cp:.2f}")
            print("=============================================================")
            # time.sleep(1)  # Simulate processing delay
            position = 0

    elif position == -1:  # Short si, Long cp
        if z <= exit_thresh or z >= stop_thresh:
            pnl_si = -(si - entry_si) * contract_size_es
            pnl_cp = (cp - entry_cp) * contract_size_nq
            pnl = pnl_si + pnl_cp

            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | SHORT EXIT  | Z = {z:.2f} | "
                  f"PnL = {pnl_color}{pnl:.2f}\033[0m | "
                  f"Entry si: {entry_si:.2f}, Exit si: {si:.2f} | "
                  f"Entry cp: {entry_cp:.2f}, Exit cp: {cp:.2f}")
            print("=============================================================")
            # time.sleep(1)  # Simulate processing delay
            position = 0

    df.iloc[i, df.columns.get_loc('position')] = position

# ==== Summary Stats ====
total_trades = len(pnl_list)
wins = sum(1 for p in pnl_list if p > 0)
losses = total_trades - wins
win_rate = (wins / total_trades) * 100 if total_trades else 0
loss_rate = 100 - win_rate

print("\n==== SUMMARY ====")
print(f"Total Trades            : {total_trades}")
print(f"Total PnL               : {total_pnl:.2f}")
print(f"Winning Trades          : \033[92m{wins}\033[0m")
print(f"Losing Trades           : \033[91m{losses}\033[0m")
print(f"Win Rate                : \033[92m{win_rate:.2f}%\033[0m")
print(f"Failure Rate            : \033[91m{loss_rate:.2f}%\033[0m")
if pnl_list:
    print(f"Max Profit Per trade    : \033[92m{max(pnl_list):.2f}\033[0m")
    print(f"Max Loss Per trade      : \033[91m{min(pnl_list):.2f}\033[0m")

# ==== Plot ====
plt.figure(figsize=(14, 6))
 
# Z-score
plt.subplot(2, 1, 1)
plt.plot(df['zscore'], label='Z-Score')
plt.axhline(entry_thresh, color='red', linestyle='--', label='Entry Threshold')
plt.axhline(-entry_thresh, color='green', linestyle='--')
plt.axhline(stop_thresh, color='darkred', linestyle=':')
plt.axhline(-stop_thresh, color='darkgreen', linestyle=':')
plt.axhline(0, color='black', linestyle='-')
plt.title('Z-Score')
plt.legend()

# PnL - cumulative
plt.subplot(2, 1, 2)
plt.plot(pd.Series(pnl_list).cumsum(), label='Cumulative PnL', color='blue')
plt.title('Cumulative PnL si and cp')
plt.legend()

plt.tight_layout()
plt.show()
