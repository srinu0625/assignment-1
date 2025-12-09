import requests
import json
import time
from datetime import datetime

API_KEY = "YOUR_LIVESQUAWK_API_KEY"  # You’ll get this from LiveSquawk support
WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/..."


def fetch_livesquawk_news():
    url = "https://api.livesquawk.com/v1/news/latest"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        news_items = []
        for item in data.get("articles", [])[:10]:
            title = item.get("headline", "No headline")
            body = item.get("body", "")
            ts = item.get("timestamp", "")
            news_items.append(f"🕒 {ts}\n**{title}**\n{body}\n")

        return news_items
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error fetching: {e}")
        return []


def send_to_teams(message):
    payload = {"message": message}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code in (200, 202):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Posted to Teams.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Webhook returned {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Teams Send Error: {e}")


def main():
    sent_news = set()
    print(f"🔄 LiveSquawk Monitor started at {datetime.now().strftime('%H:%M:%S')}")

    while True:
        news = fetch_livesquawk_news()
        new_items = [n for n in news if n not in sent_news]

        if new_items:
            msg = "📰 **LiveSquawk Latest News**\n\n" + "\n\n".join(new_items)
            send_to_teams(msg)
            sent_news.update(new_items)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No new updates.")

        time.sleep(10)  # check every 10s


if __name__ == "__main__":
    main()
