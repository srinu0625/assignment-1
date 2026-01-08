import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import winsound   # Windows only

# ====================================================
# CONFIG
# ====================================================
CSV_FILE = "D:\\Data\\ES_NQ.csv"
ROLLING_WINDOW = 120
ENTRY_Z = 2.0
EXIT_Z = 0.5

# ====================================================
# LOAD DATA
# ====================================================
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

# select correct columns
df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["ES", "NQ"]   # clean names

# ====================================================
# RETURNS (CORE INPUT)
# ====================================================
returns = np.log(df / df.shift(1)).dropna()

# ====================================================
# BACKTEST STATE
# ====================================================
position = 0            # +1 long PC2, -1 short PC2
entry_pc2 = 0.0
entry_date = None
entry_prices = None
trade_pnl = []

# ====================================================
# ROLLING PCA BACKTEST
# ====================================================
for i in range(ROLLING_WINDOW, len(returns)):

    window = returns.iloc[i - ROLLING_WINDOW:i]

    # standardize
    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    # PCA
    pca = PCA(n_components=2)
    pca.fit(X)

    pcs_window = pca.transform(X)
    pc2_series = pcs_window[:, 1]

    pc2_mean = pc2_series.mean()
    pc2_std = pc2_series.std()

    # current observation
    current_ret = scaler.transform(returns.iloc[i:i+1])
    current_pc = pca.transform(current_ret)
    pc2_now = current_pc[0, 1]

    zscore = (pc2_now - pc2_mean) / pc2_std

    date = returns.index[i]
    es_price = df.loc[date, "ES"]
    nq_price = df.loc[date, "NQ"]

    # ====================================================
    # ENTRY LOGIC
    # ====================================================
    if position == 0:

        if zscore > ENTRY_Z:
            position = -1
            entry_pc2 = pc2_now
            entry_date = date
            entry_prices = (es_price, nq_price)

            print("\n🔴 SHORT PC2 ENTRY")
            print(f"Date      : {date}")
            print(f"ES Price  : {es_price:.2f}")
            print(f"NQ Price  : {nq_price:.2f}")
            print(f"PC2       : {pc2_now:.6f}")
            print(f"Z-Score   : {zscore:.2f}")
            print(f"------------------------")

            winsound.Beep(1200, 300)

        elif zscore < -ENTRY_Z:
            position = 1
            entry_pc2 = pc2_now
            entry_date = date
            entry_prices = (es_price, nq_price)

            print("\n🟢 LONG PC2 ENTRY")
            print(f"Date      : {date}")
            print(f"ES Price  : {es_price:.2f}")
            print(f"NQ Price  : {nq_price:.2f}")
            print(f"PC2       : {pc2_now:.6f}")
            print(f"Z-Score   : {zscore:.2f}")
            print(f"------------------------")


            winsound.Beep(900, 300)

    # ====================================================
    # EXIT LOGIC
    # ====================================================
    else:
        if abs(zscore) < EXIT_Z:

            pnl = position * (pc2_now - entry_pc2)
            trade_pnl.append(pnl)

            print("\n🔵 EXIT")
            print(f"Exit Date : {date}")
            print(f"ES Price  : {es_price:.2f}")
            print(f"NQ Price  : {nq_price:.2f}")
            print(f"PC2 Exit  : {pc2_now:.6f}")
            print(f"Z-Score  : {zscore:.2f}")
            print(f"Trade PnL: {pnl:.6f}")
            print(f"---------------------------------------------")

            winsound.Beep(600, 500)

            position = 0

# ====================================================
# RESULTS
# ====================================================
pnl = pd.Series(trade_pnl)

print("\n========== PCA STAT ARB : ES + NQ ==========")
print(f"Total Trades     : {len(pnl)}")
print(f"Total PnL        : {pnl.sum():.6f}")
print(f"Average PnL      : {pnl.mean():.6f}")
print(f"Win Rate         : {(pnl > 0).mean() * 100:.2f}%")
print(f"Sharpe (raw)     : {pnl.mean() / pnl.std():.2f}")
print("===========================================")


