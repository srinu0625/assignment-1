import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ====================================================
# CONFIG (TIMEFRAME AGNOSTIC)
# ====================================================
CSV_FILE = r"D:\Data\ES_NQ.csv"

ROLLING_WINDOW = 120        # bars
ENTRY_Z = 1.5
EXIT_Z = 0.6
MAX_HALF_LIFE = 20          # bars
TREND_LIMIT = 0.0005

# ====================================================
# HELPERS
# ====================================================
def half_life(series):
    lag = series.shift(1).dropna()
    delta = series.diff().dropna()
    beta = np.polyfit(lag, delta, 1)[0]
    return -np.log(2) / beta if beta < 0 else np.inf

def max_drawdown(series):
    cum = series.cumsum()
    peak = cum.cummax()
    return (peak - cum).max()

# ====================================================
# LOAD DATA
# ====================================================
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["ES", "NQ"]

returns = np.log(df / df.shift(1)).dropna()

# ====================================================
# BACKTEST STATE
# ====================================================
position = 0
entry_pc2 = 0.0
entry_idx = None
entry_date = None

trade_log = []
pc2_pnl_series = []

# ====================================================
# ROLLING PCA BACKTEST
# ====================================================
for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    # Trend filter
    if window.mean().abs().sum() > TREND_LIMIT:
        continue

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    pca = PCA(n_components=2)
    pcs = pca.fit_transform(X)

    pc2_series = pd.Series(pcs[:, 1], index=window.index)

    hl = half_life(pc2_series)
    if hl > MAX_HALF_LIFE:
        continue

    pc2_mean = pc2_series.mean()
    pc2_std = pc2_series.std()

    current_ret = scaler.transform(returns.iloc[i:i+1])
    pc2_now = pca.transform(current_ret)[0, 1]
    z = (pc2_now - pc2_mean) / pc2_std

    date = returns.index[i]

    # ================= ENTRY =================
    if position == 0:
        if z > ENTRY_Z:
            position = -1
            entry_pc2 = pc2_now
            entry_idx = i
            entry_date = date

        elif z < -ENTRY_Z:
            position = 1
            entry_pc2 = pc2_now
            entry_idx = i
            entry_date = date

    # ================= EXIT =================
    else:
        if abs(z) < EXIT_Z:
            pnl = position * (pc2_now - entry_pc2)
            holding = i - entry_idx

            trade_log.append({
                "Entry Date": entry_date,
                "Exit Date": date,
                "Direction": "Long PC2" if position == 1 else "Short PC2",
                "Entry PC2": entry_pc2,
                "Exit PC2": pc2_now,
                "PnL": pnl,
                "Holding Bars": holding
            })

            pc2_pnl_series.append(pnl)

            position = 0

# ====================================================
# RESULTS
# ====================================================
trades = pd.DataFrame(trade_log)
pnl = trades["PnL"] if not trades.empty else pd.Series(dtype=float)

report = {
    "Total Trades": len(trades),
    "Win Rate": f"{(pnl > 0).mean() * 100:.2f}%" if len(pnl) else "0%",
    "Avg Trade": pnl.mean() if len(pnl) else 0,
    "Max Win": pnl.max() if len(pnl) else 0,
    "Max Loss": pnl.min() if len(pnl) else 0,
    "Avg Holding Time (bars)": trades["Holding Bars"].mean() if len(trades) else 0,
    "PC2 Variance (%)": round(pca.explained_variance_ratio_[1] * 100, 2),
    "Worst Drawdown (PC space)": max_drawdown(pd.Series(pc2_pnl_series)) if pc2_pnl_series else 0
}

report_df = pd.DataFrame(report.items(), columns=["Metric", "Value"])

print("\n✅ PCA STAT-ARB BACKTEST COMPLETE")
print(report_df)

# OPTIONAL: save trade log
trades.to_csv("pca_trade_log.csv", index=False)
