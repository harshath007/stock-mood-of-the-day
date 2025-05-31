import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pytz
import altair as alt
import pandas as pd
import plotly.graph_objects as go
import random

# ---------- Constants & Helpers -----------

analyzer = SentimentIntensityAnalyzer()

@st.cache_data(ttl=3600, show_spinner=False)
def get_top_50_stocks():
    """Returns list of top 50 stock tickers"""
    return ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META", "TSLA", "JPM", "JNJ", "UNH",
            "HD", "PG", "MA", "V", "XOM", "CVX", "MRK", "PEP", "KO", "LLY", "ABBV", "AVGO",
            "BAC", "WMT", "ADBE", "TMO", "CSCO", "ORCL", "ABT", "COST", "MCD", "CRM", "NKE",
            "QCOM", "DHR", "ACN", "TXN", "LIN", "NEE", "AMD", "INTC", "UPS", "UNP", "MS", "PM",
            "RTX", "IBM", "AMGN", "CAT", "LMT"]

@st.cache_data(ttl=3600, show_spinner=False)
def get_sentiment(text):
    """Calculate sentiment score for given text using VADER"""
    return analyzer.polarity_scores(text)["compound"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_news_sentiment(ticker):
    """Fetch news headlines and calculate average sentiment for a stock ticker"""
    try:
        feed_url = f"https://news.google.com/rss/search?q={ticker}+stock"
        feed = feedparser.parse(feed_url)
        headlines = [entry.title for entry in feed.entries[:3]]
        if not headlines:
            headlines = ["No recent news available."]
        sentiments = [get_sentiment(h) for h in headlines]
        avg_sent = sum(sentiments) / len(sentiments) if sentiments else 0
        return headlines, avg_sent
    except Exception as e:
        return ["Failed to fetch news"], 0

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker, hist_days=7):
    """Fetch historical stock data for given ticker"""
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=f"{hist_days+1}d")
        return hist
    except Exception as e:
        return pd.DataFrame()

def compute_mood_score(pct_change, volume_spike, sentiment):
    """Calculate overall mood score based on price change, volume spike, and sentiment"""
    return pct_change * 2 + (volume_spike - 1) * 5 + sentiment * 10

def get_mood(pct_change):
    """Return emoji based on percentage change"""
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
    """Build dataframe with daily mood history"""
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
    """Create candlestick chart for stock price history"""
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

# ----------- Streamlit UI -----------

st.set_page_config(page_title="📊 Stock Mood", layout="wide")

# Custom CSS for ticker bar animation
st.markdown("""
    <style>
        .ticker-bar {
            background: #111827;
            color: white;
            overflow: hidden;
            white-space: nowrap;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .ticker-content {
            display: inline-block;
            padding-left: 100%;
            animation: ticker 90s linear infinite;
        }
        .ticker-content span {
            margin-right: 3rem;
        }
        @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-100%); }
        }
    </style>
""", unsafe_allow_html=True)

st.title("🌞 Welcome to Stock Mood!")
st.caption("Your interactive dashboard for stock vibes — perfect for casual and curious investors.")

# Surprise me button in sidebar
with st.sidebar:
    st.header("🎲 Surprise Me!")
    if st.button("Show Me a Random Stock"):
        st.session_state["random_pick"] = random.choice(get_top_50_stocks())

# Load tickers and process data
TOP_TICKERS = get_top_50_stocks()

# Initialize progress bar for data loading
progress_bar = st.progress(0)
status_text = st.empty()

stock_moods = []
quotron_items = []

# Process each ticker
for idx, ticker in enumerate(TOP_TICKERS):
    try:
        # Update progress
        progress = (idx + 1) / len(TOP_TICKERS)
        progress_bar.progress(progress)
        status_text.text(f"Loading {ticker}... ({idx + 1}/{len(TOP_TICKERS)})")
        
        hist = get_stock_data(ticker)
        if hist.empty or len(hist) < 2:
            continue

        current_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct_change = ((current_close - prev_close) / prev_close) * 100

        # Calculate volume spike
        avg_volume = hist["Volume"][:-1].mean()
        today_volume = hist["Volume"].iloc[-1]
        volume_spike = today_volume / avg_volume if avg_volume > 0 else 1

        # Get news sentiment
        headlines, sentiment = fetch_news_sentiment(ticker)

        # Calculate mood and score
        mood = get_mood(pct_change)
        score = compute_mood_score(pct_change, volume_spike, sentiment)

        stock_moods.append({
            "ticker": ticker,
            "pct_change": pct_change,
            "mood": mood,
            "score": score,
            "hist": hist,
            "headlines": headlines,
            "sentiment": sentiment
        })

        quotron_items.append(f"{mood} <b>{ticker}</b> {pct_change:.2f}%")

    except Exception as e:
        continue

# Clear progress indicators
progress_bar.empty()
status_text.empty()

if not stock_moods:
    st.error("Failed to load stock data. Please check your internet connection and try again.")
    st.stop()

# Generate scrolling ticker (double items for smooth loop)
quotron_html = "<div class='ticker-bar'><div class='ticker-content'>" + " | ".join(quotron_items * 2) + "</div></div>"
st.markdown(quotron_html, unsafe_allow_html=True)

# Show top and bottom performers
best_stocks = sorted(stock_moods, key=lambda x: x["score"], reverse=True)[:5]
worst_stocks = sorted(stock_moods, key=lambda x: x["score"])[:5]

st.subheader("🔥 Top Movers")
cols = st.columns(5)
for i, stock in enumerate(best_stocks):
    with cols[i]:
        if st.button(f"{stock['mood']} {stock['ticker']}", key=f"top_{i}"):
            st.session_state["random_pick"] = stock['ticker']
        st.metric(
            label="Change", 
            value=f"{stock['pct_change']:.2f}%",
            delta=f"Score: {stock['score']:.1f}"
        )

st.subheader("❄️ Worst Performers")
cols = st.columns(5)
for i, stock in enumerate(worst_stocks):
    with cols[i]:
        if st.button(f"{stock['mood']} {stock['ticker']}", key=f"worst_{i}"):
            st.session_state["random_pick"] = stock['ticker']
        st.metric(
            label="Change", 
            value=f"{stock['pct_change']:.2f}%",
            delta=f"Score: {stock['score']:.1f}"
        )

# Detail view for selected/random stock
if "random_pick" in st.session_state:
    selected_ticker = st.session_state["random_pick"]
    st.header(f"📈 {selected_ticker} Details")
    
    # Find the selected stock data
    selected_stock = next((s for s in stock_moods if s["ticker"] == selected_ticker), None)
    
    if selected_stock:
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Price Change", f"{selected_stock['pct_change']:.2f}%")
        with col2:
            st.metric("Mood", selected_stock['mood'])
        with col3:
            st.metric("Mood Score", f"{selected_stock['score']:.2f}")
        with col4:
            st.metric("Sentiment", f"{selected_stock['sentiment']:.3f}")
        
        # Plot price chart
        try:
            chart_fig = plot_price_chart(selected_stock['hist'])
            st.plotly_chart(chart_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create price chart: {str(e)}")
        
        # Show recent news headlines
        st.subheader("📰 Recent News")
        for headline in selected_stock['headlines']:
            sentiment_score = get_sentiment(headline)
            sentiment_emoji = "😊" if sentiment_score > 0.1 else "😐" if sentiment_score > -0.1 else "😞"
            st.caption(f"{sentiment_emoji} {headline}")
        
        # Show mood history
        st.subheader("📊 Recent Mood History")
        try:
            mood_df = build_mood_history_df(selected_stock['hist'])
            if not mood_df.empty:
                for _, row in mood_df.iterrows():
                    st.text(f"{row['date']}: {row['emoji']} {row['pct_change']:.2f}%")
            else:
                st.info("Not enough historical data for mood history.")
        except Exception as e:
            st.error(f"Failed to build mood history: {str(e)}")
    else:
        st.error("Failed to load detailed data for the selected stock.")

# Add some space and footer
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color: #666;'>
        Made with ❤️ for curious minds | Data via Yahoo Finance & Google News
    </p>
""", unsafe_allow_html=True)

# Add refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
