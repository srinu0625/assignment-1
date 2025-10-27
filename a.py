import pandas as pd
import pandas_datareader.data as web
import datetime
import matplotlib.pyplot as plt

# ============================================
# CONFIGURATION
# ============================================
symbol_yahoo = "ES=F"       # S&P 500 Futures (Yahoo)
symbol_stooq = "^SPX"       # S&P 500 Index (Stooq backup)
start = datetime.datetime(2024, 1, 1)
end = datetime.datetime(2025, 10, 27)

print("=======================================")
print(" Fetching S&P 500 Futures / Index Data ")
print("=======================================")

# ============================================
# TRY YAHOO FINANCE FIRST
# ============================================
try:
    import yfinance as yf
    print(f"Trying Yahoo Finance for {symbol_yahoo}...")
    df = yf.download(symbol_yahoo, interval="1d", start=start, end=end, progress=False)
    if df.empty:
        raise ValueError("Yahoo returned empty data")
    print("✅ Yahoo Finance data fetched successfully")
    source = "Yahoo Finance"
except Exception as e:
    print(f"⚠️ Yahoo Finance failed: {e}")
    print("Trying Stooq (no API key needed)...")
    try:
        df = web.DataReader(symbol_stooq, "stooq", start, end)
        df = df.sort_index()
        print("✅ Data fetched successfully from Stooq")
        source = "Stooq"
    except Exception as e2:
        raise SystemExit(f"❌ Both Yahoo and Stooq failed: {e2}")

# ============================================
# BASIC ANALYSIS
# ============================================
print(f"\nData Source Used → {source}")
print(f"Total Records → {len(df)}")
print("\nLast 5 Rows:")
print(df.tail())

# Calculate moving averages
df["SMA_20"] = df["Close"].rolling(window=20).mean()
df["SMA_50"] = df["Close"].rolling(window=50).mean()

# Crossover logic
df["Signal"] = 0
df.loc[df["SMA_10"] > df["SMA_30"], "Signal"] = 1
df.loc[df["SMA_10"] < df["SMA_30"], "Signal"] = -1

# Identify buy/sell points
df["Cross"] = df["Signal"].diff()
buy_signals = df[df["Cross"] == 2]
sell_signals = df[df["Cross"] == -2]

print(f"\nBuy signals: {len(buy_signals)} | Sell signals: {len(sell_signals)}")

# ============================================
# PLOT
# ============================================
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["Close"], label="Close", color="blue", linewidth=1)
plt.plot(df.index, df["SMA_10"], label="SMA 30", linestyle="--", color="green")
plt.plot(df.index, df["SMA_10"], label="SMA 30", linestyle="--", color="orange")

# Mark crossover points
plt.scatter(buy_signals.index, df.loc[buy_signals.index, "Close"],
            label="Buy", marker="^", color="lime", s=80)
plt.scatter(sell_signals.index, df.loc[sell_signals.index, "Close"],
            label="Sell", marker="v", color="red", s=80)

plt.title(f"S&P 500 Futures / Index ({source})")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
