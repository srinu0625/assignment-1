from turtle import position
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# ==== Load data ====
df1 = pd.read_csv(r"D:\Data\BR Jun25_15min.csv")
df2 = pd.read_csv(r"D:\Data\CL Jun25_15min.csv")

entry_z = 1.5
BR_contract_size = 1000
G_contract_size = 1000
entry_br = 1
entry_H = 2.5
entry_time = 3 
entry_z = 4





df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'BR'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'CL'})
df = df1.join(df2, how='inner').dropna()

# ==== Copula transform ====
df['r_br'] = df['BR'].pct_change()
df['r_cl'] = df['CL'].pct_change()
df = df.dropna()

df['u_br'] = df['r_br'].rank(pct=True)
df['u_cl'] = df['r_cl'].rank(pct=True)

df['z_br'] = norm.ppf(df['u_br'])
df['z_cl'] = norm.ppf(df['u_cl'])

df['copula_spread'] = df['z_cl'] - df['z_br']
df['zscore'] = (df['copula_spread'] - df['copula_spread'].rolling(50).mean()) / df['copula_spread'].rolling(50).std()

# ==== Simple chart ====
plt.figure(figsize=(14,8))

for entry_z in [2]:
    plt.axhline(entry_z, color='r', linestyle='--', label=f"Entry Threshold {entry_z}")
    plt.axhline(-entry_z, color='r', linestyle='--')
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title("Coupla-based z-score with entry thresholds")
    plt.plot(df.index, df['zscore'], label = f"Copula Z-Score")
    plt.ledgend()
    plt.show()

plt.figure(figsize=(12, 8))
 for t, row in df.iterrows():
        z = row['zscore']
        if z > entry_z:
            plt.plot(t, z, 'ro')  # Red dot for short entry
        elif z < -entry_z:
            plt.plot(t, z, 'go')  # Green dot for long entry

if position != 0:
    plt.plot(t, z, 'bo')  # Blue dot for exit
    entry_br , netyr_G , entry_H , entry_Z = row['BR'] , row['G'] , row['H']     , z
    entry_time = t
    print_entry(t , side , Z , BR , G , h)

# ==== Detailed chart ====
plt.figure(figsize=(12, 10))
 if position ==1:
        pnl_BR = (BR -entry_br) * BR_contract_size
        pnl_G = -(G - entry_G) * G_contract_size
        pnl = pml_cl + pnl_BR
        position = 0
        exit_reason = "Z-score exit"
        print_exit(t , "long", z , pnl , exit_reason)
        all_trade.append[{
            "Entry Time": entry_time,
            "Exit Time": t,
            "Position": "LONG BR / SHORT G",
            "Entry Z": entry_z,
            "Entry_BR": entry_br,
            "Entry_G": entry_G,
            "Exit Z": z,
            "Exit_BR": BR,
            "Exit_G": G,
            "Hedge Ratio": entry_h,
            "PnL_BR": pnl_BR,
            "PnL_G": pnl_G,
            "PnL": pnl,
            "Exit Reason": exit_reason, 
        }]

#============summary statistics=================
total_trades = len(all_trades)
winning_trade = sum(1 for all_trade in )


# Copula z-score
plt.subplot(2,1,1)
plt.plot(df.index, df['zscore'], label="Copula Z-Score")
plt.axhline(2, color='r', linestyle='--', label="Entry Threshold")
plt.axhline(-2, color='r', linestyle='--')
plt.axhline(0, color='black', linewidth=0.8)
plt.title("Copula-based Z-Score (BR vs CL)")
plt.legend()

# Price series (for reference)
plt.subplot(2,1,2)
plt.plot(df.index, df['BR'], label="BR Price")
plt.plot(df.index, df['CL'], label="CL Price")
plt.title("Underlying Prices")
plt.legend()

plt.tight_layout()
plt.show()
