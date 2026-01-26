import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from colorama import Fore, Style, init
from scipy.stats import norm  
from tqdm import tqdm          

init(autoreset=True)

# ---- User I/O ----
file1 = r"D:\Data\CL 60 22-25.csv"
file2 = r"D:\Data\BR 60 22-25.csv"

contract_size_CL = 1000  # CL
contract_size_BR = 1000  # BR

# ---- Strategy params ----
window = 60  # rolling window for zscore and rolling percentile
entry_thresh = 2
exit_thresh  = 0.3   # fixed from 0.0 to a realistic small exit threshold
stop_thresh  = 4

# ==================== HELPERS ====================
def zscore(series):
    # rolling zscore, safe against zero standard
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std().replace(0, np.nan)
    return (series - rolling_mean) / rolling_std

def print_entry(t, z, side, CL, BR):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | ENTRY ({side_colored}) | Z = {z:.2f}")
    if "LONG CL" in side:
        print(f"   CL: {Fore.GREEN}{CL:.2f}{Style.RESET_ALL}")
        print(f"   BR: {Fore.RED}{BR:.2f}{Style.RESET_ALL}")
    else:
        print(f"   CL: {Fore.RED}{CL:.2f}{Style.RESET_ALL}")
        print(f"   BR: {Fore.GREEN}{BR:.2f}{Style.RESET_ALL}")
    print("-" * 30)
    time.sleep(5)

def print_exit(t, z, side, e_br, x_br, e_cl, x_cl, pnl):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | EXIT ({side_colored}) | Z = {z:.2f}")
    print(f"   CL: {e_br:.2f} → {x_br:.2f}")
    print(f"   BR: {e_cl:.2f} → {x_cl:.2f}")
    pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"   PnL: {pnl_color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 60)
    time.sleep(5)

# ==================== LOAD & PREP ====================
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Parse datetime
df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'CL'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'BR'})

df = df1.join(df2, how='inner').dropna()

# === COPULA METHOD INJECTION ===
# Step 1: returns
df['r_ucc'] = df['CL'].pct_change()
df['r_lcc'] = df['BR'].pct_change()
df = df.dropna()

# Parameters for safe transforms
eps = 1e-6
rank_window = window  # use same window for rolling percentile; keeps structure consistent

# Helper: percentile of last value in the window (no look-ahead)
def pct_of_last(window_values):
    arr = np.asarray(window_values)
    last = arr[-1]
    return np.sum(arr <= last) / arr.size

# Step 2: rolling rank transform (uniform [0,1]) - no look-ahead
df['u_ucc'] = df['r_ucc'].rolling(window=rank_window, min_periods=rank_window).apply(pct_of_last, raw=True)
df['u_lcc'] = df['r_lcc'].rolling(window=rank_window, min_periods=rank_window).apply(pct_of_last, raw=True)

# Clip percentiles to avoid exact 0 or 1
df['u_ucc'] = df['u_ucc'].clip(eps, 1 - eps)
df['u_lcc'] = df['u_lcc'].clip(eps, 1 - eps)

# Step 3: normal scores
df['z_ucc'] = norm.ppf(df['u_ucc'])
df['z_lcc'] = norm.ppf(df['u_lcc'])

# Step 4: copula spread
df['spread'] = df['z_lcc'] - df['z_ucc']

# Step 5: rolling zscore of that spread
df['zscore'] = zscore(df['spread'])

# ==================== BACKTEST ====================
position = 0
entry_br = entry_cl = 0.0
total_pnl = 0.0
pnl_list = []

df['position'] = 0

# Wrap loop in tqdm progress bar
for t, row in tqdm(df.iterrows(), total=len(df), desc="Backtest Running", ncols=100, colour="yellow"):
    z = row['zscore']
    if np.isnan(z):
        df.loc[t, 'position'] = position
        continue

    CL = row['CL']
    BR = row['BR']

    if position == 0:
        if z > entry_thresh:
            position = -1
            entry_br, entry_cl = CL, BR
            print_entry(t, z, "SHORT BR / LONG CL", CL, BR)
            time.sleep(5)

        elif z < -entry_thresh:
            position = +1
            entry_br, entry_cl = CL, BR
            print_entry(t, z, "LONG BR / SHORT CL", CL, BR)
            time.sleep(5)


    elif position == +1:  # LONG BR / SHORT CL
        if abs(z) < exit_thresh or z <= -stop_thresh:
            pnl_br = -(CL - entry_br) * contract_size_CL
            pnl_cl =  (BR - entry_cl) * contract_size_BR
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "LONG BR / SHORT CL", entry_br, CL, entry_cl, BR, pnl)
            position = 0
            time.sleep(5)

    elif position == -1:  # SHORT BR / LONG CL
        if abs(z) < exit_thresh or z >= stop_thresh:
            pnl_br =  (CL - entry_br) * contract_size_CL
            pnl_cl = -(BR - entry_cl) * contract_size_BR
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "SHORT BR / LONG CL", entry_br, CL, entry_cl, BR, pnl)
            position = 0
            time.sleep(5)

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
plt.figure(figsize=(10, 6))

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
plt.title('Cumulative PnL CL and BR')
plt.legend()

plt.tight_layout()
plt.show()
