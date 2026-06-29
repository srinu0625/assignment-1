import pandas as pd
import eikon as ek
import requests
import time
import re
import hashlib
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
# NEWS CATEGORIES  (Reuters / Eikon headline search queries)
# -------------------------------------------------------
NEWS_CATEGORIES = {
    "WEATHER_CLIMATE": '"Weather and Climate" AND Language:LEN',

    "GRAINS_BY_COUNTRY": '( Topic:WHT OR Topic:COR OR Topic:SOY1 OR Topic:SOYML OR soyoil ) '
                          'AND ( "United States" OR Brazil OR Argentina OR "China (PRC)" OR India OR Russia '
                          'OR Ukraine OR "European Union" OR France OR Germany OR Canada OR Australia ) '
                          'AND Language:LEN',

    "TRADE_WAR_CONFLICT": '( "Trade Wars" OR "Military Conflicts" OR WAR ) AND Language:LEN',

    "SOFTS": '( Softs OR "Softs tenders" OR "China softs imports" OR "Global Softs Market" ) '
             'AND Language:LEN',

    "COTTON": 'Cotton AND Language:LEN',

    "SUGAR": '( "Sugar Cane" OR Sugar ) AND Language:LEN',

    "COFFEE_LRC": '( Coffee OR LRCc1 ) AND Language:LEN',

    "US_PRESIDENT_TRUMP": '( "US President" OR TRUMP=CCCL ) AND Language:LEN',

    "TRADE_ESTIMATES_NOPA": '( "Trade estimates" OR "NOPA Weekly Stats" ) AND Language:LEN',

    # ---- Report-related headline keywords (Reuters writing ABOUT these reports) ----
    "WASDE": '"WASDE" AND Language:LEN',

    "GRAIN_STOCKS": '"Grain Stocks" AND Language:LEN',

    "EXPORT_SALES": '( "Export Sales" OR "Flash Sales" ) AND Language:LEN',

    "NOPA_CRUSH": '"NOPA" AND Language:LEN',

    "EXPORT_INSPECTIONS": '"Export Inspections" AND Language:LEN',

    "PROSPECTIVE_PLANTINGS": '"Prospective Plantings" AND Language:LEN',

    "CONAB": 'CONAB AND Language:LEN',

    "STATCAN": 'STATCAN AND Language:LEN',

    "COT_REPORT": '( "COT report" OR "Commitment of Traders" ) AND Language:LEN',

    "COCOA_GRINDINGS": '( "Cocoa Grindings" OR "Cocoa Grinding" ) AND Language:LEN',

    "SUGAR_CONAB_UNICA": '( UNICA OR ( Sugar AND CONAB ) ) AND Language:LEN',

    "US_DROUGHT_MONITOR": '"Drought Monitor" AND Language:LEN',

    "CROP_PROGRESS": '"Crop Progress" AND Language:LEN',

    "ACREAGE_REPORT": '"Acreage" AND Language:LEN',
}

# -------------------------------------------------------
# REPORT PAGES  — direct website monitoring
# -------------------------------------------------------
# These are checked by re-fetching the page and watching for the content
# to change (a new report being published usually changes the page).
# NOTE: this is a generic "did the page change" check, not a verified
# "new report row appeared" check — some pages may trigger false
# positives if they have rotating ads / dynamic widgets. Tell me if a
# specific one gets noisy and I'll tighten that one's detection.
REPORT_PAGES = {
    "WASDE (USDA)": "https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report",
    "US Quarterly Grain Stocks": "https://esmis.nal.usda.gov/publication/grain-stocks",
    "Export Sales (Weekly)": "https://www.fas.usda.gov/data/weekly-export-sales-04022026",
    "NOPA Crush (Monthly)": "https://www.nopa.org/resources/nopa-monthly-crush-report/",
    "Export Inspections": "https://fgisonline.ams.usda.gov/ExportGrainReport/default.aspx",
    "Prospective Plantings": "https://esmis.nal.usda.gov/publication/prospective-plantings",
    "STATCAN Crop Reports": "https://agriculture.canada.ca/en/sector/crops/reports-statistics",
    "COT Report (CME)": "https://www.cmegroup.com/tools-information/quikstrike/commitment-of-traders.html",
    "Cocoa Grindings (Candy USA)": "https://candyusa.com/cocoa-grinds-report/",
    "Cocoa Grindings (Euro Cocoa)": "https://www.eurococoa.com/all-about-grind-stats/",
    "Coffee (USDA FAS)": "https://www.fas.usda.gov/data/commodities/coffee",
    "Coffee Brazil CONAB": "https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras/safra-de-cafe",
    "Sugar UNICA": "https://www.unicadata.com.br",
    "Sugar CONAB": "https://www.conab.gov.br/info-agro/analise-de-mercado-e-estatisticas/acompanhamento-de-safra",
    "US Drought Monitor": "https://droughtmonitor.unl.edu/",
    "Weather (CPC NOAA)": "https://www.cpc.ncep.noaa.gov/",
    "Weekly Crop Progress": "https://esmis.nal.usda.gov/publication/crop-progress",
    "US Economic Calendar": "https://tradingeconomics.com/calendar",
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# Persistent dedup / state (in-memory — resets if the script restarts)
seen_stories = set()
report_page_hashes = {}   # report name -> last seen content hash

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
    urgency = row.get("urgency") or row.get("Urgency") or row.get("priority")
    if urgency is not None:
        try:
            urgency_int = int(urgency)
            if urgency_int in IMPORTANT_URGENCY_LEVELS:
                return True, urgency_int
            else:
                return False, urgency_int
        except (ValueError, TypeError):
            pass

    headline_lower = headline_text.lower()
    for kw in IMPORTANT_KEYWORDS:
        if kw.lower() in headline_lower:
            return True, "KW"

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
        clean = re.sub(r"<style.*?>.*?</style>", "", story, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<script.*?>.*?</script>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
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
# TEAMS SENDER  (shared by news headlines AND report-page alerts)
# -------------------------------------------------------
def send_to_teams(headline, url, preview, timestamp):
    message = (
        f"{headline}\n\n"
        f"{preview}\n\n"
        f"🕒 {timestamp}\n"
        f"🔗 Read full story: {url}"
    )

    payload = {"message": message}
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        return r.status_code in [200, 202]
    except Exception as e:
        print(f"      ❌ Teams post failed: {e}")
        return False


# -------------------------------------------------------
# HELPERS — NEWS
# -------------------------------------------------------
def fetch_headlines(query, count=20):
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


def now_india_time_str():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(pytz.UTC).astimezone(ist).strftime("%d %b %Y  %H:%M:%S IST")


# -------------------------------------------------------
# HELPERS — REPORT PAGES
# -------------------------------------------------------
def check_report_pages():
    """
    Fetch each report page, hash its content, and compare to the last
    known hash. First time a page is seen, we just store the baseline
    (no alert) so the bot doesn't fire on startup. After that, any
    change in the page's content posts an alert to Teams.
    Returns (updates_found, pages_checked).
    """
    updates_found = 0
    pages_checked = 0

    for name, url in REPORT_PAGES.items():
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            pages_checked += 1
            if resp.status_code != 200:
                print(f"      ⚠️  [{name}] HTTP {resp.status_code}, skipping this cycle")
                continue

            content_hash = hashlib.md5(resp.text.encode("utf-8", errors="ignore")).hexdigest()
            previous_hash = report_page_hashes.get(name)

            if previous_hash is None:
                # First time seeing this page — store baseline, don't alert
                report_page_hashes[name] = content_hash
                print(f"      🧭 [{name}] baseline stored (no alert on first run)")
                continue

            if content_hash != previous_hash:
                report_page_hashes[name] = content_hash
                print(f"      🔔 [REPORT] {name} — page changed")
                ok = send_to_teams(
                    headline=f"📊 Report Updated: {name}",
                    preview="This report page appears to have been updated — check for a new release.",
                    url=url,
                    timestamp=now_india_time_str(),
                )
                if ok:
                    updates_found += 1
                    print(f"         ✅ Posted")
                else:
                    print(f"         ❌ Post failed")

        except Exception as e:
            print(f"      ⚠️  [{name}] check failed: {e}")

    return updates_found, pages_checked


# -------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------
def monitor_news():
    print(f"\n🚀 Reuters + Reports monitor started  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Filtering news: urgency 1 (FLASH) and 2 (URGENT) + keyword fallback")
    print(f"   Watching {len(REPORT_PAGES)} report pages for changes\n")

    POLL_INTERVAL = 30

    while True:
        try:
            cycle_start = time.monotonic()
            new_posts = 0
            skipped = 0
            now_utc = datetime.now(pytz.UTC)

            # ============================================================
            # PART 1 — REUTERS NEWS HEADLINES
            # ============================================================
            for category, query in NEWS_CATEGORIES.items():
                df = fetch_headlines(query, count=20)
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

                    if story_id_str in seen_stories:
                        continue

                    pub_time = row.get("versionCreated")
                    if pd.notna(pub_time) and (now_utc - pub_time) > FRESHNESS_LIMIT:
                        continue

                    headline_text = str(row[headline_col])

                    important, urgency_val = is_important(row, headline_text)
                    if not important:
                        skipped += 1
                        continue

                    if urgency_val == "KW":
                        urgency_tag = "🔥 KEYWORD MATCH"
                    else:
                        urgency_tag = URGENCY_LABELS.get(urgency_val, f"⚡ URGENCY-{urgency_val}")

                    india_time = to_india_time(pub_time)
                    story_url = get_story_url(story_id_str)

                    print(f"   🔔 [{category}] {urgency_tag}  —  {headline_text[:60]}")
                    preview_text = get_story_preview(story_id_str)

                    ok = send_to_teams(
                        headline=headline_text,
                        preview=preview_text,
                        url=story_url,
                        timestamp=india_time,
                    )

                    if ok:
                        seen_stories.add(story_id_str)
                        new_posts += 1
                        print(f"      ✅ Posted")
                    else:
                        print(f"      ❌ Post failed")

            # ============================================================
            # PART 2 — REPORT PAGE CHECKS
            # ============================================================
            report_updates, pages_checked = check_report_pages()
            new_posts += report_updates

            print(
                f"\n⏱  Scan done  |  News posted: {new_posts - report_updates}  |  "
                f"Report updates posted: {report_updates}  |  "
                f"Skipped (normal news): {skipped}  |  "
                f"Pages checked: {pages_checked}  |  "
                f"Total news seen: {len(seen_stories)}\n"
            )

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0, POLL_INTERVAL - elapsed)
            print(f"   (cycle took {elapsed:.1f}s, sleeping {sleep_time:.1f}s)\n")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            print(f"\n🛑 Stopped.  Total important stories posted: {len(seen_stories)}")
            break
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0, POLL_INTERVAL - elapsed)
            time.sleep(sleep_time)


if __name__ == "__main__":
    monitor_news()