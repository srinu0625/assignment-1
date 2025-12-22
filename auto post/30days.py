import eikon as ek
import pandas as pd
from datetime import datetime, timedelta
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
ek.set_app_key(APP_KEY)

DAYS_BACK = 30
OUTPUT_DIR = "reuters_15min_30days"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ALL_RICS_15MIN_30D.xlsx")

# -------------------------------------------------
# RIC LIST
# -------------------------------------------------
RICS = [
     "LCOF6","LGOF6","HOF26","CLF26","NGF26",
    "LCOG6","LGOG6","HOG26","CLG26","NGG26",
    "LCOH6","LGOH6","HOH26","CLH26","NGH26",
    "LCOJ6","LGOJ6","HOJ26","CLJ26","NGJ26",
    "LCOK6","LGOK6","HOK26","CLK26","NGK26",
    "LCOM6","LGOM6","HOM26","CLM26","NGM26",
    "LCON6","LGON6","HON26","CLN26","NGN26",
    "LCOQ6","LGOQ6","HOQ26","CLQ26","NGQ26",
    "LCOU6","LGOU6","HOU26","CLU26","NGU26",
    "LCOV6","LGOV6","HOV26","CLV26","NGV26",
    "LCOX6","LGOX6","HOX26","CLX26","NGX26",
    "LCOZ6","LGOZ6","HOZ26","CLZ26","NGZ26",
    "LCOH7","LGOH7","HOH27","CLH27","NGH27",
    "LCOM7","LGOM7","HOM27","CLM27","NGM27",
    "LCOU7","LGOU7","HOU27","CLU27","NGU27",
    "LCOZ7","LGOZ7","HOZ27","CLZ27","NGZ27",
    "LCOH8","LGOH8","HOH28","CLH28","NGH28",
    "LCOM8","LGOM8","HOM28","CLM28","NGM28",
    "LCOU8","LGOU8","HOU28","CLU28","NGU28",
    "LCOZ8","LGOZ8","HOZ28","CLZ28","NGZ28",
    "LCOM9","LGOM9","HOM29","CLM29","NGM29",
    "LCOZ9","LGOZ9","HOZ29","CLZ29","NGZ29"
]

# -------------------------------------------------
# DATE RANGE
# -------------------------------------------------
END_DATE = datetime.utcnow()
START_DATE = END_DATE - timedelta(days=DAYS_BACK)

# -------------------------------------------------
# MASTER DATAFRAME
# -------------------------------------------------
master_df = pd.DataFrame()

# -------------------------------------------------
# FETCH LOOP
# -------------------------------------------------
for ric in RICS:
    try:
        print(f"Fetching {ric} ...")

        df = ek.get_timeseries(
            ric,
            start_date=START_DATE.strftime("%Y-%m-%d"),
            end_date=END_DATE.strftime("%Y-%m-%d"),
            interval="minute"
        )

        if df is None or df.empty:
            print(f"⚠️ No data for {ric}")
            continue

        # --- RESAMPLE TO 15 MIN ---
        df_15 = (
            df["CLOSE"]
            .resample("15T")
            .last()
            .dropna()
        )

        df_15.name = ric

        if master_df.empty:
            master_df = df_15.to_frame()
        else:
            master_df = master_df.join(df_15, how="outer")

    except Exception as e:
        print(f"❌ Error fetching {ric}: {e}")

# -------------------------------------------------
# SAVE TO EXCEL
# -------------------------------------------------
master_df.reset_index(inplace=True)
master_df.rename(columns={"index": "DateTime"}, inplace=True)

master_df.to_excel(OUTPUT_FILE, index=False)

print(f"\n✅ DONE. 15-minute data saved to:\n{OUTPUT_FILE}")
