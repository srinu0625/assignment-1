import pandas as pd
import numpy as np
import time

# -----------------------------------------
# CONFIG
CSV_FILE = r"D:\Data\ES 30min.csv"
TP_MULTS = [2, 4, 6]      # ATR multiples for TP1/TP2/TP3
SL_MULT = 2               # ATR stop-loss
UNITS = 3                 # 3 lots
ATR_PERIOD = 14


# -----------------------------------------
# AUTO COLUMN NAME DETECTION
# -----------------------------------------
def find_col(df, options):
    """
    Find a column-name in df matching any of the possible options.
    """
    for col in df.columns:
        clean = col.replace(" ", "").replace("_", "").lower()
        for op in options:
            if clean == op.lower():
                return col
    raise ValueError(f"Could not find any of: {options}")


# -----------------------------------------
# VERBOSE PRINTING
# -----------------------------------------
def verbose_print(row, prev, position, long_cond, short_cond):
    time.sleep(5)
    print("\n" + "-" * 70)
    print(f"Time:           {row['DATETIME']}")
    print(f"O/H/L/C:        {row['Open']} / {row['High']} / {row['Low']} / {row['Close']}")
    print(f"HH50:           {row['HH50']:.4f}")
    print(f"LL50:           {row['LL50']:.4f}")
    print(f"MA24:           {row['MA24']:.4f}")
    print(f"ATR:            {row['ATR']:.5f}")
    print(f"ATR Rising?:    {row['ATR'] > prev['ATR']}")
    print(f"Long Cond:      {long_cond}")
    print(f"Short Cond:     {short_cond}")


    if position:
        print(f"Position:       {position['side']}")
        print(f"Entry Price:    {position['entry']:.4f}")
        print(f"Stop Loss:      {position['stop']:.4f}")

        # TPs
        for idx, tp in enumerate(position['tp']):
            hit = position['hit'][idx]
            print(f"TP{idx+1}:        {tp:.4f}   HIT? {hit}")

        print(f"Units Left:     {position['units']}")
    else:
        print("Position:       FLAT")

    print("-" * 70)


# -----------------------------------------
# LOAD DATA
# -----------------------------------------
df = pd.read_csv(CSV_FILE)
print(df.columns.tolist())

# Detect columns
date_col  = find_col(df, ["date(gmt)", "date", "datetime"])
open_col  = find_col(df, ["open", "openprice"])
high_col  = find_col(df, ["high", "highprice"])
low_col   = find_col(df, ["low", "lowprice"])
close_col = find_col(df, ["close", "closeprice"])

# Rename for internal ease
df = df.rename(columns={
    date_col:  "DATETIME",
    open_col:  "Open",
    high_col:  "High",
    low_col:   "Low",
    close_col: "Close"
})

# Datetime fix
df["DATETIME"] = pd.to_datetime(df["DATETIME"], format="%d-%m-%Y %H.%M") # %H.%M") add for minutes
df = df.sort_values("DATETIME").reset_index(drop=True)


# -----------------------------------------
# INDICATORS
# -----------------------------------------
df["HH50"] = df["High"].rolling(50).max()
df["LL50"] = df["Low"].rolling(50).min()
df["MA24"] = df["Close"].rolling(24).mean()

# ATR
df["H-L"]  = df["High"] - df["Low"]
df["H-PC"] = (df["High"] - df["Close"].shift()).abs()
df["L-PC"] = (df["Low"]  - df["Close"].shift()).abs()
df["TR"]   = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
df["ATR"]  = df["TR"].rolling(ATR_PERIOD).mean()

df = df.dropna().copy()


# -----------------------------------------
# BACKTEST
# -----------------------------------------
trades = []
position = None

def log_trade(side, price, qty, reason, dt):
    print(f"TRADE → {reason} | {side} | {qty} @ {price:.4f}")
    trades.append({
        "datetime": dt,
        "side": side,
        "price": price,
        "qty": qty,
        "reason": reason
    })


for i in range(1, len(df)):
    row  = df.iloc[i]
    prev = df.iloc[i-1]

    # ENTRY CONDITIONS
    atr_up = row["ATR"] > prev["ATR"]

    long_cond = (
        prev["Close"] <= prev["HH50"] and
        row["Close"] > prev["HH50"] and
        row["Close"] > row["MA24"] and
        atr_up
    )

    short_cond = (
        prev["Close"] >= prev["LL50"] and
        row["Close"] < prev["LL50"] and
        row["Close"] < row["MA24"] and
        atr_up
    )

    # PRINT EVERYTHING
    verbose_print(row, prev, position, long_cond, short_cond)

    # ----------------------------------------------------------
    # EXIT LOGIC
    # ----------------------------------------------------------
    if position:

        side = position["side"]
        stop = position["stop"]
        tps  = position["tp"]
        dt   = row["DATETIME"]

        # LONG EXIT
        if side == "long":

            if row["Low"] <= stop:
                for _ in range(position["units"]):
                    log_trade("SELL", stop, 1, "STOP LOSS", dt)
                position = None
                continue

            for idx, tp in enumerate(tps):
                if not position["hit"][idx] and row["High"] >= tp:
                    log_trade("SELL", tp, 1, f"TP{idx+1}", dt)
                    position["hit"][idx] = True
                    position["units"] -= 1

            if position["units"] == 0:
                position = None
                continue

        # SHORT EXIT
        else:

            if row["High"] >= stop:
                for _ in range(position["units"]):
                    log_trade("BUY", stop, 1, "STOP LOSS", dt)
                position = None
                continue

            for idx, tp in enumerate(tps):
                if not position["hit"][idx] and row["Low"] <= tp:
                    log_trade("BUY", tp, 1, f"TP{idx+1}", dt)
                    position["hit"][idx] = True
                    position["units"] -= 1

            if position["units"] == 0:
                position = None
                continue


    # ----------------------------------------------------------
    # ENTRY LOGIC
    # ----------------------------------------------------------
    if position is None:

        dt = row["DATETIME"]
        atr = row["ATR"]

        # LONG ENTRY
        if long_cond:
            entry = row["Close"]
            tps  = [entry + m * atr for m in TP_MULTS]
            stop = entry - SL_MULT * atr

            position = {
                "side": "long",
                "entry": entry,
                "stop": stop,
                "tp": tps,
                "units": UNITS,
                "hit": [False] * len(tps)
            }

            log_trade("BUY", entry, UNITS, "LONG ENTRY", dt)

        # SHORT ENTRY
        elif short_cond:
            entry = row["Close"]
            tps  = [entry - m * atr for m in TP_MULTS]
            stop = entry + SL_MULT * atr

            position = {
                "side": "short",
                "entry": entry,
                "stop": stop,
                "tp": tps,
                "units": UNITS,
                "hit": [False] * len(tps)
            }

            log_trade("SELL", entry, UNITS, "SHORT ENTRY", dt)


# -----------------------------------------
# RESULTS
# -----------------------------------------
trades_df = pd.DataFrame(trades)
print("\n=============== TRADES ===============")
print(trades_df)
print("======================================")
