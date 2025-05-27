import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pytz
import altair as alt
import random

# ------------------------
# Helpers & Core Functions
# ------------------------

def is_market_open():
    now = datetime.now(pytz.timezone("US/Eastern"))
    weekday = now.weekday()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return weekday < 5 and market_open <= now <= market_close

def get_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)["compound"]

def fetch_news_sentiment(ticker):
    feed_url = f"https://news.google.com/rss/search?q={ticker}+stock"
    feed = feedparser.parse(feed_url)
    headlines = [entry.title for entry in feed.entries[:3]]
    sentiments = [get_sentiment(headline) for headline in headlines]
    avg_sent = sum(sentiments) / len(sentiments) if sentiments else 0
    return headlines, avg_sent

def get_stock_mood(ticker, hist_days=7):
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=f"{hist_days+1}d")
        if hist.empty or len(hist) < 2:
            return None

        market_open_now = is_market_open()

        if market_open_now:
            current_price = hist["Close"][-1]
            prev_close = hist["Close"][-2]
        else:
            current_price = hist["Close"][-1]
            prev_close = hist["Close"][-2]

        pct_change = ((current_price - prev_close) / prev_close) * 100
        avg_volume = hist["Volume"][:-1].mean()
        today_volume = hist["Volume"][-1]
        volume_spike = today_volume / avg_volume if avg_volume else 1

        headlines, avg_sentiment = fetch_news_sentiment(ticker)

        # Determine mood emoji and sentence
        mood = "🤔"
        sentence = "Unusual day — mixed signals."

        if pct_change > 3:
            mood = "🤑"
            sentence = f"Investors are vibing with {ticker}."
        elif pct_change < -3:
            mood = "😱"
            sentence = f"{ticker} is getting hammered today."
        elif volume_spike > 2:
            mood = "👀"
            sentence = f"Unusual activity around {ticker}."
        elif avg_sentiment > 0.3:
            mood = "😎"
            sentence = f"{ticker} is coasting with good vibes."
        elif avg_sentiment < -0.3:
            mood = "🧨"
            sentence = f"Bad press brewing for {ticker}."
        elif abs(pct_change) < 0.3 and not headlines:
            mood = "💤"
            sentence = f"{ticker} is chilling today."

        # Create mood history for last 7 days (simplified)
        mood_history = []
        for i in range(hist_days):
            day_pct_change = ((hist["Close"][i+1] - hist["Close"][i]) / hist["Close"][i]) * 100
            if day_pct_change > 2:
                mood_history.append("🤑")
            elif day_pct_change < -2:
                mood_history.append("😱")
            else:
                mood_history.append("😐")

        return {
            "ticker": ticker,
            "mood": mood,
            "sentence": sentence,
            "pct_change": pct_change,
            "volume_spike": volume_spike,
            "market_open": market_open_now,
            "headlines": headlines,
            "mood_history": mood_history
        }

    except Exception as e:
        return None

# ------------------------
# Streamlit App UI
# ------------------------

st.set_page_config(page_title="Stock Mood of the Day", layout="wide")

st.title("📈 Stock Mood of the Day")

# Input tickers (comma separated)
user_input = st.text_input("Enter 1-3 stock tickers (NYSE/NASDAQ), separated by commas:", "AAPL, TSLA")

tickers = [t.strip().upper() for t in user_input.split(",") if t.strip()][:3]

# Fetch moods for tickers
results = []
for t in tickers:
    mood_data = get_stock_mood(t)
    if mood_data:
        results.append(mood_data)
    else:
        st.warning(f"Could not fetch data for ticker: {t}")

# Display mood cards
if results:
    cols = st.columns(len(results))
    for i, data in enumerate(results):
        with cols[i]:
            st.markdown(f"### {data['ticker']} {data['mood']}")
            st.markdown(f"**Mood:** {data['sentence']}")
            st.markdown(f"**Price change:** {data['pct_change']:.2f}%")
            st.markdown(f"**Volume spike:** {data['volume_spike']:.2f}x")

            # Headlines with color-coded sentiment
            st.markdown("**Recent Headlines:**")
            for headline in data["headlines"]:
                sentiment = get_sentiment(headline)
                color = "green" if sentiment > 0.3 else "red" if sentiment < -0.3 else "gray"
                st.markdown(f"<span style='color:{color}'>{headline}</span>", unsafe_allow_html=True)

            # Market open status
            if data["market_open"]:
                st.success("📈 Market is open — live mood.")
            else:
                st.warning("📉 Market is closed — last close mood.")

            # Mood history graph (emojis timeline)
            st.markdown("**Mood History (last 7 days):**")
            # Simple emoji timeline
            emoji_str = "  ".join(data["mood_history"])
            st.markdown(f"<p style='font-size:30px'>{emoji_str}</p>", unsafe_allow_html=True)

else:
    st.info("Enter valid stock tickers above to see their moods.")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Stock Mood of the Day | Data from Yahoo Finance & Google News RSS")
