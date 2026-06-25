import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import time

# ==========================
# CONFIG
# ==========================

CSV_FILE = r"D:\Data 2\ES_NQ 60.csv"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_PATH = fr"D:\ARB_PROJECT1\PCA_RESULTS_{timestamp}.xlsx"

ROLLING_WINDOW = 120

ENTRY_Z = 2.5
EXIT_Z = 1.5
STOP_Z = 4.0

MAX_HOLD = 25

ES_MULT = 50
NQ_MULT = 20

TCOST = 5
MAX_LOSS_PER_TRADE = -500

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df["ES"] = (df["ES High"] + df["ES Low"]) / 2
df["NQ"] = (df["NQ High"] + df["NQ Low"]) / 2

df = df[["ES", "NQ"]].dropna()
returns = np.log(df / df.shift(1)).dropna()

# ==========================
# VARIABLES
# ==========================

position = 0
trade_log = []
equity = 0
equity_curve = []

# 🔥 Exit counters
exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop": 0,
    "Time Exit": 0
}

print("\n\033[1m=== PCA STAT ARB STARTED ===\033[0m\n")

# ==========================
# LOOP
# ==========================

for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    pca = PCA(n_components=2)
    pca.fit(X)

    pc1 = pca.transform(X)[:, 0]

    mean = pc1.mean()
    std = pc1.std()
    if std == 0:
        continue

    current = scaler.transform(returns.iloc[i:i+1])
    pc_now = pca.transform(current)[0, 0]

    z = (pc_now - mean) / std

    date = returns.index[i]

    es_price = df.loc[date, "ES"]
    nq_price = df.loc[date, "NQ"]

    weights = pca.components_[0] / np.linalg.norm(pca.components_[0])
    es_w, nq_w = weights

    # ==========================
    # ENTRY
    # ==========================
    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry = (date, es_price, nq_price, es_w, nq_w, i, "SHORT")
            print(f"{date} | \033[91mSHORT ES LONG NQ\033[0m | Z={z:.2f}")
            time.sleep(3)

        elif z < -ENTRY_Z:
            position = 1
            entry = (date, es_price, nq_price, es_w, nq_w, i, "LONG")
            print(f"{date} | \033[92mLONG ES SHORT NQ\033[0m | Z={z:.2f}")
            time.sleep(3)

    # ==========================
    # EXIT
    # ==========================
    else:

        holding = i - entry[5]

        es_pnl = (es_price - entry[1]) * ES_MULT * entry[3] * position
        nq_pnl = (nq_price - entry[2]) * NQ_MULT * entry[4] * position

        pnl = es_pnl - nq_pnl - TCOST

        exit_flag = False

        # 🔥 PRIORITY 1: HARD STOP
        if pnl <= MAX_LOSS_PER_TRADE:
            reason = "Hard Stop Loss"
            exit_flag = True

        # ORIGINAL LOGIC
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
            time.sleep(3)

            trade_log.append({
                "Entry Date": entry[0],
                "Exit Date": date,
                "Direction": entry[6],
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

    TradeCost = num_of_trades * TCOST
    Net = total_pnl - TradeCost

    success_rate = (total_positive_trades / num_of_trades) * 100
    failure_rate = (total_negative_trades / num_of_trades) * 100

    print("\n\033[1m--- Trading Performance Summary ---\033[0m")
    print(f"Max Profit = \033[92m{max_profit:.2f}\033[0m")
    print(f"Max Loss = \033[91m{max_loss:.2f}\033[0m")
    print(f"Gross = {total_pnl:.2f}")
    print(f"Net = {Net:.2f}")
    print(f"Max Drawdown = {max_drawdown:.2f}")
    print(f"Total Trades = {num_of_trades}")
    print(f"Success Rate = \033[92m{success_rate:.2f}%\033[0m")

    # 🔥 EXIT COUNTS PRINT
    print("\n\033[1m--- Exit Breakdown ---\033[0m")
    for k, v in exit_counts.items():
        print(f"{k}: {v}")

    # Vertical summary
    summary_df = pd.DataFrame({
        "Metric": [
            "Max Profit", "Max Loss", "Gross", "Net",
            "Max Drawdown", "Total Trades", "Success Rate %",
            "Hard Stop Count", "Mean Reversion Count",
            "Z Stop Count", "Time Exit Count"
        ],
        "Value": [
            max_profit, max_loss, total_pnl, Net,
            max_drawdown, num_of_trades, success_rate,
            exit_counts["Hard Stop Loss"],
            exit_counts["Mean Reversion"],
            exit_counts["Z Stop"],
            exit_counts["Time Exit"]
        ]
    })

# ==========================
# SAVE TO EXCEL
# ==========================

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:

    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

    equity_df = pd.DataFrame({
        "Equity": equity_series,
        "Drawdown": drawdown
    })

    equity_df.to_excel(writer, sheet_name="Equity", index=False)

print(f"\nSaved results to: {OUTPUT_PATH}")

# ==========================
# CHART
# ==========================

plt.figure(figsize=(12, 8))

plt.subplot(3, 1, 1)
plt.plot(equity_series)
plt.title("Equity Curve")

plt.subplot(3, 1, 2)
plt.plot(drawdown)
plt.title("Drawdown")

plt.subplot(3, 1, 3)
plt.plot(pnl)
plt.title("Trade PnL")

plt.tight_layout()
# plt.show()