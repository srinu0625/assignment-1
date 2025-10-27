import pandas as pd
import pandas_datareader.data as web
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import warnings
warnings.filterwarnings("ignore")

# ======================================
# CONFIGURATION
# ======================================
symbol_stooq = "^SPX"  # S&P 500 Index (close proxy for ES futures)
start = datetime.datetime(2024, 1, 1)
end = datetime.datetime(2025, 10, 27)
target_cols = ["Open", "High", "Close"]
no_of_candles = 50

print("=======================================")
print(" Fetching S&P 500 Data (from Stooq API)")
print("=======================================")

# ======================================
# FETCH DATA (NO API KEY NEEDED)
# ======================================
try:
    df = web.DataReader(symbol_stooq, "stooq", start, end)
    df = df.sort_index()
    print(f"✅ Data fetched successfully from Stooq ({len(df)} rows)")
except Exception as e:
    raise SystemExit(f"❌ Failed to fetch data from Stooq: {e}")

# Optionally save data locally
df.to_csv("SP500_from_Stooq.csv")

# ======================================
# BASIC CLEANUP (match your CSV structure)
# ======================================
df = df.reset_index().rename(columns={"Date": "Date(GMT)"})
print(f"Loaded {len(df)} rows from Stooq source.")

# ======================================
# ADAPTIVE LAG SELECTION
# ======================================
usable_rows = len(df) - 50
no_of_candles = min(no_of_candles, max(5, usable_rows // 5))
print(f"Using {no_of_candles} lag candles (auto-adjusted based on data size).")

# ======================================
# FEATURE CREATION
# ======================================
for i in range(1, no_of_candles + 1):
    df[f"lag_{i}"] = df["Close"].shift(i)

df["MA5"] = df["Close"].rolling(5).mean()
df["MA10"] = df["Close"].rolling(10).mean()

# RSI (14-period)
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 200 - (200 / (1 + rs))

df = df.dropna().reset_index(drop=True)

if len(df) < 60:
    raise ValueError(f"❌ Not enough rows ({len(df)}) after feature creation. "
                     "Please fetch more data or reduce lag count.")

# ======================================
# DEFINE FEATURES & TARGET
# ======================================
features = [f"lag_{i}" for i in range(1, no_of_candles + 1)] + ["MA5", "MA10", "RSI"]
X = df[features]
y = df[target_cols]

# ======================================
# TRAIN-TEST SPLIT
# ======================================
split_idx = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

if len(X_train) < 30 or len(X_test) < 10:
    print("⚠️ Warning: Very small dataset; predictions may be rough.")

# ======================================
# TRAIN MODEL
# ======================================
base_model = RandomForestRegressor(n_estimators=300, random_state=42)
model = MultiOutputRegressor(base_model)
model.fit(X_train, y_train)

# ======================================
# PREDICT & EVALUATE
# ======================================
y_pred = model.predict(X_test)
mae_each = mean_absolute_error(y_test, y_pred, multioutput='raw_values')

print(f"\nMean Absolute Errors:")
print(f"  Open:  {mae_each[0]:.4f}")
print(f"  High:  {mae_each[1]:.4f}")
print(f"  Close: {mae_each[2]:.4f}")

# ======================================
# NEXT-CANDLE PREDICTION
# ======================================
last_row = df.iloc[-1]
future_input = last_row[features].to_frame().T
next_pred = model.predict(future_input)[0]

print("\n=== Predicted Next Candle Prices ===")
print(f"Next Open:  {next_pred[0]:.2f}")
print(f"Next High:  {next_pred[1]:.2f}")
print(f"Next Close: {next_pred[2]:.2f}")

# ======================================
# PLOT RESULTS
# ======================================
if len(y_test) > 0:
    fig, axes = plt.subplots(3, 1, figsize=(9, 6), sharex=True)
    cols = ["Open", "High", "Close"]
    colors = ['blue', 'green', 'orange']

    for i, col in enumerate(cols):
        axes[i].plot(df["Date(GMT)"].iloc[split_idx:], y_test[col],
                     label=f"Actual {col}", linewidth=2)
        axes[i].plot(df["Date(GMT)"].iloc[split_idx:], y_pred[:, i],
                     label=f"Predicted {col}", linestyle="--", color=colors[i])
        axes[i].set_title(f"{col} Price Prediction (Test Set)")
        axes[i].set_ylabel("Price")
        axes[i].legend()
        axes[i].grid(True)

    axes[-1].set_xlabel("Date")
    axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ Skipping plot — not enough test data.")
