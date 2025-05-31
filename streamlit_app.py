import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pytz
import altair as alt
import pandas as pd
import random
import plotly.graph_objects as go

# ---------- Constants & Helpers -----------

POPULAR_TICKERS = [
    "AAPL", "TSLA", "MSFT", "GOOG", "AMZN", "NVDA", "META", "DIS",
    "NFLX", "BA", "INTC", "AMD", "CRM", "PYPL", "SQ", "UBER", "SHOP"
]

analyzer = SentimentIntensityAnalyzer()

def is_market_open():
    now = datetime.now(pytz.timezone("US/Eastern"))
    weekday = now.weekday()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, microsecond=0)
    return weekday < 5 and market_open <= now <= market_close

@st.cache_data(show_spinner=False)
def get_sentiment(text):
    return analyzer.polarity_scores(text)["compound"]

@st.cache_data(show_spinner=False)
def fetch_news_sentiment(ticker):
    feed_url = f"https://news.google.com/rss/search?q={ticker}+stock"
    feed = feedparser.parse(feed_url)
    headlines = [entry.title for entry in feed.entries[:3]]
    sentiments = [get_sentiment(h) for h in headlines]
    avg_sent = sum(sentiments) / len(sentiments) if sentiments else 0
    return headlines, avg_sent

@st.cache_data(show_spinner=False)
def get_stock_data(ticker, hist_days=7):
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period=f"{hist_days+1}d")
    return hist

def compute_mood_score(pct_change, volume_spike, sentiment):
    return pct_change * 2 + (volume_spike - 1) * 5 + sentiment * 10

def get_mood(ticker, pct_change, volume_spike, sentiment):
    if pct_change > 3:
        return "🤑", f"Investors are vibing with {ticker}."
    elif pct_change < -3:
        return "😱", f"{ticker} is getting hammered today."
    elif volume_spike > 2:
        return "👀", f"Unusual activity around {ticker}."
    elif sentiment > 0.3:
        return "😎", f"{ticker} is coasting with good vibes."
    elif sentiment < -0.3:
        return "🧨", f"Bad press brewing for {ticker}."
    elif abs(pct_change) < 0.3:
        return "😴", f"{ticker} is chilling today."
    else:
        return "🤔", f"Mixed signals for {ticker}."

def build_mood_history_df(hist):
    records = []
    for i in range(len(hist) - 1):
        day1 = hist.index[i]
        day2 = hist.index[i+1]
        close1 = hist["Close"].iloc[i]
        close2 = hist["Close"].iloc[i+1]
        pct_change = ((close2 - close1) / close1) * 100

        if pct_change > 2:
            emoji = "🤑"
        elif pct_change < -2:
            emoji = "😱"
        else:
            emoji = "😐"
        records.append({"date": day2.strftime("%Y-%m-%d"), "pct_change": pct_change, "emoji": emoji})
    return pd.DataFrame(records)

def altair_mood_chart(df):
    base = alt.Chart(df).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%m-%d')),
        y=alt.value(50)
    )
    points = base.mark_text(fontSize=28).encode(
        text='emoji',
        tooltip=[
            alt.Tooltip('date', title='Date'),
            alt.Tooltip('pct_change', title='% Change', format=".2f")
        ]
    )
    return (base.mark_rule(color='#e0e0e0') + points).properties(height=80)

def plot_price_chart(hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['Close'],
        mode='lines',
        line=dict(color='#10b981', width=2),
        name='Close Price'
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=0, r=0),
        xaxis_title='Date',
        yaxis_title='USD',
        height=250,
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )
    return fig

# ------------- Streamlit UI -------------

st.set_page_config(page_title="Stock Mood", layout="wide")
st.markdown("""
    <style>
        .main, .block-container {
            padding: 1rem;
        }
        h1, h2, h3, h4, p {
            font-family: 'Segoe UI', sans-serif;
        }
        .stock-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 1rem;
        }
        .stock-box {
            flex: 1;
            min-width: 200px;
            padding: 1rem;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            background-color: #f9f9f9;
            box-shadow: 0px 1px 3px rgba(0,0,0,0.05);
        }
        .ticker-scroll {
            overflow: hidden;
            white-space: nowrap;
            box-sizing: border-box;
            animation: ticker-scroll 40s linear infinite;
        }
        @keyframes ticker-scroll {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
    </style>
""", unsafe_allow_html=True)

st.title(":chart_with_upwards_trend: Stock Mood of the Day")

st.markdown("""
    Curious how stocks are *feeling* today?
    Get a quick pulse of the market with sentiment, volume, price, and mood — all in one glance.
""")

if st.button("🎲 Surprise Me"):
    st.session_state["tickers"] = [random.choice(POPULAR_TICKERS)]

if "tickers" not in st.session_state:
    st.session_state["tickers"] = []

user_input = st.text_input("Enter up to 3 tickers:", value=", ".join(st.session_state["tickers"]))
tickers = [t.strip().upper() for t in user_input.split(",") if t.strip()][:3]
st.session_state["tickers"] = tickers

market_open_now = is_market_open()
mood_results = []

for ticker in tickers:
    try:
        hist = get_stock_data(ticker)
        if hist.empty or len(hist) < 2:
            st.warning(f"Not enough data for {ticker}.")
            continue

        current_close = hist["Close"][-1]
        prev_close = hist["Close"][-2]
        pct_change = ((current_close - prev_close) / prev_close) * 100

        avg_volume = hist["Volume"][:-1].mean()
        today_volume = hist["Volume"][-1]
        volume_spike = today_volume / avg_volume if avg_volume else 1

        headlines, avg_sentiment = fetch_news_sentiment(ticker)

        mood_emoji, mood_sentence = get_mood(ticker, pct_change, volume_spike, avg_sentiment)
        mood_score = compute_mood_score(pct_change, volume_spike, avg_sentiment)
        mood_hist_df = build_mood_history_df(hist)

        mood_results.append({
            "ticker": ticker,
            "emoji": mood_emoji,
            "sentence": mood_sentence,
            "pct_change": pct_change,
            "volume_spike": volume_spike,
            "sentiment": avg_sentiment,
            "score": mood_score,
            "headlines": headlines,
            "history_df": mood_hist_df,
            "hist_data": hist
        })
    except Exception as e:
        st.warning(f"Error fetching data for {ticker}: {e}")

if not mood_results:
    st.info("Enter valid stock tickers to see their moods.")
    st.stop()

sorted_results = sorted(mood_results, key=lambda x: x["score"], reverse=True)
top7 = sorted_results[:7]
bottom7 = sorted_results[-7:]

st.subheader("🏆 Top 7 Mood Stocks")
top_cols = st.columns(len(top7))
for idx, data in enumerate(top7):
    with top_cols[idx]:
        st.metric(label=f"{data['ticker']} {data['emoji']}", value=f"{data['pct_change']:.2f}%")
        st.caption(data["sentence"])

st.subheader("🔻 Bottom 7 Mood Stocks")
bottom_cols = st.columns(len(bottom7))
for idx, data in enumerate(bottom7):
    with bottom_cols[idx]:
        st.metric(label=f"{data['ticker']} {data['emoji']}", value=f"{data['pct_change']:.2f}%")
        st.caption(data["sentence"])

# Quotron animated bar
st.markdown("""
    <div class='ticker-scroll'>
""", unsafe_allow_html=True)

quote_cols = st.columns(len(mood_results))
clicked_ticker = None

for i, data in enumerate(mood_results):
    with quote_cols[i]:
        if st.button(f"{data['ticker']} {data['emoji']}"):
            clicked_ticker = data['ticker']

if clicked_ticker:
    st.session_state["tickers"] = [clicked_ticker]
    st.experimental_rerun()

st.subheader("📈 Mood History & Price Charts")
for data in mood_results:
    st.markdown(f"### {data['ticker']} {data['emoji']}")
    st.altair_chart(altair_mood_chart(data["history_df"]), use_container_width=True)
    st.plotly_chart(plot_price_chart(data["hist_data"]), use_container_width=True)

st.markdown("""---
<p style='text-align:center;'>Made with ❤️ | Data via Yahoo & Google News</p>""", unsafe_allow_html=True)
