import pandas as pd
import eikon as ek
import requests
import time
from datetime import datetime
import pytz

# -------------------------------------------------------
# 1️⃣ CONFIGURATION
# -------------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"  # 🔸 Replace with your Refinitiv/Eikon App Key
TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/55b4731413d04f6a95975ba9fa82eb79/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Zcwo1Eac1WD4j7-ITfAA5YJTr9t93yezQWVZvRTKe-s"

# Initialize Eikon connection
ek.set_app_key(APP_KEY)

# -------------------------------------------------------
# 🔹 Define news categories
# -------------------------------------------------------
NEWS_CATEGORIES = {
    "Grains News": "WHEAT OR RICE OR CORN OR GRAINS OR RTRS OR DJN  OR BARCHA OR NOTENG OR BNEINT OR IFX ",
    "Livestock News": "LIVESTOCK OR CATTLE OR POULTRY OR RTRS OR DJN  OR BARCHA OR NOTENG OR BNEINT OR IFX",
    "Agri Policy News": "AGRICULTURE OR FARM POLICY OR AGRI OR RTRS OR DJN  OR BARCHA OR NOTENG OR BNEINT OR IFX",
    "Coffee News": "COFFEE OR RTRS OR DJN  OR BARCHA OR NOTENG OR BNEINT OR IFX OR SAUARB OR ARASER OR YAHNEX OR NOTENG OR BRN OR PUBT OR "
}

# -------------------------------------------------------
# 🔹 Send message to Microsoft Teams (no link)
# -------------------------------------------------------
def send_to_teams(headline, timestamp):
    """Send formatted message (headline + timestamp only)"""
    message = f"📰 {headline}\n🕒 {timestamp}"
    payload = {"message": message}  # <-- 'message' works with Power Automate
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        if r.status_code not in [200, 202]:
            print(f"⚠️ Failed to post to Teams: {r.status_code} - {r.text}")
        else:
            print(f"✅ Posted successfully: {headline[:60]}...")
    except Exception as e:
        print(f"⚠️ Error sending to Teams: {e}")

# -------------------------------------------------------
# 🔹 Fetch headlines for a given category
# -------------------------------------------------------
def fetch_news_by_category(query, count=5):
    """Fetch latest news for a specific query"""
    try:
        headlines = ek.get_news_headlines(query, count=count)
        if "versionCreated" in headlines.columns:
            headlines["versionCreated"] = pd.to_datetime(headlines["versionCreated"], errors="coerce", utc=True)
        return headlines
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Error fetching news: {e}")
        return pd.DataFrame()

# -------------------------------------------------------
# 🔹 Detect the correct headline column
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
# 🔹 Convert UTC to India Time
# -------------------------------------------------------
def to_india_time(utc_time):
    if pd.isnull(utc_time):
        return ""
    india_tz = pytz.timezone("Asia/Kolkata")
    return utc_time.tz_convert(india_tz).strftime("%Y-%m-%d %H:%M:%S IST")

# -------------------------------------------------------
# 🔹 Monitor and post new stories (no link)
# -------------------------------------------------------
def monitor_news():
    """Continuously monitor and post categorized news"""
    print(f"🌾 Monitoring news at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    seen_ids = set()

    while True:
        try:
            for category_name, query in NEWS_CATEGORIES.items():
                news_df = fetch_news_by_category(query, count=5)
                if news_df.empty:
                    continue

                headline_col = detect_headline_column(news_df)
                if not headline_col:
                    print(f"⚠️ Could not find headline column for {category_name}")
                    continue

                for _, row in news_df.iterrows():
                    story_id = row.get("storyId")
                    if story_id and story_id not in seen_ids:
                        headline_text = str(row.get(headline_col, "No headline"))
                        india_time = to_india_time(row.get("versionCreated"))

                        # Send only headline and time (no link)
                        send_to_teams(f"[{category_name}] {headline_text}", india_time)
                        seen_ids.add(story_id)

            print("✅ All current news posted!")
            time.sleep(10)  # minimal delay for new news

        except Exception as loop_error:
            print(f"⚠️ Loop error: {loop_error}")
            print("🔁 Retrying in 10 seconds...")
            time.sleep(10)

# -------------------------------------------------------
# 🔹 MAIN ENTRY POINT
# -------------------------------------------------------
if __name__ == "__main__":
    monitor_news()