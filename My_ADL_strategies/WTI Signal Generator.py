# ========================
# 1. Import Required Libraries
# ========================
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ========================
# 2. Load WTI Price Data from CSV
# ========================
# Make sure the CSV file is in the same folder, or give full path
df = pd.read_csv(r"D:\\Data\\GC Jun25_daily.csv", parse_dates=["Date"])
df = df.sort_values("Date")  # Ensure data is in date order

# ========================
# 3. Calculate Technical Indicators
# ========================
# Relative Strength Index (RSI)
df["rsi"] = RSIIndicator(close=df["Close"]).rsi()

# Moving Average Convergence Divergence (MACD)
macd = MACD(close=df["Close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

# Simple Moving Average (SMA) for trend analysis
df["sma"] = SMAIndicator(close=df["Close"], window=14).sma_indicator()

# Exponential Moving Average (EMA)
df["ema"] = EMAIndicator(close=df["Close"], window=14).ema_indicator()

# Bollinger Bands for volatility
bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
df["bb_upper"] = bb.bollinger_hband()
df["bb_lower"] = bb.bollinger_lband()

# ========================
# 4. Drop Initial Rows with Missing Values
# ========================
df.dropna(inplace=True)

# ========================
# 5. Create the Target Column (BUY = 1 if next day Close > today)
# ========================
df["target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

# ========================
# 6. Prepare Features and Labels
# ========================
features = ["rsi", "macd", "macd_signal", "sma", "ema", "bb_upper", "bb_lower"]
X = df[features]  # Features for training
y = df["target"]  # Binary target (1 = BUY, 0 = SELL)

# ========================
# 7. Split the Data into Training and Test Sets
# ========================
X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

# ========================
# 8. Train the Random Forest Classifier
# ========================
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ========================
# 9. Make Predictions on Test Set
# ========================
y_pred = model.predict(X_test)
df.loc[X_test.index, "prediction"] = y_pred  # Store predictions in DataFrame

# ========================
# 10. Save Predictions to CSV File
# ========================
df[["Date", "Close", "target", "prediction"]].to_csv("wti_predictions.csv", index=False)

# ========================
# 11. Evaluate the Model
# ========================
print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))
