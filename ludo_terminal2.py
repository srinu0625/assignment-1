<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Market Sentiment Analyzer</title>

<style>
/* KEEP YOUR EXISTING CSS (UNCHANGED) */
body { font-family: Arial; background:#0a0e17; color:white; }
.card { background:#131722; padding:15px; margin:10px 0; border-radius:8px; }
</style>
</head>

<body>

<h2>📊 Market Sentiment Dashboard</h2>

<div id="lastUpdated">Last updated: --</div>

<div class="card">
    <h3>Overall Sentiment: <span id="overallSentiment">--</span></h3>
    <p>Bullish: <span id="bullishCount">--</span></p>
    <p>Bearish: <span id="bearishCount">--</span></p>
    <p>Total News: <span id="totalCount">--</span></p>
</div>

<div class="card">
    <h3>🚨 Critical Market Events</h3>
    <div id="alertContainer">No alerts</div>
</div>

<div class="card">
    <h3>🔥 Trending Assets</h3>
    <div id="trendingList"></div>
</div>

<script>

// ================= ORIGINAL VARIABLES =================
let allNews = [];
let apiKey = "";

// ================= NEW ADDITIONS =================

// Source weighting
const sourceWeight = {
    'Reuters': 1.0,
    'Bloomberg': 1.0,
    'WSJ': 0.9,
    'CNBC': 0.8,
    'Financial Times': 1.0
};

// Asset sentiment storage
let assetSentimentMap = {};

// Bias logic
function getBias(score) {
    if (score > 0.3) return { text: "Bullish Bias", color: "lightgreen" };
    if (score < -0.3) return { text: "Bearish Bias", color: "red" };
    return { text: "Neutral", color: "orange" };
}

// ================= DEMO DATA =================
function loadDemoData() {
    allNews = [
        {source:'Reuters', published_at:new Date(), impact:3, entities:[{symbol:'AAPL', sentiment_score:0.8}]},
        {source:'Bloomberg', published_at:new Date(), impact:2, entities:[{symbol:'TSLA', sentiment_score:-0.5}]},
        {source:'CNBC', published_at:new Date(), impact:3, entities:[{symbol:'NVDA', sentiment_score:0.6}]},
        {source:'WSJ', published_at:new Date(), impact:3, entities:[{symbol:'AAPL', sentiment_score:0.7}]}
    ];
    processNews();
}

// ================= CORE LOGIC =================
function processNews() {

    const now = Date.now();
    let bullish = 0, bearish = 0;
    let totalSentiment = 0;
    let totalWeight = 0;

    assetSentimentMap = {};

    allNews.forEach(news => {

        const ageHours = (now - new Date(news.published_at)) / (1000 * 60 * 60);
        const timeWeight = Math.exp(-ageHours / 4);

        const srcWeight = sourceWeight[news.source] || 0.6;
        const finalWeight = timeWeight * srcWeight;

        news.entities.forEach(e => {

            totalSentiment += e.sentiment_score * finalWeight;
            totalWeight += finalWeight;

            if (e.sentiment_score > 0.2) bullish++;
            else if (e.sentiment_score < -0.2) bearish++;

            if (!assetSentimentMap[e.symbol]) {
                assetSentimentMap[e.symbol] = { total: 0, weight: 0 };
            }

            assetSentimentMap[e.symbol].total += e.sentiment_score * finalWeight;
            assetSentimentMap[e.symbol].weight += finalWeight;
        });
    });

    const avg = totalWeight ? totalSentiment / totalWeight : 0;

    // UI update
    document.getElementById('overallSentiment').innerText = avg.toFixed(2);
    document.getElementById('bullishCount').innerText = bullish;
    document.getElementById('bearishCount').innerText = bearish;
    document.getElementById('totalCount').innerText = allNews.length;

    displayTrending();
    displayAlerts();

    document.getElementById('lastUpdated').innerText =
        "Last updated: " + new Date().toLocaleTimeString();
}

// ================= TRENDING =================
function displayTrending() {

    const html = Object.keys(assetSentimentMap).map(sym => {

        const data = assetSentimentMap[sym];
        const avg = data.total / data.weight;
        const bias = getBias(avg);

        return `
        <div>
            <b>${sym}</b> → ${avg.toFixed(2)}
            <span style="color:${bias.color}">(${bias.text})</span>
        </div>
        `;
    }).join('');

    document.getElementById('trendingList').innerHTML = html;
}

// ================= ALERTS =================
function displayAlerts() {

    const alerts = allNews.filter(n => {
        const s = n.entities[0].sentiment_score;
        return Math.abs(s) > 0.6 && n.impact === 3;
    });

    const container = document.getElementById('alertContainer');

    if (alerts.length === 0) {
        container.innerHTML = "No critical alerts";
        return;
    }

    container.innerHTML = alerts.map(a => `
        <div>
            ⚠️ ${a.entities[0].symbol} (${a.source})
        </div>
    `).join('');
}

// ================= AUTO REFRESH =================
setInterval(loadDemoData, 60000);

// INIT
loadDemoData();

</script>

</body>
</html>