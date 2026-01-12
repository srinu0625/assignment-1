import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ====================================================
# CONFIG (DAILY DATA)
# ====================================================
CSV_FILE = r"D:\Data 2\CL_BR 60.csv"
ROLLING_WINDOW = 252
ENTRY_Z = 1.2
EXIT_Z = 0.2
OUTPUT_FILE = "PCA_CL_BR_60min.xlsx"
# ====================================================
# LOAD DATA
# ====================================================
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df = df[["CL Close", "BR Close"]].dropna()
df.columns = ["CL", "BR"]

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
trade_pnl = []
equity_curve = []
holding_days = []

cum_pnl = 0.0

# ====================================================
# BACKTEST
# ====================================================
for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    pca = PCA(n_components=2)
    pca.fit(X)

    pcs = pca.transform(X)
    pc2_series = pcs[:, 1]

    mean_pc2 = pc2_series.mean()
    std_pc2 = pc2_series.std()

    current_ret = scaler.transform(returns.iloc[i:i+1])
    pc2_now = pca.transform(current_ret)[0, 1]

    zscore = (pc2_now - mean_pc2) / std_pc2

    date = returns.index[i]
    cl_price = df.loc[date, "CL"]
    br_price = df.loc[date, "BR"]

    # Hedge weights from PC2
    loadings = pca.components_[1]
    cl_w, br_w = loadings / np.sum(np.abs(loadings))

    # ====================================================
    # ENTRY
    # ====================================================
    if position == 0:

        if zscore > ENTRY_Z:
            position = -1
            entry = {
                "Entry Date": date,
                "Entry CL": cl_price,
                "Entry BR": br_price,
                "CL_w": cl_w,
                "BR_w": br_w,
                "Entry PC2": pc2_now,
                "Direction": "SHORT CL / LONG BR",
                "Entry Index": i
            }

        elif zscore < -ENTRY_Z:
            position = 1
            entry = {
                "Entry Date": date,
                "Entry CL": cl_price,
                "Entry BR": br_price,
                "CL_w": cl_w,
                "BR_w": br_w,
                "Entry PC2": pc2_now,
                "Direction": "LONG CL / SHORT BR",
                "Entry Index": i
            }

    # ====================================================
    # EXIT
    # ====================================================
    else:
        if abs(zscore) < EXIT_Z:

            cl_pnl = (cl_price - entry["Entry CL"]) * entry["CL_w"] * position
            br_pnl = (br_price - entry["Entry BR"]) * entry["BR_w"] * position
            pnl = cl_pnl - br_pnl

            cum_pnl += pnl
            equity_curve.append(cum_pnl)
            trade_pnl.append(pnl)

            holding = i - entry["Entry Index"]
            holding_days.append(holding)

            trade_log.append({
                "Entry Date": entry["Entry Date"],
                "Exit Date": date,
                "Direction": entry["Direction"],
                "Entry CL": entry["Entry CL"],
                "Exit CL": cl_price,
                "Entry BR": entry["Entry BR"],
                "Exit BR": br_price,
                "Entry PC2": entry["Entry PC2"],
                "Exit PC2": pc2_now,
                "Z Exit": zscore,
                "Holding Days": holding,
                "PnL": round(pnl, 2)
            })
            
            position = 0

# ====================================================
# RESULTS
# ====================================================
trades_df = pd.DataFrame(trade_log)

pnl_series = trades_df["PnL"]
equity = pnl_series.cumsum()
drawdown = equity.cummax() - equity

summary_df = pd.DataFrame({
    "Metric": [
        "Total Trades",
        "Win Rate",
        "Avg Trade",
        "Max Win",
        "Max Loss",
        "Avg Holding Time (days)",
        "Worst Drawdown"
    ],
    "Value": [
        len(pnl_series),
        f"{(pnl_series > 0).mean() * 100:.2f}%",
        round(pnl_series.mean(), 2),
        round(pnl_series.max(), 2),
        round(pnl_series.min(), 2),
        round(np.mean(holding_days), 2),
        round(drawdown.max(), 2)
    ]
})

# ====================================================
# EXPORT
# ====================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\n✅ DAILY PCA STAT-ARB BACKTEST COMPLETE")
print(summary_df)
