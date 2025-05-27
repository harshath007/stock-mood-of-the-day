import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- Mood engine function ---
def stock_mood_engine(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        if hist.empty or len(hist) < 2:
            return "❓", "Insufficient data for this stock.", None, None
        
        current_price = hist["Close"][-1]
        prev_close = hist["Close"][-2]
        pct_change = ((current_price - prev_close) / prev_close) * 100
        
        avg_volume = hist["Volume"][:-1].mean()
        today_volume = hist["Volume"][-1]
        volume_spike = today_volume / avg_volume if avg_volume else 1
        
        feed_url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock"
        feed = feedparser.parse(feed_url)
        headlines = [entry.title for entry in feed.entries[:3]]
        
        analyzer = SentimentIntensityAnalyzer()
        sentiment_scores = [analyzer.polarity_scores(title)["compound"] for title in headlines]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        mood = "🤔"
        sentence = "Unusual day — mixed signals all around."
        
        if pct_change > 3:
            mood = "🤑"
            sentence = f"Investors are vibing with {ticker_symbol.upper()} today."
        elif pct_change < -3:
            mood = "😱"
            sentence = f"{ticker_symbol.upper()} is getting hammered — rough day on the market."
        elif volume_spike > 2:
            mood = "👀"
            sentence = f"Unusual activity around {ticker_symbol.upper()} — traders are watching closely."
        elif avg_sentiment > 0.3:
            mood = "😎"
            sentence = f"{ticker_symbol.upper()} is coasting with good vibes today."
        elif avg_sentiment < -0.3:
            mood = "🧨"
            sentence = f"Bad press might be brewing for {ticker_symbol.upper()}."
        elif abs(pct_change) < 0.3 and not headlines:
            mood = "💤"
            sentence = f"Nothing to see here — {ticker_symbol.upper()} is chilling today."
        
        return mood, sentence, pct_change, volume_spike
    except Exception as e:
        return "❌", "Error fetching data. Try a valid ticker.", None, None

# --- Streamlit UI ---
st.set_page_config(page_title="Stock Mood of the Day", layout="centered")

st.title("📈 Stock Mood of the Day")
st.markdown("Discover the market vibe of any NYSE/NASDAQ stock — fast & simple.")

ticker_input = st.text_input("Enter stock ticker (e.g. AAPL, TSLA)", "").upper()

# Trending stocks for quick access
trending = ["AAPL", "TSLA", "MSFT", "GOOG", "NVDA", "AMZN", "META"]
st.markdown("**Trending Stocks:** " + " | ".join(
    [f"[{sym}](#{sym})" for sym in trending]
))

if ticker_input:
    mood, sentence, pct, vol_spike = stock_mood_engine(ticker_input)
    if pct is not None:
        st.markdown(f"### {ticker_input} {mood}")
        st.markdown(f"**Mood:** {sentence}")
        st.markdown(f"**Price change:** {pct:.2f}%  |  **Volume spike:** {vol_spike:.2f}x")
    else:
        st.error(sentence)
else:
    st.info("Type a ticker symbol above to see today's stock mood!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Stock Mood of the Day | Data from Yahoo Finance & Google News RSS")
