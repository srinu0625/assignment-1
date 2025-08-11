import pandas as pd
import matplotlib.pyplot as plt
import time

# ==== File paths ====
file1 = r"C:\Users\lenovo\Documents\cl 15min.csv"
file2 = r"C:\Users\lenovo\Documents\brn 15min.csv"

# ==== Contract sizes for each product ====
contract_size_cl = 1000  # Crude Oil Futures (CL)
contract_size_brn = 1000  # Brent Crude Oil Futures (BRN)

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
df1 = df1[['Close']].rename(columns={'Close': 'cl'})
df2 = df2[['Close']].rename(columns={'Close': 'brn'})

# Merge datasets directly without resampling
df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')

# Calculate spread and z-score
df['spread'] = df['cl'] - df['brn']
df['mean'] = df['spread'].rolling(30).mean()
df['std'] = df['spread'].rolling(30).std()
df['zscore'] = (df['spread'] - df['mean']) / df['std']

# ==== Backtest Parameters ====
entry_thresh = 2.5
exit_thresh = 0
stop_thresh = 4
position = 0
entry_cl = entry_brn = 0
total_pnl = 0
pnl_list = []

df['position'] = 0
df['trade_pnl'] = 0
df['cum_pnl'] = 0

# ==== Backtest Loop ====
for i in range(30, len(df)):
    z = df['zscore'].iloc[i]
    cl = df['cl'].iloc[i]
    brn = df['brn'].iloc[i]
    t = df.index[i]

    if position == 0:
        if z > entry_thresh:
            position = -1  # Short cl, Long brn
            entry_cl = cl
            entry_brn = brn
            print(f"\033[91m{t} | SHORT ENTRY | Z = {z:.2f} | cl = {cl:.2f}, brn = {brn:.2f}\033[0m")
            # time.sleep(1)
        elif z < -entry_thresh:
            position = 1  # Long cl, Short brn
            entry_cl = cl
            entry_brn = brn
            print(f"\033[92m{t} | LONG ENTRY  | Z = {z:.2f} | cl = {cl:.2f}, brn = {brn:.2f}\033[0m")
            # time.sleep(1)

    elif position == 1:
        if z >= exit_thresh or z <= -stop_thresh:
            pnl_cl = (cl - entry_cl) * contract_size_cl
            pnl_brn = -(brn - entry_brn) * contract_size_brn
            pnl = pnl_cl + pnl_brn
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | LONG EXIT   | Z = {z:.2f} | "
                  f"PnL = {pnl_color}{pnl:.2f}\033[0m | "
                  f"Entry cl: {entry_cl:.2f}, Exit cl: {cl:.2f} | "
                  f"Entry brn: {entry_brn:.2f}, Exit brn: {brn:.2f}")
            print("=============================================================")
            # time.sleep(1)
            position = 0

    elif position == -1:
        if z <= exit_thresh or z >= stop_thresh:
            pnl_cl = -(cl - entry_cl) * contract_size_cl
            pnl_brn = (brn - entry_brn) * contract_size_brn
            pnl = pnl_cl + pnl_brn
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | SHORT EXIT  | Z = {z:.2f} | "
                  f"PnL = {pnl_color}{pnl:.2f}\033[0m | "
                  f"Entry cl: {entry_cl:.2f}, Exit cl: {cl:.2f} | "
                  f"Entry brn: {entry_brn:.2f}, Exit brn: {brn:.2f}")
            print("=============================================================")
            # time.sleep(1)
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
plt.title('Cumulative PnL CL and BRN')
plt.legend()

plt.tight_layout()
plt.show()
