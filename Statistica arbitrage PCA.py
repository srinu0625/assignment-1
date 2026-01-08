import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# ==========================
# PARAMETERS
# ==========================
ROLLING_WINDOW = 120        # PCA lookback
N_COMPONENTS = 3            # Number of PCs to remove
ENTRY_Z = 2.0
EXIT_Z = 0.5
TCOST = 0.0002              # Transaction cost per trade
CAPITAL = 1_000_000

# ==========================
# LOAD DATA
# ==========================
df = pd.read_csv("D:\\Data\\BR 60min.csv", index_col="Date(GMT)", parse_dates=True)
prices = df.dropna()

# ==========================
# RETURNS
# ==========================
returns = np.log(prices / prices.shift(1)).dropna()

# ==========================
# STORAGE
# ==========================
pnl = []
positions = pd.DataFrame(0, index=returns.index, columns=returns.columns)

# ==========================
# ROLLING PCA STAT ARB
# ==========================
for t in range(ROLLING_WINDOW, len(returns)):
    window_returns = returns.iloc[t - ROLLING_WINDOW:t]

    # Standardize
    mean = window_returns.mean()
    std = window_returns.std()
    X = (window_returns - mean) / std

    # PCA
    pca = PCA(n_components=N_COMPONENTS)
    pca.fit(X)

    # Project current return
    current_ret = (returns.iloc[t] - mean) / std
    factors = pca.transform(current_ret.values.reshape(1, -1))
    reconstructed = pca.inverse_transform(factors).flatten()

    residual = current_ret - reconstructed
    zscore = (residual - residual.mean()) / residual.std()

    # TRADING LOGIC
    pos = positions.iloc[t - 1].copy()

    for asset in returns.columns:
        if zscore[asset] > ENTRY_Z:
            pos[asset] = -1
        elif zscore[asset] < -ENTRY_Z:
            pos[asset] = 1
        elif abs(zscore[asset]) < EXIT_Z:
            pos[asset] = 0

    positions.iloc[t] = pos

    # PnL
    ret_today = returns.iloc[t]
    trade = (positions.iloc[t] - positions.iloc[t - 1]).abs()
    day_pnl = (positions.iloc[t - 1] * ret_today).sum()
    cost = trade.sum() * TCOST

    pnl.append(day_pnl - cost)

# ==========================
# RESULTS
# ==========================
pnl = pd.Series(pnl, index=returns.index[ROLLING_WINDOW:])
equity_curve = CAPITAL * (1 + pnl).cumprod()

# ==========================
# METRICS
# ==========================
sharpe = np.sqrt(252) * pnl.mean() / pnl.std()
max_dd = (equity_curve / equity_curve.cummax() - 1).min()

print("Sharpe Ratio:", round(sharpe, 2))
print("Max Drawdown:", round(max_dd * 100, 2), "%")
print("Total Return:", round((equity_curve.iloc[-1] / CAPITAL - 1) * 100, 2), "%")

# ==========================
# PLOT
# ==========================
equity_curve.plot(title="PCA Statistical Arbitrage Equity Curve", figsize=(10, 5))
plt.show()
