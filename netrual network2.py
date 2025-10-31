# =====================================
# NEURAL NETWORK TRADING ON CSV (WITH DIAGNOSTICS & PLOTS)
# =====================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from keras.models import Sequential
from keras.layers import Dense
import warnings
warnings.filterwarnings("ignore")

# -------------------------
# CONFIG
# -------------------------
file_path = r"D:\data\ES Daily.csv"   # <-- change to your path
np.random.seed(42)

# -------------------------
# LOAD CSV
# -------------------------
df = pd.read_csv(file_path)

# Clean headers (remove hidden chars, lowercase)
df.columns = [c.strip().replace('\u200b','').replace('\xa0','').lower() for c in df.columns]
print("Cleaned Columns:", list(df.columns))

# Detect date column automatically
date_col = None
for c in df.columns:
    if "date" in c:
        date_col = c
        break
if date_col is None:
    raise ValueError("No date column found in CSV headers. Columns: " + ", ".join(df.columns))
print("Using date column:", date_col)

# Keep consistent column names used later
# If your file already uses lowercase names like 'open','close' this will still work
df.rename(columns={date_col: 'date', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}, inplace=True)

# Parse date and set index
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df.dropna(subset=['date'], inplace=True)
df.set_index('date', inplace=True)
df.sort_index(inplace=True)

# If 'close' is not present or named differently, raise early
if 'close' not in df.columns:
    raise ValueError("No 'Close' or 'close' column found in CSV. Columns: " + ", ".join(df.columns))

# -------------------------
# FEATURE ENGINEERING
# -------------------------
# core price series
price = df['close'].astype(float).copy()

# returns
df['return'] = price.pct_change()

# moving averages (simple)
df['sma_10'] = price.rolling(10).mean()
df['sma_20'] = price.rolling(20).mean()
df['sma_50'] = price.rolling(50).mean()   # extra SMA for plotting

# a simple RSI proxy (not exact TA-lib but serviceable)
# We compute RSI on price changes (standard 14)
delta = price.diff()
up = delta.clip(lower=0)
down = -1 * delta.clip(upper=0)
roll_up = up.rolling(14).mean()
roll_down = down.rolling(14).mean()
rs = roll_up / (roll_down.replace(0, np.nan))
df['rsi'] = 100 - (100 / (1 + rs))

# MACD (12-26 ema minus)
ema12 = price.ewm(span=12, adjust=False).mean()
ema26 = price.ewm(span=26, adjust=False).mean()
df['macd'] = ema12 - ema26

# drop rows with NaN from indicators
df.dropna(inplace=True)

# -------------------------
# TARGET (next day direction)
# -------------------------
# target = 1 if next day's close > today's close, else 0
df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
# drop last row which will have NaN target
df = df[:-1]

# -------------------------
# FEATURE MATRIX & SPLIT
# -------------------------
features = ['return', 'sma_10', 'sma_20', 'rsi', 'macd']
X = df[features].copy()
y = df['target'].copy()

split = int(0.8 * len(df))
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# scale features
sc = StandardScaler()
X_train_scaled = sc.fit_transform(X_train)
X_test_scaled = sc.transform(X_test)

# -------------------------
# MODEL (capture history for plots)
# -------------------------
model = Sequential([
    Dense(128, activation='relu', input_dim=X.shape[1]),
    Dense(128, activation='relu'),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Use validation_split to get validation curves (10% of training used for validation)
history = model.fit(X_train_scaled, y_train, epochs=20, batch_size=16, verbose=1, validation_split=0.1)

# -------------------------
# PREDICTIONS
# -------------------------
y_pred_proba = model.predict(X_test_scaled).flatten()
y_pred = (y_pred_proba > 0.5).astype(int)

# -------------------------
# METRICS & CONFUSION MATRIX
# -------------------------
acc = accuracy_score(y_test, y_pred)
print("\nModel Accuracy on test set: {:.4f}".format(acc))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
print("Confusion matrix:\n", cm)
# -------------------------
# BUILD test_df for plotting/backtest alignment
# -------------------------
test_df = df.iloc[split:].copy()
test_df['y_true'] = y_test
test_df['y_pred'] = y_pred
test_df['y_pred_proba'] = y_pred_proba
test_df['predicted_signal'] = test_df['y_pred']
test_df['strategy_ret'] = test_df['predicted_signal'].shift(1) * test_df['return']
test_df.dropna(inplace=True)

# cumulative returns
cumulative_market = (1 + test_df['return']).cumprod()
cumulative_strategy = (1 + test_df['strategy_ret']).cumprod()

# -------------------------
# PLOTS
# -------------------------
# plt.style.use('seaborn-darkgrid')

# 1) Training / validation loss & accuracy curves
plt.figure(figsize=(10,4))
plt.plot(history.history['loss'], label='train loss')
plt.plot(history.history['val_loss'], label='val loss')
plt.title('Training & Validation Loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(history.history['accuracy'], label='train acc')
plt.plot(history.history['val_accuracy'], label='val acc')
plt.title('Training & Validation Accuracy')
plt.xlabel('Epoch')
plt.legend()
plt.show()

# 2) Confusion Matrix heatmap
plt.figure(figsize=(5,4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()

# 3) Actual vs Predicted signals (binary)
plt.figure(figsize=(12,4))
plt.plot(test_df.index, test_df['y_true'], label='Actual (1=up)', alpha=0.8)
plt.plot(test_df.index, test_df['y_pred'], label='Predicted (1=up)', alpha=0.6)
plt.title('Actual vs Predicted Signals (Test Set)')
plt.legend()
plt.show()

# 4) Price with SMAs and predicted long markers
plt.figure(figsize=(12,5))
plt.plot(test_df.index, test_df['close'], label='Close Price')
plt.plot(test_df.index, test_df['sma_10'], label='SMA 10', linewidth=0.9)
plt.plot(test_df.index, test_df['sma_50'], label='SMA 50', linewidth=0.9)
# plot markers where predicted signal = 1 (long next day)
longs = test_df[test_df['predicted_signal'] == 1]
plt.scatter(longs.index, longs['close'], marker='^', s=50, label='Predicted Long', zorder=3)
plt.title('Price with SMAs and Predicted Long Signals')
plt.legend()
plt.show()

# 5) Cumulative returns: Market vs Strategy
plt.figure(figsize=(10,5))
plt.plot(cumulative_market, label='Market Return')
plt.plot(cumulative_strategy, label='NN Strategy')
plt.title('Cumulative Returns : Market vs NN Strategy')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.legend()
plt.show()

# -------------------------
# Final numeric summary
# -------------------------
print("\nFinal Strategy Return: {:.2f}%".format((cumulative_strategy.iloc[-1]-1)*100))
print("Final Market Return: {:.2f}%".format((cumulative_market.iloc[-1]-1)*100))
