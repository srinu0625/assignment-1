import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint

# ----------------------------------------
# 1. Load Data from CSV
# ----------------------------------------
file_path = r"D:\\Data\\GC Jun25_daily.csv"  # 🔁 Replace with your CSV file path
df = pd.read_csv(file_path, parse_dates=['Datetime'], index_col='Datetime')

# Optional: Drop missing data
df = df[['WTI', 'Brent']].dropna()

# ----------------------------------------
# 2. Cointegration Test
# ----------------------------------------
score, pvalue, _ = coint(df['WTI'], df['Brent'])
print(f"📉 Cointegration p-value (WTI vs Brent): {pvalue:.4f}")

# ----------------------------------------
# 3. Calculate Spread and Z-score
# ----------------------------------------
df['spread'] = df['WTI'] - df['Brent']
df['zscore'] = (df['spread'] - df['spread'].mean()) / df['spread'].std()

# ----------------------------------------
# 4. Signal Generation
# ----------------------------------------
df['position'] = 0
df.loc[df['zscore'] < -1, 'position'] = 1   # Long WTI, Short Brent
df.loc[df['zscore'] > 1, 'position'] = -1   # Short WTI, Long Brent
df['position'] = df['position'].shift()     # Use previous signal

# ----------------------------------------
# 5. Backtest Logic (PnL from Spread)
# ----------------------------------------
df['spread_return'] = df['spread'].diff()
df['pnl'] = df['position'] * df['spread_return']
df['cumulative_pnl'] = df['pnl'].cumsum()

# ----------------------------------------
# 6. Plot Results
# ----------------------------------------
plt.figure(figsize=(14, 8))

plt.subplot(3,1,1)
plt.plot(df['WTI'], label='WTI')
plt.plot(df['Brent'], label='Brent')
plt.title('WTI vs Brent Prices')
plt.legend()

plt.subplot(3,1,2)
plt.plot(df['zscore'], label='Z-Score', color='purple')
plt.axhline(1, color='red', linestyle='--')
plt.axhline(-1, color='green', linestyle='--')
plt.title('Z-Score of Spread')
plt.legend()

plt.subplot(3,1,3)
plt.plot(df['cumulative_pnl'], label='Cumulative PnL', color='black')
plt.title('Strategy PnL')
plt.legend()

plt.tight_layout()
plt.show()

# ----------------------------------------
# 7. Performance Metrics
# ----------------------------------------
if df['pnl'].std() != 0:
    sharpe = df['pnl'].mean() / df['pnl'].std() * np.sqrt(252 * 390)
else:
    sharpe = 0

total_return = df['cumulative_pnl'].iloc[-1]
print(f"📈 Total Return: {total_return:.2f}")
print(f"📊 Sharpe Ratio: {sharpe:.2f}")
