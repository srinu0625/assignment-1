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

CSV_FILE    = r"D:\data 3\ES_NQ 60.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\ES_NQ_STAT_PCA_RESULTS 60 min IMPROVED.xlsx"

ROLLING_WINDOW = 120

ENTRY_Z = 2.5
EXIT_Z  = 1.0
STOP_Z  = 5.0

MAX_HOLD           = 15
MAX_LOSS_PER_TRADE = -1000

ES_MULT = 50
NQ_MULT = 20

TCOST = 5.0
ADF_PVALUE_THRESH = 0.10

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
        print(f"[WARN] {sym}: using mid-price")

df = df[["ES", "NQ"]].dropna()

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
prev_hr     = None

exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop":         0,
    "Time Exit":      0,
    "Early Failure":  0,
}

print("\n=== PCA STAT ARB (IMPROVED MODEL) ===\n")

# ==========================
# LOOP
# ==========================

for i in range(ROLLING_WINDOW, len(df)):

    window = np.log(df.iloc[i - ROLLING_WINDOW:i][["ES", "NQ"]])
    scaler = StandardScaler()
    X      = scaler.fit_transform(window)

    pca    = PCA(n_components=1)
    factor = pca.fit_transform(X).flatten()

    if pca.components_[0][0] < 0:
        factor = -factor

    beta_es = np.polyfit(factor, window["ES"].values, 1)
    beta_nq = np.polyfit(factor, window["NQ"].values, 1)

    pred_es = beta_es[0] * factor + beta_es[1]
    pred_nq = beta_nq[0] * factor + beta_nq[1]

    res_es = window["ES"].values - pred_es
    res_nq = window["NQ"].values - pred_nq
    spread = res_es - res_nq

    # ADF filter
    try:
        adf_p = adfuller(spread)[1]
    except:
        adf_p = 1.0

    if adf_p > ADF_PVALUE_THRESH:
        skipped_adf += 1
        continue

    bar_count += 1

    mean = spread.mean()
    std  = spread.std()
    if std == 0:
        continue

    z = (spread[-1] - mean) / std
    prev_z = (spread[-2] - mean) / std

    date     = df.index[i]
    es_price = df.iloc[i]["ES"]
    nq_price = df.iloc[i]["NQ"]

    # ==========================
    # FILTERS
    # ==========================

    # Trend filter
    trend_window = 50
    es_trend = df["ES"].iloc[i-trend_window:i].pct_change().sum()
    nq_trend = df["NQ"].iloc[i-trend_window:i].pct_change().sum()
    is_trending = abs(es_trend) > 0.02 or abs(nq_trend) > 0.02

    # Volatility filter
    vol = spread.std()
    avg_vol = np.mean([np.std(spread[-20:]), np.std(spread[-50:])])
    low_vol = vol < avg_vol * 0.8

    # Hedge ratio smoothing
    raw_hr = abs(beta_es[0]) / (abs(beta_nq[0]) + 1e-10) * (ES_MULT / NQ_MULT)
    if prev_hr is None:
        prev_hr = raw_hr
    hedge_ratio = 0.7 * prev_hr + 0.3 * raw_hr
    prev_hr = hedge_ratio

    # ==========================
    # ENTRY
    # ==========================

    if position == 0 and not is_trending and not low_vol:

        # SHORT
        if z > ENTRY_Z and prev_z > z:
            position = -1
            entry = (date, es_price, nq_price, bar_count, "SHORT", hedge_ratio)
            print(f"{date} | SHORT ES LONG NQ | Z={z:.2f}")
            time.sleep(10)

        # LONG
        elif z < -ENTRY_Z and prev_z < z:
            position = 1
            entry = (date, es_price, nq_price, bar_count, "LONG", hedge_ratio)
            print(f"{date} | LONG ES SHORT NQ | Z={z:.2f}")
            time.sleep(10)

    # ==========================
    # EXIT
    # ==========================

    elif position != 0:

        holding = bar_count - entry[3]
        hr      = entry[5]

        es_pnl  = (es_price - entry[1]) * ES_MULT * position
        nq_pnl  = (nq_price - entry[2]) * NQ_MULT * hr * (-position)
        pnl     = es_pnl + nq_pnl - TCOST

        exit_flag = False

        if pnl <= MAX_LOSS_PER_TRADE:
            pnl = MAX_LOSS_PER_TRADE
            reason = "Hard Stop Loss"
            exit_flag = True

        elif holding > 5 and pnl < -200:
            reason = "Early Failure"
            exit_flag = True

        elif abs(z) < EXIT_Z or (pnl > 0 and abs(z) < 2.0):
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

            print(f"{date} | EXIT | {reason} | PnL={pnl:.2f} | Equity={equity:.2f}")

            trade_log.append({
                "Entry Date": entry[0],
                "Exit Date": date,
                "Direction": entry[4],
                "Entry ES": entry[1],
                "Exit ES": es_price,
                "Entry NQ": entry[2],
                "Exit NQ": nq_price,
                "Hedge Ratio": round(hr, 4),
                "Holding Bars": holding,
                "Exit Reason": reason,
                "ES PnL": round(es_pnl, 2),
                "NQ PnL": round(nq_pnl, 2),
                "PnL": round(pnl, 2),
                "Equity": round(equity, 2),
            })

            position = 0

# ==========================
# SUMMARY + EXCEL
# ==========================

trades_df = pd.DataFrame(trade_log)

if not trades_df.empty:

    pnl = trades_df["PnL"]
    equity_series = pnl.cumsum()
    drawdown = equity_series - equity_series.cummax()

    summary_df = pd.DataFrame({
        "Metric": ["Total PnL", "Win Rate", "Trades"],
        "Value": [pnl.sum(), (pnl > 0).mean() * 100, len(pnl)]
    })

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        trades_df.to_excel(writer, sheet_name="Trades", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        fig, ax = plt.subplots(2, 1, figsize=(8, 6))
        ax[0].plot(equity_series.values)
        ax[0].set_title("Equity Curve")
        ax[1].plot(drawdown.values)
        ax[1].set_title("Drawdown")

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        ws = writer.book.create_sheet("Charts")
        ws.add_image(Image(buf), "A1")

print("DONE")