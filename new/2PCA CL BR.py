import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller
from openpyxl.drawing.image import Image
import time 
import io

# ==========================
# CONFIG
# ==========================

CSV_FILE    = r"D:\data 3\CL_BR 60.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\CL_BR_STAT_PCA_RESULTS 60 min 4.xlsx"

ROLLING_WINDOW = 150

ENTRY_Z = 1.5
EXIT_Z  = 0.75
STOP_Z  = 2

MAX_HOLD           = 20
MAX_LOSS_PER_TRADE = -1000

CL_MULT = 1000   # Crude Oil multiplier
BR_MULT = 1000   # Brent multiplier (adjust if needed)

TCOST = 5.0

ADF_PVALUE_THRESH = 0.10

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

for sym in ["CL", "BR"]:
    if f"{sym} Close" in df.columns:
        df[sym] = df[f"{sym} Close"]
    else:
        df[sym] = (df[f"{sym} High"] + df[f"{sym} Low"]) / 2
        print(f"[WARN] {sym}: using mid-price")
        print("a quick brown fox jumps over the lazy dog")

df = df[["CL", "BR"]].dropna()

# ==========================
# VARIABLES
# ==========================

position    = 0
entry       = None
trade_log   = []
equity      = 0
equity_curve= []
skipped_adf = 0
bar_count   = 0 

exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop":         0,
    "Time Exit":      0,
}

print("\n=== PCA STAT ARB (CL-BR) ===\n")

# ==========================
# LOOP
# ==========================

for i in range(ROLLING_WINDOW, len(df)):

    window = np.log(df.iloc[i - ROLLING_WINDOW:i][["CL", "BR"]])
    scaler = StandardScaler()
    X      = scaler.fit_transform(window)

    pca    = PCA(n_components=1)
    factor = pca.fit_transform(X).flatten()

    if pca.components_[0][0] < 0:
        factor = -factor

    beta_cl = np.polyfit(factor, window["CL"].values, 1)
    pred_cl = beta_cl[0] * factor + beta_cl[1]

    beta_br = np.polyfit(factor, window["BR"].values, 1)
    pred_br = beta_br[0] * factor + beta_br[1]

    res_cl = window["CL"].values - pred_cl
    res_br = window["BR"].values - pred_br
    spread = res_cl - res_br

    try:
        adf_p = adfuller(spread, autolag="AIC")[1]
    except Exception:
        adf_p = 1.0

    if adf_p > ADF_PVALUE_THRESH:
        skipped_adf += 1
        continue

    bar_count += 1    

    mean = spread.mean()
    std  = spread.std()
    if std == 0:
        continue

    z        = (spread[-1] - mean) / std
    date     = df.index[i]
    cl_price = df.iloc[i]["CL"]
    br_price = df.iloc[i]["BR"]

    hedge_ratio = abs(beta_cl[0]) / (abs(beta_br[0]) + 1e-10) * (CL_MULT / BR_MULT)

    # ==========================
    # ENTRY
    # ==========================

    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry = (date, cl_price, br_price, bar_count, "SHORT", hedge_ratio)
            print(f"{date} | SHORT CL LONG BR | Z={z:.2f} | HR={hedge_ratio:.3f}")
            time.sleep(10)

        elif z < -ENTRY_Z:
            position = 1
            entry = (date, cl_price, br_price, bar_count, "LONG", hedge_ratio)
            print(f"{date} | LONG CL SHORT BR | Z={z:.2f} | HR={hedge_ratio:.3f}")
            time.sleep(10)

    # ==========================
    # EXIT
    # ==========================

    else:
        holding = bar_count - entry[3]
        hr      = entry[5]

        cl_pnl  = (cl_price - entry[1]) * CL_MULT * position
        br_pnl  = (br_price - entry[2]) * BR_MULT * hr * (-position)
        pnl     = cl_pnl + br_pnl - TCOST

        exit_flag = False

        if pnl <= MAX_LOSS_PER_TRADE:
            pnl       = MAX_LOSS_PER_TRADE
            reason    = "Hard Stop Loss"
            exit_flag = True

        elif abs(z) < EXIT_Z:
            reason    = "Mean Reversion"
            exit_flag = True

        elif abs(z) > STOP_Z:
            reason    = "Z Stop"
            exit_flag = True

        elif holding > MAX_HOLD:
            reason    = "Time Exit"
            exit_flag = True

        if exit_flag:
            exit_counts[reason] += 1
            equity += pnl
            equity_curve.append(equity)

            print(f"{date} | EXIT | {reason} | PnL={pnl:.2f} | Equity={equity:.2f}")

            trade_log.append({
                "Entry Date":   entry[0],
                "Exit Date":    date,
                "Direction":    entry[4],
                "Entry CL":     entry[1],
                "Exit CL":      cl_price,
                "Entry BR":     entry[2],
                "Exit BR":      br_price,
                "Hedge Ratio":  round(hr, 4),
                "Holding Bars": holding,
                "Exit Reason":  reason,
                "CL PnL":       round(cl_pnl, 2),
                "BR PnL":       round(br_pnl, 2),
                "PnL":          round(pnl, 2),
                "Equity":       round(equity, 2),
            })
            position = 0

# ==========================
# SUMMARY
# ==========================

trades_df = pd.DataFrame(trade_log)

if trades_df.empty:
    print("\nNo trades executed.")
else:
    pnl           = trades_df["PnL"]
    equity_series = pnl.cumsum()
    drawdown      = equity_series - equity_series.cummax()

    total_pnl     = pnl.sum()
    max_profit    = pnl.max()
    max_loss      = pnl.min()
    max_drawdown  = drawdown.min()
    max_runup     = equity_series.max()
    num_trades    = len(pnl)
    wins          = (pnl > 0).sum()
    losses        = (pnl < 0).sum()
    win_rate      = wins / num_trades * 100
    avg_win       = pnl[pnl > 0].mean()
    avg_loss      = pnl[pnl < 0].mean()
    profit_factor = pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()) if losses > 0 else float("inf")
    sharpe        = (pnl.mean() / pnl.std()) * np.sqrt(26 * 252) if pnl.std() > 0 else 0

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
    print(f"\n  Exit Breakdown:")
    for k, v in exit_counts.items():
        print(f"    {k:<20}: {v}")
    print(f"\033[1m{'='*55}\033[0m\n")

    summary_dict = {
        "Metric": [
            "Total PnL", "Sharpe Ratio", "Profit Factor",
            "Max Profit", "Max Loss", "Max Drawdown", "Max Run-up",
            "Winning Trades", "Losing Trades", "Total Trades", "Win Rate (%)",
            "Avg Win", "Avg Loss",
            "Hard Stop Count", "Mean Reversion Count", "Z Stop Count", "Time Exit Count",
            "Bars Skipped (ADF)","ENTRY_Z", "EXIT_Z", "STOP_Z", "ROLLING_WINDOW",
            "MAX_HOLD","MAX_LOSS_PER_TRADE"
        ],
        "Value": [
            round(total_pnl, 2), round(sharpe, 3), round(profit_factor, 3),
            round(max_profit, 2), round(max_loss, 2), round(max_drawdown, 2), round(max_runup, 2),
            int(wins), int(losses), num_trades, round(win_rate, 2),
            round(avg_win, 2), round(avg_loss, 2),
            exit_counts["Hard Stop Loss"], exit_counts["Mean Reversion"],
            exit_counts["Z Stop"], exit_counts["Time Exit"],
            skipped_adf,
            ENTRY_Z, EXIT_Z, STOP_Z,ROLLING_WINDOW,MAX_HOLD,
            MAX_LOSS_PER_TRADE
        ],
    }
    summary_df = pd.DataFrame(summary_dict)

    # ==========================
    # SAVE TO EXCEL
    # ==========================

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        trades_df.to_excel(writer, sheet_name="Trades",  index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        fig, ax = plt.subplots(2, 1, figsize=(8, 6))
        ax[0].plot(equity_series.values)
        ax[0].set_title("Equity Curve")
        ax[1].plot(drawdown.values, color="red")
        ax[1].set_title("Drawdown")
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)

        book = writer.book
        ws   = book.create_sheet("Charts")
        img  = Image(img_buffer)
        ws.add_image(img, "A1")

    print(f"Saved results to: {OUTPUT_PATH}")