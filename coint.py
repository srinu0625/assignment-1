# ============================================================
# COINTEGRATION PAIRS TRADING
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
ENTRY_Z_LIST  = [2]                                                                                                                                                                                                                         
EXIT_Z        = 0.5
STOP_Z        = 4
ADF_PVAL_MAX  = 0.05

# ==================== HELPERS ====================
def zscore(series, window):
    m = series.rolling(window).mean()
    s = series.rolling(window).std().replace(0, np.nan)
    return (series - m) / s

def adf_pvalue(series):
    return adfuller(series, autolag="AIC")[1]

def print_entry(t, side, z, cl, br, h):
    print(f"{t} | ENTRY | {side} | Z={z:.2f} | hedge={h:.3f}")
    print(f"   CL={cl:.2f}  BR={br:.2f}")
    print("-" * 60)
    # time.sleep(2.5) 

def print_exit(t, side, z, pnl, reason):
    color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"{t} | EXIT | {side} | Z={z:.2f} | {reason}")
    print(f"   PnL: {color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 70)
    # time.sleep(2.5)

# ==================== LOAD DATA ====================
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'CL'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'BR'})

df = df1.join(df2, how='inner').dropna()

# ==================== HEDGE RATIO (PRICE OLS) ====================
df['hedge'] = df['BR'].rolling(WINDOW).apply(
    lambda x: np.polyfit(
        x.values.astype(float),
        df.loc[x.index, 'CL'].values.astype(float),
        1
    )[0],
    raw=False
)
df.dropna(inplace=True)

# ==================== SPREAD ====================
df['spread'] = df['CL'] - df['hedge'] * df['BR']
df['spread_pct'] = df['spread'].pct_change()

# ==================== ADF FILTER ====================
df['adf_pval'] = df['spread_pct'].rolling(ADF_WINDOW).apply(
    lambda x: adf_pvalue(x.dropna()),
    raw=False
)
df = df[df['adf_pval'] < ADF_PVAL_MAX]
df.dropna(inplace=True)

# ==================== Z-SCORE ====================
df['zscore'] = zscore(df['spread'], WINDOW)
df.dropna(inplace=True)

## ==================== BACKTEST ====================
all_trades = []

for ENTRY_Z in ENTRY_Z_LIST:

    position = 0
    entry_cl = entry_br = entry_h = entry_z = None
    entry_time = None

    for t, row in tqdm(df.iterrows(), total=len(df), desc=f"Z={ENTRY_Z}"):

        CL, BR, z, h = row['CL'], row['BR'], row['zscore'], row['hedge']

        # ========== ENTRY ==========
        if position == 0:

            if z > ENTRY_Z:
                position = -1
                side = "SHORT CL / LONG BR"

            elif z < -ENTRY_Z:
                position = 1
                side = "LONG CL / SHORT BR"

            if position != 0:
                entry_cl, entry_br, entry_h, entry_z = CL, BR, h, z
                entry_time = t
                print_entry(t, side, z, CL, BR, h)

        # ========== MANAGE / EXIT ==========
        else:
            exit_reason = None
            if abs(z) >= STOP_Z:
                exit_reason = "Z_STOP"
            elif abs(z) <= EXIT_Z:
                exit_reason = "TARGET"

            if exit_reason:
                # Correct PnL calculation per trade type
                if position == 1:  # LONG CL / SHORT BR
                    pnl_CL = (CL - entry_cl) * CL_contract_size
                    pnl_BR = -(BR - entry_br) * BR_contract_size
                    pnl = pnl_CL + pnl_BR

                elif position == -1:  # SHORT CL / LONG BR
                    pnl_CL = (entry_cl - CL) * CL_contract_size
                    pnl_BR = -(entry_br - BR) * BR_contract_size
                    pnl = pnl_CL + pnl_BR

                side_str = "LONG" if position == 1 else "SHORT"
                print_exit(t, side_str, z, pnl, exit_reason)

                all_trades.append({
                    "Entry Time": entry_time,
                    "Exit Time": t,
                    "Position": "LONG CL / SHORT BR" if position == 1 else "SHORT CL / LONG BR",
                    "Entry Z": entry_z,
                    "Entry_CL": entry_cl,
                    "Entry_BR": entry_br,
                    "Exit Z": z,
                    "Exit_CL": CL,
                    "Exit_BR": BR,
                    "Hedge Ratio": entry_h,
                    "PnL_CL": pnl_CL,
                    "PnL_BR": pnl_BR,
                    "PnL": pnl,
                    "Exit Reason": exit_reason, 
                })

                # Reset position
                position = 0

# ==================== SUMMARY ====================
trades_df = pd.DataFrame(all_trades)

if not trades_df.empty:
    trades_df['CumPnL'] = trades_df['PnL'].cumsum()
    peak = trades_df['CumPnL'].cummax()
    drawdown = trades_df['CumPnL'] - peak

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
        "Max Drawdown": drawdown.min(),
        "Max Run-up": trades_df['CumPnL'].max(),
        "Success Rate %": len(wins)/len(trades_df)*100,
        "Failure Rate %": len(losses)/len(trades_df)*100,
        "Entry Z": ENTRY_Z,
        "EXIT_Z": EXIT_Z,
        "STOP_Z": STOP_Z,
        "WINDOW": WINDOW
    }

    print("\n" + "="*55)
    print("        COPULA PAIRS TRADING SUMMARY        ")
    print("="*55)
    for k, v in summary.items():
        if "Rate" in k:
            print(f"{k:<15}: {v:.2f}%")
        else:
            print(f"{k:<15}: {v:.2f}")
    print("="*60)

# ==================== EXCEL EXPORT ====================
with pd.ExcelWriter("CL_BR_contegration_modified_Dw T1_.xlsx", engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    pd.DataFrame(list(summary.items()), columns=["Metric", "Value"]).to_excel(
        writer, sheet_name="Summary", index=False
    )

print("\nExcel saved: CL_BR_contegration_modified_D_T1.xlsx")
