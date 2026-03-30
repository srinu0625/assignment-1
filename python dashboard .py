import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html

# ====================================
# CONFIG
# ====================================

CSV_FILE = r"D:\Data\BR 5min.csv"

# ====================================
# LOAD DATA
# ====================================

df = pd.read_csv(CSV_FILE)

# Fix time format like 4.30 → 4:30
df["Date(GMT)"] = df["Date(GMT)"].astype(str).str.replace(".", ":", regex=False)

# Convert to datetime
df["Date(GMT)"] = pd.to_datetime(df["Date(GMT)"], format="%d-%m-%Y %H:%M")

df = df.sort_values("Date(GMT)")

# ====================================
# STRATEGY METRICS
# ====================================

df["PnL"] = df["Close"].diff()

df["Equity"] = df["PnL"].cumsum()

df["Drawdown"] = df["Equity"].cummax() - df["Equity"]

# Indicator
df["EMA20"] = df["Close"].ewm(span=20).mean()

# ====================================
# CREATE SUBPLOTS
# ====================================

fig = make_subplots(

    rows=4,
    cols=1,

    shared_xaxes=True,

    vertical_spacing=0.03,

    subplot_titles=(

        "Price Chart",
        "Equity Curve",
        "Drawdown",
        "PnL Distribution"

    ),

    row_heights=[0.5,0.2,0.15,0.15]
)

# ====================================
# CANDLESTICK
# ====================================

fig.add_trace(

    go.Candlestick(

        x=df["Date(GMT)"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],

        name="Price"

    ),

    row=1,
    col=1
)

# EMA

fig.add_trace(

    go.Scatter(

        x=df["Date(GMT)"],
        y=df["EMA20"],

        mode="lines",

        name="EMA20"

    ),

    row=1,
    col=1
)

# ====================================
# EQUITY CURVE
# ====================================

fig.add_trace(

    go.Scatter(

        x=df["Date(GMT)"],
        y=df["Equity"],

        mode="lines",

        name="Equity Curve"

    ),

    row=2,
    col=1
)

# ====================================
# DRAWDOWN
# ====================================

fig.add_trace(

    go.Scatter(

        x=df["Date(GMT)"],
        y=df["Drawdown"],

        fill="tozeroy",

        name="Drawdown"

    ),

    row=3,
    col=1
)

# ====================================
# PNL DISTRIBUTION
# ====================================

fig.add_trace(

    go.Histogram(

        x=df["PnL"],

        nbinsx=40,

        name="PnL Distribution"

    ),

    row=4,
    col=1
)

# ====================================
# LAYOUT
# ====================================

fig.update_layout(

    template="plotly_dark",

    height=1000,

    title="Quant Trading Strategy Dashboard",

    xaxis_rangeslider_visible=False
)

# ====================================
# DASH APP
# ====================================

app = Dash(__name__)

app.layout = html.Div(

    style={"backgroundColor":"#111111"},

    children=[

        html.H1(

            "Trading Strategy Dashboard",

            style={

                "textAlign":"center",
                "color":"white"

            }

        ),

        dcc.Graph(

            figure=fig

        )

    ]
)

# ====================================
# RUN SERVER
# ====================================

if __name__ == "__main__":

    app.run(debug=True)