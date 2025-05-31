import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pytz
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import random

# ---------- Configuration & Setup -----------
st.set_page_config(page_title="StockMood Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Custom CSS for professional UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .news-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    .news-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 5px 20px rgba(59, 130, 246, 0.1);
    }
    
    .ticker-banner {
        background: linear-gradient(90deg, #1e293b, #334155, #475569);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        overflow: hidden;
        position: relative;
    }
    
    .ticker-content {
        display: flex;
        white-space: nowrap;
        animation: scroll 120s linear infinite;
    }
    
    .ticker-item {
        margin-right: 3rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .section-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .subsection-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #334155;
        margin: 2rem 0 1rem 0;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    .sentiment-positive {
        color: #059669;
        background: #d1fae5;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .sentiment-negative {
        color: #dc2626;
        background: #fee2e2;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .sentiment-neutral {
        color: #64748b;
        background: #f1f5f9;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .market-status {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .market-open {
        background: #10b981;
        color: white;
    }
    
    .market-closed {
        background: #ef4444;
        color: white;
    }
    
    .performance-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .global-market-card {
        background: linear-gradient(135deg, #fef7ff 0%, #f3e8ff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #8b5cf6;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------- Data Functions -----------

@st.cache_data(ttl=300)
def get_major_indices():
    return {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones", 
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        "^VIX": "VIX"
    }

@st.cache_data(ttl=300)
def get_global_markets():
    return {
        "^FTSE": "FTSE 100 (UK)",
        "^GDAXI": "DAX (Germany)",
        "^FCHI": "CAC 40 (France)",
        "^N225": "Nikkei 225 (Japan)",
        "^HSI": "Hang Seng (Hong Kong)",
        "000001.SS": "Shanghai Composite",
        "^AXJO": "ASX 200 (Australia)",
        "^BVSP": "Bovespa (Brazil)"
    }

@st.cache_data(ttl=300)
def get_sectors():
    return {
        "XLK": "Technology",
        "XLF": "Financial",
        "XLV": "Healthcare", 
        "XLE": "Energy",
        "XLI": "Industrial",
        "XLC": "Communication",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate"
    }

@st.cache_data(ttl=300)
def get_top_stocks():
    return [
        "AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE",
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BRK-B", "AXP", "USB", "PNC",
        "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN",
        "WMT", "PG", "KO", "PEP", "COST", "MCD", "NKE", "HD", "TGT", "SBUX",
        "BA", "CAT", "GE", "MMM", "XOM", "CVX", "COP", "SLB", "EOG", "KMI",
        "V", "MA", "DIS", "CRM", "ORCL", "IBM", "INTC", "AMD", "QCOM", "CSCO"
    ]

@st.cache_data(ttl=1800)
def get_stock_data(ticker, period="1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        
        if hist.empty:
            return None, None
            
        return hist, info
    except Exception as e:
        return None, None

@st.cache_data(ttl=1800)
def get_comprehensive_news(query, max_articles=10):
    try:
        google_url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(google_url)
        
        articles = []
        for entry in feed.entries[:max_articles]:
            try:
                sentiment_score = analyzer.polarity_scores(entry.title)["compound"]
                
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "Unknown"),
                    "source": entry.get("source", {}).get("title", "Google News"),
                    "sentiment": sentiment_score,
                    "summary": entry.get("summary", entry.title)[:200] + "..."
                })
            except:
                continue
                
        return articles
    except Exception as e:
        return []

def get_sentiment_label(score):
    if score > 0.1:
        return "Positive", "sentiment-positive"
    elif score < -0.1:
        return "Negative", "sentiment-negative"
    else:
        return "Neutral", "sentiment-neutral"

def calculate_performance_metrics(hist):
    if hist is None or hist.empty:
        return {}
    
    current_price = hist['Close'].iloc[-1]
    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
    
    daily_change = ((current_price - prev_price) / prev_price) * 100
    
    volatility = hist['Close'].pct_change().rolling(30).std().iloc[-1] * 100 if len(hist) > 30 else 0
    
    avg_volume = hist['Volume'].mean()
    current_volume = hist['Volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        "current_price": current_price,
        "daily_change": daily_change,
        "volatility": volatility,
        "volume_ratio": volume_ratio,
        "rsi": rsi.iloc[-1] if not rsi.empty else 50,
        "52_week_high": hist['High'].max(),
        "52_week_low": hist['Low'].min()
    }

def create_advanced_chart(hist, ticker):
    if hist is None or hist.empty:
        return None
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{ticker} Price Chart', 'Volume', 'RSI'),
        row_heights=[0.6, 0.2, 0.2]
    )
    
    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    if len(hist) > 20:
        ma20 = hist['Close'].rolling(20).mean()
        fig.add_trace(
            go.Scatter(x=hist.index, y=ma20, line=dict(color='orange', width=1), name='MA20'),
            row=1, col=1
        )
    
    if len(hist) > 50:
        ma50 = hist['Close'].rolling(50).mean()
        fig.add_trace(
            go.Scatter(x=hist.index, y=ma50, line=dict(color='blue', width=1), name='MA50'),
            row=1, col=1
        )
    
    colors = ['red' if close < open else 'green' for close, open in zip(hist['Close'], hist['Open'])]
    fig.add_trace(
        go.Bar(x=hist.index, y=hist['Volume'], marker_color=colors, name='Volume'),
        row=2, col=1
    )
    
    if len(hist) > 14:
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        fig.add_trace(
            go.Scatter(x=hist.index, y=rsi, line=dict(color='purple', width=2), name='RSI'),
            row=3, col=1
        )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text=f"Technical Analysis - {ticker}",
        xaxis_rangeslider_visible=False
    )
    
    return fig

def get_market_status():
    now = datetime.now(pytz.timezone('US/Eastern'))
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    is_weekday = now.weekday() < 5
    is_market_hours = market_open <= now <= market_close
    
    return is_weekday and is_market_hours

# ---------- Educational Functions -----------

def add_educational_tooltips():
    st.markdown("""
    ### 💡 Quick Guide for New Investors
    
    **Market Terms Made Simple:**
    - **Stock Price**: The current cost to buy one share of a company
    - **% Change**: How much the stock price went up (green) or down (red) today
    - **Volume**: How many shares were traded (high volume = lots of interest)
    - **Market Cap**: Total value of all company shares combined
    - **P/E Ratio**: Price compared to earnings (lower often = better value)
    - **RSI**: Momentum indicator (above 70 = might be overpriced, below 30 = might be underpriced)
    - **VIX**: "Fear Index" - measures market uncertainty (higher = more worried investors)
    
    **Reading the Charts:**
    - **Green candles**: Stock closed higher than it opened
    - **Red candles**: Stock closed lower than it opened
    - **Moving averages**: Trend lines that smooth out price movements
    - **Volume bars**: Show trading activity levels
    
    **News Sentiment:**
    - **Positive**: Good news that might push prices up
    - **Negative**: Bad news that might push prices down  
    - **Neutral**: News with unclear impact on prices
    """)

def explain_market_status():
    is_open = get_market_status()
    current_time = datetime.now(pytz.timezone('US/Eastern'))
    
    if is_open:
        st.success("🟢 **Market is OPEN** - Prices are updating in real-time during trading hours (9:30 AM - 4:00 PM ET, Monday-Friday)")
    else:
        st.info("🔴 **Market is CLOSED** - Prices shown are from the last trading session. Markets are closed on weekends and holidays.")
    
    st.caption(f"Current Eastern Time: {current_time.strftime('%I:%M %p on %A, %B %d')}")

def add_beginner_tips():
    with st.expander("🎓 New to Investing? Start Here!"):
        st.markdown("""
        **Getting Started Tips:**
        
        1. **Start Small**: Only invest money you can afford to lose
        2. **Diversify**: Don't put all your money in one stock
        3. **Do Research**: Understand what the company does before buying
        4. **Think Long-term**: Stock prices go up and down daily, but good companies tend to grow over years
        5. **Don't Panic**: Market drops are normal - stay calm and stick to your plan
        
        **What to Look For:**
        - Companies you understand and believe in
        - Consistent growth over time
        - Reasonable P/E ratios (not too high)
        - Positive news sentiment trends
        - Strong fundamentals (good revenue, manageable debt)
        
        **Red Flags:**
        - Stocks that seem "too good to be true"
        - Companies with consistently negative news
        - Extremely high volatility without clear reasons
        - Pressure to "buy now or miss out"
        """)

def enhanced_sidebar():
    with st.sidebar:
        st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h1 style="color: #3b82f6;">📊 StockMood Pro</h1></div>', unsafe_allow_html=True)
        st.caption("Your friendly guide to the stock market")
        
        page = st.selectbox(
            "Navigate to:",
            ["🏠 Dashboard", "📈 Stock Analysis", "📰 News & Sentiment", "🌍 Global Markets", "🎓 Learning Center"],
            index=0
        )
        
        st.markdown("---")
        
        is_open = get_market_status()
        status_text = "🟢 OPEN" if is_open else "🔴 CLOSED"
        st.markdown(f"**Market Status:** {status_text}")
        
        if is_open:
            st.success("✅ Live prices updating")
        else:
            st.info("⏰ Next open: Monday 9:30 AM ET")
        
        current_time = datetime.now(pytz.timezone('US/Eastern'))
        st.markdown(f"**Eastern Time:** {current_time.strftime('%I:%M %p')}")
        
        st.markdown("---")
        
        st.markdown("**📈 Market Snapshot**")
        
        spy_hist, _ = get_stock_data("SPY", "2d")
        if spy_hist is not None and not spy_hist.empty:
            current = spy_hist['Close'].iloc[-1]
            prev = spy_hist['Close'].iloc[-2] if len(spy_hist) > 1 else current
            change = ((current - prev) / prev) * 100
            color = "#10b981" if change >= 0 else "#ef4444"
            st.markdown(f'<div style="color: {color}; font-weight: bold;">S&P 500: {change:+.2f}%</div>', unsafe_allow_html=True)
            st.caption("(Tracks 500 largest US companies)")
        
        vix_hist, _ = get_stock_data("^VIX", "2d")
        if vix_hist is not None and not vix_hist.empty:
            vix_current = vix_hist['Close'].iloc[-1]
            vix_color = "#ef4444" if vix_current > 25 else "#10b981"
            st.markdown(f'<div style="color: {vix_color}; font-weight: bold;">Fear Index: {vix_current:.1f}</div>', unsafe_allow_html=True)
            if vix_current > 30:
                st.caption("😰 High fear - market uncertainty")
            elif vix_current < 20:
                st.caption("😊 Low fear - market calm")
            else:
                st.caption("😐 Moderate uncertainty")
        
        st.markdown("---")
        
        tips = [
            "💡 **Tip**: Diversification means not putting all your money in one stock - it helps reduce risk!",
            "💡 **Tip**: Green usually means prices went up, red means they went down.",
            "💡 **Tip**: Volume shows how many people are buying/selling - high volume often means big news!",
            "💡 **Tip**: P/E ratio compares price to earnings - lower is often better value.",
            "💡 **Tip**: The VIX measures fear - when it's high, the market is usually more volatile.",
            "💡 **Tip**: Moving averages smooth out price movements to show trends more clearly.",
            "💡 **Tip**: Market cap is company size - larger companies are usually less risky."
        ]
        
        daily_tip = tips[datetime.now().day % len(tips)]
        st.info(daily_tip)
        
        st.markdown("---")
        
        if st.button("🎲 Surprise Me!", help="Get a random stock to learn about"):
            random_ticker = random.choice(get_top_stocks())
            st.session_state['surprise_ticker'] = random_ticker
            st.success(f"Let's explore: {random_ticker}")
        
        if 'surprise_ticker' in st.session_state:
            st.markdown(f"**Exploring:** {st.session_state['surprise_ticker']}")
        
        st.markdown("---")
        st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem;">Built for curious minds 💙</div>', unsafe_allow_html=True)
    
    return page

# ---------- Page Functions -----------

def dashboard_page():
    st.markdown('<div class="section-header">📊 StockMood Pro Dashboard</div>', unsafe_allow_html=True)
    
    is_open = get_market_status()
    status_class = "market-open" if is_open else "market-closed"
    status_text = "MARKET OPEN" if is_open else "MARKET CLOSED"
    
    st.markdown(f'<div class="market-status {status_class}">{status_text}</div>', unsafe_allow_html=True)
    
    indices = get_major_indices()
    ticker_items = []
    
    for symbol, name in indices.items():
        hist, _ = get_stock_data(symbol, "5d")
        if hist is not None and not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change_pct = ((current - prev) / prev) * 100
            color = "#10b981" if change_pct >= 0 else "#ef4444"
            arrow = "↑" if change_pct >= 0 else "↓"
            ticker_items.append(f'<span class="ticker-item" style="color: {color}">{name}: {current:.2f} {arrow} {change_pct:.2f}%</span>')
    
    if ticker_items:
        ticker_html = f'<div class="ticker-banner"><div class="ticker-content">{"".join(ticker_items * 3)}</div></div>'
        st.markdown(ticker_html, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        spy_hist, _ = get_stock_data("SPY", "5d")
        if spy_hist is not None and not spy_hist.empty:
            current = spy_hist['Close'].iloc[-1]
            prev = spy_hist['Close'].iloc[-2] if len(spy_hist) > 1 else current
            change = ((current - prev) / prev) * 100
            st.metric("S&P 500 (SPY)", f"${current:.2f}", f"{change:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        vix_hist, _ = get_stock_data("^VIX", "5d")
        if vix_hist is not None and not vix_hist.empty:
            current = vix_hist['Close'].iloc[-1]
            st.metric("Fear Index (VIX)", f"{current:.2f}", "Volatility Measure")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        gold_hist, _ = get_stock_data("GLD", "5d")
        if gold_hist is not None and not gold_hist.empty:
            current = gold_hist['Close'].iloc[-1]
            prev = gold_hist['Close'].iloc[-2] if len(gold_hist) > 1 else current
            change = ((current - prev) / prev) * 100
            st.metric("Gold (GLD)", f"${current:.2f}", f"{change:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        dxy_hist, _ = get_stock_data("UUP", "5d")
        if dxy_hist is not None and not dxy_hist.empty:
            current = dxy_hist['Close'].iloc[-1]
            st.metric("USD Index (UUP)", f"${current:.2f}", "Dollar Strength")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="subsection-header">🏭 Sector Performance</div>', unsafe_allow_html=True)
    
    sectors = get_sectors()
    sector_data = []
    
    for symbol, name in sectors.items():
        hist, _ = get_stock_data(symbol, "5d")
        if hist is not None and not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev) / prev) * 100
            sector_data.append({"Sector": name, "Change %": change, "Price": current})
    
    if sector_data:
        sector_df = pd.DataFrame(sector_data)
        sector_df = sector_df.sort_values("Change %", ascending=False)
        
        fig = px.bar(
            sector_df, 
            x="Sector", 
            y="Change %",
            color="Change %",
            color_continuous_scale=["red", "yellow", "green"],
            title="Daily Sector Performance"
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="subsection-header">🚀 Top Daily Movers</div>', unsafe_allow_html=True)
    
    stocks = get_top_stocks()
    movers_data = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(stocks[:20]):
        progress_bar.progress((i + 1) / 20)
        status_text.text(f"Analyzing {ticker}...")
        
        hist, info = get_stock_data(ticker, "5d")
        if hist is not None and not hist.empty:
            metrics = calculate_performance_metrics(hist)
            movers_data.append({
                "Ticker": ticker,
                "Price": metrics.get("current_price", 0),
                "Change %": metrics.get("daily_change", 0),
                "Volume Ratio": metrics.get("volume_ratio", 1),
                "RSI": metrics.get("rsi", 50)
            })
    
    progress_bar.empty()
    status_text.empty()
    
    if movers_data:
        movers_df = pd.DataFrame(movers_data)
        
        gainers = movers_df.nlargest(5, "Change %")
        losers = movers_df.nsmallest(5, "Change %")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Top Gainers**")
            for _, row in gainers.iterrows():
                change_color = "#10b981" if row["Change %"] >= 0 else "#ef4444"
                st.markdown(f"""
                <div class="performance-card">
                    <strong>{row['Ticker']}</strong> - ${row['Price']:.2f}<br>
                    <span style="color: {change_color}; font-weight: bold;">
                        {row['Change %']:.2f}% 
                    </span>
                    <small>| RSI: {row['RSI']:.1f}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**🔴 Top Losers**")
            for _, row in losers.iterrows():
                change_color = "#10b981" if row["Change %"] >= 0 else "#ef4444"
                st.markdown(f"""
                <div class="performance-card">
                    <strong>{row['Ticker']}</strong> - ${row['Price']:.2f}<br>
                    <span style="color: {change_color}; font-weight: bold;">
                        {row['Change %']:.2f}%
                    </span>
                    <small>| RSI: {row['RSI']:.1f}</small>
                </div>
                """, unsafe_allow_html=True)

def stock_analysis_page():
    st.markdown('<div class="section-header">📈 Stock Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Enter Stock Ticker:", value="AAPL", help="Enter any valid stock ticker (e.g., AAPL, MSFT, GOOGL)")
    
    with col2:
        time_period = st.selectbox("Time Period:", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    
    if ticker:
        ticker = ticker.upper()
        
        hist, info = get_stock_data(ticker, time_period)
        
        if hist is not None and not hist.empty:
            metrics = calculate_performance_metrics(hist)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Current Price", f"${metrics['current_price']:.2f}", f"{metrics['daily_change']:.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("52W High", f"${metrics['52_week_high']:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("52W Low", f"${metrics['52_week_low']:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("RSI", f"{metrics['rsi']:.1f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col5:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                vol_status = "High" if metrics['volume_ratio'] > 1.5 else "Normal"
                st.metric("Volume", vol_status, f"{metrics['volume_ratio']:.1f}x avg")
                st.markdown('</div>', unsafe_allow_html=True)
            
            chart = create_advanced_chart(hist, ticker)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            if info:
                st.markdown('<div class="subsection-header">🏢 Company Information</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.write(f"**Company:** {info.get('longName', 'N/A')}")
                    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                    st.write(f"**Market Cap:** ${info.get('marketCap', 0):,.0f}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "**Dividend Yield:** N/A")
                    st.write(f"**Beta:** {info.get('beta', 'N/A')}")
                    st.write(f"**52W Change:** {((metrics['current_price'] - metrics['52_week_low']) / metrics['52_week_low'] * 100):.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if 'longBusinessSummary' in info:
                    st.markdown('<div class="subsection-header">📋 Business Summary</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.write(info['longBusinessSummary'])
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="subsection-header">📰 Recent News & Sentiment</div>', unsafe_allow_html=True)
            
            news_articles = get_comprehensive_news(f"{ticker} stock", 8)
            
            if news_articles:
                for article in news_articles:
                    sentiment_label, sentiment_class = get_sentiment_label(article['sentiment'])
                    
                    st.markdown(f"""
                    <div class="news-card">
                        <h4 style="margin-bottom: 0.5rem; color: #1e293b;">{article['title']}</h4>
                        <div style="margin-bottom: 0.8rem;">
                            <span class="{sentiment_class}">{sentiment_label} ({article['sentiment']:.3f})</span>
                            <span style="margin-left: 1rem; color: #64748b; font-size: 0.9rem;">
                                {article['source']} • {article['published']}
                            </span>
                        </div>
                        <p style="color: #475569; line-height: 1.5;">{article['summary']}</p>
                        <a href="{article['link']}" target="_blank" style="color: #3b82f6; text-decoration: none;">
                            Read full article →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error(f"Could not fetch data for {ticker}. Please check the ticker symbol.")

def news_page():
    st.markdown('<div class="section-header">📰 Market News & Sentiment Analysis</div>', unsafe_allow_html=True)
    
    news_categories = {
        "📊 Market Overview": "stock market news today",
        "💰 Economic Indicators": "economic indicators GDP inflation",
        "🏦 Federal Reserve": "federal reserve interest rates",
        "🌍 Global Markets": "global markets international trading",
        "⚡ Technology": "technology stocks FAANG",
        "🏥 Healthcare": "healthcare stocks pharmaceuticals",
        "⚡ Energy": "energy stocks oil gas",
        "🏗️ Infrastructure": "infrastructure stocks utilities",
        "💎 Commodities": "commodities gold silver oil",
        "🏠 Real Estate": "real estate REIT housing market"
    }
    
    selected_category = st.selectbox("Select News Category:", list(news_categories.keys()))
    search_query = news_categories[selected_category]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        custom_search = st.text_input("Or search custom topic:", placeholder="Enter your own search terms...")
    with col2:
        if st.button("🔍 Search"):
            if custom_search:
                search_query = custom_search
    
    with st.spinner("Fetching latest news and analyzing sentiment..."):
        articles = get_comprehensive_news(search_query, 15)
    
    if articles:
        sentiments = [article['sentiment'] for article in articles]
        avg_sentiment = np.mean(sentiments)
        positive_count = sum(1 for s in sentiments if s > 0.1)
        negative_count = sum(1 for s in sentiments if s < -0.1)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        st.markdown('<div class="subsection-header">📊 Sentiment Overview</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            overall_label, _ = get_sentiment_label(avg_sentiment)
            st.metric("Overall Sentiment", overall_label, f"Score: {avg_sentiment:.3f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Positive News", f"{positive_count}", f"{positive_count/len(articles)*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Negative News", f"{negative_count}", f"{negative_count/len(articles)*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Neutral News", f"{neutral_count}", f"{neutral_count/len(articles)*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        sentiment_data = pd.DataFrame({
            'Sentiment': ['Positive', 'Negative', 'Neutral'],
            'Count': [positive_count, negative_count, neutral_count]
        })
        
        fig = px.pie(
            sentiment_data, 
            values='Count', 
            names='Sentiment',
            color='Sentiment',
            color_discrete_map={'Positive': '#10b981', 'Negative': '#ef4444', 'Neutral': '#64748b'},
            title="News Sentiment Distribution"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="subsection-header">📰 Latest Articles</div>', unsafe_allow_html=True)
        
        articles_sorted = sorted(articles, key=lambda x: abs(x['sentiment']), reverse=True)
        
        for i, article in enumerate(articles_sorted):
            sentiment_label, sentiment_class = get_sentiment_label(article['sentiment'])
            
            intensity = abs(article['sentiment'])
            if intensity > 0.5:
                intensity_label = "Strong"
            elif intensity > 0.3:
                intensity_label = "Moderate"
            else:
                intensity_label = "Mild"
            
            st.markdown(f"""
            <div class="news-card">
                <h3 style="margin-bottom: 0.8rem; color: #1e293b; line-height: 1.3;">{article['title']}</h3>
                <div style="margin-bottom: 1rem; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                    <span class="{sentiment_class}">{sentiment_label} • {intensity_label}</span>
                    <span style="color: #64748b; font-size: 0.9rem;">Score: {article['sentiment']:.3f}</span>
                    <span style="color: #64748b; font-size: 0.9rem;">{article['source']}</span>
                    <span style="color: #64748b; font-size: 0.9rem;">{article['published']}</span>
                </div>
                <p style="color: #475569; line-height: 1.6; margin-bottom: 1rem;">{article['summary']}</p>
                <a href="{article['link']}" target="_blank" 
                   style="color: #3b82f6; text-decoration: none; font-weight: 500;">
                    Read full article →
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No news articles found for the selected topic. Try a different search term.")

def global_markets_page():
    st.markdown('<div class="section-header">🌍 Global Markets Overview</div>', unsafe_allow_html=True)
    
    global_markets = get_global_markets()
    
    st.markdown('<div class="subsection-header">🏛️ Major Global Indices</div>', unsafe_allow_html=True)
    
    global_data = []
    
    with st.spinner("Loading global market data..."):
        for symbol, name in global_markets.items():
            hist, info = get_stock_data(symbol, "5d")
            if hist is not None and not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev) * 100
                
                global_data.append({
                    "Market": name,
                    "Symbol": symbol,
                    "Price": current,
                    "Change %": change,
                    "Status": "🟢 Open" if change >= 0 else "🔴 Down"
                })
    
    if global_data:
        cols = st.columns(3)
        
        for i, market in enumerate(global_data):
            col_idx = i % 3
            with cols[col_idx]:
                change_color = "#10b981" if market["Change %"] >= 0 else "#ef4444"
                arrow = "↑" if market["Change %"] >= 0 else "↓"
                
                st.markdown(f"""
                <div class="global-market-card">
                    <h4 style="margin-bottom: 0.5rem; color: #1e293b;">{market['Market']}</h4>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b; margin-bottom: 0.5rem;">
                        {market['Price']:.2f}
                    </div>
                    <div style="color: {change_color}; font-weight: bold; font-size: 1.1rem;">
                        {arrow} {market['Change %']:.2f}%
                    </div>
                    <div style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
                        {market['Symbol']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        global_df = pd.DataFrame(global_data)
        
        fig = px.bar(
            global_df,
            x="Market",
            y="Change %",
            color="Change %",
            color_continuous_scale=["red", "yellow", "green"],
            title="Global Markets Daily Performance",
            text="Change %"
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="subsection-header">💱 Currency Markets</div>', unsafe_allow_html=True)
    
    currency_pairs = {
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD", 
        "USDJPY=X": "USD/JPY",
        "USDCAD=X": "USD/CAD",
        "AUDUSD=X": "AUD/USD"
    }
    
    currency_data = []
    
    for symbol, name in currency_pairs.items():
        hist, _ = get_stock_data(symbol, "5d")
        if hist is not None and not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev) / prev) * 100
            currency_data.append({
                "Pair": name,
                "Rate": current,
                "Change %": change
            })
    
    if currency_data:
        cols = st.columns(3)
        for i, currency in enumerate(currency_data):
            col_idx = i % 3
            with cols[col_idx]:
                change_color = "#10b981" if currency["Change %"] >= 0 else "#ef4444"
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="color: #1e293b;">{currency['Pair']}</h4>
                    <div style="font-size: 1.3rem; font-weight: bold;">
                        {currency['Rate']:.4f}
                    </div>
                    <div style="color: {change_color}; font-weight: bold;">
                        {currency['Change %']:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('<div class="subsection-header">🏗️ Commodities</div>', unsafe_allow_html=True)
    
    commodities = {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "Crude Oil",
        "NG=F": "Natural Gas"
    }
    
    commodity_data = []
    
    for symbol, name in commodities.items():
        hist, _ = get_stock_data(symbol, "5d")
        if hist is not None and not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev) / prev) * 100
            commodity_data.append({
                "Commodity": name,
                "Price": current,
                "Change %": change
            })
    
    if commodity_data:
        commodity_df = pd.DataFrame(commodity_data)
        
        fig = px.bar(
            commodity_df,
            x="Commodity",
            y="Change %",
            color="Change %",
            color_continuous_scale=["red", "yellow", "green"],
            title="Commodities Performance",
            text="Change %"
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def learning_center_page():
    st.markdown('<div class="section-header">🎓 Learning Center</div>', unsafe_allow_html=True)
    st.markdown("**Everything you need to know about investing, explained simply**")
    
    st.markdown('<div class="subsection-header">📚 Stock Market Basics</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4>🏢 What Are Stocks?</h4>
        <p>When you buy a stock, you're buying a tiny piece of a company. If the company does well, your piece becomes more valuable. If it struggles, your piece loses value.</p>
        
        <p><strong>Example:</strong> If you buy Apple stock, you own a small part of Apple. When Apple sells more iPhones and makes more money, your stock usually becomes worth more.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
        <h4>📈 How Do Prices Change?</h4>
        <p>Stock prices go up when more people want to buy than sell, and down when more want to sell than buy. It's like an auction!</p>
        
        <p><strong>What moves prices:</strong></p>
        <ul>
        <li>Company news (good earnings = up, bad news = down)</li>
        <li>Economic news (interest rates, employment)</li>
        <li>Investor emotions (fear and greed)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4>🎯 Different Types of Investments</h4>
        <p><strong>Individual Stocks:</strong> Buying pieces of one company (riskier but higher potential)</p>
        <p><strong>Index Funds:</strong> Buying tiny pieces of many companies at once (safer, steadier growth)</p>
        <p><strong>ETFs:</strong> Like index funds but trade like stocks</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
        <h4>⚖️ Risk vs. Reward</h4>
        <p>Generally, the chance for higher returns comes with higher risk of losing money.</p>
        
        <p><strong>Lower Risk:</strong> Big, stable companies, index funds</p>
        <p><strong>Higher Risk:</strong> Small companies, new industries, individual stock picks</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="subsection-header">📊 How to Read This Dashboard</div>', unsafe_allow_html=True)
    
    add_educational_tooltips()
    
    st.markdown('<div class="subsection-header">💰 Simple Investment Strategies</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="performance-card">
        <h4>🐢 Conservative Approach</h4>
        <p><strong>Goal:</strong> Steady, slow growth</p>
        <p><strong>Strategy:</strong> Buy index funds, blue-chip stocks</p>
        <p><strong>Risk:</strong> Low</p>
        <p><strong>Example:</strong> 70% S&P 500 fund, 30% individual large companies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="performance-card">
        <h4>🚗 Balanced Approach</h4>
        <p><strong>Goal:</strong> Moderate growth with some stability</p>
        <p><strong>Strategy:</strong> Mix of index funds and individual stocks</p>
        <p><strong>Risk:</strong> Medium</p>
        <p><strong>Example:</strong> 50% index funds, 50% individual stocks you research</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="performance-card">
        <h4>🚀 Growth Approach</h4>
        <p><strong>Goal:</strong> Higher returns, accepting higher risk</p>
        <p><strong>Strategy:</strong> Individual growth stocks, emerging sectors</p>
        <p><strong>Risk:</strong> High</p>
        <p><strong>Example:</strong> Tech stocks, small companies, sector bets</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="subsection-header">❌ Common Beginner Mistakes</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="news-card">
    <h4 style="color: #dc2626;">Mistakes to Avoid:</h4>
    <ul style="line-height: 1.8;">
    <li><strong>Investing money you need soon:</strong> Only invest money you won't need for at least 5 years</li>
    <li><strong>Putting everything in one stock:</strong> If that company fails, you lose everything</li>
    <li><strong>Trying to time the market:</strong> Nobody can predict short-term price movements</li>
    <li><strong>Panic selling:</strong> Markets go down sometimes - don't sell just because of fear</li>
    <li><strong>Following hot tips:</strong> Do your own research instead of following trends</li>
    <li><strong>Not having a plan:</strong> Know why you're investing and what your goals are</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

def main():
    page = enhanced_sidebar()
    
    if page in ["🏠 Dashboard", "📈 Stock Analysis"]:
        add_beginner_tips()
    
    if page == "🏠 Dashboard":
        explain_market_status()
    
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "📈 Stock Analysis":
        stock_analysis_page()
    elif page == "📰 News & Sentiment":
        news_page()
    elif page == "🌍 Global Markets":
        global_markets_page()
    elif page == "🎓 Learning Center":
        learning_center_page()

if __name__ == "__main__":
    main()
