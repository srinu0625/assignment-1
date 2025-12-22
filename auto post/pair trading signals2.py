import time
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import eikon as ek
import xlwings as xw

# ================= CONFIG =================
EIKON_APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"

PAIRS = [

    ("LGOF6", "LCOF6"),
    ("LGOG6", "LCOG6"),
    ("LGOH6", "LCOH6"),
    ("LGOM6", "LCOM6"),
    ("LGOU6", "LCOU6"),
    ("LGOZ6", "LCOZ6"),
    ("LGOM7", "LCOM7"),
    ("LGOZ7", "LCOZ7"),
    ("LGOM8", "LCOM8")

]

EIKON_INTERVAL = "minute"
WINDOW_BARS = 960
RESAMPLE_RULE = "5D"
PVALUE_THRESHOLD = 0.05
ZSCORE_ENTRY = 2.5
ZSCORE_EXIT = 0.5

WRITE_TO_EXCEL = True
EXCEL_PATH = os.path.abspath("Thursday 18-12-2025.xlsx")
EXCEL_SHEET = "Dashboard"

MIN_ALIGNED_BARS = 20

# ================= DASHBOARD MAP =================
BLOCK_START = {
    "OR": 2,
    "3MS": 8,
    "6MS": 14,
    "3MF": 20,
    "6MF": 26,
    "12MS": 32,
    "CDR": 38
}

ROW_MAP = {
    "VWAP": 0,
    "5D_ZS": 1,
    "10D_ZS": 2,
    "20D_ZS": 3
}

COL_START = 3  # Column C

# ================= UTILS =================
def log(msg: str):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)

def safe_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def zscore(s: pd.Series) -> pd.Series:
    if s.empty:
        return pd.Series(dtype=float)
    sd = s.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / sd

# ================= DATA =================
def fetch_timeseries(ric: str) -> pd.Series:
    df = ek.get_timeseries(ric, count=WINDOW_BARS, interval=EIKON_INTERVAL)
    s = safe_numeric(df.iloc[:, 0]).dropna()
    s.index = pd.to_datetime(s.index)
    return s

def align_latest(y: pd.Series, x: pd.Series) -> pd.DataFrame:
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    df.columns = ["Y", "X"]
    return df

def engle_granger(df: pd.DataFrame) -> dict:
    X = sm.add_constant(df["X"])
    model = sm.OLS(df["Y"], X).fit()
    resid = df["Y"] - model.predict(X)

    try:
        pval = adfuller(resid.dropna(), autolag="AIC")[1]
    except:
        pval = 1.0

    return {
        "intercept": model.params["const"],
        "beta": model.params["X"],
        "resid": resid,
        "pvalue": pval
    }

def build_signal(df: pd.DataFrame, pv: float):
    spread = float(df["spread"].iloc[-1])
    z = float(df["z"].iloc[-1])

    sig = "NO_TRADE"
    if pv < PVALUE_THRESHOLD:
        if z > ZSCORE_ENTRY:
            sig = "SELL_SPREAD"
        elif z < -ZSCORE_ENTRY:
            sig = "BUY_SPREAD"
        elif abs(z) < ZSCORE_EXIT:
            sig = "EXIT"

    return sig, spread, z

# ================= EXCEL =================
class ExcelWriter:
    def __init__(self, path: str, sheet: str, pairs: list):
        self.path = path
        self.sheet = sheet
        self.pairs = pairs

        self.app = xw.App(visible=True, add_book=False)
        self.app.api.ScreenUpdating = True

        if os.path.exists(path):
            self.wb = self.app.books.open(path)
        else:
            self.wb = self.app.books.add()
            self.wb.save(path)

        try:
            self.sht = self.wb.sheets[sheet]
        except:
            self.sht = self.wb.sheets.add(sheet)

        self._init_layout()

    def _init_layout(self):
        for i, (y, _) in enumerate(self.pairs):
            self.sht.cells(1, COL_START + i).value = y

        for block, base in BLOCK_START.items():
            self.sht.cells(base, 1).value = block
            for m, off in ROW_MAP.items():
                self.sht.cells(base + off, 2).value = m

        self.sht.autofit()

    def write_row(self, row_index, *, last_y, last_x,
                  intercept, beta, spread, z, pvalue, signal):

        tenor_idx = row_index - 2
        block = "OR"

        values = {
            "VWAP": spread,
            "5D_ZS": z,
            "10D_ZS": z,
            "20D_ZS": z
        }

        for metric, val in values.items():
            r = BLOCK_START[block] + ROW_MAP[metric]
            c = COL_START + tenor_idx
            cell = self.sht.cells(r, c)
            cell.value = val

            if val is None or np.isnan(val):
                cell.color = None
            elif val > 0:
                cell.color = (255, 0, 0)
            else:
                cell.color = (0, 176, 80)

        #  FORCE LIVE REFRESH
        self.app.api.CalculateFull()

    def safe_save_close(self):
        try:
            self.wb.save(self.path)
        finally:
            try: self.wb.close()
            except: pass
            try: self.app.quit()
            except: pass

# ================= MAIN =================
def main():
    log("Starting Reuters dashboard engine")
    ek.set_app_key(EIKON_APP_KEY)

    writer = ExcelWriter(EXCEL_PATH, EXCEL_SHEET, PAIRS) if WRITE_TO_EXCEL else None

    try:
        while True:
            for i, (ric_y, ric_x) in enumerate(PAIRS, start=2):
                y = fetch_timeseries(ric_y)
                x = fetch_timeseries(ric_x)

                y = y.resample(RESAMPLE_RULE).last()
                x = x.resample(RESAMPLE_RULE).last()

                df = align_latest(y, x)
                if len(df) < MIN_ALIGNED_BARS:
                    continue

                eg = engle_granger(df)
                df["spread"] = eg["resid"]
                df["z"] = zscore(df["spread"])

                sig, spread, z = build_signal(df, eg["pvalue"])

                if writer:
                    writer.write_row(
                        i,
                        last_y=df["Y"].iloc[-1],
                        last_x=df["X"].iloc[-1],
                        intercept=eg["intercept"],
                        beta=eg["beta"],
                        spread=spread,
                        z=z,
                        pvalue=eg["pvalue"],
                        signal=sig
                    )

                log(f"{ric_y}/{ric_x} | z={z:.2f} | {sig}")

            time.sleep(900)

    except KeyboardInterrupt:
        log("Stopping engine")

    finally:
        if writer:
            writer.safe_save_close()
        log("Stopped cleanly")

if __name__ == "__main__":
    main()
