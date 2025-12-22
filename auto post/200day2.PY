import eikon as ek
import pandas as pd
from datetime import datetime, timedelta
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
ek.set_app_key(APP_KEY)

DAYS = 200
END_DATE = datetime(2025, 12, 19)
START_DATE = END_DATE - timedelta(days=400)

OUTPUT_DIR = "reuters_200day_csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------
# RIC GROUPS BY EXCHANGE
# -------------------------------------------------
ICE_RICS = [
    "LCOF6","LCOG6","LCOH6","LCOJ6","LCOK6","LCOM6","LCON6","LCOQ6","LCOU6","LCOV6",
    "LCOX6","LCOZ6","LCOH7","LCOM7","LCOU7","LCOZ7","LCOH8","LCOM8","LCOU8","LCOZ8",
    "LCOM9","LCOZ9",

    "LGOF6","LGOG6","LGOH6","LGOJ6","LGOK6","LGOM6","LGON6","LGOQ6","LGOU6","LGOV6",
    "LGOX6","LGOZ6","LGOH7","LGOM7","LGOU7","LGOZ7","LGOH8","LGOM8","LGOU8","LGOZ8",
    "LGOM9","LGOZ9"
]

NYMEX_RICS = [
    "CLF26","CLG26","CLH26","CLJ26","CLK26","CLM26","CLN26","CLQ26","CLU26","CLV26",
    "CLX26","CLZ26","CLH27","CLM27","CLU27","CLZ27","CLH28","CLM28","CLU28","CLZ28",
    "CLM29","CLZ29",

    "HOF26","HOG26","HOH26","HOJ26","HOK26","HOM26","HON26","HOQ26","HOU26","HOV26",
    "HOX26","HOZ26","HOH27","HOM27","HOU27","HOZ27","HOH28","HOM28","HOU28","HOZ28",
    "HOM29","HOZ29",

    "NGF26","NGG26","NGH26","NGJ26","NGK26","NGM26","NGN26","NGQ26","NGU26","NGV26",
    "NGX26","NGZ26","NGH27","NGM27","NGU27","NGZ27","NGH28","NGM28","NGU28","NGZ28",
    "NGM29","NGZ29"
]

# -------------------------------------------------
# FETCH FUNCTION
# -------------------------------------------------
def fetch_exchange_data(rics):
    data_frames = []

    for ric in rics:
        try:
            print(f"Fetching {ric}")
            df = ek.get_timeseries(
                ric,
                start_date=START_DATE.strftime("%Y-%m-%d"),
                end_date=END_DATE.strftime("%Y-%m-%d"),
                interval="daily"
            )

            if df is None or df.empty:
                continue

            df = df.tail(DAYS)[["CLOSE"]]
            df.reset_index(inplace=True)
            df.columns = ["Date", ric]

            data_frames.append(df)

        except Exception as e:
            print(f"Skipping {ric}: {e}")

    if not data_frames:
        return pd.DataFrame()

    out = data_frames[0]
    for d in data_frames[1:]:
        out = out.merge(d, on="Date", how="outer")

    return out.sort_values("Date")

# -------------------------------------------------
# FETCH & SAVE CSVs
# -------------------------------------------------
ice_df = fetch_exchange_data(ICE_RICS)
ice_csv = os.path.join(OUTPUT_DIR, "ICE_Europe_200D_Close.csv")
ice_df.to_csv(ice_csv, index=False)

nymex_df = fetch_exchange_data(NYMEX_RICS)
nymex_csv = os.path.join(OUTPUT_DIR, "NYMEX_200D_Close.csv")
nymex_df.to_csv(nymex_csv, index=False)

print("DONE → Two CSV files created (ICE & NYMEX).")
