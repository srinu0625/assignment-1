import yfinance as yf
import pandas as pd
from datetime import datetime

# ==== ETF Proxies for Futures ====
tickers = {
    "ES_proxy": "SPY",   # S&P 500 ETF
    "NQ_proxy": "QQQ",   # Nasdaq 100 ETF
    "YM_proxy": "DIA",   # Dow Jones ETF
    "CL_proxy": "USO"    # Crude Oil ETF
}

# ==== Date range ====
start_date = "2025-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

data = {}
for name, ticker in tickers.items():
    df = yf.download(ticker, start=start_date, end=end_date, interval="1d")
    df.reset_index(inplace=True)
    data[name] = df
    print(f"\n{name} ({ticker}) Data from {start_date} to {end_date}:")
    print(df.head())

# ==== Save to CSV ====
for name, df in data.items():
    df.to_csv(f"{name}_2025.csv", index=False)
