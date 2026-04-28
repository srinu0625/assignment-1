import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import time 
import io

# ==========================
# CONFIG
# ==========================
CSV_FILE    = r"D:\data 3\ES_NQ 15.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\ES_NQ_UPDATED___15min 3___@__==_.xlsx"

ROLLING_WINDOW = 200  # Increased for stability

#  Z OPTIMIZATION LIST
Z_LIST = [0.5, 1, 1.5, 2, 2.5, 3]
RESULT_MATRIX = []
SUMMARY_MATRIX = []

MAX_HOLD           = 20
MAX_LOSS_PER_TRADE = -1000

ES_MULT = 50
NQ_MULT = 20

TCOST = 20.0  # FIXED: Realistic cost for ES+NQ round turn
ADF_PVALUE_THRESH = 0.05  # Stricter threshold

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

for sym in ["ES", "NQ"]:
    if f"{sym} Close" in df.columns:
        df[sym] = df[f"{sym} Close"]
    else:
        df[sym] = (df[f"{sym} High"] + df[f"{sym} Low"]) / 2
        print(f"[WARN] {sym}: using mid-price — prefer Close")

df = df[["ES", "NQ"]].dropna()
log_df = np.log(df)  # Pre-calculate log prices

print("\n\033[1m=== PCA STAT ARB (COINTEGRATION FIX) ===\033[0m\n")

# ==========================
#  OPEN EXCEL WRITER
# ==========================
writer = pd.ExcelWriter(OUTPUT_PATH.replace(".xlsx", "_FIXED.xlsx"), engine="openpyxl")

# ==========================
#  MAIN OPTIMIZATION LOOP
# ==========================

for ENTRY_Z in Z_LIST:

    EXIT_Z = ENTRY_Z * 0.5
    STOP_Z = ENTRY_Z * 1.5  # Tighter stop

    print(f"\n\n\033[96m===== RUNNING FOR Z = {ENTRY_Z} =====\033[0m\n")

    # RESET VARIABLES
    position    = 0
    entry       = None
    trade_log   = []
    equity      = 0
    equity_curve= []
    skipped_adf = 0
    skipped_hl  = 0
    bar_count   = 0 
    z_prev      = 0  # ADDED: For crossing detection

    exit_counts = {
        "Hard Stop Loss": 0,
        "Mean Reversion": 0,
        "Z Stop":         0,
        "Time Exit":      0,
    }

    # ===== MAIN LOOP =====
    for i in range(ROLLING_WINDOW, len(df)):
        
        # Get log prices for window
        window_log = log_df.iloc[i - ROLLING_WINDOW:i]
        window_es = window_log["ES"].values
        window_nq = window_log["NQ"].values
        
        # FIXED: Proper cointegration - Regress ES on NQ
        X = sm.add_constant(window_nq)
        model = OLS(window_es, X).fit()
        beta = model.params[1]  # Hedge ratio
        alpha = model.params[0]
        
        # FIXED: Correct spread calculation
        spread = window_es - beta * window_nq
        
        # ADF test on spread
        try:
            adf_p = adfuller(spread, autolag="AIC")[1]
        except Exception:
            adf_p = 1.0

        if adf_p > ADF_PVALUE_THRESH:
            skipped_adf += 1
            z_prev = 0
            continue
        
        # ADDED: Half-life check
        spread_lag = spread[:-1]
        delta = np.diff(spread)
        if len(delta) > 10 and np.std(spread_lag) > 0:
            try:
                hl_model = OLS(delta, sm.add_constant(spread_lag)).fit()
                theta = hl_model.params[1]
                if theta < 0:
                    half_life = -np.log(2) / theta
                else:
                    half_life = np.inf
            except:
                half_life = np.inf
        else:
            half_life = np.inf
            
        if half_life < 2 or half_life > 50:
            skipped_hl += 1
            z_prev = 0
            continue

        bar_count += 1    

        # FIXED: No look-ahead bias - use past data only for mean/std
        past_spread = spread[:-1]  # Exclude current bar
        mean = past_spread.mean()
        std = past_spread.std()
        
        if std == 0 or np.isnan(std):
            continue

        z = (spread[-1] - mean) / std
        
        # Current prices (original scale)
        date = df.index[i]
        es_price = df.iloc[i]["ES"]
        nq_price = df.iloc[i]["NQ"]

        # FIXED: Proper hedge ratio calculation
        # Dollar neutral: if Long ES, Short NQ -> NQ contracts = ES contracts * beta * (ES_MULT/NQ_MULT)
        dollar_hedge_ratio = abs(beta) * (ES_MULT / NQ_MULT)

        if position == 0:
            # FIXED: Entry on CROSSINGS, not levels
            # Short ES Long NQ: when Z crosses UP through ENTRY_Z (overbought)
            if z_prev < ENTRY_Z and z >= ENTRY_Z:
                position = -1
                entry = (date, es_price, nq_price, bar_count, "SHORT", dollar_hedge_ratio, beta)
                print(f"{date} | \033[91mSHORT ES LONG NQ\033[0m | Z={z:.2f} | Beta={beta:.3f} | HL={half_life:.1f}")
                time.sleep(5)  # Reduced sleep for faster backtest

            # Long ES Short NQ: when Z crosses DOWN through -ENTRY_Z (oversold)
            elif z_prev > -ENTRY_Z and z <= -ENTRY_Z:
                position = 1
                entry = (date, es_price, nq_price, bar_count, "LONG", dollar_hedge_ratio, beta)
                print(f"{date} | \033[92mLONG ES SHORT NQ\033[0m | Z={z:.2f} | Beta={beta:.3f} | HL={half_life:.1f}")
                time.sleep(5)

        else:
            holding = bar_count - entry[3]
            hr = entry[5]
            entry_beta = entry[6]
            
            # FIXED: Correct PnL calculation with proper direction
            if entry[4] == "LONG":
                # Long ES, Short NQ
                es_pnl = (es_price - entry[1]) * ES_MULT
                nq_pnl = (entry[2] - nq_price) * NQ_MULT * hr
            else:  # SHORT
                # Short ES, Long NQ
                es_pnl = (entry[1] - es_price) * ES_MULT
                nq_pnl = (nq_price - entry[2]) * NQ_MULT * hr
                
            pnl = es_pnl + nq_pnl - TCOST

            exit_flag = False

            if pnl <= MAX_LOSS_PER_TRADE:
                pnl = MAX_LOSS_PER_TRADE
                reason = "Hard Stop Loss"
                exit_flag = True

            elif abs(z) < EXIT_Z:
                reason = "Mean Reversion"
                exit_flag = True

            elif abs(z) > STOP_Z:
                reason = "Z Stop"
                exit_flag = True

            elif holding > MAX_HOLD:
                reason = "Time Exit"
                exit_flag = True

            if exit_flag:
                exit_counts[reason] += 1
                equity += pnl
                equity_curve.append(equity)

                color = "\033[92m" if pnl > 0 else "\033[91m"
                print(f"{date} | \033[93mEXIT\033[0m | {reason} | {color}PnL=${pnl:.2f}\033[0m | Equity=${equity:.2f}")

                trade_log.append({
                    "Entry Date": entry[0],
                    "Exit Date": date,
                    "Direction": entry[4],
                    "Entry ES": entry[1],
                    "Exit ES": es_price,
                    "Entry NQ": entry[2],
                    "Exit NQ": nq_price,
                    "Hedge Ratio": round(hr, 4),
                    "Beta": round(entry_beta, 4),
                    "Holding Bars": holding,
                    "Exit Reason": reason,
                    "ES PnL": round(es_pnl, 2),
                    "NQ PnL": round(nq_pnl, 2),
                    "PnL": round(pnl, 2),
                    "Equity": round(equity, 2),
                })
                position = 0
        
        # Store current Z for next iteration (crossing detection)
        z_prev = z

    # ===== SUMMARY =====
    trades_df = pd.DataFrame(trade_log)

    if trades_df.empty:
        print(f"\nNo trades executed for Z={ENTRY_Z}.")
        continue

    pnl = trades_df["PnL"]
    equity_series = pnl.cumsum()
    drawdown = equity_series - equity_series.cummax()
    z_name = str(ENTRY_Z).replace('.', '_')

    trades_df.to_excel(writer, sheet_name=f"Z_{z_name}_Trades", index=False)

    total_pnl = pnl.sum()
    max_profit = pnl.max()
    max_loss = pnl.min()
    max_drawdown = drawdown.min()
    max_runup = equity_series.max()
    num_trades = len(pnl)
    wins = (pnl > 0).sum()
    losses = (pnl < 0).sum()
    win_rate = wins / num_trades * 100 if num_trades > 0 else 0
    avg_win = pnl[pnl > 0].mean() if wins > 0 else 0
    avg_loss = pnl[pnl < 0].mean() if losses > 0 else 0
    profit_factor = abs(pnl[pnl > 0].sum() / pnl[pnl < 0].sum()) if losses > 0 and pnl[pnl < 0].sum() != 0 else float("inf")
    sharpe = (pnl.mean() / pnl.std()) * np.sqrt(26 * 252) if pnl.std() > 0 else 0

    print(f"\n\033[1m{'='*55}\033[0m")
    print(f"  {'Total PnL':<25}: ${total_pnl:>10,.2f}")
    print(f"  {'Sharpe Ratio':<25}: {sharpe:>10.3f}")
    print(f"  {'Profit Factor':<25}: {profit_factor:>10.3f}")
    print(f"  {'Max Drawdown':<25}: ${max_drawdown:>10,.2f}")
    print(f"  {'Max Run-up':<25}: ${max_runup:>10,.2f}")
    print(f"  {'Total Trades':<25}: {num_trades:>10}")
    print(f"  {'Win Rate':<25}: {win_rate:>9.1f}%")
    print(f"  {'Avg Win':<25}: ${avg_win:>10,.2f}")
    print(f"  {'Avg Loss':<25}: ${avg_loss:>10,.2f}")
    print(f"  Bars skipped (ADF) : {skipped_adf:,}")
    print(f"  Bars skipped (HL)  : {skipped_hl:,}")
    print(f"\n  Exit Breakdown:")
    for k, v in exit_counts.items():
        print(f"    {k:<20}: {v}")
    print(f"\033[1m{'='*55}\033[0m\n")

    SUMMARY_MATRIX.append({
        "Z": ENTRY_Z,
        "Total PnL": round(total_pnl, 2),
        "Sharpe Ratio": round(sharpe, 3),
        "Profit Factor": round(profit_factor, 3),
        "Max Profit": round(max_profit, 2),
        "Max Loss": round(max_loss, 2),
        "Max Drawdown": round(max_drawdown, 2),
        "Max Run-up": round(max_runup, 2),
        "Winning Trades": int(wins),
        "Losing Trades": int(losses),
        "Total Trades": num_trades,
        "Win Rate (%)": round(win_rate, 2),
        "Avg Win": round(avg_win, 2),
        "Avg Loss": round(avg_loss, 2),
        "Hard Stop Count": exit_counts["Hard Stop Loss"],
        "Mean Reversion Count": exit_counts["Mean Reversion"],
        "Z Stop Count": exit_counts["Z Stop"],
        "Time Exit Count": exit_counts["Time Exit"],
        "Bars Skipped (ADF)": skipped_adf,
        "Bars Skipped (HL)": skipped_hl,
    })

    # Chart
    fig, ax = plt.subplots(2, 1, figsize=(8, 6))
    ax[0].plot(equity_series.values)
    ax[0].set_title(f"Equity Curve Z={ENTRY_Z}")
    ax[1].plot(drawdown.values)
    ax[1].set_title("Drawdown")
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)

    ws = writer.book.create_sheet(f"Z_{z_name}_Charts")
    img = Image(img_buffer)
    ws.add_image(img, "A1")

    # STORE MATRIX
    RESULT_MATRIX.append({
        "Z": ENTRY_Z,
        "Trades": num_trades,
        "WinRate": round(win_rate, 2),
        "PnL": round(total_pnl, 2),
        "Drawdown": round(max_drawdown, 2),
        "Sharpe": round(sharpe, 3),
        "PF": round(profit_factor, 3)
    })

# ==========================
# FINAL MATRIX
# ==========================

result_df = pd.DataFrame(RESULT_MATRIX)
summary_df = pd.DataFrame(SUMMARY_MATRIX)
summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\n\033[1m===== PERFORMANCE MATRIX =====\033[0m")
print(result_df.sort_values(by="PnL", ascending=False))

result_df.to_excel(writer, sheet_name="Z_Performance_Matrix", index=False)

# CLOSE FILE
writer.close()
print(f"\n\033[1mResults saved to: {OUTPUT_PATH.replace('.xlsx', '_FIXED.xlsx')}\033[0m")
