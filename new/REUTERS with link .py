import pandas as pd
import eikon as ek
import requests
import time
from datetime import datetime
import pytz
# from config import teams_webhook_url
# -------------------------------------------------------
# 1️⃣ CONFIGURATION
# -------------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"  # 
TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/60b2e30fbc954d44a0ad6a2fbe958ce2/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b0w27fZV4iTXdMNFwd8HgbYeen3xyVdALXyf8HO-8Ac"

# Initialize Eikon connection
ek.set_app_key(APP_KEY)

# -------------------------------------------------------
# 🔹 Define news categories
# -------------------------------------------------------
NEWS_CATEGORIES = {

    "GRAINS": "GRAINS AND ENGLISH ",
    "NOPA": "NOPA OR 'Statistics Canada' AND ENGLISH ",
    "CRUDE_METAL_FOREX": "(CRUDE OR METAL OR FOREX OR TARIFFS) AND ENGLISH ",
    "WAR": "(WAR OR UKRAINE OR ISRAEL OR GAZA OR RUSSIA) AND ENGLISH ",
    "BIOFUEL": "(BIOFUEL OR ETHANOL OR BIODIESEL) AND ENGLISH ",
    "RTRS_AGRI": "RTRS AND (GRAINS OR AGRI) AND ENGLISH NOT (DJN"
    "V OR RITV) ",        
    "COCO_COFFEE": "(COCOA OR COFFEE) AND ENGLISH ",
    "COTTON_SUGAR": "(COTTON OR SUGAR) AND ENGLISH"

}

# -------------------------------------------------------
# 🔹 Send message to Microsoft Teams (via Power Automate)
# -------------------------------------------------------
def send_to_teams(headline, link, timestamp):
    """Send formatted message to Power Automate / Teams webhook"""
    message = f"🌾 {headline}\n\n🕒 {timestamp}\n🔗 [Read full story]({link})"
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
# 🔹 Monitor and post new stories
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
                        try:
                            story_url = ek.get_news_story_url(story_id)
                        except Exception:
                            story_url = "https://www.reuters.com"

                        headline_text = str(row.get(headline_col, "No headline"))
                        india_time = to_india_time(row.get("versionCreated"))
                        # Send news with category
                        send_to_teams(f"[{category_name}] {headline_text}", story_url, india_time)
                        seen_ids.add(story_id)

            print("✅ All current news posted!")  # <-- Line at end after posting
            time.sleep(10)  # Minimal delay for new news

        except Exception as loop_error:
            print(f"⚠️ Loop error: {loop_error}")
            print("🔁 Retrying in 10 seconds...")
            time.sleep(10)



# -------------------------------------------------------
# 🔹 MAIN ENTRY POINT
# -------------------------------------------------------
if __name__ == "__main__":
    monitor_news()
