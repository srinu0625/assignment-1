import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
CSV_FILE = r"C:\Users\lenovo\Downloads\CL BR D.csv"   # columns = assets, rows = time

N_COMPONENTS = 3
ENTRY_Z = 2.0
EXIT_Z = 0.5
STOP_Z = 3.5

CAPITAL = 100000

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(CSV_FILE, index_col=0, parse_dates=True)

# forward fill missing
df = df.fillna(method='fill')

# =========================
# RETURNS
# =========================
returns = df.pct_change().dropna()

# =========================
# STANDARDIZE
# =========================
scaler = StandardScaler()
ret_scaled = scaler.fit_transform(returns)

# =========================
# PCA
# =========================
pca = PCA(n_components=N_COMPONENTS)
factors = pca.fit_transform(ret_scaled)

# reconstruct returns
reconstructed = pca.inverse_transform(factors)

# residuals (alpha signal)
residuals = ret_scaled - reconstructed
residuals = pd.DataFrame(residuals, index=returns.index, columns=returns.columns)

# =========================
# Z-SCORE
# =========================
zscore = (residuals - residuals.rolling(50).mean()) / residuals.rolling(50).std()

# =========================
# BACKTEST
# =========================
positions = pd.DataFrame(0, index=returns.index, columns=returns.columns)
pnl = []

capital = CAPITAL

for i in range(50, len(returns)):
    daily_pnl = 0
    
    for asset in returns.columns:
        z = zscore.iloc[i][asset]
        ret = returns.iloc[i][asset]

        # ENTRY
        if z > ENTRY_Z:
            positions.iloc[i][asset] = -1  # short
        elif z < -ENTRY_Z:
            positions.iloc[i][asset] = 1   # long

        # EXIT
        elif abs(z) < EXIT_Z:
            positions.iloc[i][asset] = 0

        # STOP LOSS
        elif abs(z) > STOP_Z:
            positions.iloc[i][asset] = 0

        else:
            positions.iloc[i][asset] = positions.iloc[i-1][asset]

        # PnL
        daily_pnl += positions.iloc[i-1][asset] * ret * capital

    pnl.append(daily_pnl)

# =========================
# RESULTS
# =========================
pnl = pd.Series(pnl, index=returns.index[50:])
cum_pnl = pnl.cumsum()

print("=================================")
print("PCA STAT ARB RESULTS")
print("=================================")
print(f"Total PnL     : {cum_pnl.iloc[-1]:.2f}")
print(f"Sharpe        : {(pnl.mean()/pnl.std()) * np.sqrt(252):.2f}")
print(f"Max Drawdown  : {(cum_pnl.cummax() - cum_pnl).max():.2f}")

# =========================
# PLOT
# =========================
plt.figure()
plt.plot(cum_pnl)
plt.title("Cumulative PnL - PCA Stat Arb")
plt.show()