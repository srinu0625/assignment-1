import pandas as pd
import eikon as ek
import requests
import time
from datetime import datetime
import pytz

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/55b4731413d04f6a95975ba9fa82eb79/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Zcwo1Eac1WD4j7-ITfAA5YJTr9t93yezQWVZvRTKe-s"

ek.set_app_key(APP_KEY)

# -------------------------------------------------------
# NEWS QUERIES (cleaned)
# -------------------------------------------------------
NEWS_TABS = {
    "GRAINS": "GRAINS",
    "NOPA": "NOPA AND statistics canada",
    "Crude etal forex": "(CRUDE OR METAL OR FOREX OR Tariffs AND English) AND LEN",
    "WAR": "WAR ",
    "BIOFUEL": "BIOF AND LEN",
    "RTRS AGRI": "RTRS AND LEN AND (GRO OR GRA) NOT (DJNV OR RITV OR V)",
    "COCO/COFFEE": "(Cocoa[COC] OR Coffee[COF]) AND Eglish [LEN] NEWS2.0",
    "COTTON/SUGAR": "{Cotton OR Sugar) AND English AND (North America OR South America OR Europe OR Asia/Pacific)"
}

# -------------------------------------------------------
# SEND MESSAGE TO TEAMS
# -------------------------------------------------------
def send_to_teams(headline, timestamp):
    message = f"🔥 {headline}\n🕒 {timestamp}"
    payload = {"message": message}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        if response.status_code in [200, 202]:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} | Posted: {headline[:70]}...")
        else:
            print(f"⚠️ Teams post failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ Error sending to Teams: {e}")

# -------------------------------------------------------
# FETCH LATEST NEWS
# -------------------------------------------------------
def fetch_news(query):
    try:
        df = ek.get_news_headlines(query, count=20)
        if df is None or df.empty:
            return pd.DataFrame()
        df["versionCreated"] = pd.to_datetime(df["versionCreated"], errors="coerce", utc=True)
        return df
    except Exception as e:
        print(f"❌ Error fetching news for '{query}': {e}")
        return pd.DataFrame()

# -------------------------------------------------------
# DETECT HEADLINE COLUMN
# -------------------------------------------------------
def detect_headline_column(df):
    possible_cols = ["headline", "text", "title", "storyText", "storyTitle"]
    for col in possible_cols:
        if col in df.columns:
            return col
    for col in df.columns:
        if df[col].dtype == object:
            return col
    return None

# -------------------------------------------------------
# UTC → IST
# -------------------------------------------------------
def to_india_time(utc_time):
    if pd.isnull(utc_time):
        return ""
    india_tz = pytz.timezone("Asia/Kolkata")
    return utc_time.tz_convert(india_tz).strftime("%Y-%m-%d %H:%M:%S IST")

# -------------------------------------------------------
# MAIN FLASH MONITOR
# -------------------------------------------------------
def monitor_flashes():
    print(f"🚀 Flash Monitor Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    seen_ids = set()
    first_run = True

    while True:
        try:
            for category, query in NEWS_TABS.items():
                df = fetch_news(query)
                if df.empty:
                    continue

                headline_col = detect_headline_column(df)
                if not headline_col:
                    continue

                for _, row in df.iterrows():
                    story_id = row.get("storyId")
                    if not story_id:
                        continue

                    created_time = row.get("versionCreated")
                    if pd.isnull(created_time):
                        continue

                    age_sec = (datetime.utcnow().replace(tzinfo=pytz.utc) - created_time).total_seconds()
                    headline = str(row.get(headline_col, "")).strip()

                    # Post only if new + within 2 minutes
                    if story_id not in seen_ids and age_sec < 120:
                        if not first_run:
                            print(f"🚨 Flash Detected [{category}]: {headline[:80]}...")
                            send_to_teams(f"[{category}] {headline}", to_india_time(created_time))
                        seen_ids.add(story_id)

            first_run = False
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Loop error: {e}")
            time.sleep(2)

# -------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------
if __name__ == "__main__":
    monitor_flashes()
