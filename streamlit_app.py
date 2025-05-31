import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pytz
import altair as alt
import pandas as pd
import plotly.graph_objects as go

# ---------- Constants & Helpers -----------

analyzer = SentimentIntensityAnalyzer()

@st.cache_data(ttl=3600, show_spinner=False)
def get_top_50_stocks():
    return ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META", "TSLA", "JPM", "JNJ", "UNH",
            "HD", "PG", "MA", "V", "XOM", "CVX", "MRK", "PEP", "KO", "LLY", "ABBV", "AVGO",
            "BAC", "WMT", "ADBE", "TMO", "CSCO", "ORCL", "ABT", "COST", "MCD", "CRM", "NKE",
            "QCOM", "DHR", "ACN", "TXN", "LIN", "NEE", "AMD", "INTC", "UPS", "UNP", "MS", "PM",
            "RTX", "IBM", "AMGN", "CAT", "LMT"]

@st.cache_data(ttl=3600, show_spinner=False)
def get_sentiment(text):
    return analyzer.polarity_scores(text)["compound"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_news_sentiment(ticker):
    feed_url = f"https://news.google.com/rss/search?q={ticker}+stock"
    feed = feedparser.parse(feed_url)
    headlines = [entry.title for entry in feed.entries[:3]]
    if not headlines:
        headlines = ["No recent news available."]
    sentiments = [get_sentiment(h) for h in headlines]
    avg_sent = sum(sentiments) / len(sentiments) if sentiments else 0
    return headlines, avg_sent

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker, hist_days=7):
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period=f"{hist_days+1}d")
    return hist

def compute_mood_score(pct_change, volume_spike, sentiment):
    return pct_change * 2 + (volume_spike - 1) * 5 + sentiment * 10

def get_mood(pct_change):
    if pct_change > 5:
        return "🚀"
    elif pct_change > 1:
        return "📈"
    elif pct_change > -1:
        return "😐"
    elif pct_change > -5:
        return "📉"
    else:
        return "💥"

def build_mood_history_df(hist):
    records = []
    for i in range(len(hist) - 1):
        day1 = hist.index[i]
        day2 = hist.index[i+1]
        close1 = hist["Close"].iloc[i]
        close2 = hist["Close"].iloc[i+1]
        pct_change = ((close2 - close1) / close1) * 100
        emoji = get_mood(pct_change)
        records.append({"date": day2.strftime("%Y-%m-%d"), "pct_change": pct_change, "emoji": emoji})
    return pd.DataFrame(records)

def plot_price_chart(hist):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='Candlestick'
    ))
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=300,
        margin=dict(t=10, b=10, l=0, r=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    return fig

def plot_mood_history(df):
    chart = alt.Chart(df).mark_text(
        align='center',
        baseline='middle',
        fontSize=24
    ).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.value(0),
        text='emoji'
    ).properties(height=50)
    return chart

# ----------- Streamlit UI -----------

st.set_page_config(page_title="📊 Stock Mood App", layout="wide")

st.markdown("""
    <style>
        .ticker-bar {
            background: #111827;
            color: white;
            overflow: hidden;
            white-space: nowrap;
            padding: 0.5rem;
            font-size: 1rem;
            position: relative;
        }
        .ticker-content {
            display: inline-block;
            padding-left: 100%;
            animation: ticker 60s linear infinite;
        }
        .ticker-content span {
            margin-right: 3rem;
        }
        @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-100%); }
        }
        @media (max-width: 768px) {
            .stock-columns {
                grid-template-columns: 1fr !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Stock Mood of the Day")

# Load tickers
TOP_TICKERS = get_top_50_stocks()

# Sidebar search
with st.sidebar:
    st.header("🔍 Search Ticker")
    search_ticker = st.text_input("Enter Ticker (e.g., AAPL)").upper()
    show_history = st.checkbox("Show Mood History Chart")

stock_moods = []
quotron_items = []

for ticker in TOP_TICKERS:
    try:
        hist = get_stock_data(ticker)
        if hist.empty or len(hist) < 2:
            continue

        current_close = hist["Close"][-1]
        prev_close = hist["Close"][-2]
        pct_change = ((current_close - prev_close) / prev_close) * 100

        avg_volume = hist["Volume"][:-1].mean()
        today_volume = hist["Volume"][-1]
        volume_spike = today_volume / avg_volume if avg_volume > 0 else 1

        headlines, sentiment = fetch_news_sentiment(ticker)

        mood = get_mood(pct_change)
        score = compute_mood_score(pct_change, volume_spike, sentiment)

        stock_moods.append({
            "ticker": ticker,
            "pct_change": pct_change,
            "mood": mood,
            "score": score,
            "hist": hist,
            "headlines": headlines
        })

        quotron_items.append(f"{mood} <b>{ticker}</b> {pct_change:.2f}%")

    except Exception as e:
        st.warning(f"⚠️ Error loading data for {ticker}: {e}")
        continue

# Generate Quotron HTML (double the content for seamless loop)
quotron_html = "<div class='ticker-bar'><div class='ticker-content'>" + " | ".join(quotron_items * 2) + "</div></div>"
st.markdown(quotron_html, unsafe_allow_html=True)

# Sort
best_stocks = sorted(stock_moods, key=lambda x: x["score"], reverse=True)[:5]
bad_stocks = sorted(stock_moods, key=lambda x: x["score"])[:5]

# Top Moods
st.header("🔥 Top Mood Stocks")
cols = st.columns(5)
for i, stock in enumerate(best_stocks):
    with cols[i]:
        st.metric(label=f"{stock['mood']} {stock['ticker']}", value=f"{stock['pct_change']:.2f}%")
        st.plotly_chart(plot_price_chart(stock['hist']), use_container_width=True)
        for headline in stock["headlines"]:
            st.caption(f"📰 {headline}")
        if show_history:
            st.altair_chart(plot_mood_history(build_mood_history_df(stock['hist'])), use_container_width=True)

# Worst Moods
st.header("❄️ Worst Mood Stocks")
cols = st.columns(5)
for i, stock in enumerate(bad_stocks):
    with cols[i]:
        st.metric(label=f"{stock['mood']} {stock['ticker']}", value=f"{stock['pct_change']:.2f}%")
        st.plotly_chart(plot_price_chart(stock['hist']), use_container_width=True)
        for headline in stock["headlines"]:
            st.caption(f"📰 {headline}")
        if show_history:
            st.altair_chart(plot_mood_history(build_mood_history_df(stock['hist'])), use_container_width=True)

# Manual search view
if search_ticker:
    st.header(f"🔎 {search_ticker} Details")
    try:
        hist = get_stock_data(search_ticker)
        headlines, sentiment = fetch_news_sentiment(search_ticker)
        st.plotly_chart(plot_price_chart(hist), use_container_width=True)
        st.markdown(f"**News Sentiment**: {sentiment:.2f}")
        for headline in headlines:
            st.caption(f"📰 {headline}")
        if show_history:
            df = build_mood_history_df(hist)
            st.altair_chart(plot_mood_history(df), use_container_width=True)
    except Exception as e:
        st.error(f"Could not load data for {search_ticker}: {e}")

st.markdown("""---<p style='text-align:center;'>Made with ❤️ | Data via Yahoo & Google News</p>""", unsafe_allow_html=True)
