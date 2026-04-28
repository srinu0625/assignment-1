import requests
import feedparser
import json
import   time
from datetime import datetime

# === Teams Webhook ===
webhook_url = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/55b4731413d04f6a95975ba9fa82eb79/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Zcwo1Eac1WD4j7-ITfAA5YJTr9t93yezQWVZvRTKe-s"
# === RSS Feeds (add or remove as needed) ===
RSS_FEEDS = {
       "trading economics": "https://tradingeconomics.com/rss/news.aspx",
       "trading economics (economy)": "https://tradingeconomics.com/rss/news.aspx?i=economy",
       "trading economics (interest-rate)": "https://tradingeconomics.com/rss/news.aspx?i=interest-rate",
       "trading economics (inflation)": "https://tradingeconomics.com/rss/news.aspx?i=inflation",
       "trading economics (gdp)": "https://tradingeconomics.com/rss/news.aspx?i=gdp",
       "trading economics (labour)": "https://tradingeconomics.com/rss/news.aspx?i=labour"
}

# === Fetch Headlines from Multiple RSS Sources ===
def fetch_all_headlines():
    headlines = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No entries found for {source}")
                continue

            for entry in feed.entries[:5]:  # Get top 5 news per source
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                
                # Try to get full text or summary
                summary = entry.get("summary", "") or entry.get("description", "")
                summary = summary.replace("\n", " ").replace("\r", " ").strip()

                # Create ~5 lines of text (about 120 words)
                words = summary.split()
                five_lines = " ".join(words[:120])

                # Format message for Teams
                if title and link:
                    message = (
                        f"🟢 **{source}** — {title}\n\n"
                        f"{five_lines}\n\n"
                        f"🔗 {link}"
                    )
                    headlines.append(message)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error fetching {source}: {e}")

    return headlines[:1]  # send only first 5 total items


# === Send message to Microsoft Teams ===
def send_teams_message(message):
    payload = {"message": message}
    headers = {"Content-Types": "application/json"}

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sent ({response.status_code}): {message[:60]}...")
    except requests.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Teams send error : {e}")

# === Main Loop ===
def main():
    sent_headlines = set()
    print(f"🔄 Monitoring Multiple RSS feed  at {datetime.now().strftime('%H:%M:%S')}")

    while True:
        try:
            headlines = fetch_all_headlines()
            new_headlines = [h for h in headlines if h not in sent_headlines]
 
            if new_headlines:
                combined_message = " Latest Headlines:\n" + "\n".join(new_headlines)
                send_teams_message(combined_message)
                sent_headlines.update(new_headlines)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {len(new_headlines)} new headlines sent.")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No new updates .")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")

        time.sleep(10)  # fetch every 30 seconds

if __name__ == "__main__":
    main()

