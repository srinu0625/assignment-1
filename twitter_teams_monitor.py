import tweepy
import requests
import time
import logging
from datetime import datetime

# ==========================================

# CONFIGURATION

# ==========================================

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAw%2F%2BQEAAAAA3SyDBqwPbxXjcDA51%2B7xWEGTcvM%3DDicc02KYDAMwbgEshbl9Z72HMgDM3B0VgSx2bLGMo3nraUR8wZ"

TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/60b2e30fbc954d44a0ad6a2fbe958ce2/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b0w27fZV4iTXdMNFwd8HgbYeen3xyVdALXyf8HO-8Ac%22"

CHECK_INTERVAL = 15
MAX_TWEETS_PER_ACCOUNT = 20

# ==========================================

# LOGGING

# ==========================================

logging.basicConfig(
filename="twitter_monitor.log",
level=logging.INFO,
format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================================

# X CLIENT

# ==========================================

client = tweepy.Client(
bearer_token=BEARER_TOKEN,
wait_on_rate_limit=True
)

# ==========================================

# LOAD ACCOUNTS

# ==========================================

def load_accounts():
    with open("accounts.txt", "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip()
        ]

# ==========================================

# TEAMS

# ==========================================

def send_to_teams(account, tweet_text, tweet_url):
    payload = {
        "text":
            f"🐦 X MARKET UPDATE\n\n"
            f"Account: @{account}\n\n"
            f"{tweet_text}\n\n"
            f"{tweet_url}"
    }

    for attempt in range(3):
        try:
            r = requests.post(
                TEAMS_WEBHOOK_URL,
                json=payload,
                timeout=5
            )

            if r.status_code in [200, 202]:
                return True

        except Exception as e:
            logging.error(f"Teams Error Attempt {attempt+1}: {e}")

        time.sleep(2)

    return False

# ==========================================

# USER LOOKUP CACHE

# ==========================================

user_cache = {}

def get_user_id(username):
    if username in user_cache:
        return user_cache[username]

    user = client.get_user(username=username)

    if user.data:
        user_cache[username] = user.data.id
        return user.data.id

    return None

# ==========================================

# TRACK POSTED TWEETS

# ==========================================

seen_tweets = {}

# ==========================================

# MAIN LOOP

# ==========================================

print("=" * 80)
print("X MARKET NEWS MONITOR STARTED")
print("=" * 80)

while True:
    try:
        accounts = load_accounts()

        print("\nLoaded Accounts:")
        print(accounts)


        for account in accounts:
            try:
                print(f"\nChecking @{account}")

                user_id = get_user_id(account)

                print(f"User ID = {user_id}")

                if not user_id:
                    continue

                if account not in seen_tweets:
                    seen_tweets[account] = set()

                print("Fetching tweets...")

                tweets = client.get_users_tweets(
                    id=user_id,
                    max_results=MAX_TWEETS_PER_ACCOUNT
                )

                print(tweets)

                if not tweets.data:
                    continue

                for tweet in reversed(tweets.data):
                    tweet_id = tweet.id

                    if tweet_id in seen_tweets[account]:
                        continue

                    tweet_url = f"https://x.com/{account}/status/{tweet_id}"

                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    print("\n" + "=" * 80)
                    print("🐦 X MARKET UPDATE")
                    print("=" * 80)
                    print(f"TIME    : {now}")
                    print(f"ACCOUNT : @{account}")
                    print("-" * 80)
                    print(tweet.text)
                    print("-" * 80)
                    print(tweet_url)
                    print("=" * 80)

                    ok = send_to_teams(account, tweet.text, tweet_url)

                    if ok:
                        seen_tweets[account].add(tweet_id)
                        logging.info(f"Posted @{account} {tweet_id}")

                if len(seen_tweets[account]) > 5000:
                    seen_tweets[account].clear()

            except Exception as e:
                print(f"\nERROR @{account}: {e}")
                logging.error(f"Account Error {account}: {e}")

    except Exception as e:
        print(f"\nMAIN ERROR: {e}")
        logging.error(f"Main Loop Error: {e}")

    time.sleep(CHECK_INTERVAL)

