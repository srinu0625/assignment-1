import pandas as pd
import eikon as ek 
import requests
import time 
from datetime import datetime
import pytz
from config import TEAMS_WEBHOOK_URL
# -------------------------------------------------------
# 1️⃣ CONFIGURATION
# -------------------------------------------------------           
app_key = "92e0a59a8e994142bab0f82d8294e1df404da224"  # 🔸 Replace with your Refinitiv Eikon App Key
ek.set_app_key(app_key)
# -------------------------------------------------------
# 🔹 Helper: Send to Teams
# -------------------------------------------------------
def send_to_teams(category, headline, story_id, timestamp):
    """Send formatted message to Teams"""
    message = f"🌾 [{category}]\n\n🕒 {timestamp}\n\n📰 {headline}\n\n🔗 Read full story: https://www.reuters.com/article/{story_id}"
    payload = {"text": message}
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
# 🔹 Define news categories
# -------------------------------------------------------
NEWS_CATEGORIES = {
    "GRAINS": "GRAINS AND ENGLISH ",
    "NOPA": "NOPA OR 'Statistics Canada' AND ENGLISH ",
    "CRIDE_METAL_FOREX" : "(CRUDE OR METAL OR FOREX OR TRAFFICS) AND ENGLISH ",
    "WAR": "WAR AND ENGLISH "
    "BIOFUEL": "(BIOFUEL OR ETHANOL OR BIODIESEL) AND ENGLISH ",
    "RTRS_AGRI": "RTRS AND (GRAINS OR AGRI)
    "COCO_COFFEE": "(COCOA OR COFFEE) AND ENGLISH ",
    "COTTON_SUGAR": "(COTTON OR SUGAR) AND ENGLISH"
    "WAR": "(WAR OR UKRAINE OR ISRAEL OR GAZA OR RUSSIA) AND ENGLISH"
}

def detect_headline_column(df):
    possible_cols = ["headline", "text", "little", "storytext", "storytitle"]
    for col in possible_cols:
        if col in df.columns:
            return col
        return None

def to_detect_link_column(df):
    possible_columns = ["storyID", "Link", "url"]
    for col in possible_columns:
        if col in df.columns:
            return col
        return None
    
def detect_timestamp_column(df):
    possible_cols = ["versionCreated", "time", "date"]
    for col in possible_cols:
        if col in df.colums:
            return col
        return None
def monitor_news():
    for category, query in NEWS_CATEGORIES.items():
        DF = fetch_news(query, count=5)
        if DF.empty:
            continue
        headline = detect_headline_column(DF)
        link = to_detect_link_column(DF)
        timestamp = detect_timestamp_column(DF)
        for index, row in DF.iterrows():
            headline_text = row[headline] if headline else "NO HEADINE FOUND"
            story_id = row[link] if link else "NO LINK FOUND"
            timestamp_VALUE = row[timestamp] if timestamp else datetime.now(pytz.utc)

            send_to_teams(category, headline_text, story_id, timestamp VALUE)
            
            # -------------------------------------------------------
#---------------------------------------------
# main entry point)
#---------------------------------------------
if __name__ == "__main__":
    monitor_news()

