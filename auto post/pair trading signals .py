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
RESAMPLE_RULE = "30T"

PVALUE_THRESHOLD = 0.05
ZSCORE_ENTRY = 2.5
ZSCORE_EXIT = 0.5

EXCEL_PATH = os.path.abspath("Thursday_18_12_2025.xlsx")
EXCEL_SHEET = "Dashboard"

MIN_ALIGNED_BARS = 20

# ================= UTILS =================

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)

def safe_numeric(s):
    return pd.to_numeric(s, errors="coerce")

# ================= DATA =================

def fetch_timeseries(ric, count, interval):
    df = ek.get_timeseries(ric, count=count, interval=interval)
    col = next((c for c in df.columns if c.lower() in ["close", "bid"]), df.columns[0])
    s = safe_numeric(df[col]).dropna()
    s.index = pd.to_datetime(s.index)
    return s

def resample_series(s, rule):
    return s.resample(rule).last().dropna()

def align_latest(y, x):
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    df.columns = ["Y", "X"]
    return df

# ================= STATS =================

def engle_granger(df):
    X = sm.add_constant(df["X"])
    model = sm.OLS(df["Y"], X).fit()
    resid = df["Y"] - model.predict(X)
    try:
        pval = adfuller(resid.dropna(), autolag="AIC")[1]
    except:
        pval = 1.0
    return model.params["const"], model.params["X"], resid, pval

def zscore(s):
    sd = s.std()
    return (s - s.mean()) / sd if sd else s * 0

def build_signal(z, p):
    if p >= PVALUE_THRESHOLD:
        return "NO_TRADE"
    if z > ZSCORE_ENTRY:
        return "SELL_SPREAD"
    if z < -ZSCORE_ENTRY:
        return "BUY_SPREAD"
    if abs(z) < ZSCORE_EXIT:
        return "EXIT"
    return "HOLD"

# ================= EXCEL DASHBOARD =================

class ExcelWriter:
    def __init__(self, path, sheet, pairs):
        self.app = xw.App(visible=True, add_book=False)
        self.app.display_alerts = False
        self.app.screen_updating = True
        self.app.calculation = "automatic"

        if os.path.exists(path):
            self.wb = self.app.books.open(path)
        else:
            self.wb = self.app.books.add()
            self.wb.save(path)

        self.sht = self.wb.sheets[sheet] if sheet in [s.name for s in self.wb.sheets] else self.wb.sheets.add(sheet)
        self._layout(pairs)

    def _layout(self, pairs):
        headers = [
            "Y","X","Last_Y","Last_X",
            "Intercept","Beta","Spread",
            "Z","ADF_p","Signal","Updated"
        ]
        self.sht.range("A1").value = headers

        for i, (y, x) in enumerate(pairs, start=2):
            self.sht.range(f"A{i}").value = y
            self.sht.range(f"B{i}").value = x

        self.sht.autofit()

    def _signal_color(self, signal):
        return {
            "BUY_SPREAD": (0, 176, 80),
            "SELL_SPREAD": (192, 0, 0),
            "EXIT": (255, 192, 0),
            "HOLD": (217, 217, 217),
            "NO_TRADE": (217, 217, 217)
        }.get(signal, (255, 255, 255))

    def _z_color(self, z):
        z = max(min(z, 3), -3)
        if z > 0:
            return (255, int(255 - 60*z), int(255 - 60*z))
        return (int(255 + 60*z), 255, int(255 + 60*z))

    def write_row(self, row, data, z, signal):
        rng = self.sht.range(f"C{row}:K{row}")
        rng.value = data

        # Flash update
        rng.color = (255, 255, 153)
        self.app.calculate()
        time.sleep(0.1)

        # Apply colors
        self.sht.range(f"J{row}").color = self._signal_color(signal)
        self.sht.range(f"I{row}").color = self._z_color(z)

        self.app.calculate()

    def close(self, path):
        self.wb.save(path)
        self.wb.close()
        self.app.quit()

# ================= MAIN =================

def main():
    ek.set_app_key(EIKON_APP_KEY)
    writer = ExcelWriter(EXCEL_PATH, EXCEL_SHEET, PAIRS)
    log("Live dashboard started")

    try:
        while True:
            for i, (ry, rx) in enumerate(PAIRS, start=2):
                y = resample_series(fetch_timeseries(ry, WINDOW_BARS, EIKON_INTERVAL), RESAMPLE_RULE)
                x = resample_series(fetch_timeseries(rx, WINDOW_BARS, EIKON_INTERVAL), RESAMPLE_RULE)

                df = align_latest(y, x)
                if len(df) < MIN_ALIGNED_BARS:
                    continue

                intercept, beta, resid, pval = engle_granger(df)
                z = zscore(resid).iloc[-1]
                sig = build_signal(z, pval)

                writer.write_row(
                    i,
                    [
                        float(df["Y"].iloc[-1]),
                        float(df["X"].iloc[-1]),
                        intercept,
                        beta,
                        float(resid.iloc[-1]),
                        z,
                        pval,
                        sig,
                        datetime.now().strftime("%H:%M:%S")
                    ],
                    z,
                    sig
                )

                log(f"{ry}/{rx} | z={z:.2f} | {sig}")

            time.sleep(30)

    except KeyboardInterrupt:
        log("Stopping")

    finally:
        writer.close(EXCEL_PATH)
        log("Excel saved & closed")

if __name__ == "__main__":
    main()
