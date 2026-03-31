import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ==========================
# CONFIG
# ==========================

CSV_FILE = r"D:\data 3\ES_NQ 15.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\ES_NQ PCA_RESULTS 15min.xlsx"

ROLLING_WINDOW = 150

ENTRY_Z = 2.0
EXIT_Z = 1.5
STOP_Z = 4.0

MAX_HOLD = 20
MAX_LOSS_PER_TRADE = -1500

ES_MULT = 50
NQ_MULT = 20

TCOST = 5

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df["ES"] = (df["ES High"] + df["ES Low"]) / 2
df["NQ"] = (df["NQ High"] + df["NQ Low"]) / 2

df = df[["ES", "NQ"]].dropna()

# ==========================
# VARIABLES
# ==========================

position = 0
trade_log = []
equity = 0
equity_curve = []

exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop": 0,
    "Time Exit": 0
}

print("\n\033[1m=== PCA STAT ARB (RESIDUAL MODEL) STARTED ===\033[0m\n")

# ==========================
# LOOP
# ==========================

for i in range(ROLLING_WINDOW, len(df)):

    window = np.log(df.iloc[i - ROLLING_WINDOW:i][["ES", "NQ"]])

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    # PCA factor
    pca = PCA(n_components=1)
    factor = pca.fit_transform(X).flatten()

    # regression
    beta_es = np.polyfit(factor, window["ES"], 1)
    pred_es = beta_es[0] * factor + beta_es[1]

    beta_nq = np.polyfit(factor, window["NQ"], 1)
    pred_nq = beta_nq[0] * factor + beta_nq[1]

    # residual spread
    res_es = window["ES"].values - pred_es
    res_nq = window["NQ"].values - pred_nq
    spread = res_es - res_nq

    mean = spread.mean()
    std = spread.std()

    if std == 0:
        continue

    z = (spread[-1] - mean) / std

    date = df.index[i]
    es_price = df.iloc[i]["ES"]
    nq_price = df.iloc[i]["NQ"]

    # ==========================
    # ENTRY
    # ==========================

    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry = (date, es_price, nq_price, i, "SHORT")
            print(f"{date} | \033[91mSHORT ES LONG NQ\033[0m | Z={z:.2f}")

        elif z < -ENTRY_Z:
            position = 1
            entry = (date, es_price, nq_price, i, "LONG")
            print(f"{date} | \033[92mLONG ES SHORT NQ\033[0m | Z={z:.2f}")

    # ==========================
    # EXIT
    # ==========================

    else:

        holding = i - entry[3]

        es_pnl = (es_price - entry[1]) * ES_MULT * position
        nq_pnl = (nq_price - entry[2]) * NQ_MULT * position

        pnl = es_pnl - nq_pnl - TCOST

        exit_flag = False

        # HARD STOP
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

            print(f"{date} | \033[93mEXIT\033[0m | {reason} | {color}PnL={pnl:.2f}\033[0m | Equity={equity:.2f}")

            trade_log.append({
                "Entry Date": entry[0],
                "Exit Date": date,
                "Direction": entry[4],
                "Entry ES": entry[1],
                "Exit ES": es_price,
                "Entry NQ": entry[2],
                "Exit NQ": nq_price,
                "Holding Bars": holding,
                "Exit Reason": reason,
                "PnL": pnl,
                "Equity": equity
            })

            position = 0

# ==========================
# SUMMARY
# ==========================

trades_df = pd.DataFrame(trade_log)

if not trades_df.empty:

    pnl = trades_df["PnL"]

    total_pnl = pnl.sum()
    positive_pnl = pnl[pnl > 0].sum()
    negative_pnl = pnl[pnl < 0].sum()

    total_positive_trades = (pnl > 0).sum()
    total_negative_trades = (pnl < 0).sum()
    num_of_trades = len(pnl)

    max_profit = pnl.max()
    max_loss = pnl.min()

    equity_series = pnl.cumsum()
    drawdown = equity_series - equity_series.cummax()
    max_drawdown = drawdown.min()
    max_runup = equity_series.max()

    success_rate = (total_positive_trades / num_of_trades) * 100
    failure_rate = (total_negative_trades / num_of_trades) * 100

    print("\n\033[1m--- Trading Performance Summary ---\033[0m")
    print(f"     Max Profit = \033[92m{max_profit:.2f}\033[0m")
    print(f"       Max Loss = \033[91m{max_loss:.2f}\033[0m")
    print(f"   Positive PnL = \033[92m{positive_pnl:.2f}\033[0m")
    print(f"   Negative PnL = \033[91m{negative_pnl:.2f}\033[0m")
    print(f"          Gross = {total_pnl:.2f}")
    print(f"   Max Drawdown = {max_drawdown:.2f}")
    print(f"     Max Run-up = {max_runup:.2f}")
    print(f"Positive Trades = {total_positive_trades}")
    print(f"Negative Trades = {total_negative_trades}")
    print(f"   Total Trades = {num_of_trades}")
    print(f"   Success Rate = \033[92m{success_rate:.2f}%\033[0m")
    print(f"   Failure Rate = \033[91m{failure_rate:.2f}%\033[0m")

    print("\n\033[1m--- Exit Breakdown ---\033[0m")
    for k, v in exit_counts.items():
        print(f"{k}: {v}")

# ==========================
# SAVE
# ==========================

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)

# ==========================
# CHARTS
# ==========================

if not trades_df.empty:

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(equity_series)
    plt.title("Equity Curve")

    plt.subplot(2, 1, 2)
    plt.plot(drawdown)
    plt.title("Drawdown")

    plt.tight_layout()
    plt.show()