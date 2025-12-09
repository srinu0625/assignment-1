#!/usr/bin/env python3
"""
ATR Scaling Backtest (2x, 4x, 8x) with 24-MA filter (enabled).
Modifications:
- Entry condition unchanged.
- Entry fill price:
    LONG  -> current candle HIGH
    SHORT -> current candle LOW
- Exit detection: same (intra-bar HIGH/LOW vs TP/SL levels).
- Exit fill price:
    LONG exits  -> current candle LOW
    SHORT exits -> current candle HIGH
- Saves detailed CSV of all fills
"""
import eikon as ek
import pandas as pd
import csv
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
ek.set_app_key(APP_KEY)

RIC = "ESc1"                # change to desired RIC
START = "2020-01-01"
END = None
INTERVAL = "minute"
RESAMPLE_PERIOD = "15T"     # set to '1T' to skip resampling

ATR_PERIOD = 14
MA_PERIOD = 24
LOOKBACK_HHLL = 50

UNITS_PER_ENTRY = 3
SL_MULT = 2.0
TP_MULTS = [2.0, 4.0, 8.0]  # TP1, TP2, TP3

LOG_CSV = "atr_scaling_trades_simple.csv"
DEBUG = False

# -----------------------
# GLOBALS
# -----------------------
cum_pnl = 0.0
peak_pnl = 0.0
max_runup = 0.0
max_drawdown = 0.0


# -----------------------
# HELPERS
# -----------------------
def printp(msg):
    if DEBUG:
        print(msg)


# -----------------------
# FETCH + RESAMPLE
# -----------------------
def fetch_and_resample(ric, start=START, end=END, interval=INTERVAL, resample_period=RESAMPLE_PERIOD):
    print(f"[INFO] fetching {ric}...")
    df = ek.get_timeseries(
        ric,
        fields=['CLOSE','HIGH','LOW','OPEN','VOLUME'],
        start_date=start,
        end_date=end,
        interval=interval
    )
    if df is None or df.empty:
        raise RuntimeError("No data returned from Eikon.")

    df = df.reset_index()
    df.rename(columns={df.columns[0]: 'DATETIME'}, inplace=True)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    df = df.sort_values('DATETIME').reset_index(drop=True)
    df.set_index('DATETIME', inplace=True)

    if resample_period and resample_period != '1T':
        df_r = df.resample(resample_period).agg({
            'OPEN': 'first', 'HIGH': 'max', 'LOW': 'min', 'CLOSE': 'last', 'VOLUME': 'sum'
        }).dropna().reset_index()
    else:
        df_r = df.reset_index()

    df_r = df_r[['DATETIME','OPEN','HIGH','LOW','CLOSE','VOLUME']]
    df_r = df_r.sort_values('DATETIME').reset_index(drop=True)
    return df_r


# -----------------------
# INDICATORS (Wilder ATR)
# -----------------------
def compute_indicators(df):
    df = df.copy()
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    df = df.sort_values('DATETIME').reset_index(drop=True)
    df['prev_close'] = df['CLOSE'].shift(1)

    df['tr1'] = df['HIGH'] - df['LOW']
    df['tr2'] = (df['HIGH'] - df['prev_close']).abs()
    df['tr3'] = (df['LOW'] - df['prev_close']).abs()
    df['TR'] = df[['tr1','tr2','tr3']].max(axis=1)
    df['ATR'] = df['TR'].ewm(alpha=1.0/ATR_PERIOD, adjust=False).mean()

    df['MA24'] = df['CLOSE'].rolling(window=MA_PERIOD, min_periods=1).mean()
    df['HH50'] = df['HIGH'].rolling(window=LOOKBACK_HHLL, min_periods=1).max()
    df['LL50'] = df['LOW'].rolling(window=LOOKBACK_HHLL, min_periods=1).min()

    return df


# -----------------------
# RECORD + PRINT
# -----------------------
def record_fill(trades, when, side, reason_title, reason_detail, price, qty, position_before, lot_id=None, atr=None):
    global cum_pnl, peak_pnl, max_runup, max_drawdown

    trade_pnl = 0.0
    entry_price = position_before.get('entry_price') if position_before else None

    if reason_title not in ("ENTRY","INFO") and entry_price is not None:
        if position_before['side'] == 'long':
            trade_pnl = (price - entry_price) * qty
        else:
            trade_pnl = (entry_price - price) * qty

        cum_pnl += trade_pnl
        peak_pnl = max(peak_pnl, cum_pnl)
        max_runup = max(max_runup, cum_pnl)
        drawdown = cum_pnl - peak_pnl
        max_drawdown = min(max_drawdown, drawdown)

    qty_remaining = ""
    if position_before and isinstance(position_before.get('units_remaining',None),(int,float)):
        try:
            qty_remaining = max(0, position_before['units_remaining'] - qty)
        except Exception:
            qty_remaining = position_before.get('units_remaining')

    row = {
        'datetime': pd.to_datetime(when).strftime("%Y-%m-%d %H:%M:%S"),
        'side': side,
        'reason_title': reason_title,
        'reason_detail': reason_detail,
        'entry_price': float(entry_price) if entry_price is not None else "",
        'exit_price': float(price) if price is not None else "",
        'qty_exited': float(qty),
        'qty_remaining': float(qty_remaining) if qty_remaining != "" else "",
        'position_side': position_before['side'] if position_before else "",
        'ATR': float(atr) if atr is not None else "",
        'lot_id': lot_id if lot_id is not None else "",
        'trade_pnl': round(trade_pnl,2),
        'cum_pnl': round(cum_pnl,2)
    }
    trades.append(row)

    # console print simplified
    if DEBUG:
        try:
            print(f"[{reason_title}] {when} {side} price={price:.4f} qty={qty} lot={lot_id} pnl={trade_pnl:.2f} cum={cum_pnl:.2f}")
        except Exception:
            print(f"[{reason_title}] {when} {side} price={price} qty={qty} lot={lot_id} pnl={trade_pnl:.2f} cum={cum_pnl:.2f}")


# -----------------------
# BACKTEST
# -----------------------
def sequential_backtest(df):
    trades = []
    position = None

    global cum_pnl, peak_pnl, max_runup, max_drawdown
    cum_pnl = peak_pnl = max_runup = max_drawdown = 0.0

    for i in range(1, len(df)):
        row = df.loc[i]
        prev = df.loc[i-1]
        dt = row['DATETIME']

        # EXIT logic if in position
        if position is not None:
            # attach for info
            position['ATR'] = row['ATR']

            # -----------------------
            # LONG position exits
            # -----------------------
            if position['side'] == 'long':
                # STOP LOSS (triggered by intra-bar LOW) -> exit fill uses row['LOW']
                if row['LOW'] <= position['stop']:
                    # exit all remaining lots at LONG-EXIT-PRICE = row['LOW']
                    exit_price = row['LOW']
                    while position['units_remaining'] > 0:
                        lot_id = position['remaining_lots'].pop(0)
                        reason_title = "STOP LOSS"
                        reason_detail = f"BAR LOW {row['LOW']:.4f} <= STOP {position['stop']:.4f}"
                        record_fill(trades, dt, "SELL", reason_title, reason_detail, exit_price, 1, position, lot_id=lot_id, atr=row['ATR'])
                        position['units_remaining'] -= 1
                    position = None
                    continue

                # TAKE PROFITS (triggered by HIGH) -> exit fill uses row['LOW'] per your rule
                for idx, tp in enumerate(position['tp_prices']):
                    if position['tp_hit_flags'][idx]:
                        continue
                    if row['HIGH'] >= tp:
                        exit_price = row['LOW']  # long exit uses candle LOW
                        lot_id = position['remaining_lots'].pop(0)
                        reason_title = f"TP{idx+1} HIT"
                        reason_detail = f"HIGH {row['HIGH']:.4f} >= TP{idx+1} {tp:.4f}"
                        record_fill(trades, dt, "SELL", reason_title, reason_detail, exit_price, 1, position, lot_id=lot_id, atr=row['ATR'])
                        position['units_remaining'] -= 1
                        position['tp_hit_flags'][idx] = True

                        # trail SL updates (INFO records use TP price for clarity)
                        if idx == 0:
                            prev_stop = position['stop']
                            position['stop'] = position['entry_price']
                            record_fill(trades, dt, "INFO", "STOP MOVED", f"After TP1: stop {prev_stop:.4f} -> {position['stop']:.4f}", tp, 0, position, lot_id=None, atr=row['ATR'])
                        elif idx == 1:
                            prev_stop = position['stop']
                            position['stop'] = position['tp_prices'][0]
                            record_fill(trades, dt, "INFO", "STOP MOVED", f"After TP2: stop {prev_stop:.4f} -> {position['stop']:.4f}", tp, 0, position, lot_id=None, atr=row['ATR'])

                # clear if fully exited
                if position and position['units_remaining'] <= 0:
                    position = None
                    continue

            # -----------------------
            # SHORT position exits (mirror)
            # -----------------------
            elif position['side'] == 'short':
                # STOP LOSS (triggered by intra-bar HIGH) -> exit fill uses row['HIGH']
                if row['HIGH'] >= position['stop']:
                    exit_price = row['HIGH']
                    while position['units_remaining'] > 0:
                        lot_id = position['remaining_lots'].pop(0)
                        reason_title = "STOP LOSS"
                        reason_detail = f"BAR HIGH {row['HIGH']:.4f} >= STOP {position['stop']:.4f}"
                        record_fill(trades, dt, "BUY", reason_title, reason_detail, exit_price, 1, position, lot_id=lot_id, atr=row['ATR'])
                        position['units_remaining'] -= 1
                    position = None
                    continue

                # TAKE PROFITS (triggered by LOW) -> exit fill uses row['HIGH'] per your rule
                for idx, tp in enumerate(position['tp_prices']):
                    if position['tp_hit_flags'][idx]:
                        continue
                    if row['LOW'] <= tp:
                        exit_price = row['HIGH']  # short exit uses candle HIGH
                        lot_id = position['remaining_lots'].pop(0)
                        reason_title = f"TP{idx+1} HIT"
                        reason_detail = f"LOW {row['LOW']:.4f} <= TP{idx+1} {tp:.4f}"
                        record_fill(trades, dt, "BUY", reason_title, reason_detail, exit_price, 1, position, lot_id=lot_id, atr=row['ATR'])
                        position['units_remaining'] -= 1
                        position['tp_hit_flags'][idx] = True

                        # trail SL updates (INFO records)
                        if idx == 0:
                            prev_stop = position['stop']
                            position['stop'] = position['entry_price']
                            record_fill(trades, dt, "INFO", "STOP MOVED", f"After TP1: stop {prev_stop:.4f} -> {position['stop']:.4f}", tp, 0, position, lot_id=None, atr=row['ATR'])
                        elif idx == 1:
                            prev_stop = position['stop']
                            position['stop'] = position['tp_prices'][0]
                            record_fill(trades, dt, "INFO", "STOP MOVED", f"After TP2: stop {prev_stop:.4f} -> {position['stop']:.4f}", tp, 0, position, lot_id=None, atr=row['ATR'])
                if position and position['units_remaining'] <= 0:
                    position = None
                    continue

        # ENTRY logic (if no position)
        if position is None and not pd.isna(prev['ATR']):
            long_cond = (prev['CLOSE'] <= prev['HH50']) and (row['CLOSE'] > prev['HH50']) and (row['CLOSE'] > row['MA24'])
            short_cond = (prev['CLOSE'] >= prev['LL50']) and (row['CLOSE'] < prev['LL50']) and (row['CLOSE'] < row['MA24'])

            if long_cond or short_cond:
                # ---- FILL PRICES (modified) ----
                if long_cond:
                    # Entry fill = current candle HIGH (as requested)
                    entry_price = row['HIGH']
                    atr = row['ATR']
                    tp_prices = [entry_price + m * atr for m in TP_MULTS]
                    tp_hit_flags = [False]*len(TP_MULTS)
                    remaining_lots = list(range(1, UNITS_PER_ENTRY+1))
                    position = {
                        'side': 'long',
                        'entry_price': entry_price,
                        'units_total': UNITS_PER_ENTRY,
                        'units_remaining': UNITS_PER_ENTRY,
                        'stop': entry_price - SL_MULT * atr,
                        'tp_prices': tp_prices,
                        'tp_hit_flags': tp_hit_flags,
                        'remaining_lots': remaining_lots
                    }
                    reason_detail = f"Entry at HIGH {entry_price:.4f} | SL {position['stop']:.4f} | TPs {[round(x,4) for x in tp_prices]} | ATR {atr:.4f}"
                    record_fill(trades, dt, "BUY", "ENTRY", reason_detail, entry_price, UNITS_PER_ENTRY, position, lot_id=None, atr=atr)

                elif short_cond:
                    # Entry fill = current candle LOW (as requested)
                    entry_price = row['LOW']
                    atr = row['ATR']
                    tp_prices = [entry_price - m * atr for m in TP_MULTS]
                    tp_hit_flags = [False]*len(TP_MULTS)
                    remaining_lots = list(range(1, UNITS_PER_ENTRY+1))
                    position = {
                        'side': 'short',
                        'entry_price': entry_price,
                        'units_total': UNITS_PER_ENTRY,
                        'units_remaining': UNITS_PER_ENTRY,
                        'stop': entry_price + SL_MULT * atr,
                        'tp_prices': tp_prices,
                        'tp_hit_flags': tp_hit_flags,
                        'remaining_lots': remaining_lots
                    }
                    reason_detail = f"Entry at LOW {entry_price:.4f} | SL {position['stop']:.4f} | TPs {[round(x,4) for x in tp_prices]} | ATR {atr:.4f}"
                    record_fill(trades, dt, "SELL", "ENTRY", reason_detail, entry_price, UNITS_PER_ENTRY, position, lot_id=None, atr=atr)

                printp(f"ENTRY created at {entry_price} side={'LONG' if long_cond else 'SHORT'} dt={dt}")

    return trades


# -----------------------
# SAVE CSV
# -----------------------
def save_trades_csv(trades, filename=LOG_CSV):
    keys = [
        "datetime", "side", "reason_title", "reason_detail",
        "entry_price", "exit_price", "qty_exited", "qty_remaining",
        "position_side", "ATR", "lot_id", "trade_pnl", "cum_pnl"
    ]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for t in trades:
            row = {k: t.get(k, "") for k in keys}
            writer.writerow(row)
    print(f"[OK] saved trades to {filename}")


# -----------------------
# MAIN
# -----------------------
def main():
    print("[INFO] start backtest")
    df = fetch_and_resample(RIC)
    df = compute_indicators(df)
    trades = sequential_backtest(df)
    save_trades_csv(trades)
    # summary
    print("Total records:", len(trades))
    print(f"Cumulative P&L: {cum_pnl:.2f} | Max Runup: {max_runup:.2f} | Max Drawdown: {max_drawdown:.2f}")


if __name__ == "__main__":
    main()
