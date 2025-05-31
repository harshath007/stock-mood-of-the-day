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

@st.cache_data(show_spinner=False)
def get_top_50_stocks():
    sp500 = yf.Ticker("^GSPC")
    return ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META", "TSLA", "JPM", "JNJ", "UNH", "HD", "PG", "MA", "V", "XOM", "CVX", "MRK", "PEP", "KO", "LLY", "ABBV", "AVGO", "BAC", "WMT", "ADBE", "TMO", "CSCO", "ORCL", "ABT", "COST", "MCD", "CRM", "NKE", "QCOM", "DHR", "ACN", "TXN", "LIN", "NEE", "AMD", "INTC", "UPS", "UNP", "MS", "PM", "RTX", "IBM", "AMGN", "CAT", "LMT"]

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

# ------------- Streamlit UI -------------

st.set_page_config(page_title="📊 Stock Mood App", layout="wide")

st.markdown("""
    <style>
        .ticker-bar {
            background: #111827;
            color: white;
            overflow: hidden;
            white-space: nowrap;
            box-sizing: border-box;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .ticker-content {
            display: inline-block;
            padding-left: 100%;
            animation: ticker 30s linear infinite;
        }
        @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-100%); }
        }
        .stock-columns {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }
        .stock-box {
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Stock Mood of the Day")

# Load top 50 tickers
TOP_TICKERS = get_top_50_stocks()

# Create ticker data for Quotron
quotron_html = "<div class='ticker-bar'><div class='ticker-content'>"
stock_moods = []

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
        volume_spike = today_volume / avg_volume if avg_volume else 1

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
        quotron_html += f"<span style='margin-right:2rem;'>{mood} <b>{ticker}</b> {pct_change:.2f}%</span>"
    except:
        continue

quotron_html += "</div></div>"
st.markdown(quotron_html, unsafe_allow_html=True)

# Sort stocks by mood score
best_stocks = sorted(stock_moods, key=lambda x: x["score"], reverse=True)[:5]
bad_stocks = sorted(stock_moods, key=lambda x: x["score"])[:5]

st.header("🔥 Top Mood Stocks")
with st.container():
    cols = st.columns(5)
    for i, stock in enumerate(best_stocks):
        with cols[i]:
            st.metric(label=f"{stock['mood']} {stock['ticker']}", value=f"{stock['pct_change']:.2f}%")
            st.plotly_chart(plot_price_chart(stock['hist']), use_container_width=True)
            for headline in stock["headlines"]:
                st.caption(f"📰 {headline}")

st.header("❄️ Worst Mood Stocks")
with st.container():
    cols = st.columns(5)
    for i, stock in enumerate(bad_stocks):
        with cols[i]:
            st.metric(label=f"{stock['mood']} {stock['ticker']}", value=f"{stock['pct_change']:.2f}%")
            st.plotly_chart(plot_price_chart(stock['hist']), use_container_width=True)
            for headline in stock["headlines"]:
                st.caption(f"📰 {headline}")

st.markdown("""---
<p style='text-align:center;'>Made with ❤️ | Data via Yahoo & Google News</p>""", unsafe_allow_html=True)
