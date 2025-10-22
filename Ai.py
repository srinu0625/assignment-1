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
# Outright and Spread pairs for comparison
product_pairs = {
    "NQ": (r"C:\Users\lenovo\Downloads\NQ 60min (2).csv", r"C:\Users\lenovo\Downloads\NQ s.csv"),
    "ES": (r"C:\Users\lenovo\Downloads\ES 60min (2).csv", r"C:\Users\lenovo\Downloads\ES s.csv")
}

target_cols = ["Open", "High", "Close"]
no_of_candles = 120
summary = []

# ======================================
# FUNCTION: Train & Process Product
# ======================================
def process_product(symbol, file_path):
    print(f"\n==============================")
    print(f" Processing {symbol}")
    print(f"==============================")

    df = pd.read_csv(file_path)
    df["Date(GMT)"] = pd.to_datetime(df["Date(GMT)"], errors="coerce", infer_datetime_format=True)
    df = df.dropna(subset=["Date(GMT)"]).sort_values("Date(GMT)").reset_index(drop=True)

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
        merged = pd.merge_asof(
            outright, spread, on="Date(GMT)",
            direction="nearest", tolerance=pd.Timedelta("10min")
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

    returns = df.copy()
    for col in df.columns:
        if col != "Date(GMT)":
            returns[col] = df[col].pct_change()
    returns = returns.dropna().reset_index(drop=True)

    cols = [c for c in df.columns if c != "Date(GMT)"]

    corr_matrix = returns[cols].corr()
    z_scores = (returns[cols] - returns[cols].mean()) / returns[cols].std()
    z_matrix = z_scores.corr()
    hedge_matrix = pd.DataFrame(np.zeros((len(cols), len(cols))), index=cols, columns=cols)

    for i in cols:
        for j in cols:
            valid = returns[[i, j]].dropna()
            hedge_matrix.loc[i, j] = (
                1 if i == j else np.polyfit(valid[j], valid[i], 1)[0]
            )

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(f"{sym} Outright vs Spread Relationships", fontsize=12, fontweight="bold")

    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="YlGnBu", ax=axes[0])
    axes[0].set_title("Correlation")

    sns.heatmap(z_matrix, annot=True, fmt=".2f", cmap="RdBu_r", ax=axes[1])
    axes[1].set_title("Z-Score Correlation")

    sns.heatmap(hedge_matrix, annot=True, fmt=".2f", cmap="Greens", ax=axes[2])
    axes[2].set_title("Hedge Ratios")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


# ======================================
# SUMMARY OUTPUT
# ======================================
summary_df = pd.DataFrame(summary)
print("\n===== MODEL SUMMARY =====")
print(summary_df.round(3))
