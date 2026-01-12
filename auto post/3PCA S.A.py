import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ====================================================
# CONFIG
# ====================================================
CSV_FILE = r"D:\Data\ES_NQ.csv"
ROLLING_WINDOW = 252
ENTRY_Z = 0.8
EXIT_Z = 0.2
MAX_HOLD = 20
OUTPUT_FILE = "PCA_ES_NQ_DAILY_ORDERBOOK.xlsx"

# ====================================================
# LOAD DATA
# ====================================================
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["ES", "NQ"]

# ====================================================
# LOG RETURNS
# ====================================================
returns = np.log(df / df.shift(1)).dropna()

# ====================================================
# STATE
# ====================================================
position = 0
entry = {}
trade_log = []
order_book = []
cum_pnl = 0.0
trade_id = 0

# ====================================================
# BACKTEST
# ====================================================
for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    pca = PCA(n_components=2)
    pca.fit(X)

    pc2 = pca.transform(X)[:, 1]
    mean_pc2 = pc2.mean()
    std_pc2 = pc2.std()

    if std_pc2 < 1e-6:
        continue

    pc2_now = pca.transform(
        scaler.transform(returns.iloc[i:i+1])
    )[0, 1]

    z = (pc2_now - mean_pc2) / std_pc2
    date = returns.index[i]

    w = pca.components_[1]
    w = w / np.sum(np.abs(w))
    es_w, nq_w = w

    es_price = df.loc[date, "ES"]
    nq_price = df.loc[date, "NQ"]

    # ================= ENTRY =================
    if position == 0:

        if z > ENTRY_Z:
            position = -1
            direction = "SHORT ES / LONG NQ"
            es_side, nq_side = "SELL", "BUY"

        elif z < -ENTRY_Z:
            position = 1
            direction = "LONG ES / SHORT NQ"
            es_side, nq_side = "BUY", "SELL"

        else:
            continue

        trade_id += 1

        entry = {
            "Trade ID": trade_id,
            "Entry Date": date,
            "Entry Index": i,
            "ES_w": es_w,
            "NQ_w": nq_w,
            "Entry PC2": pc2_now,
            "Direction": direction,
            "ES Side": es_side,
            "NQ Side": nq_side
        }

        # ---- Order Book (ENTRY) ----
        order_book.extend([
            {"Trade ID": trade_id, "Date": date, "Instrument": "ES",
             "Action": "ENTRY", "Side": es_side, "Weight": es_w, "Price": es_price},
            {"Trade ID": trade_id, "Date": date, "Instrument": "NQ",
             "Action": "ENTRY", "Side": nq_side, "Weight": nq_w, "Price": nq_price}
        ])

    # ================= EXIT =================
    else:
        hold = i - entry["Entry Index"]

        if abs(z) < EXIT_Z or hold >= MAX_HOLD:

            es_ret = returns.iloc[i]["ES"]
            nq_ret = returns.iloc[i]["NQ"]

            pnl = position * (es_ret * entry["ES_w"] - nq_ret * entry["NQ_w"])
            cum_pnl += pnl

            # ---- Order Book (EXIT) ----
            exit_es = "BUY" if entry["ES Side"] == "SELL" else "SELL"
            exit_nq = "BUY" if entry["NQ Side"] == "SELL" else "SELL"

            order_book.extend([
                {"Trade ID": entry["Trade ID"], "Date": date, "Instrument": "ES",
                 "Action": "EXIT", "Side": exit_es, "Weight": entry["ES_w"], "Price": es_price},
                {"Trade ID": entry["Trade ID"], "Date": date, "Instrument": "NQ",
                 "Action": "EXIT", "Side": exit_nq, "Weight": entry["NQ_w"], "Price": nq_price}
            ])

            trade_log.append({
                "Entry Date": entry["Entry Date"],
                "Exit Date": date,
                "Direction": entry["Direction"],
                "Holding Days": hold,
                "PnL": pnl,
                "CumPnL": cum_pnl
            })

            position = 0

# ====================================================
# EXPORT
# ====================================================
trades_df = pd.DataFrame(trade_log)
order_book_df = pd.DataFrame(order_book)

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    order_book_df.to_excel(writer, sheet_name="OrderBook", index=False)

print("✅ Order-book style Excel generated:", OUTPUT_FILE)
