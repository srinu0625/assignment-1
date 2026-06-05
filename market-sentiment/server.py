"""
Reuters / Refinitiv Eikon  ──  Flask API Server
================================================
Run this WHILE your Eikon / Workspace desktop app is open.

  pip install flask flask-cors eikon pandas pytz
  python server.py

Then open index.html in your browser.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import eikon as ek
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz

# ── CONFIG ──────────────────────────────────────────────
APP_KEY = "92e0a59a8e994142bab0f82d8294e1df404da224"
ek.set_app_key(APP_KEY)

app = Flask(__name__)
CORS(app)   # allow index.html (file://) to call us

IST = pytz.timezone("Asia/Kolkata")

# ── NEWS CATEGORIES (from your Python script) ───────────
NEWS_CATEGORIES = {
    "GRAINS":       "( Topic:WHT OR Topic:COR OR Topic:SOY1 OR Topic:SOYML OR Topic:SOIL ) AND Language:LEN",
    "RTRS_GRAINS":  "Source:RTRS AND Language:LEN AND ( Product:GRO OR Topic:GRA ) NOT ( Product:DJNV OR Product:RITV OR Topic:VID OR Product:LCNBC ) NOT Topic:FILING NOT Source:TRANS NOT Topic:PRESSR",
    "COCOA_COFFEE": "( Topic:COC OR Topic:COF ) AND Language:LEN",
    "CRUDE_METALS_FX": "( Topic:CRU OR Topic:METL OR Topic:FRXRTE ) AND Language:LEN",
    "ECON_BIOFUEL": "( Topic:CEN OR Topic:BIOF OR Topic:ECB OR Topic:BOIT OR R:USF= ) AND Language:LEN",
    "WAR":          "Topic:WAR AND Language:LEN",
    "LME_WAREHOUSE":"\"LME WAREHOUSE\"",
    "MCE_REGIONS":  "Topic:MCE AND ( Topic:US OR Topic:EU OR Topic:ASIA ) AND Language:LEN",
    "TARIFFS":      "Topic:TRF AND Language:LEN",
    "POTUS":        "Topic:POTUS AND Language:LEN",
    "USDA_SYC":     "Report:USDA/EST OR Report:SYC/U",
    "COCOA_NCA":    'Topic:COC AND ( "NCA" OR "eca" OR Topic:ASIA ) AND Language:LEN',
    "COFFEE_ICO":   'Topic:COF AND ( "ICO" OR Topic:NAMER OR Topic:EUROP ) AND Language:LEN',
    "SUGAR_CHINA":  "Topic:SUGCN AND Language:LEN",
}

# ── RIC map for price / chart data ──────────────────────
CATEGORY_RICS = {
    "GRAINS":          ["WHc1", "Cc1", "Sc1"],
    "RTRS_GRAINS":     ["WHc1", "Cc1", "Sc1"],
    "COCOA_COFFEE":    ["CCc1", "KCc1"],
    "CRUDE_METALS_FX": ["CLc1", "GCc1", "EUR=", "JPY="],
    "ECON_BIOFUEL":    ["UST10YT=RR", "BOc1"],
    "WAR":             ["CLc1", "GCc1", "UST10YT=RR"],
    "LME_WAREHOUSE":   ["MCUL3", "MALUM3", "MZN3"],
    "MCE_REGIONS":     ["MCOc1"],
    "TARIFFS":         ["EUR=", "CNY=", "JPY=", ".DXY"],
    "POTUS":           [".SPX", ".DJI", ".IXIC"],
    "USDA_SYC":        ["WHc1", "Cc1", "Sc1"],
    "COCOA_NCA":       ["CCc1"],
    "COFFEE_ICO":      ["KCc1"],
    "SUGAR_CHINA":     ["SBc1"],
}

# ── HELPERS ─────────────────────────────────────────────
def strip_html(text):
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", clean).strip()

def to_ist(utc_time):
    if pd.isnull(utc_time):
        return "N/A"
    try:
        return utc_time.tz_convert(IST).strftime("%d %b %Y %H:%M IST")
    except Exception:
        return str(utc_time)

def score_headline(text):
    """Naive sentiment score -1 … +1 from keyword matching."""
    if not text:
        return 0.0
    txt = text.lower()
    bull_words = ["rise","rises","gain","gains","rally","rallies","surge","surges","up","high",
                  "growth","grows","positive","bullish","strong","beat","beats","upgrade","buy",
                  "record","jump","jumps","boost","boosts","recovery","recovers","optimistic"]
    bear_words = ["fall","falls","drop","drops","decline","declines","slump","slumps","down","low",
                  "loss","losses","negative","bearish","weak","miss","misses","downgrade","sell",
                  "crash","crashes","cut","cuts","recession","concern","fears","risk","warn","warning"]
    score = sum(1 for w in bull_words if w in txt) - sum(1 for w in bear_words if w in txt)
    total = sum(1 for w in bull_words + bear_words if w in txt) or 1
    return max(-1.0, min(1.0, score / total))

def get_headline_col(df):
    for c in ["headline", "text", "title", "storyText", "storyTitle"]:
        if c in df.columns:
            return c
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return None

# ── ROUTES ──────────────────────────────────────────────

@app.route("/api/categories")
def categories():
    return jsonify(list(NEWS_CATEGORIES.keys()))


@app.route("/api/news")
def news():
    cat   = request.args.get("category", "GRAINS")
    count = int(request.args.get("count", 20))
    query = NEWS_CATEGORIES.get(cat)
    if not query:
        return jsonify({"error": "Unknown category"}), 400

    try:
        df = ek.get_news_headlines(query, count=count)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if df is None or df.empty:
        return jsonify([])

    # normalise timestamp
    if "versionCreated" in df.columns:
        df["versionCreated"] = pd.to_datetime(df["versionCreated"], errors="coerce", utc=True)

    hcol = get_headline_col(df)
    rows = []
    for _, row in df.iterrows():
        story_id  = str(row.get("storyId", ""))
        headline  = str(row.get(hcol, "")) if hcol else ""
        pub_utc   = row.get("versionCreated")
        sentiment = score_headline(headline)

        # Try to fetch preview
        preview = ""
        if story_id:
            try:
                body = ek.get_news_story(story_id)
                preview = strip_html(body)[:400]
                if len(strip_html(body)) > 400:
                    preview = preview.rsplit(" ", 1)[0] + "..."
            except Exception:
                pass

        # Build story URL
        story_url = ""
        if story_id:
            try:
                u = ek.get_news_story_url(story_id)
                story_url = u if (u and "reuters.com" in u) else \
                    f"https://www.reuters.com/search/news?storyId={story_id}"
            except Exception:
                story_url = f"https://www.reuters.com/search/news?storyId={story_id}"

        rows.append({
            "id":        story_id,
            "headline":  headline,
            "preview":   preview,
            "url":       story_url,
            "time_utc":  pub_utc.isoformat() if pd.notna(pub_utc) else None,
            "time_ist":  to_ist(pub_utc),
            "sentiment": round(sentiment, 4),
            "source":    "Reuters",
            "category":  cat,
        })

    return jsonify(rows)


@app.route("/api/prices")
def prices():
    cat  = request.args.get("category", "GRAINS")
    rics = CATEGORY_RICS.get(cat, ["WHc1"])

    fields = ["CF_LAST", "CF_NETCHNG", "PCTCHNG", "CF_HIGH", "CF_LOW", "CF_VOLUME", "DSPLY_NAME"]
    try:
        df, _ = ek.get_data(rics, fields)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    result = []
    for _, row in df.iterrows():
        result.append({
            "ric":    row.get("Instrument", ""),
            "name":   row.get("DSPLY_NAME", ""),
            "last":   row.get("CF_LAST"),
            "change": row.get("CF_NETCHNG"),
            "pct":    row.get("PCTCHNG"),
            "high":   row.get("CF_HIGH"),
            "low":    row.get("CF_LOW"),
            "volume": row.get("CF_VOLUME"),
        })
    return jsonify(result)


@app.route("/api/timeseries")
def timeseries():
    ric      = request.args.get("ric", "WHc1")
    interval = request.args.get("interval", "daily")   # daily | hourly | minute
    days     = int(request.args.get("days", 90))

    end   = datetime.now(pytz.UTC)
    start = end - timedelta(days=days)

    try:
        df = ek.get_timeseries(
            ric,
            fields=["OPEN","HIGH","LOW","CLOSE","VOLUME"],
            start_date=start.strftime("%Y-%m-%dT%H:%M:%S"),
            end_date=end.strftime("%Y-%m-%dT%H:%M:%S"),
            interval=interval,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if df is None or df.empty:
        return jsonify([])

    bars = []
    for ts, row in df.iterrows():
        bars.append({
            "time":   int(ts.timestamp()),
            "open":   float(row.get("OPEN")  or 0),
            "high":   float(row.get("HIGH")  or 0),
            "low":    float(row.get("LOW")   or 0),
            "close":  float(row.get("CLOSE") or 0),
            "volume": float(row.get("VOLUME") or 0),
        })
    return jsonify(bars)


@app.route("/api/sentiment_summary")
def sentiment_summary():
    """Aggregate sentiment across all 14 categories (fast – only 3 headlines each)."""
    summary = {}
    for cat, query in NEWS_CATEGORIES.items():
        try:
            df = ek.get_news_headlines(query, count=3)
            hcol = get_headline_col(df)
            if df is None or df.empty or not hcol:
                summary[cat] = 0.0
                continue
            scores = [score_headline(str(r)) for r in df[hcol]]
            summary[cat] = round(sum(scores) / len(scores), 4) if scores else 0.0
        except Exception:
            summary[cat] = 0.0
    return jsonify(summary)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "ts": datetime.utcnow().isoformat()})


# ── RUN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✅  Reuters Eikon Flask API  ──  http://localhost:5000")
    print("   Make sure Eikon / Workspace desktop is running first!\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
