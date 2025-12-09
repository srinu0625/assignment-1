import time
import os
from datetime import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import eikon as ek
import xlwings as xw

EIKON_APP_KEY = "your_app_key_here"

PAIRS = [
    ("ESc1", "NQc1"),
    ("ESc1", "YMc1"),
    # Add more pairs as needed
]

EIKON_INTERVAL = "minute"
WINDOW_BARS = 960
RESAMPLE_RULE = "15T"
REFRESH_SECONDS = 60
PVALUE_THRESHOLD = 0.05
ZSCORE_ENTRY = 2.5
ZSCORE_EXIT = 0.5

WRITE_TO_EXCEL = True
EXCEL_PATH = os.path.abspath("PairTrading_Multi.xlsx")
EXCEL_SHEET = "Output"
FETCH_RETRIES = 2
FETCH_RETRY_SLEEP = 2.0
MIN_ALIGNED_BARS = 20

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def safe_numeric(s):
    return pd.to_numeric(s, errors="coerce")

def fetch_timeseries(ric, count, interval):
    for attempt in range(1, FETCH_RETRIES + 2):
        try:
            df = ek.get_timeseries(ric, count=count, interval=interval)
            if df is None or df.empty:
                raise RuntimeError(f"No data for {ric}")
            cols = [c for c in ["CLOSE", "BID", "Close", "Bid", "close", "bid"] if c in df.columns]
            if cols:
                s = df[cols[0]].copy()
            else:
                num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                s = df[num_cols[0]].copy() if num_cols else safe_numeric(df.iloc[:, 0]).copy()
            s = safe_numeric(s).dropna()
            if s.empty:
                raise RuntimeError(f"No numeric values for {ric}")
            s.index = pd.to_datetime(s.index)
            return s
        except Exception as e:
            log(f"fetch_timeseries attempt {attempt} failed for {ric}: {e}")
            if attempt <= FETCH_RETRIES:
                time.sleep(FETCH_RETRY_SLEEP)
            else:
                log(f"Giving up on {ric} for this cycle.")
                return pd.Series(dtype=float)
    return pd.Series(dtype=float)

def resample_series(s, rule):
    if s is None or s.empty:
        return pd.Series(dtype=float)
    if not rule:
        return s
    return s.resample(rule).last().dropna()

def align_latest(y, x):
    if y is None or x is None or y.empty or x.empty:
        return pd.DataFrame()
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    if df.empty:
        return pd.DataFrame()
    df = df.iloc[:, :2].apply(safe_numeric).dropna()
    df.columns = ["Y", "X"]
    return df

def engle_granger(df):
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
        except Exception:
            pvalue = 1.0
        return {"intercept": intercept, "beta": beta, "resid": resid, "pvalue": pvalue}
    except Exception as e:
        log(f"engle_granger error: {e}")
        zero_resid = pd.Series(0.0, index=df.index if (df is not None and not df.empty) else pd.DatetimeIndex([]))
        return {"intercept": 0.0, "beta": 0.0, "resid": zero_resid, "pvalue": 1.0}

def zscore(s):
    if s is None or s.empty:
        return pd.Series(dtype=float)
    m = s.mean()
    sd = s.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return pd.Series(0.0, index=s.index)
    return (s - m) / sd

def build_signal(df, pv):
    if df is None or df.empty or "spread" not in df.columns or "z" not in df.columns:
        return "NO_TRADE", float("nan"), float("nan")
    try:
        spread = float(df["spread"].iloc[-1])
        z = float(df["z"].iloc[-1])
    except Exception:
        return "NO_TRADE", float("nan"), float("nan")
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

class ExcelWriter:
    def __init__(self, path, sheet):
        self.path = path
        self.sheet = sheet
        self.app = xw.App(visible=False, add_book=False)
        if os.path.exists(path):
            try:
                self.wb = self.app.books.open(path, read_only=False)
            except Exception:
                self.wb = self.app.books.open(path)
        else:
            self.wb = self.app.books.add()
            self.wb.save(path)
        try:
            self.sht = self.wb.sheets[sheet]
        except Exception:
            self.sht = self.wb.sheets.add(sheet)
        self._init_layout()

    def _init_layout(self):
        headers = ["Y", "X", "Last_Y", "Last_X", "Intercept", "Beta", "Spread", "Z", "ADF_p", "Signal", "Updated"]
        self.sht.range("A1").value = headers
        self.sht.autofit()

    def append_row(self, yname, xname, last_y, last_x, intercept, beta, spread, z, pvalue, signal):
        # Find next empty row after data for appending
        last_row = self.sht.range('A' + str(self.sht.cells.last_cell.row)).end('up').row
        next_row = last_row + 1 if last_row > 1 else 2
        vals = [yname, xname, last_y, last_x, intercept, beta, spread, z, pvalue, signal, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        self.sht.range(f"A{next_row}").value = vals

    def safe_save_close(self):
        try:
            self.wb.save(self.path)
        except Exception as e:
            print(f"Excel save failed: {e}")
        finally:
            try:
                self.wb.close()
            except Exception as e:
                print(f"Excel close error: {e}")
            try:
                self.app.quit()
            except Exception:
                pass

def main():
    log("Starting pair trading engine.")
    ek.set_app_key(EIKON_APP_KEY)
    writer = ExcelWriter(EXCEL_PATH, EXCEL_SHEET) if WRITE_TO_EXCEL else None

    log("Engine running. Ctrl+C to stop.")
    try:
        while True:
            for ric_y, ric_x in PAIRS:
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
                        writer.append_row(
                            yname=ric_y, xname=ric_x,
                            last_y=float(df["Y"].iloc[-1]),
                            last_x=float(df["X"].iloc[-1]),
                            intercept=eg["intercept"], beta=eg["beta"],
                            spread=spread, z=z, pvalue=eg["pvalue"], signal=sig
                        )

                    log(f"{ric_y}/{ric_x} | p={eg['pvalue']:.4f} | z={z:.3f} | {sig}")

                except Exception as e:
                    log(f"Error processing {ric_y}/{ric_x}: {e}")
            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        log("🛑 Stopping engine (KeyboardInterrupt). Please wait, saving Excel...")

    finally:
        if writer:
            writer.safe_save_close()
        log("✅ Engine stopped cleanly. Goodbye.")

if __name__ == "__main__":
    main()
