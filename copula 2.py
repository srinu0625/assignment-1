import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from colorama import Fore, Style, init
from scipy.stats import norm   # for normal quantile transform

# ==================== INIT ====================
init(autoreset=True)

# ---- User I/O ----
file1 = r"D:\Data\BR Jun25_5min.csv"
file2 = r"D:\Data\CL Jun25_5min.csv"

contract_size_br = 1000  # BR
contract_size_cl = 1000  # CL

# ---- Strategy params ----
window = 50              # rolling window for zscore
entry_thresh = 2.0
exit_thresh  = 0.0
stop_thresh  = 4.0
limit = 450

# ==================== HELPERS ====================
def zscore(series):
    return (series - series.rolling(window).mean()) / series.rolling(window).std()

def print_entry(t, z, side, BR, CL):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | ENTRY ({side_colored}) | Z = {z:.2f}")
    if "LONG BR" in side:
        print(f"   BR: {Fore.GREEN}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.RED}{CL:.2f}{Style.RESET_ALL}")
    else:
        print(f"   BR: {Fore.RED}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.GREEN}{CL:.2f}{Style.RESET_ALL}")
    print("-" * 30)

def print_exit(t, z, side, e_br, x_br, e_cl, x_cl, pnl):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | EXIT ({side_colored}) | Z = {z:.2f}")
    print(f"   BR: {e_br:.2f} → {x_br:.2f}")
    print(f"   CL: {e_cl:.2f} → {x_cl:.2f}")
    pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"   PnL: {pnl_color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 60)

# ==================== LOAD & PREP ====================
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'BR'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'CL'})

df = df1.join(df2, how='inner').dropna()

# === COPULA METHOD INJECTION ===
# Step 1: returns
df['r_br'] = df['BR'].pct_change()
df['r_cl'] = df['CL'].pct_change()
df = df.dropna()

# Step 2: rank transform (uniform [0,1])
df['u_br'] = df['r_br'].rank(pct=True)
df['u_cl'] = df['r_cl'].rank(pct=True)

# Step 3: normal scores
df['z_br'] = norm.ppf(df['u_br'])
df['z_cl'] = norm.ppf(df['u_cl'])

# Step 4: copula spread = difference
df['spread'] = df['z_cl'] - df['z_br']

# Step 5: rolling zscore of that spread
df['zscore'] = zscore(df['spread'])

# ==================== BACKTEST ====================
position = 0
entry_br = entry_cl = 0.0
total_pnl = 0.0
pnl_list = []

df['position'] = 0

for t, row in df.iterrows():
    z = row['zscore']
    if np.isnan(z):
        continue

    BR = row['BR']
    CL = row['CL']

    if position == 0:
        if z > entry_thresh:
            position = -1
            entry_br, entry_cl = BR, CL
            print_entry(t, z, "SHORT CL / LONG BR", BR, CL)
            time.sleep(0.5)

        elif z < -entry_thresh:
            position = +1
            entry_br, entry_cl = BR, CL
            print_entry(t, z, "LONG CL / SHORT BR", BR, CL)
            time.sleep(0.5)

    elif position == +1:  # LONG CL / SHORT BR
        if abs(z) < exit_thresh or z <= -stop_thresh:
            pnl_br = -(BR - entry_br) * contract_size_br
            pnl_cl =  (CL - entry_cl) * contract_size_cl
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "LONG CL / SHORT BR", entry_br, BR, entry_cl, CL, pnl)
            time.sleep(0.5)
            position = 0

    elif position == -1:  # SHORT CL / LONG BR
        if abs(z) < exit_thresh or z >= stop_thresh:
            pnl_br =  (BR - entry_br) * contract_size_br
            pnl_cl = -(CL - entry_cl) * contract_size_cl
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "SHORT CL / LONG BR", entry_br, BR, entry_cl, CL, pnl)
            time.sleep(0.5)
            position = 0

    df.loc[t, 'position'] = position

# ==================== SUMMARY ====================
wins = sum(p > 0 for p in pnl_list)
losses = sum(p <= 0 for p in pnl_list)
total_trades = len(pnl_list)
win_rate = (wins / total_trades * 100) if total_trades else 0.0
loss_rate = 100 - win_rate
max_profit = max(pnl_list) if pnl_list else 0
max_loss   = min(pnl_list) if pnl_list else 0
avg_pnl    = np.mean(pnl_list) if pnl_list else 0
cum_pnl    = np.sum(pnl_list) if pnl_list else 0

print("\n" + "="*40)
print("          TRADING SUMMARY         ")
print("="*40)
print(f"Total Trades     : {total_trades}")
print(f"Total PnL        : {cum_pnl:.2f}")
print(f"Winning Trades   : {wins}")
print(f"Losing Trades    : {losses}")
print(f"Win Rate         : {win_rate:.2f}%")
print(f"Failure Rate     : {loss_rate:.2f}%")
print(f"Max Profit/Trade : {max_profit:.2f}")
print(f"Max Loss/Trade   : {max_loss:.2f}")
print(f"Average PnL/Trade: {avg_pnl:.2f}")
print("="*40)

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
# plt.show()
