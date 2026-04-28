import pandas as pd
import numpy as np
from scipy.stats import norm
from tqdm import tqdm 
from colorama import Fore, Style, init
import time

# ==================== INIT ====================
init(autoreset=True)

# ==================== USER INPUT ====================
file1 = r"D:\Data\CL d 19-25.csv"
file2 = r"D:\Data\BR d 19-25.csv"

CL_contract_size = 1000
BR_contract_size = 1000

WINDOW    = 50
ENTRY_Z   = 1.5
EXIT_Z    = 0.5
STOP_LOSS = -500

# ==================== HELPERS ====================
def rolling_percentile(arr):
    return np.sum(arr <= arr[-1]) / len(arr)

def zscore(series, window):
    m = series.rolling(window).mean()
    s = series.rolling(window).std().replace(0, np.nan)
    return (series - m) / s

def print_entry(t, side, z, cl, br, h):
    print(f"{t} | ENTRY | {side} | Z={z:.2f} | h={h:.3f}")
    print(f"   CL={cl:.2f}  BR={br:.2f}")
    print("-"*60)

def print_exit(t, side, z, pnl, reason, h):
    color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"{t} | EXIT  | {side} | Z={z:.2f} | h={h:.3f} | {reason}")
    print(f"   PnL: {color}{pnl:.2f}{Style.RESET_ALL}")
    print("="*70)

# ==================== LOAD DATA ====================
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'CL'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'BR'})

df = df1.join(df2, how='inner').dropna()

# ==================== RETURNS ====================
df['r_cl'] = df['CL'].pct_change()
df['r_br'] = df['BR'].pct_change()
df.dropna(inplace=True)

# ==================== HEDGE RATIO ====================
df['hedge'] = df['r_br'].rolling(WINDOW).apply(
    lambda x: np.polyfit(x, df['r_cl'][x.index], 1)[0], raw=False
).fillna(1)

# ==================== COPULA ====================
eps = 1e-6

df['u_cl'] = df['r_cl'].rolling(WINDOW).apply(rolling_percentile, raw=True).clip(eps, 1-eps)
df['u_br'] = df['r_br'].rolling(WINDOW).apply(rolling_percentile, raw=True).clip(eps, 1-eps)

df['z_cl'] = norm.ppf(df['u_cl'])
df['z_br'] = norm.ppf(df['u_br'])

df['spread'] = df['z_br'] - df['z_cl']
df['zscore'] = zscore(df['spread'], WINDOW)

df.dropna(inplace=True)

# ==================== BACKTEST ====================
position = 0
entry_cl = entry_br = entry_z = entry_h = None
entry_time = None

trades = []

equity = 0
peak_equity = 0
max_drawdown = 0
max_runup = 0

for t, row in tqdm(df.iterrows(), total=len(df), desc="Backtest Running"):

    z  = row['zscore']
    CL = row['CL']
    BR = row['BR']
    h  = row['hedge']

    # ===== ENTRY =====
    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry_cl, entry_br, entry_z, entry_h = CL, BR, z, h
            entry_time = t
            print_entry(t, "SHORT (CL) / LONG (BR)", z, CL, BR, h)
            time.sleep(0)

        elif z < -ENTRY_Z:
            position = 1
            entry_cl, entry_br, entry_z, entry_h = CL, BR, z, h
            entry_time = t
            print_entry(t, "LONG (CL) / SHORT (BR)", z, CL, BR, h)
            time.sleep(0)

    # ===== MANAGE =====
    else:

        if position == 1:
            # LONG CL, SHORT BR * h
            pnl_live = (
                (CL - entry_cl) * CL_contract_size
                - entry_h * (BR - entry_br) * BR_contract_size
            )
        else:
            # SHORT CL, LONG BR * h
            pnl_live = (
                - (CL - entry_cl) * CL_contract_size
                + entry_h * (BR - entry_br) * BR_contract_size
            )

        exit_reason = None
        if pnl_live <= STOP_LOSS:
            exit_reason = "STOP_LOSS"
            pnl_live = max(pnl_live, STOP_LOSS)  # <-- CAP PnL at STOP_LOSS
        elif abs(z) < EXIT_Z:
            exit_reason = "MEAN_REVERT"

        if exit_reason:
            side = "LONG" if position == 1 else "SHORT"
            
            print_exit(t, side, z, pnl_live, exit_reason, entry_h)
            time.sleep(0)

            equity += pnl_live
            peak_equity = max(peak_equity, equity)
            max_drawdown = min(max_drawdown, equity - peak_equity)
            max_runup = max(max_runup, equity)

            trades.append({
                "Entry Time": entry_time.strftime("%Y-%m-%d %H:%M"),
                "Exit Time": t.strftime("%Y-%m-%d %H:%M"),
                "Position": "LONG CL / SHORT BR" if position == 1 else "SHORT CL / LONG BR",
                "Entry CL": entry_cl,
                "Exit CL": CL,
                "Entry BR": entry_br,
                "Exit BR": BR,
                "Entry Z": entry_z,
                "Exit Z": z,
                "Hedge Ratio": entry_h,
                "PnL": pnl_live,
                "Exit Reason": exit_reason
            })

            position = 0

# ==================== SUMMARY ====================
trades_df = pd.DataFrame(trades)

wins   = trades_df[trades_df['PnL'] > 0]
losses = trades_df[trades_df['PnL'] < 0]

total_trades = len(trades_df)
total_pnl = trades_df['PnL'].sum()

win_rate  = len(wins) / total_trades * 100 if total_trades else 0
loss_rate = 100 - win_rate

avg_win  = wins['PnL'].mean() if not wins.empty else 0
avg_loss = abs(losses['PnL'].mean()) if not losses.empty else 0
avg_pnl  = total_pnl / total_trades if total_trades else 0

expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)

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
with pd.ExcelWriter("CL_BR_Cointegration 60 T2.xlsx", engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\nExcel saved: CL_BR_Cointegration 60 T2.xlsx")
