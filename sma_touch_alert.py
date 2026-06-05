"""
SMA (50, 100, 200) Touch Alert System
======================================
Logic: Touch = (Low <= SMA) AND (High >= SMA)
Data : Local CSV files — no internet required
"""

import pandas as pd
from tabulate import tabulate
from datetime import datetime
import time

# ─────────────────────────────────────────────
#  ★  CONFIG — Set your CSV file paths here
# ─────────────────────────────────────────────

FILES = {
    "60min":  r"D:\Data\CL 60min.csv",
    "240min": r"D:\Data\CL 240min.csv",
    "Daily":  r"D:\Data\CL Daily.csv",
}

SMA_PERIODS = [50, 100, 200]

# Column name mapping — adjust if your CSV uses different names
# e.g. "Open", "High", "Low", "Close", "Volume", "Date", "Time" etc.
COL_MAP = {
    "date":   "Date",
    "open":   "Open",
    "high":   "High",
    "low":    "Low",
    "close":  "Close",
}

# ─────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────

def load_csv(file_path: str, tf_label: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

        # Rename columns to standard internal names using COL_MAP
        rename = {v: k for k, v in COL_MAP.items()}   # flip: "Date" -> "date"
        df.rename(columns=rename, inplace=True)

        # Parse and sort by date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True)
            df.sort_values("date", ascending=True, inplace=True)
            df.set_index("date", inplace=True)

        # Ensure numeric OHLC
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["high", "low", "close"], inplace=True)
        print(f"  ✓ Loaded [{tf_label}]  {len(df)} bars  →  {file_path}")
        return df

    except FileNotFoundError:
        print(f"  ✗ File not found [{tf_label}]: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"  ✗ Error loading [{tf_label}]: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  CORE LOGIC
# ─────────────────────────────────────────────

def compute_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def sma_touch(df: pd.DataFrame, sma_period: int):
    """
    Touch = Low <= SMA  AND  High >= SMA
    i.e. the SMA value lies within the candle's high-low range.
    Returns (bool Series of touches, SMA Series)
    """
    sma = compute_sma(df["close"], sma_period)
    touched = (df["low"] <= sma) & (df["high"] >= sma)
    return touched, sma


# ─────────────────────────────────────────────
#  SCAN — check the latest bar only
# ─────────────────────────────────────────────

def scan_latest(dataframes: dict) -> list:
    alerts = []

    for tf_label, df in dataframes.items():
        if df.empty:
            continue
        if len(df) < max(SMA_PERIODS):
            print(f"  ⚠ [{tf_label}] Not enough bars "
                  f"(need {max(SMA_PERIODS)}, got {len(df)})")
            time.sleep(2)
            continue

        for sma_period in SMA_PERIODS:
            touched_s, sma_s = sma_touch(df, sma_period)

            last_time  = df.index[-1]
            last_high  = float(df["high"].iloc[-1])
            last_low   = float(df["low"].iloc[-1])
            last_close = float(df["close"].iloc[-1])
            last_sma   = float(sma_s.iloc[-1])
            is_touched = bool(touched_s.iloc[-1])

            if is_touched:
                alerts.append({
                    "time":       last_time,
                    "timeframe":  tf_label,
                    "sma_period": sma_period,
                    "sma_value":  round(last_sma,   4),
                    "high":       round(last_high,  4),
                    "low":        round(last_low,   4),
                    "close":      round(last_close, 4),
                })

    return alerts


# ─────────────────────────────────────────────
#  BACKTEST — all historical touches
# ─────────────────────────────────────────────

def backtest_all(dataframes: dict) -> pd.DataFrame:
    rows = []

    for tf_label, df in dataframes.items():
        if df.empty or len(df) < max(SMA_PERIODS):
            continue

        print(f"  Scanning {tf_label} ...")

        for sma_period in SMA_PERIODS:
            touched_s, sma_s = sma_touch(df, sma_period)
            touch_df = df[touched_s].copy()

            for bar_time, bar in touch_df.iterrows():
                rows.append({
                    "Time":      bar_time,
                    "Timeframe": tf_label,
                    "SMA":       sma_period,
                    "SMA Value": round(float(sma_s.loc[bar_time]), 4),
                    "High":      round(float(bar["high"]),         4),
                    "Low":       round(float(bar["low"]),          4),
                    "Close":     round(float(bar["close"]),        4),
                })

    result = pd.DataFrame(rows)
    if not result.empty:
        result.sort_values("Time", ascending=False, inplace=True)
        result.reset_index(drop=True, inplace=True)
    return result


# ─────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────

def print_status_table(dataframes: dict):
    """Print full 9-combo status table for the latest bar."""
    rows = []
    for tf_label, df in dataframes.items():
        if df.empty or len(df) < max(SMA_PERIODS):
            for sp in SMA_PERIODS:
                rows.append({
                    "Timeframe": tf_label, "SMA": sp,
                    "SMA Value": "N/A", "High": "N/A",
                    "Low":       "N/A", "Close": "N/A",
                    "Touch?":    "N/A",
                })
            continue

        for sp in SMA_PERIODS:
            touched_s, sma_s = sma_touch(df, sp)
            rows.append({
                "Timeframe": tf_label,
                "SMA":       sp,
                "SMA Value": round(float(sma_s.iloc[-1]),      4),
                "High":      round(float(df["high"].iloc[-1]),  4),
                "Low":       round(float(df["low"].iloc[-1]),   4),
                "Close":     round(float(df["close"].iloc[-1]), 4),
                "Touch?":    "✅ YES" if touched_s.iloc[-1] else "❌  No",
            })

    print(tabulate(rows, headers="keys", tablefmt="pretty"))


def print_backtest_results(result: pd.DataFrame):
    if result.empty:
        print("  No SMA touches found in history.")
        return

    # Touch count summary
    summary = (
        result.groupby(["Timeframe", "SMA"])
        .size()
        .reset_index(name="Touches")
    )
    print("\n  ── Summary ──")
    print(tabulate(summary, headers="keys", tablefmt="simple", showindex=False))

    # Most recent 30 touches
    recent = result.head(30).copy()
    recent["Time"] = recent["Time"].dt.strftime("%Y-%m-%d %H:%M")
    print("\n  ── Most Recent 30 Touches ──")
    print(tabulate(recent, headers="keys", tablefmt="simple", showindex=False))

    # Save full results to CSV
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"sma_touch_backtest_{ts}.csv"
    result.to_csv(out, index=False)
    print(f"\n  Full results saved → {out}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  SMA Touch Alert  |  Local CSV Mode")
    print("="*60)

    # ── Load all CSVs ──────────────────────────
    print("\n  Loading files ...")
    dataframes = {
        tf: load_csv(path, tf)
        for tf, path in FILES.items()
    }

    # ── Latest bar status table ────────────────
    print("\n" + "="*60)
    print(f"  Status  |  Latest Bar  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    print_status_table(dataframes)

    # ── Alert messages for latest bar ─────────
    alerts = scan_latest(dataframes)
    print()
    if alerts:
        print("  🔔 ALERTS TRIGGERED:")
        for a in alerts:
            print(
                f"     {str(a['time'])[:16]}  |  {a['timeframe']:7s}  "
                f"|  SMA {a['sma_period']:3d} = {a['sma_value']:.2f}  "
                f"|  H={a['high']:.2f}  L={a['low']:.2f}  C={a['close']:.2f}"
            )
    else:
        print("  ✓  No SMA touches on the latest bar.")

    # ── Backtest all history ───────────────────
    print("\n" + "="*60)
    print("  Backtest  |  All Historical Touches")
    print("="*60 + "\n")
    result = backtest_all(dataframes)
    print_backtest_results(result)

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
