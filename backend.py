# backend.py

from flask import Flask, jsonify
import requests
import pandas as pd
from textblob import TextBlob
import snscrape.modules.twitter as sntwitter

app = Flask(__name__)

# ---------------------------
# 1. FETCH NEWS (FREE API)
# ---------------------------
def fetch_news():
    url = "https://newsapi.org/v2/top-headlines?category=business&apiKey=YOUR_REAL_KEY"
    try:
        res = requests.get(url).json()
        articles = res.get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except:
        return []


# ---------------------------
# 2. FETCH TWITTER (NO API)
# ---------------------------
def fetch_tweets(query="stock market", limit=20):
    tweets = []
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i > limit:
                break
            tweets.append(tweet.content)
    except:
        pass
    return tweets


# ---------------------------
# 3. SENTIMENT ANALYSIS
# ---------------------------
def get_sentiment(texts):
    scores = []

    for t in texts:
        polarity = TextBlob(t).sentiment.polarity
        scores.append(polarity)

    if not scores:
        return 0, "Neutral"

    avg = sum(scores) / len(scores)

    if avg > 0.1:
        return avg, "Bullish"
    elif avg < -0.1:
        return avg, "Bearish"
    else:
        return avg, "Neutral"


# ---------------------------
# 4. TRADING SIGNAL ENGINE
# ---------------------------
def generate_signal(sentiment_score):
    if sentiment_score > 0.2:
        return "STRONG BUY"
    elif sentiment_score > 0.05:
        return "BUY"
    elif sentiment_score < -0.2:
        return "STRONG SELL"
    elif sentiment_score < -0.05:
        return "SELL"
    else:
        return "HOLD"


# ---------------------------
# MAIN API
# ---------------------------
@app.route("/data")
def data():

    news = fetch_news()
    tweets = fetch_tweets()

    combined = news + tweets

    score, sentiment = get_sentiment(combined)
    signal = generate_signal(score)

    return jsonify({
        "sentiment_score": round(score, 3),
        "overall_sentiment": sentiment,
        "signal": signal,
        "news": news[:5],
        "tweets": tweets[:5]
    })


if __name__ == "__main__":
    app.run(debug=True)