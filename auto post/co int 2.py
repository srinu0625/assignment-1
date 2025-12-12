
    #!/usr/bin/env python3
# UNIVERSAL ATR Scaling Strategy Backtest (Intraday + Daily)

import eikon as ek
import pandas as pd
import csv
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
ek.set_app_key(APP_KEY)

RIC = "LCOc1"
START = "2024-01-01"
END = None

# --------------------------------------------
# MASTER TIMEFRAME CONTROL
# --------------------------------------------
TIMEFRAME = "60"   # 5,10,15,30,60,240 or "D"

if TIMEFRAME == "D":
    INTERVAL = "daily"
    RESAMPLE_PERIOD = "D"
else:
    INTERVAL = "minute"
    RESAMPLE_PERIOD = f"{TIMEFRAME}T"

ATR_PERIOD = 14
MA_PERIOD = 24
LOOKBACK_HHLL = 50

UNITS_PER_ENTRY = 3
SL_MULT = 2.0
TP_MULTS = [2.0, 4.0, 8.0]

LOG_CSV = "BRN_60min.csv"
DEBUG = False

# GLOBAL PNL METRICS
cum_pnl = 0.0
peak_pnl = 0.0
max_runup = 0.0
max_drawdown = 0.0


def printp(msg):
    if DEBUG:
        print(msg)


# ================================================================
# FETCH + RESAMPLE DATA
# ================================================================
def fetch_data(ric):
    print(f"[INFO] Fetching {ric} | INTERVAL={INTERVAL} | TF={TIMEFRAME}")

    df = ek.get_timeseries(
        ric,
        fields=['CLOSE', 'HIGH', 'LOW', 'OPEN', 'VOLUME'],
        start_date=START,
        end_date=END,
        interval=INTERVAL
    )

    if df is None or df.empty:
        raise RuntimeError("NO DATA RETURNED")

    df.reset_index(inplace=True)
    df.rename(columns={df.columns[0]: 'DATETIME'}, inplace=True)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], utc=True)
    df.set_index('DATETIME', inplace=True)
    df.sort_index(inplace=True)

    # intraday resample
    if TIMEFRAME != "D":
        df2 = df.resample(RESAMPLE_PERIOD, label='right', closed='right').agg({
            "OPEN": "first",
            "HIGH": "max",
            "LOW": "min",
            "CLOSE": "last",
            "VOLUME": "sum"
        })
        df2[['OPEN', 'HIGH', 'LOW', 'CLOSE']] = df2[['OPEN', 'HIGH', 'LOW', 'CLOSE']].fillna(method='ffill')
        df2['VOLUME'] = df2['VOLUME'].fillna(0)
        return df2.reset_index()

    # daily no resampling
    return df.reset_index()


# ================================================================
# INDICATORS
# ================================================================
def compute_indicators(df):
    df = df.copy()

    df['prev_close'] = df['CLOSE'].shift(1)

    # TRUE RANGE
    df['tr1'] = df['HIGH'] - df['LOW']
    df['tr2'] = (df['HIGH'] - df['prev_close']).abs()
    df['tr3'] = (df['LOW'] - df['prev_close']).abs()
    df['TR'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

    # ATR
    df['ATR'] = df['TR'].ewm(alpha=1/ATR_PERIOD, adjust=False).mean()

    # MA24
    df['MA24'] = df['CLOSE'].rolling(MA_PERIOD).mean()

    # HH50 / LL50
    df['HH50'] = df['HIGH'].rolling(LOOKBACK_HHLL).max()
    df['LL50'] = df['LOW'].rolling(LOOKBACK_HHLL).min()

    return df


# ================================================================
# RECORD TRADE
# ================================================================
def record_fill(trades, when, side, reason_title, reason_detail,
                price, qty, position_before, lot_id=None, atr=None, ma24=None):

    global cum_pnl, peak_pnl, max_runup, max_drawdown
    trade_pnl = 0.0

    # entry_price for pnl
    entry_price = position_before['entry_price'] if (position_before and "entry_price" in position_before) else None
    prior_side = position_before['side'] if position_before else ""

    # PNL only for exits
    if reason_title not in ("ENTRY", "INFO") and entry_price is not None:
        if prior_side == "long":
            trade_pnl = (price - entry_price) * qty
        else:
            trade_pnl = (entry_price - price) * qty

        cum_pnl += trade_pnl
        peak_pnl = max(peak_pnl, cum_pnl)
        max_runup = max(max_runup, cum_pnl)
        dd = cum_pnl - peak_pnl
        max_drawdown = min(max_drawdown, dd)

    qty_remaining = ""
    if position_before and "units_remaining" in position_before:
        qty_remaining = position_before['units_remaining']

    trades.append({
        "datetime": when.strftime("%Y-%m-%d %H:%M"),
        "side": side,
        "reason_title": reason_title,
        "reason_detail": reason_detail,
        "entry_price": entry_price if entry_price else "",
        "exit_price": price,
        "qty_exited": qty,
        "qty_remaining": qty_remaining,
        "position_side": prior_side,
        "ATR": atr if atr else "",
        "MA24": ma24 if ma24 else "",
        "lot_id": lot_id if lot_id else "",
        "trade_pnl": round(trade_pnl, 2),
        "cum_pnl": round(cum_pnl, 2)
    })


# ================================================================
# BACKTEST LOOP
# ================================================================
def sequential_backtest(df):
    trades = []
    position = None

    global cum_pnl, peak_pnl, max_runup, max_drawdown
    cum_pnl = peak_pnl = max_runup = max_drawdown = 0.0

    for i in range(1, len(df)):
        row = df.loc[i]
        prev = df.loc[i - 1]
        dt = row['DATETIME']

        # ------------------------------------------------------
        # EXIT LOGIC
        # ------------------------------------------------------
        if position:

            # ========== LONG EXITS ==========
            if position["side"] == "long":

                # STOP LOSS
                if row["LOW"] <= position["stop"]:
                    while position["units_remaining"] > 0:
                        lot = position["remaining_lots"].pop(0)
                        record_fill(trades, dt, "SELL", "STOP LOSS",
                                    f"LOW {row['LOW']} <= STOP {position['stop']}",
                                    position["stop"], 1, position,
                                    lot_id=lot, atr=row["ATR"], ma24=row["MA24"])
                        position["units_remaining"] -= 1

                    position = None
                    continue

                # TAKE PROFITS
                for idx, tp in enumerate(position["tp_prices"]):
                    if not position["tp_hit_flags"][idx] and row["HIGH"] >= tp:
                        lot = position["remaining_lots"].pop(0)
                        record_fill(trades, dt, "SELL", f"TP{idx+1} HIT",
                                    f"HIGH {row['HIGH']} >= TP {tp}",
                                    tp, 1, position,
                                    lot_id=lot, atr=row["ATR"], ma24=row["MA24"])

                        position["tp_hit_flags"][idx] = True
                        position["units_remaining"] -= 1

                        if idx == 0:
                            position["stop"] = position["entry_price"]
                        if idx == 1:
                            position["stop"] = position["tp_prices"][0]

                if position and position["units_remaining"] <= 0:
                    position = None
                    continue

            # ========== SHORT EXITS ==========
            else:

                # STOP LOSS
                if row["HIGH"] >= position["stop"]:
                    while position["units_remaining"] > 0:
                        lot = position["remaining_lots"].pop(0)
                        record_fill(trades, dt, "BUY", "STOP LOSS",
                                    f"HIGH {row['HIGH']} >= STOP {position['stop']}",
                                    position["stop"], 1, position,
                                    lot_id=lot, atr=row["ATR"], ma24=row["MA24"])
                        position["units_remaining"] -= 1

                    position = None
                    continue

                # TAKE PROFITS
                for idx, tp in enumerate(position["tp_prices"]):
                    if not position["tp_hit_flags"][idx] and row["LOW"] <= tp:
                        lot = position["remaining_lots"].pop(0)
                        record_fill(trades, dt, "BUY", f"TP{idx+1} HIT",
                                    f"LOW {row['LOW']} <= TP {tp}",
                                    tp, 1, position,
                                    lot_id=lot, atr=row["ATR"], ma24=row["MA24"])

                        position["tp_hit_flags"][idx] = True
                        position["units_remaining"] -= 1

                        if idx == 0:
                            position["stop"] = position["entry_price"]
                        if idx == 1:
                            position["stop"] = position["tp_prices"][0]

                if position and position["units_remaining"] <= 0:
                    position = None
                    continue

        # ---------------- SKIP NaN rows ----------------
        if (
            pd.isna(row["ATR"]) or
            pd.isna(row["MA24"]) or
            pd.isna(prev["HH50"]) or
            pd.isna(prev["LL50"])
        ):
            continue

        atr_up = row["ATR"] > prev["ATR"]

        # ------------------------------------------------------
        # ENTRY LOGIC
        # ------------------------------------------------------

        # LONG ENTRY
        long_cond = (
            prev["CLOSE"] <= prev["HH50"] and
            row["CLOSE"] > prev["HH50"] and
            row["CLOSE"] > row["MA24"] and
            atr_up
        )

        # SHORT ENTRY
        short_cond = (
            prev["CLOSE"] >= prev["LL50"] and
            row["CLOSE"] < prev["LL50"] and
            row["CLOSE"] < row["MA24"] and
            atr_up
        )

        # ========== LONG ENTRY ==========
        if long_cond:
            entry = row["CLOSE"]
            atr = row["ATR"]
            tps = [entry + m * atr for m in TP_MULTS]

            position = {
                "side": "long",
                "entry_price": entry,
                "units_remaining": UNITS_PER_ENTRY,
                "stop": entry - SL_MULT * atr,
                "tp_prices": tps,
                "tp_hit_flags": [False, False, False],
                "remaining_lots": [1, 2, 3]
            }

            # qty = 0 on entry
            record_fill(trades, dt, "BUY", "ENTRY",
                        f"Long | SL={position['stop']} | TPs={tps}",
                        entry, 0, position,
                        atr=atr, ma24=row["MA24"])

        # ========== SHORT ENTRY ==========
        elif short_cond:
            entry = row["CLOSE"]
            atr = row["ATR"]
            tps = [entry - m * atr for m in TP_MULTS]

            position = {
                "side": "short",
                "entry_price": entry,
                "units_remaining": UNITS_PER_ENTRY,
                "stop": entry + SL_MULT * atr,
                "tp_prices": tps,
                "tp_hit_flags": [False, False, False],
                "remaining_lots": [1, 2, 3]
            }

            record_fill(trades, dt, "SELL", "ENTRY",
                        f"Short | SL={position['stop']} | TPs={tps}",
                        entry, 0, position,
                        atr=atr, ma24=row["MA24"])

    return trades


# ================================================================
# SAVE CSV
# ================================================================
def save_trades_csv(trades, filename=LOG_CSV):
    keys = [
        "datetime", "side", "reason_title", "reason_detail",
        "entry_price", "exit_price", "qty_exited", "qty_remaining",
        "position_side", "ATR", "MA24", "lot_id", "trade_pnl", "cum_pnl"
    ]
    with open(filename, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for t in trades:
            w.writerow(t)
    print("[OK] Saved:", filename)


# ================================================================
# MAIN
# ================================================================
def main():
    df = fetch_data(RIC)
    df = compute_indicators(df)
    trades = sequential_backtest(df)
    save_trades_csv(trades)

    print("Total Trades:", len(trades))
    print("Cum PNL:", cum_pnl)
    print("Max Runup:", max_runup)
    print("Max Drawdown:", max_drawdown)


if __name__ == "__main__":
    main()