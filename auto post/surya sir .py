import eikon as ek
import pandas as pd
from datetime import datetime, timedelta, time

# -------------------------
# CONFIG
# -------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
RIC = "ESc1"
INTERVAL = "minute"
YEARS = 5
OUTPUT_FILE = "ES_5yr_P1_C_H_L.xlsx"

# Times for your logic
P1_TIME = time(0, 30)     # 12:30 AM
C_TIME  = time(14, 30)    # 2:30 PM

ek.set_app_key(APP_KEY)

# -------------------------
# DOWNLOAD 5 YEARS (SAFE MODE)
# -------------------------
print("Downloading full 5-year ES minute data (safe mode)...")

df_list = []
end = datetime.now()

for _ in range(YEARS):
    start = end - timedelta(days=365)
    print(f"Fetching: {start.date()} → {end.date()}")

    try:
        df_part = ek.get_timeseries(
            RIC,
            fields=["OPEN", "HIGH", "LOW", "CLOSE"],
            interval=INTERVAL,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d")
        )
    except Exception as e:
        print("Error:", e)
        end = start
        continue

    if df_part is not None and not df_part.empty:
        df_list.append(df_part)

    end = start

# Merge all partial downloads
df = pd.concat(df_list).sort_index()

# Remove timezone (Excel cannot write timezone-aware timestamps)
df.index = pd.to_datetime(df.index).tz_localize(None)

print("Total rows downloaded:", len(df))


# -------------------------
# EXTRACT P1, C, H, L DAILY
# -------------------------
rows = []

for day, dfd in df.groupby(df.index.date):

    dfd = dfd.sort_index()

    # P1
    try:
        P1 = dfd.between_time(P1_TIME, P1_TIME)["CLOSE"].iloc[0]
    except:
        continue

    # C
    try:
        C = dfd.between_time(C_TIME, C_TIME)["CLOSE"].iloc[0]
    except:
        continue

    # H & L between P1→C
    intraday = dfd.between_time(P1_TIME, C_TIME)
    H = intraday["HIGH"].max()
    L = intraday["LOW"].min()

    rows.append([day, P1, C, H, L])


result = pd.DataFrame(rows, columns=["Date", "P1", "C", "H", "L"])

# -------------------------
# SAVE TO EXCEL
# -------------------------
result.to_excel(OUTPUT_FILE, index=False)

print("DONE → Saved to:", OUTPUT_FILE)
