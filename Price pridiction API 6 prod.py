import pandas as pd
import pandas_datareader.data as web
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import datetime
import warnings
warnings.filterwarnings("ignore")

# ======================================
# CONFIGURATION
# ======================================
products = {
    "ES": "^SPX",     # S&P 500 Index
    "NQ": "^NDX",     # Nasdaq 100 Index
    "YM": "^DJI",     # Dow Jones Industrial Average
    # "GC": "XAUUSD",     # Gold Futures (COMEX)
    # "SI": "XAGUSD",     # Silver Futures (COMEX)
    # "CL": "USOIL"      # Crude Oil Futures (NYMEX)
}

start = datetime.datetime(2018, 1, 1)
end = datetime.datetime(2025, 10, 27)
target_cols = ["Open", "High", "Close", "Low"]
no_of_candles = 150

# ======================================
# MASTER STORAGE
# ======================================
results_summary = []
combined_actual = pd.DataFrame()
combined_pred = pd.DataFrame()

# ======================================
# LOOP THROUGH PRODUCTS
# ======================================
for product, symbol in products.items():
    print(f"\n=======================================")
    print(f" Fetching Data for {product} ({symbol})")
    print(f"=======================================")

    # FETCH
    try:
        df = web.DataReader(symbol, "stooq", start, end)
        df = df.sort_index()
        print(f" {product} data fetched successfully ({len(df)} rows)")
    except Exception as e:
        print(f" Failed to fetch {product}: {e}")
        continue

    df = df.reset_index().rename(columns={"Date": "Date(GMT)"})

    # ADAPTIVE LAG SELECTION
    usable_rows = len(df) - 50
    lag_candles = min(no_of_candles, max(5, usable_rows // 5))

    # FEATURE CREATION
    for i in range(1, lag_candles + 1):
        df[f"lag_{i}"] = df["Close"].shift(i)

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 200 - (200 / (1 + rs))
    df = df.dropna().reset_index(drop=True)

    if len(df) < 60:
        print(f" Not enough data for {product}, skipping.")
        continue

    features = [f"lag_{i}" for i in range(1, lag_candles + 1)] + ["MA5", "MA10", "RSI"]
    X = df[features]
    y = df[target_cols]

    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    base_model = RandomForestRegressor(n_estimators=300, random_state=42)
    model = MultiOutputRegressor(base_model)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae_each = mean_absolute_error(y_test, y_pred, multioutput='raw_values')

    # Print results
    print(f"\n {product} Mean Absolute Errors:")
    print(f"  Open:  {mae_each[0]:.4f}")
    print(f"  High:  {mae_each[1]:.4f}")
    print(f"  Low:   {mae_each[2]:.4f}")
    print(f"  Close: {mae_each[3]:.4f}")

    # Next candle prediction
    last_row = df.iloc[-1]
    future_input = last_row[features].to_frame().T
    next_pred = model.predict(future_input)[0]
    print(f"\n {product} Next Candle Prediction:")
    print(f"  Open:  {next_pred[0]:.2f}")
    print(f"  High:  {next_pred[1]:.2f}")
    print(f"  Low:   {next_pred[2]:.2f}")
    print(f"  Close: {next_pred[3]:.2f}")

    # Store summary
    results_summary.append({
        "MAE_Low"    : mae_each[2],
        "Product"    : product,
        "MAE_Open"   : mae_each[0],
        "MAE_High"   : mae_each[1],
        "MAE_Close"  : mae_each[3],
        "Pred_Open"  : next_pred[0],
        "Pred_High"  : next_pred[1],
        "Pred_Low"   : next_pred[2],
        "Pred_Close" : next_pred[3]
    })

    # Append to combined for correlation
    combined_actual[f"{product}_Close_Actual"] = y_test["Close"].reset_index(drop=True)
    combined_pred[f"{product}_Close_Pred"] = pd.Series(y_pred[:, 2])

# ======================================
# SUMMARY TABLE
# ======================================
summary_df = pd.DataFrame(results_summary)
print("\n=================== SUMMARY ===================")
print(summary_df.round(3))

# ======================================
# HEATMAP ANALYSIS
# ======================================
print("\nGenerating cross-product correlation heatmaps...")

combined_actual = combined_actual.dropna()
combined_pred = combined_pred.dropna()

# 1. Correlation of actual prices
corr_actual = combined_actual.corr()

# 2. Correlation of predicted prices
corr_pred = combined_pred.corr()

# 3. Hedge ratios (slopes)
hedge_matrix = pd.DataFrame(np.zeros_like(corr_actual), 
                            columns=corr_actual.columns, index=corr_actual.columns)
for c1 in combined_actual.columns:
    for c2 in combined_actual.columns:
        if c1 != c2:
            model = LinearRegression().fit(combined_actual[[c2]], combined_actual[c1])
            hedge_matrix.loc[c1, c2] = model.coef_[0]
        else:
            hedge_matrix.loc[c1, c2] = 1.0

# ======================================
# PLOT HEATMAPS
# ======================================
fig, axes = plt.subplots(1, 3, figsize=(10, 5))

sns.heatmap(corr_actual, annot=True, fmt=".2f", cmap="YlGnBu", ax=axes[0])
axes[0].set_title("Actual Price Correlation")

sns.heatmap(corr_pred, annot=True, fmt=".2f", cmap="RdBu_r", ax=axes[1])
axes[1].set_title("Predicted Price Correlation")

sns.heatmap(hedge_matrix, annot=True, fmt=".2f", cmap="Blues", ax=axes[2],
            cbar_kws={"label": "Hedge Slope"})
axes[2].set_title("Hedge Ratios (Regression Slopes)")

plt.suptitle("Cross-Market Relationship Heatmaps (Actual vs Predicted)", fontsize=14, fontweight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()
