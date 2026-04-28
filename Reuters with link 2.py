import pandas as pd
import eikon as ek
import requests
import time
import re
from datetime import datetime, timedelta
import pytz

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
TEAMS_WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/60b2e30fbc954d44a0ad6a2fbe958ce2/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b0w27fZV4iTXdMNFwd8HgbYeen3xyVdALXyf8HO-8Ac"

ek.set_app_key(APP_KEY)

# -------------------------------------------------------
# NEWS CATEGORIES
# -------------------------------------------------------
NEWS_CATEGORIES = {
    "GRAINS": "( Topic:WHT OR Topic:COR OR Topic:SOY1 OR Topic:SOYML OR Topic:SOIL ) AND Language:LEN",
    "RTRS_GRAINS": "Source:RTRS AND Language:LEN AND ( Product:GRO OR Topic:GRA ) NOT ( Product:DJNV OR Product:RITV OR Topic:VID OR Product:LCNBC ) NOT Topic:FILING NOT Source:TRANS NOT Topic:PRESSR",
    "COCOA_COFFEE": "( Topic:COC OR Topic:COF ) AND Language:LEN",
    "CRUDE_METALS_FX": "( Topic:CRU OR Topic:METL OR Topic:FRXRTE ) AND Language:LEN",
    "ECON_BIOFUEL": "( Topic:CEN OR Topic:BIOF OR Topic:ECB OR Topic:BOIT OR R:USF= ) AND Language:LEN",
    "WAR": "Topic:WAR AND Language:LEN",
    "LME_WAREHOUSE": "\"LME WAREHOUSE\"",
    "MCE_REGIONS": "Topic:MCE AND ( Topic:US OR Topic:EU OR Topic:ASIA ) AND Language:LEN",
    "TARIFFS": "Topic:TRF AND Language:LEN",
    "POTUS": "Topic:POTUS AND Language:LEN",
    "USDA_SYC": "Report:USDA/EST OR Report:SYC/U",
    "COCOA_NCA": 'Topic:COC AND ( "NCA" OR "eca" OR Topic:ASIA ) AND Language:LEN',
    "COFFEE_ICO": 'Topic:COF AND ( "ICO" OR Topic:NAMER OR Topic:EUROP ) AND Language:LEN',
    "SUGAR_CHINA": "Topic:SUGCN AND Language:LEN"
}

# Persistent deduplication across all cycles
seen_stories = set()
FRESHNESS_LIMIT = timedelta(hours=2)
PREVIEW_CHAR_LIMIT = 400  # Characters shown as preview in Teams


# -------------------------------------------------------
# STORY PREVIEW FETCHER
# -------------------------------------------------------
def get_story_preview(story_id):
    """
    Fetches the full story body from Eikon for THIS story_id
    and returns a short plain-text preview (~400 chars).
    """
    try:
        story = ek.get_news_story(story_id)
        if not story:
            return ""

        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", " ", story)
        # Collapse whitespace
        clean = re.sub(r"\s+", " ", clean).strip()

        if len(clean) > PREVIEW_CHAR_LIMIT:
            # Cut at last complete word before the limit
            truncated = clean[:PREVIEW_CHAR_LIMIT].rsplit(" ", 1)[0]
            return truncated + "..."

        return clean

    except Exception as e:
        print(f"      ⚠️  Preview fetch failed ({story_id}): {e}")
        return ""


# -------------------------------------------------------
# STORY URL BUILDER  — unique per story_id
# -------------------------------------------------------
def get_story_url(story_id):
    """
    Returns a URL that is UNIQUE to this story_id.
      1. Tries the Eikon API (returns a direct Reuters URL when available).
      2. Falls back to a Reuters search deep-link using the story's own ID.
    """
    try:
        url = ek.get_news_story_url(story_id)
        if url and "reuters.com" in url and "error" not in url.lower():
            return url
    except Exception:
        pass

    # Each story_id produces a different URL here — no shared fallback
    return f"https://www.reuters.com/search/news?sort=date-desc&storyId={story_id}"


# -------------------------------------------------------
# TEAMS MESSAGE SENDER
# -------------------------------------------------------
def send_to_teams(category, headline, preview, url, timestamp):
    """
    Posts a Teams message containing:
      - Category tag
      - Full headline
      - Story preview paragraph (~400 chars)
      - Publish time in IST
      - Unique story link
    """
    lines = [
        f"📰 [{category}]",
        f"{headline}",
        "",
    ]

    if preview:
        lines.append(preview)
        lines.append("")

    lines += [
        f"🕒 {timestamp}",
        f"🔗 Read full story: {url}",
    ]

    payload = {"message": "\n".join(lines)}
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        return r.status_code in [200, 202]
    except Exception as e:
        print(f"      ❌ Teams post failed: {e}")
        return False


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def fetch_headlines(query, count=5):
    try:
        df = ek.get_news_headlines(query, count=count)
        if "versionCreated" in df.columns:
            df["versionCreated"] = pd.to_datetime(
                df["versionCreated"], errors="coerce", utc=True
            )
        return df
    except Exception as e:
        print(f"   ❌ Headline fetch error: {e}")
        return pd.DataFrame()


def get_headline_column(df):
    for col in ["headline", "text", "title", "storyText", "storyTitle"]:
        if col in df.columns:
            return col
    for col in df.columns:
        if df[col].dtype == object:
            return col
    return None


def to_india_time(utc_time):
    if pd.isnull(utc_time):
        return "N/A"
    ist = pytz.timezone("Asia/Kolkata")
    return utc_time.tz_convert(ist).strftime("%d %b %Y  %H:%M:%S IST")


# -------------------------------------------------------
# MAIN MONITOR LOOP
# -------------------------------------------------------
def monitor_news():
    print(f"\n🚀 Reuters LIVE monitor started  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    while True:
        try:
            new_posts = 0
            now_utc = datetime.now(pytz.UTC)

            for category, query in NEWS_CATEGORIES.items():

                df = fetch_headlines(query, count=5)
                if df.empty:
                    continue

                headline_col = get_headline_column(df)
                if not headline_col:
                    continue

                for _, row in df.iterrows():

                    story_id = row.get("storyId")
                    if not story_id or pd.isna(story_id):
                        continue

                    story_id_str = str(story_id)

                    # ── Skip already-posted ──
                    if story_id_str in seen_stories:
                        continue

                    # ── Skip stale stories (> 2 hrs old) ──
                    pub_time = row.get("versionCreated")
                    if pd.notna(pub_time) and (now_utc - pub_time) > FRESHNESS_LIMIT:
                        continue

                    headline_text = str(row[headline_col])
                    india_time    = to_india_time(pub_time)

                    # ── FIX 1: URL unique to THIS story_id ──
                    story_url = get_story_url(story_id_str)

                    # ── FIX 2: Preview from THIS story_id ──
                    print(f"   📥 [{category}] {headline_text[:60]}")
                    preview_text = get_story_preview(story_id_str)

                    # ── Post to Teams ──
                    ok = send_to_teams(
                        category  = category,
                        headline  = headline_text,
                        preview   = preview_text,
                        url       = story_url,
                        timestamp = india_time,
                    )

                    if ok:
                        seen_stories.add(story_id_str)
                        new_posts += 1
                        print(f"      ✅ Posted")
                    else:
                        print(f"      ❌ Post failed")

            print(
                f"\n⏱  Scan done  |  New: {new_posts}  |  "
                f"Total seen: {len(seen_stories)}  |  Sleeping 15 s...\n"
            )
            time.sleep(15)

        except KeyboardInterrupt:
            print(f"\n🛑 Stopped.  Total posted: {len(seen_stories)}")
            break
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    monitor_news()