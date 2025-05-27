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

EMOJI_MAP = {
    "bull": "🤑",
    "bear": "😱",
    "neutral": "😐"
}

analyzer = SentimentIntensityAnalyzer()

def is_market_open():
    now = datetime.now(pytz.timezone("US/Eastern"))
    weekday = now.weekday()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
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
    score = pct_change * 2 + (volume_spike - 1) * 5 + sentiment * 10
    return score

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
        return "💤", f"{ticker} is chilling today."
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
    points = base.mark_text(fontSize=30).encode(
        text='emoji',
        tooltip=[
            alt.Tooltip('date', title='Date'),
            alt.Tooltip('pct_change', title='% Change', format=".2f")
        ]
    )
    rule = base.mark_rule(color='lightgray')
    chart = (rule + points).properties(height=80)
    return chart

def plot_price_chart(hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['Close'],
        mode='lines+markers',
        name='Close Price',
        line=dict(color='royalblue', width=2)
    ))
    fig.update_layout(title='Stock Price Trend', xaxis_title='Date', yaxis_title='Price (USD)', height=300)
    return fig

# ------------- Streamlit UI -------------

st.set_page_config(page_title="Stock Mood of the Day", layout="wide")
st.title("📈 Stock Mood of the Day")

# Surprise Me button
if st.button("🎲 Surprise Me!"):
    random_ticker = random.choice(POPULAR_TICKERS)
    st.session_state["tickers"] = [random_ticker]

# Input box or load from session_state
if "tickers" not in st.session_state:
    st.session_state["tickers"] = []

user_input = st.text_input(
    "Enter 1-3 stock tickers (NYSE/NASDAQ), separated by commas:",
    value=", ".join(st.session_state["tickers"]) if st.session_state["tickers"] else ""
)

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
    st.info("Enter valid stock tickers above to see their moods.")
    st.stop()

# Determine the winner of the battle (highest mood score)
winner = max(mood_results, key=lambda x: x["score"]) if len(mood_results) > 1 else None

cols = st.columns(len(mood_results))
for idx, data in enumerate(mood_results):
    with cols[idx]:
        border = "3px solid gold" if winner and data["ticker"] == winner["ticker"] and len(mood_results) > 1 else "1px solid #ddd"
        st.markdown(f"""
            <div style="
                border:{border};
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 5px rgb(0 0 0 / 0.1);
                text-align:center;
                ">
                <h2>{data['ticker']} {data['emoji']} {'🏆' if winner and data['ticker'] == winner['ticker'] and len(mood_results) > 1 else ''}</h2>
                <p style="font-weight:bold;">{data['sentence']}</p>
                <p>Price change: {data['pct_change']:.2f}%</p>
                <p>Volume spike: {data['volume_spike']:.2f}x</p>
                <p>Avg sentiment: {data['sentiment']:.2f}</p>
                <p><em>{'Market is open — live mood.' if market_open_now else 'Market is closed — last close mood.'}</em></p>
                <h4>Recent Headlines:</h4>
                <ul style="text-align:left; padding-left:20px;">
        """, unsafe_allow_html=True)

        for headline in data["headlines"]:
            sent_score = get_sentiment(headline)
            color = "green" if sent_score > 0.3 else "red" if sent_score < -0.3 else "gray"
            st.markdown(f'<li style="color:{color};">{headline}</li>', unsafe_allow_html=True)

        st.markdown("</ul>", unsafe_allow_html=True)
        st.markdown("### Mood History (last 7 days)")
        st.altair_chart(altair_mood_chart(data["history_df"]), use_container_width=True)
        st.markdown("### Stock Price Trend")
        st.plotly_chart(plot_price_chart(data["hist_data"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Stock Mood of the Day | Data from Yahoo Finance & Google News RSS")
