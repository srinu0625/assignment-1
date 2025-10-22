import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ======================================
# CONFIGURATION
# ======================================
product_pairs = {
    "ES": (r"D:\ES 60min.csv", r"D:\ES s.csv"),
    "NQ": (r"D:\NQ 60min.csv", r"D:\NQ s.csv")
}

target_cols = ["Open", "High", "Close"]
no_of_candles = 120
summary = []

def safe_slope(x, y):
    if len(x) < 3:
        return np.nan
    try:
        return np.polyfit(x, y, 1)[0]
    except Exception:
        return np.nan

# ======================================
# FUNCTION: Train & Process Product
# ======================================
def process_product(symbol, file_path):
    print(f"\n==============================")
    print(f" Processing {symbol}")
    print(f"==============================")

    # Read CSV safely with proper parsing
    try:
        df = pd.read_csv(file_path, sep=",", engine="python")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Parse date column — custom format like 30-05-2022 5.00
    if "Date(GMT)" in df.columns:
        try:
            df["Date(GMT)"] = pd.to_datetime(
                df["Date(GMT)"], format="%d-%m-%Y %H.%M", errors="coerce"
            )
        except Exception:
            df["Date(GMT)"] = pd.to_datetime(df["Date(GMT)"], errors="coerce")
    else:
        print(f"⚠️ Date(GMT) column missing in {symbol}")
        return None

    df = df.dropna(subset=["Date(GMT)"]).sort_values("Date(GMT)").reset_index(drop=True)
    print(f"Loaded {symbol} → shape: {df.shape}, date range: {df['Date(GMT)'].min()} to {df['Date(GMT)'].max()}")

    if len(df) < 100:
        print(f"⚠️ Skipping {symbol} — not enough data ({len(df)} rows).")
        return None

    usable_rows = len(df) - 50
    n = min(no_of_candles, max(5, usable_rows // 5))

    # Lag Features
    for i in range(1, n + 1):
        df[f"lag_{i}"] = df["Close"].shift(i)
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()

    # RSI
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 200 - (200 / (1 + rs))
    df = df.dropna().reset_index(drop=True)

    if len(df) < 60:
        print(f"⚠️ Skipping {symbol} — insufficient rows after feature creation.")
        return None

    features = [f"lag_{i}" for i in range(1, n + 1)] + ["MA5", "MA10", "RSI"]
    X = df[features]
    y = df[target_cols]

    # Split
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Model
    model = MultiOutputRegressor(RandomForestRegressor(n_estimators=300, random_state=42))
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae_each = mean_absolute_error(y_test, y_pred, multioutput="raw_values")

    print(f"MAE → Open: {mae_each[0]:.4f}, High: {mae_each[1]:.4f}, Close: {mae_each[2]:.4f}")

    last_row = df.iloc[-1]
    next_pred = model.predict(last_row[features].to_frame().T)[0]
    print(f"Next Candle Prediction → Open: {next_pred[0]:.2f}, High: {next_pred[1]:.2f}, Close: {next_pred[2]:.2f}")

    summary.append({
        "Product": symbol,
        "MAE_Open": mae_each[0],
        "MAE_High": mae_each[1],
        "MAE_Close": mae_each[2],
        "Pred_Open": next_pred[0],
        "Pred_High": next_pred[1],
        "Pred_Close": next_pred[2]
    })

    # Return only Date + OHLC renamed
    df_renamed = df[["Date(GMT)"] + target_cols].rename(columns={c: f"{symbol}_{c}" for c in target_cols})
    return df_renamed

# ======================================
# OUTRIGHT VS SPREAD ANALYSIS
# ======================================
pair_results = {}

for sym, (outright_path, spread_path) in product_pairs.items():
    outright = process_product(f"{sym}_Outright", outright_path)
    spread = process_product(f"{sym}_Spread", spread_path)

    if outright is not None and spread is not None:
        try:
            outright = outright.set_index("Date(GMT)").resample("60min").last().dropna().reset_index()
            spread = spread.set_index("Date(GMT)").resample("60min").last().dropna().reset_index()
            print(f"After resample {sym} outright shape: {outright.shape}, spread shape: {spread.shape}")
        except Exception as e:
            print(f"Resample failed for {sym}: {e}")

        merged = pd.merge_asof(
            outright, spread, on="Date(GMT)",
            direction="nearest", tolerance=pd.Timedelta("2h")
        )
        merged = merged.dropna().reset_index(drop=True)
        pair_results[sym] = merged
        print(f"✅ Merged {sym} outright vs spread shape: {merged.shape}")
    else:
        print(f"❌ Skipping {sym} — missing outright or spread data.")

# ======================================
# HEATMAPS FOR OUTRIGHT VS SPREAD
# ======================================
for sym, df in pair_results.items():
    print(f"\n📊 Generating Heatmaps for {sym} Outright vs Spread")

    if df.empty:
        print(f"⚠️ Merged dataframe for {sym} is empty — skipping heatmaps.")
        continue

    returns = df.copy()
    for col in df.columns:
        if col != "Date(GMT)":
            returns[col] = df[col].pct_change()
    returns = returns.dropna().reset_index(drop=True)

    if returns.empty:
        print(f"⚠️ No returns for {sym} after pct_change — skipping heatmaps.")
        continue

    cols = [c for c in df.columns if c != "Date(GMT)"]

    corr_matrix = returns[cols].corr()
    z_scores = (returns[cols] - returns[cols].mean()) / returns[cols].std()
    z_matrix = z_scores.corr()

    hedge_matrix = pd.DataFrame(np.nan, index=cols, columns=cols)
    for i in cols:
        for j in cols:
            valid = returns[[i, j]].dropna()
            if len(valid) >= 3:
                slope = safe_slope(valid[j].values, valid[i].values)
                hedge_matrix.loc[i, j] = slope
            elif i == j:
                hedge_matrix.loc[i, j] = 1.0
            else:
                hedge_matrix.loc[i, j] = np.nan

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(f"{sym} Outright vs Spread Relationships", fontsize=12, fontweight="bold")

    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="YlGnBu", ax=axes[0], annot_kws={"size":8})
    axes[0].set_title("Correlation")

    sns.heatmap(z_matrix, annot=True, fmt=".2f", cmap="RdBu_r", ax=axes[1], annot_kws={"size":8})
    axes[1].set_title("Z-Score Correlation")

    sns.heatmap(hedge_matrix, annot=True, fmt=".2f", cmap="Greens", ax=axes[2], annot_kws={"size":8}, cbar_kws={"label":"Hedge Slope"})
    axes[2].set_title("Hedge Ratios (slope)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show(block=True)

# ======================================
# SUMMARY OUTPUT
# ======================================
summary_df = pd.DataFrame(summary)
print("\n===== MODEL SUMMARY =====")
print(summary_df.round(3))
