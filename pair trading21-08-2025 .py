#!/usr/bin/env python3
import time
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import eikon as ek
import xlwings as xw

# =====================
# === USER CONFIG =====
# =====================
EIKON_APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"

PAIRS = [
    ("LGOF6", "LCOF6"),
    ("LGOG6", "LCOG6"),
    ("LGOH6", "LCOH6"),
    ("LGOM6", "LCOM6"),
    ("LGOU6", "LCOU6"),
    ("LGOZ6", "LCOZ6"),
]

EIKON_INTERVAL = "minute"
WINDOW_BARS = 960
RESAMPLE_RULE = "15T"
PVALUE_THRESHOLD = 0.05
ZSCORE_ENTRY = 2.5
ZSCORE_EXIT = 0.5

WRITE_TO_EXCEL = True
EXCEL_PATH = os.path.abspath("PairTrading_Multi 10-12-2025---2.xlsx")
EXCEL_SHEET = "Dashboard"

FETCH_RETRIES = 2
FETCH_RETRY_SLEEP = 2.0
MIN_ALIGNED_BARS = 20

# =====================
# === HELPERS =========
# =====================

def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def safe_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def fetch_timeseries(ric: str, count: int, interval: str) -> pd.Series:
    last_ex = None
    for attempt in range(1, FETCH_RETRIES + 2):
        try:
            df = ek.get_timeseries(ric, count=count, interval=interval)
            if df is None or df.empty:
                raise RuntimeError(f"No data for {ric}")

            cols = [c for c in ["CLOSE","BID","Close","Bid","close","bid"] if c in df.columns]
            if cols:
                s = df[cols[0]].copy()
            else:
                nc = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                if nc:
                    s = df[nc[0]].copy()
                else:
                    s = safe_numeric(df.iloc[:,0]).copy()

            s = safe_numeric(s).dropna()
            if s.empty:
                raise RuntimeError(f"No numeric values for {ric}")

            s.index = pd.to_datetime(s.index)
            return s

        except Exception as e:
            last_ex = e
            log(f"fetch_timeseries attempt {attempt} failed for {ric}: {e}")
            if attempt <= FETCH_RETRIES:
                time.sleep(FETCH_RETRY_SLEEP)
            else:
                log(f"Giving up on {ric} for this cycle.")
                return pd.Series(dtype=float)

    return pd.Series(dtype=float)

def resample_series(s: pd.Series, rule: str | None) -> pd.Series:
    if s is None or s.empty:
        return pd.Series(dtype=float)
    if not rule:
        return s
    return s.resample(rule).last().dropna()

def align_latest(y: pd.Series, x: pd.Series) -> pd.DataFrame:
    if y is None or x is None or y.empty or x.empty:
        return pd.DataFrame()
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    if df.empty:
        return pd.DataFrame()
    df = df.iloc[:, :2].apply(safe_numeric).dropna()
    df.columns = ["Y", "X"]
    return df

def engle_granger(df: pd.DataFrame) -> dict:
    try:
        if df is None or len(df) < 10:
            raise RuntimeError("Not enough data for regression")

        X = sm.add_constant(df["X"].astype(float))
        Y = df["Y"].astype(float)
        model = sm.OLS(Y, X).fit()

        intercept = float(model.params.get("const", 0.0))
        beta = float(model.params.get("X", model.params.iloc[-1]))

        resid = Y - (intercept + beta * df["X"].astype(float))

        try:
            adf_res = adfuller(resid.dropna(), autolag="AIC")
            pvalue = float(adf_res[1])
        except:
            pvalue = 1.0

        return {"intercept": intercept, "beta": beta, "resid": resid, "pvalue": pvalue}

    except Exception as e:
        log(f"engle_granger error: {e}")
        zero_resid = pd.Series(0.0, index=df.index if (df is not None and not df.empty) else pd.DatetimeIndex([]))
        return {"intercept": 0.0, "beta": 0.0, "resid": zero_resid, "pvalue": 1.0}

def zscore(s: pd.Series) -> pd.Series:
    if s is None or s.empty:
        return pd.Series(dtype=float)
    m = s.mean()
    sd = s.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return pd.Series(0.0, index=s.index)
    return (s - m) / sd

def build_signal(df: pd.DataFrame, pv: float):
    if df is None or df.empty or "spread" not in df.columns or "z" not in df.columns:
        return "NO_TRADE", float("nan"), float("nan")

    spread = float(df["spread"].iloc[-1])
    z = float(df["z"].iloc[-1])

    sig = "NO_TRADE"

    if pv < PVALUE_THRESHOLD and not np.isnan(z):
        if z > ZSCORE_ENTRY:
            sig = "SELL_SPREAD"
        elif z < -ZSCORE_ENTRY:
            sig = "BUY_SPREAD"
        elif abs(z) < ZSCORE_EXIT:
            sig = "EXIT"
        else:
            sig = "HOLD"

    return sig, spread, z

# =====================
# === FIXED EXCEL WRITER (FINAL VERSION) ===
# =====================
class ExcelWriter:
    def __init__(self, path: str, sheet: str, pairs: list):
        self.path = path
        self.sheet = sheet
        self.pairs = pairs
        self.app = xw.App(visible=False, add_book=False)

        if os.path.exists(path):
            self.wb = self.app.books.open(path)
        else:
            self.wb = self.app.books.add()
            self.wb.save(path)

        try:
            self.sht = self.wb.sheets[sheet]
        except:
            self.sht = self.wb.sheets.add(sheet)

        if self.sht.range("A1").value != "Y":
            self._init_layout()

        last = self.sht.range("A" + str(self.sht.cells.last_cell.row)).end("up").row
        self.current_row = last + 1
        if self.current_row < 2:
            self.current_row = 2

    def _init_layout(self):
        headers = ["Y","X","Last_Y","Last_X","Intercept","Beta",
                   "Spread","Z","ADF_p","Signal","Updated"]
        self.sht.range("A1").value = headers
        for i, (y, x) in enumerate(self.pairs, start=2):
            self.sht.range(f"A{i}").value = y
            self.sht.range(f"B{i}").value = x
        self.sht.autofit()

    def write_row(self, row_index, *, last_y, last_x, intercept, beta, spread, z, pvalue, signal):
        vals = [last_y, last_x, intercept, beta, spread, z, pvalue, signal,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        pair_y = self.pairs[row_index - 2][0] if 0 <= (row_index - 2) < len(self.pairs) else ""
        pair_x = self.pairs[row_index - 2][1] if 0 <= (row_index - 2) < len(self.pairs) else ""
        self.sht.range(f"A{self.current_row}").value = [pair_y, pair_x] + vals
        self.current_row += 1

    def safe_save_close(self):
        try:
            self.wb.save(self.path)
            log("Excel workbook saved.")
        except Exception as e:
            log(f"Excel save failed: {e}")
        finally:
            try: self.wb.close()
            except: pass
            try: self.app.quit()
            except: pass

# =====================
# === MAIN LOOP =======
# =====================
def main():
    log("Starting pair trading engine.")
    try:
        ek.set_app_key(EIKON_APP_KEY)
    except Exception as e:
        log(f"Failed to set Eikon app key: {e}")

    writer = None
    if WRITE_TO_EXCEL:
        try:
            writer = ExcelWriter(EXCEL_PATH, EXCEL_SHEET, PAIRS)
            log(f"Excel initialized: {EXCEL_PATH} -> sheet '{EXCEL_SHEET}'")
        except Exception as e:
            log(f"Excel init failed: {e}")
            writer = None

    log("Engine running. Ctrl+C to stop.")

    try:
        while True:
            now = datetime.now()
            log(f"Starting processing cycle at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            for i, (ric_y, ric_x) in enumerate(PAIRS, start=2):
                try:
                    y = fetch_timeseries(ric_y, WINDOW_BARS, EIKON_INTERVAL)
                    x = fetch_timeseries(ric_x, WINDOW_BARS, EIKON_INTERVAL)

                    if RESAMPLE_RULE:
                        y = resample_series(y, RESAMPLE_RULE)
                        x = resample_series(x, RESAMPLE_RULE)

                    df = align_latest(y, x)

                    if df.empty or len(df) < MIN_ALIGNED_BARS:
                        log(f"{ric_y}/{ric_x}: insufficient aligned bars ({len(df)}). skipping.")
                        continue

                    eg = engle_granger(df)

                    df["spread"] = eg["resid"]
                    df["z"] = zscore(df["spread"])

                    sig, spread, z = build_signal(df, eg["pvalue"])

                    if writer:
                        writer.write_row(
                            i,
                            last_y=float(df["Y"].iloc[-1]),
                            last_x=float(df["X"].iloc[-1]),
                            intercept=eg["intercept"],
                            beta=eg["beta"],
                            spread=spread,
                            z=z,
                            pvalue=eg["pvalue"],
                            signal=sig
                        )

                    log(f"{ric_y}/{ric_x} | p={eg['pvalue']:.4f} | z={z:.3f} | {sig}")

                except Exception as e:
                    log(f"Error processing {ric_y}/{ric_x}: {e}")

            # --- wait until next 15-minute boundary ---
            now = datetime.now()
            minutes = (now.minute // 15 + 1) * 15
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutes)
            sleep_seconds = max((next_run - datetime.now()).total_seconds(), 0)
            log(f"Sleeping for {int(sleep_seconds)} seconds until next 15-minute cycle.")
            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        log("Stopping engine. Saving Excel...")

    finally:
        if writer:
            writer.safe_save_close()
        log("Engine stopped cleanly.")

if __name__ == "__main__":
    main()
