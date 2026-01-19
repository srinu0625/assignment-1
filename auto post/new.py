import pandas as pd
import eikon as ek 
import requests
import time 
from datetime import datetime
import pytz
from config import TEAMS_WEBHOOK_URL
import sklearn.decomposition import PCA 
from sklearn.preprocessing import StandardScalar
import winsound # Windows only

CSV_FILE = "D:\\Data\\ES_NQ.csv"
ROLLING_WINDOW = 120
ENTRY_Z = 2.0
EXIT_Z = 0.5

# -------------------------------------------------------
# 1️⃣ CONFIGURATION
# -------------------------------------------------------           
app_key = "92e0a59a8e994142bab0f82d8294e1df404da224"  # 🔸 Replace with your Refinitiv Eikon App Key
ek.set_app_key(app_key)
# select correct colums
df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["es", "nq"]   # clean names
df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)


df = df[["ES Close", "NQ Close"]].dropna()
df.columns = ["ES", "NQ"]

if not trades_df.empty:
    pnl_series = trades_df["Pnl"]
    equity = pnl_series.cumsum()
    drawdown = eqity.cummax()- equity
else:
    pnl_series = pd.Series(dtype = float)
    drawdown = pd.series(dtype = float)

summary_df = pd.Dataframe({})

with pd.Excelwriter(OUTPUT_FILE, engine = "openpyxl") as writer:
    trades_df.to_excel(writer,sheet_name = "Trades" , index = False)
    summary_df.to_excel(writer,sheetname = "summary",index = False)

# final console summary
print("\n=====Final model health===========")
print(summary_df)

returns = np.log(df/df.shift(1)).dropna()
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

    try: 
        response = request.post (webhook_url,headers= headers,date=json,dumps)
    except requests.requestException as e:
        print("%H:%M:%S")
for i  in range (ROLLING_WINDOW, len(returns)):
    window = returns.iloc{i - ROLLING Window:i}
    scalar = StandardScalar scalar.fit_transform(window)

    pca = PCA(n_components = 2)
    pca.fit(X)

    pcs = pca.transform(X)
    pc2_series = pcs (:1,mean_pc2 = pc2_series.mean(),std_pc2 = pc2_series.std())


for i in range (ROOLING_WiNDOW,len(returns)):
    window = returns.lo[i - ROLLING_WINDOW:i]

    scalar = StandardScalar()
    X = scalar.fit_transform(window)
df.columns = ["ES","NQ"]   # clean names
returns = np.log(df/df.shift(1)).dropna()

def main():
    sent_headlines = set()
    print(f"monitoring multiple rss feeds at ")

    while true:
        try:
            if headlines = fetch_all_headlines()
               new_headlines:



# -------------------------------------------------------
# 🔹 Fetch news headlines
# -------------------------------------------------------
for i in range (ROLLING_WINDOW, len(returns)):
    window = returns.iloc[i - ROLLING_WINDOW:i]

    # standardscalar
    scalar = StandardScaler()
    X = scalar.fit_transform(window)

    Exception as ek
    print (f"[{time.strftime("%H:%M:%S")}]")
    return pd.dataframes()
   
    if positon == 0:
        if Zscore > entry_Z:
            position = -1
            entry_pc2= pc2_now
            entry_date = datetime

entry_prices = None

if "versioncreated" in df.columnsd

    pca = PCA(n_components=2)
    pca.fit(X)

    pcs = pca.transform(X)
    pc2_series = pcs[:, 1]

    mean_pc2 = pc2_series.mean()
    std_pc2 = pc2_series.std()

    current_ret = scalar.transform(returns.iloc[i:i+1])
    pc2_now = pca.transform(current_ret)[0, 1]

    zscore = (pc2_now - mean_pc2) / std_pc2


trades_df= pd.dateframes 

def fetch_news(query, count=5):
    try:
        df = ek.get_news_headlines(query, count=count)
        if "versionCreated" in df.columns:
            df["versionCreated"] = pd.to_datetime(df["versionCreated"], errors="coerce", utc=True)
        return df
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Error fetching news for query '{query}': {e}")
        return pd.DataFrame()
    if position == 0:
        if zscore > entry_Z:
            position = -1 
            entry_pc2 = pc2_now
            entry_date = date 

entry_prices = None
       
    
# -------------------------------------------------------
# 🔹 Define news categories
# -------------------------------------------------------
NEWS_CATEGORIES = {

    "GRAINS": "GRAINS AND ENGLISH ",
    "NOPA": "NOPA OR 'Statistics Canada' AND ENGLISH ",
    "CRIDE_METAL_FOREX" : "(CRUDE OR METAL OR FOREX OR TRAFFICS) AND ENGLISH ",
    "WAR": "WAR AND ENGLISH ",
    "BIOFUEL": "(BIOFUEL OR ETHANOL OR BIODIESEL) AND ENGLISH ",
    "RTRS_AGRI": "RTRS AND (GRAINS OR AGRI)",
    "COCO_COFFEE": "(COCOA OR COFFEE) AND ENGLISH ",
    "COTTON_SUGAR": "(COTTON OR SUGAR) AND ENGLISH",
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

