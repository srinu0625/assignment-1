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
products = {
    "BR": r"D:\BR 240min.csv",
    "CL": r"D:\CL 240min.csv",
    "ES": r"D:\ES 240min.csv"
}

target_cols = ["Open", "High", "Close"]
no_of_candles = 120

# Data storage
combined_data = pd.DataFrame()
summary = []


# ======================================
# FUNCTION: Process each product
# ======================================
def process_product(symbol, file_path):
    print(f"\n==============================")
    print(f" Processing {symbol}")
    print(f"==============================")

    # --- Load Data ---
    df = pd.read_csv(file_path)
    df["Date(GMT)"] = pd.to_datetime(
        df["Date(GMT)"], format="%d-%m-%Y %H.%M", errors="coerce"
    )
    df = df.dropna(subset=["Date(GMT)"]).sort_values("Date(GMT)").reset_index(drop=True)

    if len(df) < 100:
        print(f"⚠️ Skipping {symbol} — not enough data ({len(df)} rows).")
        return None

    # --- Feature Creation ---
    usable_rows = len(df) - 50
    n = min(no_of_candles, max(5, usable_rows // 5))

    # Lag features
    for i in range(1, n + 1):
        df[f"lag_{i}"] = df["Close"].shift(i)

    # Moving Averages
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()

    # RSI Calculation
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 200 - (200 / (1 + rs))
    df = df.dropna().reset_index(drop=True)

    if len(df) < 60:
        print(f"⚠️ Skipping {symbol} — insufficient rows after feature creation ({len(df)}).")
        return None

    # --- Define Features & Targets ---
    features = [f"lag_{i}" for i in range(1, n + 1)] + ["MA5", "MA10", "RSI"]
    X = df[features]
    y = df[target_cols]

    # --- Train/Test Split ---
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # --- Train Model ---
    model = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=300, random_state=42)
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # --- Performance Metrics ---
    mae_each = mean_absolute_error(y_test, y_pred, multioutput="raw_values")
    print(f"MAE → Open: {mae_each[0]:.4f}, High: {mae_each[1]:.4f}, Close: {mae_each[2]:.4f}")

    # --- Next Candle Prediction ---
    last_row = df.iloc[-1]
    next_pred = model.predict(last_row[features].to_frame().T)[0]
    print(
        f"Next Candle Prediction → "
        f"Open: {next_pred[0]:.2f}, High: {next_pred[1]:.2f}, Close: {next_pred[2]:.2f}"
    )

    # --- Store Summary ---
    summary.append({
        "Product": symbol,
        "MAE_Open": mae_each[0],
        "MAE_High": mae_each[1],
        "MAE_Close": mae_each[2],
        "Pred_Open": next_pred[0],
        "Pred_High": next_pred[1],
        "Pred_Close": next_pred[2]
    })

    # --- Return for Heatmaps ---
    df_renamed = df[["Date(GMT)"] + target_cols].rename(
        columns={c: f"{symbol}_{c}" for c in target_cols}
    )
    return df_renamed


# ======================================
# RUN FOR EACH PRODUCT
# ======================================
for sym, path in products.items():
    result = process_product(sym, path)
    if result is not None:
        if combined_data.empty:
            combined_data = result
        else:
            combined_data = pd.merge_asof(
                combined_data, result, on="Date(GMT)",
                direction="nearest", tolerance=pd.Timedelta("10min")
            )

# ======================================
# SUMMARY OUTPUT
# ======================================
summary_df = pd.DataFrame(summary)
print("\n===== MODEL SUMMARY =====")
print(summary_df.round(3))


# ======================================
# COMBINED HEATMAPS
# ======================================
if combined_data.empty:
    print("❌ No data merged — exiting heatmap generation.")
else:
    combined_data = combined_data.dropna().reset_index(drop=True)
    print(f"\nMerged data shape for heatmaps: {combined_data.shape}")

    # --- Compute Returns ---
    returns = combined_data.copy()
    for col in combined_data.columns:
        if col != "Date(GMT)":
            returns[col] = combined_data[col].pct_change()
    returns = returns.dropna().reset_index(drop=True)

    # --- Matrices ---
    cols = [c for c in combined_data.columns if c != "Date(GMT)"]
    corr_matrix = returns[cols].corr()
    z_scores = (returns[cols] - returns[cols].mean()) / returns[cols].std()
    z_matrix = z_scores.corr()
    z_slope_matrix = z_scores.diff().corr()

    hedge_matrix = pd.DataFrame(np.zeros((len(cols), len(cols))),
                                index=cols, columns=cols)
    for i in cols:
        for j in cols:
            hedge_matrix.loc[i, j] = (
                1 if i == j else np.polyfit(returns[j], returns[i], 1)[0]
            )

    # --- Plot 4 Heatmaps Together ---
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))

    sns.heatmap(corr_matrix, annot=True, fmt=".2f",
                cmap="YlGnBu", ax=axes[0, 0], annot_kws={"size": 8})
    axes[0, 0].set_title("Correlation Matrix (All Products)",fontsize=9)
    axes[0, 0].tick_params(axis='x', labelsize=6)
    axes[0, 0].tick_params(axis='y', labelsize=6)
    axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

    sns.heatmap(z_matrix, annot=True, fmt=".2f",
                cmap="RdBu_r", ax=axes[0, 1], annot_kws={"size": 8})
    axes[0, 1].set_title("Z-Score Matrix (All Products)",fontsize=9)
    axes[0, 1].tick_params(axis='x', labelsize=6)
    axes[0, 1].tick_params(axis='y', labelsize=6)
    axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

    sns.heatmap(z_slope_matrix, annot=True, fmt=".2f",
                cmap="PiYG", ax=axes[1, 0], annot_kws={"size": 8})
    axes[1, 0].set_title("Z-Score Slope Matrix (All Products)",fontsize=9)
    axes[1, 0].tick_params(axis='x', labelsize=6)
    axes[1, 0].tick_params(axis='y', labelsize=6)
    axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45, ha='right')

    sns.heatmap(hedge_matrix, annot=True, fmt=".2f",
                cmap="Greens", ax=axes[1, 1], annot_kws={"size": 8})
    axes[1, 1].set_title("Hedge Ratio Matrix (All Products)",fontsize=9)
    axes[1, 1].tick_params(axis='x', labelsize=6)
    axes[1, 1].tick_params(axis='y', labelsize=6)
    axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.show()
