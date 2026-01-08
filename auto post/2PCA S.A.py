import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ====================================================
# CONFIG (DAILY DATA)
# ====================================================
CSV_FILE = r"D:\Data\ES_NQ.csv"
ROLLING_WINDOW = 252          # 1 trading year
ENTRY_Z = 1.2
EXIT_Z = 0.2
OUTPUT_FILE = "PCA_ES_NQ_DAILY_REAL.xlsx"

# ====================================================
# LOAD DATA
# ====================================================
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["ES", "NQ"]

# ====================================================
# DAILY LOG RETURNS
# ====================================================
returns = np.log(df / df.shift(1)).dropna()

# ====================================================
# STATE VARIABLES
# ====================================================
position = 0                 # +1 long ES/short NQ, -1 opposite
entry_prices = None
entry_weights = None
entry_index = None

trade_log = []
trade_pnl = []
equity_curve = []
holding_bars = []

cum_pnl = 0.0

# ====================================================
# BACKTEST LOOP
# ====================================================
for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    # Standardize
    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    # PCA
    pca = PCA(n_components=2)
    pca.fit(X)

    # PC2 time series
    pcs = pca.transform(X)
    pc2_series = pcs[:, 1]

    mean_pc2 = pc2_series.mean()
    std_pc2 = pc2_series.std()

    # Current PC2
    current_ret = scaler.transform(returns.iloc[i:i+1])
    pc2_now = pca.transform(current_ret)[0, 1]

    zscore = (pc2_now - mean_pc2) / std_pc2

    date = returns.index[i]
    es_price = df.loc[date, "ES"]
    nq_price = df.loc[date, "NQ"]

    # Hedge weights from PC2 loadings
    loadings = pca.components_[1]
    es_w, nq_w = loadings / np.sum(np.abs(loadings))

    # ====================================================
    # ENTRY
    # ====================================================
    if position == 0:

        if zscore > ENTRY_Z:
            position = -1   # SHORT ES, LONG NQ
            entry_prices = (es_price, nq_price)
            entry_weights = (es_w, nq_w)
            entry_index = i

            trade_log.append([
                date, es_price, nq_price, pc2_now, zscore,
                "SHORT ES / LONG NQ"
            ])

        elif zscore < -ENTRY_Z:
            position = 1    # LONG ES, SHORT NQ
            entry_prices = (es_price, nq_price)
            entry_weights = (es_w, nq_w)
            entry_index = i

            trade_log.append([
                date, es_price, nq_price, pc2_now, zscore,
                "LONG ES / SHORT NQ"
            ])

    # ====================================================
    # EXIT
    # ====================================================
    else:
        if abs(zscore) < EXIT_Z:

            es_pnl = (es_price - entry_prices[0]) * entry_weights[0] * position
            nq_pnl = (nq_price - entry_prices[1]) * entry_weights[1] * position
            pnl = es_pnl - nq_pnl

            cum_pnl += pnl
            equity_curve.append(cum_pnl)
            trade_pnl.append(pnl)
            holding_bars.append(i - entry_index)

            trade_log.append([
                date, es_price, nq_price, pc2_now, zscore,
                "EXIT"
            ])

            position = 0

# ====================================================
# RESULTS
# ====================================================
pnl = pd.Series(trade_pnl)
equity = pd.Series(equity_curve)
drawdown = equity.cummax() - equity

# ====================================================
# TRADE LOG
# ====================================================
trades_df = pd.DataFrame(
    trade_log,
    columns=["Date", "ES", "NQ", "PC2", "Z", "Action"]
)

# ====================================================
# SUMMARY
# ====================================================
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
        len(pnl),
        f"{(pnl > 0).mean() * 100:.2f}%" if len(pnl) else "0%",
        round(pnl.mean(), 6) if len(pnl) else 0,
        round(pnl.max(), 6) if len(pnl) else 0,
        round(pnl.min(), 6) if len(pnl) else 0,
        round(np.mean(holding_bars), 2) if holding_bars else 0,
        round(drawdown.max(), 6) if not drawdown.empty else 0
    ]
})

# ====================================================
# EXPORT EXCEL
# ====================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\n✅ DAILY PCA STAT-ARB BACKTEST COMPLETE")
print(summary_df)
