import requests
import feedparser
import json
import time
from datetime import datetime

# === Teams Webhook ===
webhook_url = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/55b4731413d04f6a95975ba9fa82eb79/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Zcwo1Eac1WD4j7-ITfAA5YJTr9t93yezQWVZvRTKe-s"

# === RSS Feeds ===
RSS_FEEDS = {
    "Investing.com": "https://www.investing.com/rss/news_25.rss",
    "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "financialjuice": "https://www.financialjuice.com/home"
}

# === Fetch Headlines + Summaries ===
def fetch_all_headlines():
    headlines = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No entries found for {source}")
                continue

            for entry in feed.entries[:5]:  # top 5 per source
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                # remove HTML tags and shorten
                clean_summary = (
                    summary.replace("<p>", "")
                    .replace("</p>", "")
                    .replace("<br>", "")
                    .replace("<b>", "")
                    .replace("</b>", "")
                    .replace("&nbsp;", " ")
                )
                clean_summary = (clean_summary[:250] + "...") if len(clean_summary) > 250 else clean_summary

                if title:
                    headlines.append(f"📰 [{source}] {title}\n🧾 {clean_summary}\n")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error fetching {source}: {e}")
    return headlines

# === Send message to Microsoft Teams ===
def send_teams_message(message):
    payload = {"message": message}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sent ({response.status_code}): {message[:80]}...")
    except requests.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Teams send error: {e}")

# === Main Loop ===
def main():
    sent_headlines = set()
    print(f"🔄 Monitoring multiple RSS feeds at {datetime.now().strftime('%H:%M:%S')}")

    while True:
        try:
            headlines = fetch_all_headlines()
            new_headlines = [h for h in headlines if h not in sent_headlines]

            if new_headlines:
                combined_message = "\n".join(new_headlines[:5])  # send only latest few
                send_teams_message(combined_message)
                sent_headlines.update(new_headlines)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {len(new_headlines)} new stories sent.")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No new updates.")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")

        time.sleep(10)  # fetch every 10 seconds

if __name__ == "__main__":
    main()
