import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# ==== Load data ====
df1 = pd.read_csv(r"D:\Data\BR Jun25_15min.csv")
df2 = pd.read_csv(r"D:\Data\CL Jun25_15min.csv")

df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'BR'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close':'CL'})
df = df1.join(df2, how='inner').dropna()

# ==== Copula transform ====
df['r_br'] = df['BR'].pct_change()
df['r_cl'] = df['CL'].pct_change()
df = df.dropna()

df['u_br'] = df['r_br'].rank(pct=True)
df['u_cl'] = df['r_cl'].rank(pct=True)

df['z_br'] = norm.ppf(df['u_br'])
df['z_cl'] = norm.ppf(df['u_cl'])

df['copula_spread'] = df['z_cl'] - df['z_br']
df['zscore'] = (df['copula_spread'] - df['copula_spread'].rolling(50).mean()) / df['copula_spread'].rolling(50).std()

# ==== Simple chart ====
plt.figure(figsize=(14,8))

# Copula z-score
plt.subplot(2,1,1)
plt.plot(df.index, df['zscore'], label="Copula Z-Score")
plt.axhline(2, color='r', linestyle='--', label="Entry Threshold")
plt.axhline(-2, color='r', linestyle='--')
plt.axhline(0, color='black', linewidth=0.8)
plt.title("Copula-based Z-Score (BR vs CL)")
plt.legend()

# Price series (for reference)
plt.subplot(2,1,2)
plt.plot(df.index, df['BR'], label="BR Price")
plt.plot(df.index, df['CL'], label="CL Price")
plt.title("Underlying Prices")
plt.legend()

plt.tight_layout()
plt.show()
