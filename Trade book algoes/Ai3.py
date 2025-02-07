import quandl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set your Quandl API key
quandl.ApiConfig.api_key = 'your_api_key'

# Fetch futures data for S&P 500 and NASDAQ from CME
sp500_futures = quandl.get('CME/ESH5')  # Example for S&P 500 futures
nasdaq_futures = quandl.get('CME/NQH5')  # Example for NASDAQ futures

# Combine and analyze the data
df = pd.DataFrame({'S&P 500': sp500_futures['Settle'], 'NASDAQ': nasdaq_futures['Settle']})

# Calculate the daily returns
df_returns = df.pct_change().dropna()

# Calculate the correlation matrix
correlation_matrix = df_returns.corr()

# Print the correlation matrix
print("Correlation Matrix:")
print(correlation_matrix)

# Visualize the correlation matrix with a heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Correlation Matrix of S&P 500 Futures and NASDAQ Futures')
plt.show()
