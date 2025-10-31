# =====================================
# SIMPLE NEURAL NETWORK TRADING MODEL
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
# ------------------------- CONFIG -------------------------
FILE = r"D:\data\ES Daily.csv"
np.random.seed(65)

# ------------------------- DATA -------------------------
df = pd.read_csv(FILE)
df.columns = [c.strip().lower().replace('\u200b','').replace('\xa0','') for c in df.columns]
date_col = next((c for c in df.columns if "date" in c), None)
if date_col is None:
    raise ValueError("No date column found.")
df.rename(columns={date_col: 'date'}, inplace=True)

df['date'] = pd.to_datetime(df['date'], errors='coerce')
df.dropna(subset=['date'], inplace=True)
df.set_index('date', inplace=True)
df.sort_index(inplace=True)

if 'close' not in df.columns:
    raise ValueError("No 'close' column found.")

# ------------------------- FEATURES -------------------------
price = df['close'].astype(float)
df['return'] = price.pct_change()

df['sma_10'] = price.rolling(10).mean()
df['sma_20'] = price.rolling(20).mean()
df['sma_50'] = price.rolling(50).mean()

delta = price.diff()
up, down = delta.clip(lower=0), -delta.clip(upper=0)
rs = up.rolling(14).mean() / down.rolling(14).mean().replace(0, np.nan)
df['rsi'] = 100 - (100 / (1 + rs))

ema12, ema26 = price.ewm(span=12, adjust=False).mean(), price.ewm(span=26, adjust=False).mean()
df['macd'] = ema12 - ema26

df.dropna(inplace=True)
df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
df = df[:-1]

# ------------------------- SPLIT -------------------------
features = ['return', 'sma_10', 'sma_20', 'rsi', 'macd']
X, y = df[features], df['target']
split = int(0.8 * len(df))
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

scaler = StandardScaler()
X_train, X_test = scaler.fit_transform(X_train), scaler.transform(X_test)

# ------------------------- MODEL -------------------------
model = Sequential([
    Dense(128, activation='relu', input_dim=X.shape[1]),
    Dense(128, activation='relu'),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
history = model.fit(X_train, y_train, epochs=20, batch_size=16, validation_split=0.1, verbose=1)

# ------------------------- EVAL -------------------------
y_pred_proba = model.predict(X_test).flatten()
y_pred = (y_pred_proba > 0.5).astype(int)

print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nReport:\n", classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.show()

# ------------------------- STRATEGY BACKTEST -------------------------
test = df.iloc[split:].copy()
test['pred'] = y_pred
test['ret'] = test['return']
test['strategy_ret'] = test['pred'].shift(1) * test['ret']
test.dropna(inplace=True)

market_cum = (1 + test['ret']).cumprod()
strategy_cum = (1 + test['strategy_ret']).cumprod()

plt.plot(market_cum, label='Market Return')
plt.plot(strategy_cum, label='NN Strategy')
plt.legend(); plt.title('Cumulative Returns'); plt.show()

print(f"\nFinal Strategy Return: {(strategy_cum.iloc[-1]-1)*100:.2f}%")
print(f"Final Market Return: {(market_cum.iloc[-1]-1)*100:.2f}%")

# ------------------------- TRAIN HISTORY -------------------------
plt.figure(figsize=(10,4))
plt.plot(history.history['accuracy'], label='Train Acc')
plt.plot(history.history['val_accuracy'], label='Val Acc')
plt.title('Accuracy Curve'); plt.legend(); plt.show()
