# Import necessary libraries
import pandas as pd             # Used to handle and manipulate data in tabular form.
import seaborn as sns           # A Python library for data visualization, especially for heatmaps.
import matplotlib.pyplot as plt # A plotting library used for visualizations.

# File paths for S&P 500 and Gold data
file_path1 = r"D:\candles\bt 240.csv" # S&P 500
file_path2 = r"D:\candles\et 240.csv"  # NASDAQ
file_path3 = r"D:\candles\do 240.csv"  # NASDAQ


 # dow jones

# Load the data
try:
    data1 = pd.read_csv(file_path1)
    data2 = pd.read_csv(file_path2)
    data3 = pd.read_csv(file_path3)
except Exception as e:
    print("Error loading data:", e)
    exit()

# Create a DataFrame with the 'Close' prices of all datasets
combined_df = pd.DataFrame({
    'bitcoin': data1['close'],  # S&P 500
    'etherium ': data2['close'],  # NASDAQ
    'dollar': data3['close'],  # dow
    "eth": data4["close"], # eth
})


# Drop rows with missing values
combined_df = combined_df.dropna()

# Calculate the daily returns for each variable
returns = combined_df.pct_change(fill_method=None).dropna()

# Calculate the correlation matrix
correlation_matrix = returns.corr()
correlation_matrix_percentage = correlation_matrix * 100

# Print the correlation matrix
print("Correlation Matrix  (as percentage):")
print(correlation_matrix)
print("-----------------------------------------------")

# Visualize the correlation matrix with a heatmap
plt.figure(figsize=(8, 3))
sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap='RdYlGn',  # Red for negative, white for neutral, green for positive
    center=0,       # Set the midpoint for white
    fmt='.2f',
    linewidths=0.5
)
plt.title('Correlation Matrix of currencies 240min')

# Save the plot as a file (e.g., PNG) in the desired directory
save_path = r"D:\PNL output\correlation of currencies 240min.png"  # Update the path here
plt.savefig(save_path)

# Show the plot
plt.show()

print(f"Heatmap saved ")

