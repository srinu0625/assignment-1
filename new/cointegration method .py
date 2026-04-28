# ============================================================
# COINTEGRATION PAIRS TRADING – FULL WORKING CODE
# CL vs BR | Rolling OLS + ADF Test + Spread Z-Score
# ============================================================

import pandas as pd
import numpy as np
from tqdm import tqdm
from colorama import Fore, Style, init
from statsmodels.tsa.stattools import adfuller
import time

# ==================== INIT ====================
init(autoreset=True)

# ==================== USER INPUT ====================
file1 = r"D:\Data\CL 60 22-25.csv"
file2 = r"D:\Data\BR 60 22-25.csv"

CL_contract_size = 1000
BR_contract_size = 1000

WINDOW        = 30
ADF_WINDOW    = max(150, 2 * WINDOW)
ENTRY_Z       = 2.1
EXIT_Z        = 0.3
STOP_LOSS     = -250
ADF_PVAL_MAX  = 0.05

# ==================== HELPER FUNCTIONS ====================

def zscore(series, window):
    mean = series.rolling(window).mean()
    std  = series.rolling(window).std().replace(0, np.nan)
    return (series - mean) / std

def adf_pvalue(series):
    return adfuller(series, autolag='AIC')[1]

def print_entry(t, side, z, cl, br, h):
    print(f"{t} | ENTRY | {side} | Z={z:.2f} | hedge={h:.3f}")
    print(f"   CL={cl:.2f}  BR={br:.2f}")
    print("-" * 60)
    time.sleep(3.5)

def print_exit(t, side, z, pnl, reason, h):
    color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"{t} | EXIT | {side} | Z={z:.2f} | hedge={h:.3f} | {reason}")
    print(f"   PnL: {color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 70)
    time.sleep(3.5)

# ==================== LOAD DATA ====================

df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'CL'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'BR'})

df = df1.join(df2, how='inner').dropna()

# ==================== 🔧 PRECISION FIX (ADDED) ====================

df['CL'] = df['CL'].astype('float64')
df['BR'] = df['BR'].astype('float64')

# ==================== HEDGE RATIO (PRICE OLS – STABLE) ====================
# CL = a + h * BR

df['hedge'] = df['BR'].rolling(WINDOW).apply(
    lambda x: np.polyfit(
        x.values.astype('float64'),
        df.loc[x.index, 'CL'].values.astype('float64'),
        1
    )[0],
    raw=False
)

# ==================== 🔧 SAFETY FIX (ADDED) ====================

df['hedge'] = df['hedge'].replace(0, np.nan)
df.dropna(inplace=True)

# ==================== SPREAD ====================

df['spread'] = df['CL'] - df['hedge'] * df['BR']

# ==================== SPREAD % CHANGE (ADF TEST) ====================

df['spread_pct'] = df['spread'].pct_change()

# ==================== COINTEGRATION TEST ====================

df['adf_pval'] = df['spread_pct'].rolling(ADF_WINDOW).apply(
    lambda x: adf_pvalue(x.dropna()),
    raw=False
)

# ==================== Z-SCORE ====================

df['zscore'] = zscore(df['spread'], WINDOW)

# ==================== FILTER VALID REGIMES ====================

df = df[df['adf_pval'] < ADF_PVAL_MAX]
df.dropna(inplace=True)

# ==================== BACKTEST ====================

position = 0
entry_cl = entry_br = entry_z = entry_h = None
entry_time = None

equity = 0
peak_equity = 0
max_drawdown = 0
max_runup = 0

trades = []

for t, row in tqdm(df.iterrows(), total=len(df), desc="Backtest Running"):

    CL = row['CL']
    BR = row['BR']
    z  = row['zscore']
    h  = row['hedge']

    # ================= ENTRY =================
    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry_cl, entry_br, entry_z, entry_h = CL, BR, z, h
            entry_time = t
            print_entry(t, "SHORT CL / LONG BR", z, CL, BR, h)

        elif z < -ENTRY_Z:
            position = 1
            entry_cl, entry_br, entry_z, entry_h = CL, BR, z, h
            entry_time = t
            print_entry(t, "LONG CL / SHORT BR", z, CL, BR, h)

    # ================= MANAGE =================
    else:

        if position == 1:
            pnl = (CL - entry_cl) * CL_contract_size \
                  - entry_h * (BR - entry_br) * BR_contract_size
        else:
            pnl = -(CL - entry_cl) * CL_contract_size \
                  + entry_h * (BR - entry_br) * BR_contract_size

        exit_reason = None

        if pnl <= STOP_LOSS:
            pnl = STOP_LOSS
            exit_reason = "STOP_LOSS"

        elif abs(z) < EXIT_Z:
            exit_reason = "MEAN_REVERT"

        if exit_reason:
            side = "LONG" if position == 1 else "SHORT"
            print_exit(t, side, z, pnl, exit_reason, entry_h)

            equity += pnl
            peak_equity = max(peak_equity, equity)
            max_drawdown = min(max_drawdown, equity - peak_equity)
            max_runup = max(max_runup, equity)

            trades.append({
                "Entry Time": entry_time,
                "Exit Time": t,
                "Position": "LONG CL / SHORT BR" if position == 1 else "SHORT CL / LONG BR",
                "Entry CL": entry_cl,
                "Exit CL": CL,
                "Entry BR": entry_br,
                "Exit BR": BR,
                "Hedge Ratio": entry_h,
                "Entry Z": entry_z,
                "Exit Z": z,
                "PnL": pnl,
                "Exit Reason": exit_reason
            })

            position = 0

# ==================== SUMMARY ====================

trades_df = pd.DataFrame(trades)

wins   = trades_df[trades_df['PnL'] > 0]
losses = trades_df[trades_df['PnL'] < 0]

summary = {
    "Total Trades": len(trades_df),
    "Gross PnL": trades_df['PnL'].sum(),
    "Average PnL": trades_df['PnL'].mean(),
    "Max Profit": trades_df['PnL'].max(),
    "Max Loss": trades_df['PnL'].min(),
    "Positive PnL": wins['PnL'].sum(),
    "Negative PnL": losses['PnL'].sum(),
    "Total Long PnL": trades_df[trades_df['Position']=="LONG CL / SHORT BR"]['PnL'].sum(),
    "Total Short PnL": trades_df[trades_df['Position']=="SHORT CL / LONG BR"]['PnL'].sum(),
    "Max Drawdown": max_drawdown,
    "Max Run-up": max_runup,
    "Success Rate %": len(wins)/len(trades_df)*100 if len(trades_df) else 0,
    "Failure Rate %": len(losses)/len(trades_df)*100 if len(trades_df) else 0,
    "Entry Z": ENTRY_Z,
    "Exit Z": EXIT_Z,
    "Stop Loss": STOP_LOSS,
    "WINDOW": WINDOW
}

print("\n" + "="*55)
print("        COPULA PAIRS TRADING SUMMARY        ")
print("="*55)
print("Total Trades    : {}".format(summary["Total Trades"]))
print("Gross PnL       : {:.2f}".format(summary["Gross PnL"]))
print("Average PnL     : {:.2f}".format(summary["Average PnL"]))
print("Max Profit      : {:.2f}".format(summary["Max Profit"]))
print("Max Loss        : {:.2f}".format(summary["Max Loss"]))
print("Positive PnL    : {:.2f}".format(summary["Positive PnL"]))
print("Negative PnL    : {:.2f}".format(summary["Negative PnL"]))
print("Total Long PnL  : {:.2f}".format(summary["Total Long PnL"]))
print("Total Short PnL : {:.2f}".format(summary["Total Short PnL"]))
print("Max Drawdown    : {:.2f}".format(summary["Max Drawdown"]))
print("Max Run-up      : {:.2f}".format(summary["Max Run-up"]))
print("Success Rate %  : {:.2f}%".format(summary["Success Rate %"]))
print("Failure Rate %  : {:.2f}%".format(summary["Failure Rate %"]))
print("="*60)

# ==================== EXCEL EXPORT ====================

with pd.ExcelWriter("CL_BR_Cointegration_D_T4.xlsx", engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\nExcel saved: CL_BR_Cointegration_D_T4.xlsx")
