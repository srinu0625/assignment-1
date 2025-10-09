import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")

# ======== CONFIG DATA =========
file_path = r"D:\Data\BR daily.csv"   # path to your file
target_cols = ["Open", "High", "Close"]
No_of_candles = 7  # desired max candles

# ======== LOAD DATA ===============
df = pd.read_csv(file_path)
df["Date(GMT)"] = pd.to_datetime(df["Date(GMT)"], format="%d-%m-%Y %H.%M", errors="coerce")
df = df.dropna(subset=["Date(GMT)"]).sort_values("Date(GMT)").reset_index(drop=True)

print(f"Loaded {len(df)} rows from file.")

# ======== ADAPTIVE LAG SELECTION =========
usable_rows = len(df) - 50  # keep some for training/testing
no_of_candles = min(No_of_candles, max(5, usable_rows // 5))
print(f"Using {no_of_candles} lag candles (auto-adjusted based on data size).")

# ======== FEATURE CREATION ========= 
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
                     "Please provide more historical data or reduce lag count.")

# ======== DEFINE FEATURES & TARGET =========
features = [f"lag_{i}" for i in range(1, no_of_candles + 1)] + ["MA5", "MA10", "RSI"]
X = df[features]
y = df[target_cols]

# ======== TRAIN-TEST SPLIT =========
split_idx = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

if len(X_train) < 30 or len(X_test) < 10:
    print("⚠️ Warning: Very small dataset; predictions may be rough.")

# ======== TRAIN MODEL =========
base_model = RandomForestRegressor(n_estimators=300, random_state=42)
model = MultiOutputRegressor(base_model)
model.fit(X_train, y_train)

# ======== PREDICT & EVALUATE =========
y_pred = model.predict(X_test)
mae_each = mean_absolute_error(y_test, y_pred, multioutput='raw_values')

print(f"\nMean Absolute Errors:")
print(f"  Open:  {mae_each[0]:.4f}")
print(f"  High:  {mae_each[1]:.4f}")
print(f"  Close: {mae_each[2]:.4f}")

# ======== NEXT-CANDLE PREDICTION =========
last_row = df.iloc[-1]
future_input = last_row[features].to_frame().T
next_pred = model.predict(future_input)[0]

print("\n=== Predicted Next Candle Prices ===")
print(f"Next Open:  {next_pred[0]:.2f}")
print(f"Next High:  {next_pred[1]:.2f}")
print(f"Next Close: {next_pred[2]:.2f}")

# ======== PLOT RESULTS =========
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
