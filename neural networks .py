# =====================================
#  Neural Network TRADING MODEL 
# =================================

import os
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from keras.models import Sequential
from keras.layers import Dense
# import tensorflow as tf
import warnings
warnings.filterwarnings("ignore")

# ------------------------- data path  -------------------------
FILE = r"C:\Users\lenovo\Desktop\Dummy.csv"      
SEED = 42     # change seed here for consistent repeatable results

# ------------------------- FIX RANDOMNESS -------------------------
os.environ['PYTHONHASHSEED'] = str(SEED)
np.random.seed(SEED)
random.seed(SEED)
tf.random.set_seed(SEED)
tf.config.experimental.enable_op_determinism()  

# ------------------------- DATA -------------------------
df = pd.read_csv(FILE)
df.columns = [c.strip().lower().replace('\u200b','').replace('\xa0','') for c in df.columns]

date_col = next((c for c in df.columns if "date" in c), None)
if not date_col:
    raise ValueError("No date column found.")
df.rename(columns={date_col: 'date'}, inplace=True)

df['date'] = pd.to_datetime(df['date'], errors='coerce')
df.dropna(subset=['date'], inplace=True)
df.set_index('date', inplace=True)
df.sort_index(inplace=True)

if 'close' not in df.columns:
    raise ValueError("No 'close' column found.")

price = df['close'].astype(float)
df['return'] = price.pct_change()

# ------------------------- indicators -------------------------
df['sma_10'] = price.rolling(10).mean()
df['sma_20'] = price.rolling(20).mean()

delta = price.diff()
up = delta.clip(lower=0)
down = -delta.clip(upper=0)
rs = up.rolling(14).mean() / down.rolling(14).mean().replace(0, np.nan)
df['rsi'] = 100 - (100 / (1 + rs))

ema12 = price.ewm(span=12, adjust=False).mean()
ema26 = price.ewm(span=26, adjust=False).mean()
df['macd'] = ema12 - ema26

df.dropna(inplace=True)

# Target: 1 if next close > current close, else 0
df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
df = df[:-1]

# ------------------------- SPLIT -------------------------
features = ['return', 'sma_10', 'sma_20', 'rsi', 'macd']
X = df[features]
y = df['target']

split = int(0.8 * len(df))
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# ------------------------- MODEL -------------------------
model = Sequential([
    Dense(128, activation='relu', input_dim=X.shape[1]),
    Dense(128, activation='relu'),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

history = model.fit(
    X_train, y_train,
    epochs=20, batch_size=16,
    validation_split=0.1,
    verbose=1  # silent training (set to 1 to see progress)
)

# ------------------------- EVALUATION -------------------------
y_pred_proba = model.predict(X_test).flatten()
y_pred = (y_pred_proba > 0.5).astype(int)

print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.show()

# ------------------------- BACKTEST ----------------------
test = df.iloc[split:].copy()
test['pred'] = y_pred
test['strategy_ret'] = test['pred'].shift(1) * test['return']
test.dropna(inplace=True)

market_cum = (1 + test['return']).cumprod()
strategy_cum = (1 + test['strategy_ret']).cumprod()

plt.plot(market_cum, label='Market Return')
plt.plot(strategy_cum, label='Neural network Strategy')
plt.legend()
plt.title('Cumulative Returns')
plt.show()

print(f"\nFinal Strategy Return: {(strategy_cum.iloc[-1]-1)*100:.2f}%")
print(f"Final Market Return: {(market_cum.iloc[-1]-1)*100:.2f}%")

# ------------------------- Train chart -------------------------
plt.figure(figsize=(8,4))
plt.plot(history.history['accuracy'], label='Train Acc')
plt.plot(history.history['val_accuracy'], label='Validation Acc')
plt.title('Accuracy Curve')
plt.legend()
plt.show()

# ------------------------- Signal Chart -------------------------
plt.figure(figsize=(12, 6))
plt.plot(test.index, test['close'], label='Close Price', color='gray', alpha=0.7)

# Buy signals (pred = 1)
buy_signals = test[test['pred'] == 1]
plt.scatter(buy_signals.index, buy_signals['close'], label='Buy Signal', marker='^', color='green', s=70)

# Sell signals (pred = 0)
sell_signals = test[test['pred'] == 0]
plt.scatter(sell_signals.index, sell_signals['close'], label='Sell Signal', marker='v', color='red', s=70)

plt.title("Neural Network Generated Buy/Sell Signals")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ------------------------- signal chart -------------------------
plt.figure(figsize=(12, 6))
plt.plot(test.index, test['close'], label='Close Price', color='gray', alpha=0.6)
plt.plot(test.index, test['sma_10'], label='SMA 10', color='blue', linewidth=1.2)
# plt.plot(test.index, test['sma_20'], label='SMA 20', color='orange', linewidth=1.2)

ema12 = test['close'].ewm(span=12, adjust=False).mean()
ema26 = test['close'].ewm(span=26, adjust=False).mean()
plt.plot(test.index, ema12, label='EMA 12', color='green', linewidth=1)
# plt.plot(test.index, ema26, label='EMA 26', color='red', linewidth=1)

buy_signals = test[test['pred'] == 1]
sell_signals = test[test['pred'] == 0]

plt.scatter(buy_signals.index, buy_signals['close'], label='Buy Signal', marker='^', color='lime', s=70)
plt.scatter(sell_signals.index, sell_signals['close'], label='Sell Signal', marker='v', color='red', s=70)

plt.title("Neural Network Buy/Sell Signals with SMA & EMA")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()


