import pandas as pd
import matplotlib.pyplot as plt
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

## ==== File paths ====
file1 = r"D:\Data\BR Jun25_15min.csv"
file2 = r"D:\Data\CL Jun25_15min.csv"

# ==== Contract sizes for each product ====
contract_size_es = 1000  # E-mini    S&P 500 Futures (BR)
contract_size_nq = 1000  # E-mini Nasdaq-100 Futures (CL)

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
df1 = df1[['Close']].rename(columns={'Close': 'BR'})
df2 = df2[['Close']].rename(columns={'Close': 'CL'})

# Merge datasets directly without resampling
df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')

# Calculate spread and z-score
df['spread'] = df['BR'] - df['CL']
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

def print_entry(t, z, side, BR, CL):
    # Replace LONG/SHORT words with colored ones
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    
    # First line stays white, only LONG/SHORT highlighted
    print(f"{t} | ENTRY ({side_colored}) | Z = {z:.2f}")
    
    if "LONG BR" in side:
        print(f"   BR: {Fore.GREEN}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.RED}{CL:.2f}{Style.RESET_ALL}")
    else:
        print(f"   BR: {Fore.RED}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.GREEN}{CL:.2f}{Style.RESET_ALL}")
    print("-" * 60)

def print_exit(t, z, side, entry_ucc, exit_ucc, entry_lcc, exit_lcc, pnl):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    
    # First line stays white, only LONG/SHORT highlighted
    print(f"{t} | EXIT ({side_colored}) | Z = {z:.2f}")
    print(f"   BR: {entry_ucc:.2f} → {exit_ucc:.2f}")
    print(f"   CL: {entry_lcc:.2f} → {exit_lcc:.2f}")

    pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"   PnL: {pnl_color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 60)

# ==== Backtest Loop ====
for i in range(60, len(df)):
    z = df['zscore'].iloc[i]
    BR = df['BR'].iloc[i]
    CL = df['CL'].iloc[i]
    t = df.index[i]

    if position == 0:
        if z > entry_thresh:
            position = -1  # Short BR, Long CL
            entry_ucc, entry_lcc = BR, CL
            print_entry(t, z, "SHORT BR / LONG CL", BR, CL)
            time.sleep(0.5)
        elif z < -entry_thresh:
            position = 1  # Long BR, Short CL
            entry_ucc, entry_lcc = BR, CL
            print_entry(t, z, "LONG BR / SHORT CL", BR, CL)
            time.sleep(0.5)

    elif position == 1:
        if z >= exit_thresh or z <= -stop_thresh:
            pnl_ucc = (BR - entry_ucc) * contract_size_es
            pnl_lcc = -(CL - entry_lcc) * contract_size_nq
            pnl = pnl_ucc + pnl_lcc
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "LONG BR / SHORT CL", entry_ucc, BR, entry_lcc, CL, pnl)
            time.sleep(0.5)
            position = 0

    elif position == -1:
        if z <= exit_thresh or z >= stop_thresh:
            pnl_ucc = -(BR - entry_ucc) * contract_size_es
            pnl_lcc = (CL - entry_lcc) * contract_size_nq
            pnl = pnl_ucc + pnl_lcc
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "SHORT BR / LONG CL", entry_ucc, BR, entry_lcc, CL, pnl)
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
print(f"Winning Trades          : {Fore.GREEN}{wins}{Style.RESET_ALL}")
print(f"Losing Trades           : {Fore.RED}{losses}{Style.RESET_ALL}")
print(f"Win Rate                : {Fore.GREEN}{win_rate:.2f}%{Style.RESET_ALL}")
print(f"Failure Rate            : {Fore.RED}{loss_rate:.2f}%{Style.RESET_ALL}")
if pnl_list:
    print(f"Max Profit Per trade    : {Fore.GREEN}{max(pnl_list):.2f}{Style.RESET_ALL}")
    print(f"Max Loss Per trade      : {Fore.RED}{min(pnl_list):.2f}{Style.RESET_ALL}")

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
plt.title('Cumulative PnL BR and CL')
plt.legend()

plt.tight_layout()
plt.show()
