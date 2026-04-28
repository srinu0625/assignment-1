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
# IMPORTANCE FILTER SETTINGS
# -------------------------------------------------------
# Reuters urgency levels:
#   1 = FLASH     — market-moving, most critical
#   2 = URGENT    — breaking / important
#   3 = Normal    — routine (we skip these)
IMPORTANT_URGENCY_LEVELS = {1, 2}

# Keyword fallback — catches important stories even if urgency field is missing
# Matched case-insensitively against the headline text
IMPORTANT_KEYWORDS = [
    "flash", "urgent", "breaking", "alert",
    "halts", "suspends", "bans", "crashes", "collapses",
    "sanctions", "embargo", "default", "bankruptcy",
    "record high", "record low", "all-time",
    "explosion", "attack", "killed", "dead",
    "USDA", "fed rate", "rate hike", "rate cut",
    "export ban", "crop failure", "drought", "flood",
]

# Urgency emoji labels shown in the Teams post
URGENCY_LABELS = {
    1: "🔴 FLASH",
    2: "🟠 URGENT",
    3: "🟢 NORMAL",   # won't be posted but defined for completeness
}

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
    "LME_WAREHOUSE": '"LME WAREHOUSE"',
    "MCE_REGIONS": "Topic:MCE AND ( Topic:US OR Topic:EU OR Topic:ASIA ) AND Language:LEN",
    "TARIFFS": "Topic:TRF AND Language:LEN",
    "POTUS": "Topic:POTUS AND Language:LEN",
    "USDA_SYC": "Report:USDA/EST OR Report:SYC/U",
    "COCOA_NCA": 'Topic:COC AND ( "NCA" OR "eca" OR Topic:ASIA ) AND Language:LEN',
    "COFFEE_ICO": 'Topic:COF AND ( "ICO" OR Topic:NAMER OR Topic:EUROP ) AND Language:LEN',
    "SUGAR_CHINA": "Topic:SUGCN AND Language:LEN",
}

# Persistent deduplication
seen_stories = set()
FRESHNESS_LIMIT = timedelta(hours=2)
PREVIEW_CHAR_LIMIT = 400


# -------------------------------------------------------
# IMPORTANCE CHECK  ← core logic
# -------------------------------------------------------
def is_important(row, headline_text):
    """
    Returns (True, urgency_level) if the story is important, else (False, None).

    Priority order:
      1. Reuters urgency field (1 or 2)  — most reliable
      2. Keyword match in headline        — fallback when urgency is missing
    """
    # --- Primary: check Eikon urgency field ---
    urgency = row.get("urgency") or row.get("Urgency") or row.get("priority")
    if urgency is not None:
        try:
            urgency_int = int(urgency)
            if urgency_int in IMPORTANT_URGENCY_LEVELS:
                return True, urgency_int
            else:
                # urgency 3 or higher = normal, skip
                return False, urgency_int
        except (ValueError, TypeError):
            pass  # urgency field exists but isn't a number — fall through to keyword check

    # --- Fallback: keyword match in headline ---
    headline_lower = headline_text.lower()
    for kw in IMPORTANT_KEYWORDS:
        if kw.lower() in headline_lower:
            return True, "KW"   # "KW" means keyword-triggered

    return False, None


# -------------------------------------------------------
# STORY PREVIEW FETCHER
# -------------------------------------------------------
def get_story_preview(story_id):
    """Fetch and truncate story body for THIS story_id."""
    try:
        story = ek.get_news_story(story_id)
        if not story:
            return ""
        clean = re.sub(r"<[^>]+>", " ", story)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) > PREVIEW_CHAR_LIMIT:
            return clean[:PREVIEW_CHAR_LIMIT].rsplit(" ", 1)[0] + "..."
        return clean
    except Exception as e:
        print(f"      ⚠️  Preview fetch failed ({story_id}): {e}")
        return ""


# -------------------------------------------------------
# STORY URL  — unique per story_id
# -------------------------------------------------------
def get_story_url(story_id):
    try:
        url = ek.get_news_story_url(story_id)
        if url and "reuters.com" in url and "error" not in url.lower():
            return url
    except Exception:
        pass
    return f"https://www.reuters.com/search/news?sort=date-desc&storyId={story_id}"


# -------------------------------------------------------
# TEAMS SENDER
# -------------------------------------------------------
def send_to_teams(category, headline, preview, url, timestamp, urgency_tag):
    """
    Posts headline + preview + link to Teams.
    urgency_tag is shown at the top so the reader knows why it was flagged.
    """
    lines = [
        f"{urgency_tag}  [{category}]",
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
def fetch_headlines(query, count=10):
    """Fetch more headlines per cycle so we don't miss urgent ones."""
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
# MAIN LOOP
# -------------------------------------------------------
def monitor_news():
    print(f"\n🚀 Reuters IMPORTANT-ONLY monitor started  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Filtering: urgency 1 (FLASH) and 2 (URGENT) + keyword fallback\n")

    while True:
        try:
            new_posts = 0
            skipped   = 0
            now_utc   = datetime.now(pytz.UTC)

            for category, query in NEWS_CATEGORIES.items():

                df = fetch_headlines(query, count=10)
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

                    # Skip already posted
                    if story_id_str in seen_stories:
                        continue

                    # Skip stale (> 2 hrs)
                    pub_time = row.get("versionCreated")
                    if pd.notna(pub_time) and (now_utc - pub_time) > FRESHNESS_LIMIT:
                        continue

                    headline_text = str(row[headline_col])

                    # ── IMPORTANCE GATE ──────────────────────────────
                    important, urgency_val = is_important(row, headline_text)
                    if not important:
                        skipped += 1
                        seen_stories.add(story_id_str)  # mark seen so we don't recheck
                        continue
                    # ────────────────────────────────────────────────

                    # Build the urgency label for the Teams post
                    if urgency_val == "KW":
                        urgency_tag = "🔥 KEYWORD MATCH"
                    else:
                        urgency_tag = URGENCY_LABELS.get(urgency_val, f"⚡ URGENCY-{urgency_val}")

                    india_time   = to_india_time(pub_time)
                    story_url    = get_story_url(story_id_str)

                    print(f"   🔔 [{category}] {urgency_tag}  —  {headline_text[:60]}")
                    preview_text = get_story_preview(story_id_str)

                    ok = send_to_teams(
                        category   = category,
                        headline   = headline_text,
                        preview    = preview_text,
                        url        = story_url,
                        timestamp  = india_time,
                        urgency_tag= urgency_tag,
                    )

                    if ok:
                        seen_stories.add(story_id_str)
                        new_posts += 1
                        print(f"      ✅ Posted")
                    else:
                        print(f"      ❌ Post failed")

            print(
                f"\n⏱  Scan done  |  Posted: {new_posts}  |  "
                f"Skipped (normal): {skipped}  |  "
                f"Total seen: {len(seen_stories)}  |  Sleeping 15 s...\n"
            )
            time.sleep(15)

        except KeyboardInterrupt:
            print(f"\n🛑 Stopped.  Total important stories posted: {len(seen_posts)}")
            break
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    monitor_news()