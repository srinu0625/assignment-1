import pandas as pd
import matplotlib.pyplot as plt
import time

# Load data
file1 = r"C:\Users\lenovo\Downloads\NYMEX_CL1!, 15_5c0b5.csv"
file2 = r"C:\Users\lenovo\Downloads\ICEEUR_DLY_BRN1!, 15_08646.csv"

df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Clean column names
df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# Parse datetime
df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1.set_index('Date(GMT)', inplace=True)
df2.set_index('Date(GMT)', inplace=True)

# Keep only 'Close'
df1 = df1[['Close']].rename(columns={'Close': 'CL'})
df2 = df2[['Close']].rename(columns={'Close': 'BRN'})

# Merge and resample
df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')
df = df.resample('30T').last().dropna()

# Spread and Z-Score
df['spread'] = df['CL'] - df['BRN']
df['mean'] = df['spread'].rolling(30).mean()
df['std'] = df['spread'].rolling(30).std()
df['zscore'] = (df['spread'] - df['mean']) / df['std']

# Backtest
entry_thresh = 2.5
exit_thresh = 0
stop_thresh = 4
position = 0
entry_cl = 0
entry_brn = 0
contract_size = 100
pnl = 0
total_pnl = 0
pnl_list = []

for i in range(30, len(df)):
    z = df['zscore'].iloc[i]
    cl = df['CL'].iloc[i]
    brn = df['BRN'].iloc[i]
    t = df.index[i]

    if position == 0:
        if z > entry_thresh:
            position = -1
            entry_cl = cl
            entry_brn = brn
            print(f"\033[91m{t} | SHORT ENTRY | Z = {z:.2f}\033[0m")
            time.sleep(0.3)
        elif z < -entry_thresh:
            position = 1
            entry_cl = cl
            entry_brn = brn
            print(f"\033[92m{t} | LONG ENTRY  | Z = {z:.2f}\033[0m")
            time.sleep(0.3)

    elif position == 1:
        if z >= exit_thresh or z <= -stop_thresh:
            pnl = (cl - entry_cl - (brn - entry_brn)) * contract_size
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | LONG EXIT   | Z = {z:.2f} | PnL = {pnl_color}{pnl:.2f}\033[0m")
            time.sleep(0.3)
            position = 0

    elif position == -1:
        if z <= exit_thresh or z >= stop_thresh:
            pnl = -(cl - entry_cl - (brn - entry_brn)) * contract_size
            total_pnl += pnl
            pnl_list.append(pnl)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            print(f"{t} | SHORT EXIT  | Z = {z:.2f} | PnL = {pnl_color}{pnl:.2f}\033[0m")
            time.sleep(0.3)
            position = 0

# Summary
total_trades = len(pnl_list)
wins = sum(1 for p in pnl_list if p > 0)
losses = total_trades - wins
win_rate = (wins / total_trades) * 100 if total_trades else 0
loss_rate = 100 - win_rate

win_color = "\033[92m"
loss_color = "\033[91m"

print("\n==== SUMMARY ====")
print(f"Total Trades   : {total_trades}")
print(f"Total PnL      : {total_pnl:.2f}")
print(f"Winning Trades : {win_color}{wins}\033[0m")
print(f"Losing Trades  : {loss_color}{losses}\033[0m")
print(f"Win Rate       : {win_color}{win_rate:.2f}%\033[0m")
print(f"Failure Rate   : {loss_color}{loss_rate:.2f}%\033[0m")
print(f"Max Profit     : \033[92m{max(pnl_list):.2f}\033[0m" if pnl_list else "N/A")
print(f"Max Loss       : \033[91m{min(pnl_list):.2f}\033[0m" if pnl_list else "N/A")

# Plotting
df['position'] = 0
for i in range(1, len(df)):
    df.iloc[i, df.columns.get_loc('position')] = position

df['pnl'] = df['position'].shift(1) * (df['CL'].diff() - df['BRN'].diff()) * contract_size
df['cum_pnl'] = df['pnl'].cumsum()

plt.figure(figsize=(14, 6))
plt.subplot(2, 1, 1)
plt.plot(df['cum_pnl'], label='Cumulative PnL')
plt.title('Cumulative PnL')
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(df['zscore'], label='Z-Score')
plt.axhline(entry_thresh, color='red', linestyle='--', label='Entry Threshold')
plt.axhline(-entry_thresh, color='green', linestyle='--')
plt.axhline(stop_thresh, color='darkred', linestyle=':')
plt.axhline(-stop_thresh, color='darkgreen', linestyle=':')
plt.axhline(0, color='black', linestyle='-')
plt.title('Z-Score')
plt.legend()

plt.tight_layout()
plt.show()
