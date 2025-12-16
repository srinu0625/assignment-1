import pandas as pd

import eikon as ek

import requests

import time

from datetime import datetime

import pytz
 
# -------------------------------------------------------

# 1️⃣ CONFIGURATION

# -------------------------------------------------------

APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"  # Replace with your valid Eikon App Key

TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/55b4731413d04f6a95975ba9fa82eb79/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Zcwo1Eac1WD4j7-ITfAA5YJTr9t93yezQWVZvRTKe-s"
 
ek.set_app_key(APP_KEY)
 
# -------------------------------------------------------

# 2️⃣ NEWS QUERIES (TABS)

# -------------------------------------------------------

NEWS_TABS = {

    "GRAINS": "GRAINS AND ENGLISH",

    "NOPA": "NOPA OR 'Statistics Canada' AND ENGLISH",

    "CRUDE_METAL_FOREX": "(CRUDE OR METAL OR FOREX OR TARIFFS) AND ENGLISH",

    "WAR": "(WAR OR UKRAINE OR ISRAEL OR GAZA OR RUSSIA) AND ENGLISH",

    "BIOFUEL": "(BIOFUEL OR ETHANOL OR BIODIESEL) AND ENGLISH",

    "RTRS_AGRI": "RTRS AND (GRAINS OR AGRI) AND ENGLISH NOT (DJNV OR RITV)",

    "COCO_COFFEE": "(COCOA OR COFFEE) AND ENGLISH",

    "COTTON_SUGAR": "(COTTON OR SUGAR) AND ENGLISH"

}
 
# -------------------------------------------------------

# 🔹 Helper: Send to Teams

# -------------------------------------------------------

def send_to_teams(category, headline, story_id, timestamp):

    """Send formatted message to Teams"""

    message = f"🔥 **[{category}]**\n📰 {headline}\n🕒 {timestamp}\n🆔 Story ID: {story_id}"

    payload = {"message": message}

    headers = {"Content-Type": "application/json"}
 
    try:

        r = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers, timeout=10)

        if r.status_code not in [200, 202]:

            print(f"⚠️ Teams Post Failed ({r.status_code}): {r.text}")

        else:

            print(f"✅ Posted: {headline[:80]}...")

    except Exception as e:

        print(f"⚠️ Error sending to Teams: {e}")
 
# -------------------------------------------------------

# 🔹 Fetch news headlines

# -------------------------------------------------------

def fetch_news(query, count=5):

    try:

        df = ek.get_news_headlines(query, count=count)

        if "versionCreated" in df.columns:

            df["versionCreated"] = pd.to_datetime(df["versionCreated"], errors="coerce", utc=True)

        return df

    except Exception as e:

        print(f"[{time.strftime('%H:%M:%S')}] ❌ Error fetching news for query '{query}': {e}")

        return pd.DataFrame()
 
# -------------------------------------------------------

# 🔹 Detect headline column

# -------------------------------------------------------

def detect_headline_column(df):

    for col in ["headline", "text", "title", "storyText", "storyTitle"]:

        if col in df.columns:

            return col

    for col in df.columns:

        if df[col].dtype == object:

            return col

    return None
 
# -------------------------------------------------------

# 🔹 Convert UTC to India time

# -------------------------------------------------------

def to_india_time(utc_time):

    if pd.isnull(utc_time):

        return ""

    tz = pytz.timezone("Asia/Kolkata")

    return utc_time.tz_convert(tz).strftime("%Y-%m-%d %H:%M:%S IST")
 
# -------------------------------------------------------

# 🔹 Monitor and post Reuters news

# -------------------------------------------------------

def monitor_reuters_news():

    print(f"🟢 Monitoring Reuters news since {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    seen_ids = set()
 
    while True:

        try:

            for category, query in NEWS_TABS.items():

                df = fetch_news(query, count=10)

                if df.empty:

                    continue
 
                headline_col = detect_headline_column(df)

                if not headline_col:

                    print(f"⚠️ No headline column for {category}")

                    continue
 
                for _, row in df.iterrows():

                    story_id = row.get("storyId")

                    if not story_id or story_id in seen_ids:

                        continue
 
                    headline = str(row.get(headline_col, "No headline")).strip()

                    timestamp = to_india_time(row.get("versionCreated"))

                    # 🔥 Send to Teams with fire emoji and story ID

                    send_to_teams(category, headline, story_id, timestamp)

                    seen_ids.add(story_id)
 
            print("🔁 Cycle complete. Checking again in 60 seconds...\n")

            time.sleep(3)
 
        except Exception as e:

            print(f"⚠️ Error in loop: {e}")

            time.sleep(5)
 
# -------------------------------------------------------

# MAIN ENTRY

# -------------------------------------------------------

if __name__ == "__main__":

    monitor_reuters_news()

 