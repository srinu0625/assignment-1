import pandas as pd
import matplotlib.pyplot as plt
import time

## ==== File paths ====
file1 = r"C:\Users\lenovo\Downloads\ucc 15min.csv"
file2 = r"C:\Users\lenovo\Downloads\lcc 15min.csv"

# ==== Contract sizes for each product ====
contract_size_ucc = 1  # Crude Oil Futures (ucc)
contract_size_lcc = 1  # Brent Crude Oil Futures (lcc)

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
df1 = df1[['Close']].rename(columns={'Close': 'ucc'})
df2 = df2[['Close']].rename(columns={'Close': 'lcc'})

# Merge datasets directly without resampling
df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')

# Calculate spread and z-score
df['spread'] = df['ucc'] - df['lcc']
df['mean'] = df['spread'].rolling(60).mean()
df['std'] = df['spread'].rolling(60).std()
df['zscore'] = (df['spread'] - df['mean']) / df['std']

# ==== Backtest Parameters ====
entry_thresh = 2.5
exit_thresh = 0
stop_thresh = 4
position = 0
entry_ucc = entry_lcc = 0
total_pnl = 0
pnl_list = []

df['position'] = 0
df['trade_pnl'] = 0
df['cum_pnl'] = 0

# ==== Backtest Loop ====
for i in range(60, len(df)):
    z = df['zscore'].iloc[i]
    ucc = df['ucc'].iloc[i]
    lcc = df['lcc'].iloc[i]
    t = df.index[i]

    if position == 0:
        if z > entry_thresh:
            position = -1  # Short ucc, Long lcc
            entry_ucc = ucc
            entry_lcc = lcc
            print(f"\033[91m{t} | SHORT ENTRY | Z = {z:.2f} | ucc = {ucc:.2f}, lcc = {lcc:.2f}\033[0m")
            time.sleep(0.5)
        elif z < -entry_thresh:
            position = 1  # Long ucc, Short lcc
            entry_ucc = ucc
            entry_lcc = lcc
            print(f"\033[92m{t} | LONG ENTRY  | Z = {z:.2f} | ucc = {ucc:.2f}, lcc = {lcc:.2f}\033[0m")
            time.sleep(0.5)

    elif position == 1:
        if z >= exit_thresh or z <= -stop_thresh:
            pnl_ucc = (ucc - entry_ucc) * contract_size_ucc
            pnl_lcc = -(lcc - entry_lcc) * contract_size_lcc
            pnl = pnl_ucc + pnl_lcc
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            pnl_color = "\033[92m" if pnl > 0 else "\033[91m"
            print(f"{t} | LONG EXIT   | Z = {z:.2f}")
            print(f"PnL: {pnl_color}{pnl:.2f}\033[0m")

            print(f"Entry UCC: {entry_ucc:.2f} → Exit UCC: {ucc:.2f}")
            print(f"Entry LCC: {entry_lcc:.2f} → Exit LCC: {lcc:.2f}")
            print("=============================================================")

            time.sleep(0.5)
            position = 0

    elif position == -1:
        if z <= exit_thresh or z >= stop_thresh:
            pnl_ucc = -(ucc - entry_ucc) * contract_size_ucc
            pnl_lcc = (lcc - entry_lcc) * contract_size_lcc
            pnl = pnl_ucc + pnl_lcc
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | SHORT EXIT  | Z = {z:.2f} ")
            print(f"PnL : {pnl_color}{pnl:.2f}\033[0m ")

            print(f"Entry ucc: {entry_ucc:.2f}, Exit ucc: {ucc:.2f}")
            print(f"Entry lcc: {entry_lcc:.2f}, Exit lcc: {lcc:.2f}")
            print("=============================================================")
            time.sleep(0.5)
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

# Z-score plot
plt.subplot(2, 1, 1)
plt.plot(df['zscore'], label='Z-Score')
plt.axhline(entry_thresh, color='red', linestyle='--', label='Entry Threshold')
plt.axhline(-entry_thresh, color='green', linestyle='--')
plt.axhline(stop_thresh, color='darkred', linestyle=':')
plt.axhline(-stop_thresh, color='darkgreen', linestyle=':')
plt.axhline(0, color='black', linestyle='-')
plt.title('Z-Score')
plt.legend()

# Cumulative PnL plot
plt.subplot(2, 1, 2)
plt.plot(pd.Series(pnl_list).cumsum(), label='Cumulative PnL', color='blue')
plt.title('Cumulative PnL ucc and lcc')
plt.legend()

plt.tight_layout()
plt.show()
