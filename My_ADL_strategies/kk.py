import pandas as pd
import pandas_ta as ta

# Load data
df = pd.read_csv("data.csv")  # Replace with your file
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# --- Indicators ---
# MACD
df['macd'], df['macd_signal'], _ = ta.macd(df['Close'], fast=12, slow=26, signal=9)

# RSI 14
df['rsi_14'] = ta.rsi(df['Close'], length=14)

# EMA 14
df['ema_14'] = ta.ema(df['Close'], length=14)

# Modified EMA_RSI logic: EMA(14) × RSI(14)
df['ema_rsi_mod'] = df['ema_14'] * df['rsi_14']

# ATR 14
df['atr_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

# --- Backtest variables ---
position = None
entry_price = 0
stop_loss = 0
target = 0

for i in range(1, len(df)):
    # --- LONG ENTRY ---
    if position is None and df['macd'].iloc[i] > df['macd_signal'].iloc[i] and df['ema_rsi_mod'].iloc[i] < 50:
        position = 'long'
        entry_price = df['Close'].iloc[i]
        stop_loss = entry_price - 2 * df['atr_14'].iloc[i]
        target = entry_price + 3 * df['atr_14'].iloc[i]
        print(f"{df.index[i]}: Long Entry at {entry_price:.2f} | SL: {stop_loss:.2f} | Target: {target:.2f}")

    # --- SHORT ENTRY ---
    elif position is None and df['macd'].iloc[i] < df['macd_signal'].iloc[i] and df['ema_rsi_mod'].iloc[i] > 50:
        position = 'short'
        entry_price = df['Close'].iloc[i]
        stop_loss = entry_price + 2 * df['atr_14'].iloc[i]
        target = entry_price - 3 * df['atr_14'].iloc[i]
        print(f"{df.index[i]}: Short Entry at {entry_price:.2f} | SL: {stop_loss:.2f} | Target: {target:.2f}")

    # --- LONG EXIT ---
    elif position == 'long':
        if df['Close'].iloc[i] <= stop_loss:
            print(f"{df.index[i]}: Long Exit at {df['Close'].iloc[i]:.2f} | Reason: Stop Loss Hit")
            position = None
        elif df['Close'].iloc[i] >= target:
            print(f"{df.index[i]}: Long Exit at {df['Close'].iloc[i]:.2f} | Reason: Target Hit")
            position = None

    # --- SHORT EXIT ---
    elif position == 'short':
        if df['Close'].iloc[i] >= stop_loss:
            print(f"{df.index[i]}: Short Exit at {df['Close'].iloc[i]:.2f} | Reason: Stop Loss Hit")
            position = None
        elif df['Close'].iloc[i] <= target:
            print(f"{df.index[i]}: Short Exit at {df['Close'].iloc[i]:.2f} | Reason: Target Hit")
            position = None
