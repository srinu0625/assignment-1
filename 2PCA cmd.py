# ==========================================================
# PCA STAT ARB STRATEGY (ES vs NQ)
# ----------------------------------------------------------
# Simple explanation:
# We are trying to catch moments where ES and NQ move apart
# more than usual, and trade that they will come back together.
# ==========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

CSV_FILE = r"D:\data 3\ES_NQ 5.csv"   # input data file
OUTPUT_PATH = r"D:\ARB_PROJECT1\ES_NQ PCA_RESULTS 5min.xlsx"  # where results will be saved

ROLLING_WINDOW = 150   # how much past data we use to understand behaviour

ENTRY_Z = 3.0   # enter trade when deviation is big
EXIT_Z = 1.5    # exit when things calm down
STOP_Z = 4.0    # emergency exit if things go too far

MAX_HOLD = 20   # don’t stay in a trade forever

ES_MULT = 50    # ES contract multiplier
NQ_MULT = 20    # NQ contract multiplier

TCOST = 5       # trading cost per trade
MAX_LOSS_PER_TRADE = -500   # hard stop loss

# --------------------------
# LOAD DATA
# --------------------------

# read CSV and set date as index
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

# create a cleaner price (mid price instead of close)
df["ES"] = (df["ES High"] + df["ES Low"]) / 2
df["NQ"] = (df["NQ High"] + df["NQ Low"]) / 2

# keep only needed columns
df = df[["ES", "NQ"]].dropna()

# convert to returns (this is what PCA will look at)
returns = np.log(df / df.shift(1)).dropna()

# --------------------------
# VARIABLES
# --------------------------

position = 0    # 0 = no trade, 1 = long spread, -1 = short spread
trade_log = []
equity = 0
equity_curve = []

exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop": 0,
    "Time Exit": 0
}

print("\nStarting PCA Stat Arb...\n")

# --------------------------
# MAIN LOOP
# --------------------------

for i in range(ROLLING_WINDOW, len(returns)):

    # take last N candles
    window = returns.iloc[i - ROLLING_WINDOW:i]

    # scale data so PCA behaves properly
    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    # run PCA
    pca = PCA(n_components=2)
    pca.fit(X)

    # first component = spread idea
    pc1 = pca.transform(X)[:, 0]

    # get average behaviour of spread
    mean = pc1.mean()
    std = pc1.std()
    if std == 0:
        continue

    # current point projected into PCA world
    current = scaler.transform(returns.iloc[i:i+1])
    pc_now = pca.transform(current)[0, 0]

    # how far from normal?
    z = (pc_now - mean) / std

    date = returns.index[i]

    es_price = df.loc[date, "ES"]
    nq_price = df.loc[date, "NQ"]

    # weights (rough relationship between ES & NQ)
    weights = pca.components_[0] / np.linalg.norm(pca.components_[0])
    es_w, nq_w = weights

    # --------------------------
    # ENTRY
    # --------------------------

    if position == 0:

        # spread too high → expect it to fall
        if z > ENTRY_Z:
            position = -1
            entry = (date, es_price, nq_price, es_w, nq_w, i, "SHORT")
            print(f"{date} | SHORT spread | Z={z:.2f}")

        # spread too low → expect it to rise
        elif z < -ENTRY_Z:
            position = 1
            entry = (date, es_price, nq_price, es_w, nq_w, i, "LONG")
            print(f"{date} | LONG spread | Z={z:.2f}")

    # --------------------------
    # EXIT
    # --------------------------

    else:

        holding = i - entry[5]

        # calculate PnL
        es_pnl = (es_price - entry[1]) * ES_MULT * entry[3] * position
        nq_pnl = (nq_price - entry[2]) * NQ_MULT * entry[4] * position
        pnl = es_pnl - nq_pnl - TCOST

        exit_flag = False

        # stop loss
        if pnl <= MAX_LOSS_PER_TRADE:
            reason = "Hard Stop Loss"
            exit_flag = True

        # main exit (mean reversion)
        elif abs(z) < EXIT_Z:
            reason = "Mean Reversion"
            exit_flag = True

        # extreme move protection
        elif abs(z) > STOP_Z:
            reason = "Z Stop"
            exit_flag = True

        # time exit
        elif holding > MAX_HOLD:
            reason = "Time Exit"
            exit_flag = True

        if exit_flag:

            exit_counts[reason] += 1

            equity += pnl
            equity_curve.append(equity)

            print(f"{date} | EXIT | {reason} | PnL={pnl:.2f}")

            trade_log.append({
                "Entry Date": entry[0],
                "Exit Date": date,
                "Direction": entry[6],
                "PnL": pnl
            })

            position = 0

# --------------------------
# SUMMARY
# --------------------------

trades_df = pd.DataFrame(trade_log)

if not trades_df.empty:

    pnl = trades_df["PnL"]

    total_pnl = pnl.sum()
    num_trades = len(pnl)
    win_rate = (pnl > 0).mean() * 100

    equity_series = pnl.cumsum()
    drawdown = equity_series - equity_series.cummax()

    print("\nSummary:")
    print(f"Total PnL: {total_pnl:.2f}")
    print(f"Trades: {num_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Max Drawdown: {drawdown.min():.2f}")

# --------------------------
# SAVE RESULTS
# --------------------------

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)

print(f"\nSaved to: {OUTPUT_PATH}")

# --------------------------
# PLOTS
# --------------------------

plt.figure(figsize=(12, 8))

plt.subplot(2, 1, 1)
plt.plot(equity_series)
plt.title("Equity Curve")

plt.subplot(2, 1, 2)
plt.plot(drawdown)
plt.title("Drawdown")

plt.tight_layout()
plt.show()