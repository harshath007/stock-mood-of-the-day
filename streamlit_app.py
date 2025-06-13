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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Root Variables */
    :root {
        --primary-blue: #2563eb;
        --primary-purple: #7c3aed;
        --success-green: #059669;
        --danger-red: #dc2626;
        --warning-orange: #d97706;
        --neutral-gray: #64748b;
        --bg-light: #f8fafc;
        --bg-white: #ffffff;
        --text-dark: #0f172a;
        --text-medium: #334155;
        --text-light: #64748b;
        --border-light: #e2e8f0;
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-light);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--neutral-gray);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-medium);
    }
    
    /* Enhanced Cards */
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid var(--border-light);
        border-left: 4px solid var(--primary-blue);
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple));
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);
        border-left-color: var(--primary-purple);
    }
    
    .metric-card:hover::before {
        transform: scaleX(1);
    }
    
    /* Enhanced News Cards */
    .news-card {
        background: var(--bg-white);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .news-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple));
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-blue);
    }
    
    .news-card:hover::after {
        transform: scaleX(1);
    }
    
    /* Enhanced Ticker Banner */
    .ticker-banner {
        background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        overflow: hidden;
        position: relative;
        box-shadow: var(--shadow-lg);
    }
    
    .ticker-banner::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .ticker-content {
        display: flex;
        white-space: nowrap;
        animation: scroll 120s linear infinite;
        align-items: center;
    }
    
    .ticker-item {
        margin-right: 3rem;
        font-weight: 600;
        font-size: 1.1rem;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    /* Enhanced Headers */
    .section-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--text-dark);
        margin-bottom: 1.5rem;
        text-align: center;
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        letter-spacing: -0.025em;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple));
        border-radius: 2px;
    }
    
    .subsection-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-medium);
        margin: 2.5rem 0 1.5rem 0;
        border-bottom: 2px solid var(--border-light);
        padding-bottom: 0.75rem;
        position: relative;
    }
    
    .subsection-header::before {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: var(--primary-blue);
    }
    
    /* Enhanced Sentiment Badges */
    .sentiment-positive {
        color: var(--success-green);
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.875rem;
        border: 1px solid #86efac;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .sentiment-negative {
        color: var(--danger-red);
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.875rem;
        border: 1px solid #fca5a5;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .sentiment-neutral {
        color: var(--neutral-gray);
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.875rem;
        border: 1px solid #cbd5e1;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Enhanced Market Status */
    .market-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        border-radius: 30px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.875rem;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    
    .market-status::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: pulse-light 2s infinite;
    }
    
    @keyframes pulse-light {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    .market-open {
        background: linear-gradient(135deg, var(--success-green), #10b981);
        color: white;
        animation: pulse-glow 2s infinite;
    }
    
    .market-closed {
        background: linear-gradient(135deg, var(--danger-red), #ef4444);
        color: white;
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(5, 150, 105, 0); }
    }
    
    /* Enhanced Performance Cards */
    .performance-card {
        background: linear-gradient(145deg, var(--bg-white) 0%, var(--bg-light) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .performance-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-blue), var(--primary-purple));
        transition: width 0.3s ease;
    }
    
    .performance-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .performance-card:hover::before {
        width: 8px;
    }
    
    /* Enhanced Global Market Cards */
    .global-market-card {
        background: linear-gradient(145deg, #fefbff 0%, #f3e8ff 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e9d5ff;
        border-left: 4px solid var(--primary-purple);
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .global-market-card::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 0;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-purple), #8b5cf6);
        transition: width 0.3s ease;
    }
    
    .global-market-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .global-market-card:hover::after {
        width: 4px;
    }
    
    /* Enhanced Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 0 16px 16px 0;
        border-right: 1px solid var(--border-light);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Enhanced Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, var(--bg-white), var(--bg-light));
        border: 1px solid var(--border-light);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    /* Enhanced Text Inputs */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid var(--border-light);
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* Enhanced Select Boxes */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid var(--border-light);
        transition: all 0.3s ease;
    }
    
    /* Loading Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .metric-card, .news-card, .performance-card, .global-market-card {
        animation: fadeIn 0.6s ease-out forwards;
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem 1rem;
        }
        
        .section-header {
            font-size: 2rem;
        }
        
        .subsection-header {
            font-size: 1.5rem;
        }
        
        .ticker-item {
            font-size: 1rem;
            margin-right: 2rem;
        }
        
        .metric-card, .news-card, .performance-card {
            padding: 1rem;
        }
    }
    
    /* Enhanced Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple));
        border-radius: 10px;
    }
    
    /* Enhanced Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--bg-light), var(--bg-white));
        border-radius: 12px;
        border: 1px solid var(--border-light);
        font-weight: 600;
    }
    
    /* Toast Notifications */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: var(--shadow-md);
    }
    
    /* Custom Tooltips */
    [title] {
        position: relative;
    }
    
    [title]:hover::after {
        content: attr(title);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: var(--text-dark);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: var(--shadow-lg);
    }
    
    /* Improved spacing and typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        line-height: 1.2;
        color: var(--text-dark);
    }
    
    p {
        line-height: 1.6;
        color: var(--text-medium);
    }
    
    /* Enhanced data tables */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }
    
    .dataframe th {
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .dataframe td {
        padding: 1rem;
        border-bottom: 1px solid var(--border-light);
    }
    
    .dataframe tr:hover {
        background: var(--bg-light);
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

def get_performance_emoji(change_pct):
    """Get emoji based on stock performance"""
    if change_pct >= 10:
        return "🚀"  # Rocket - huge gains
    elif change_pct >= 5:
        return "🔥"  # Fire - strong gains
    elif change_pct >= 2:
        return "📈"  # Chart up - good gains
    elif change_pct >= 0.5:
        return "✅"  # Check - small gains
    elif change_pct >= -0.5:
        return "➡️"  # Arrow right - flat
    elif change_pct >= -2:
        return "⚠️"  # Warning - small losses
    elif change_pct >= -5:
        return "📉"  # Chart down - bad losses
    elif change_pct >= -10:
        return "💔"  # Broken heart - heavy losses
    else:
        return "💥"  # Explosion - crash

def get_volume_emoji(volume_ratio):
    """Get emoji based on volume activity"""
    if volume_ratio >= 3:
        return "🌋"  # Volcano - explosive volume
    elif volume_ratio >= 2:
        return "🔥"  # Fire - high volume
    elif volume_ratio >= 1.5:
        return "📊"  # Chart - elevated volume
    elif volume_ratio >= 0.8:
        return "📈"  # Normal volume
    else:
        return "💤"  # Sleeping - low volume

def get_rsi_emoji(rsi):
    """Get emoji based on RSI levels"""
    if rsi >= 80:
        return "🔴"  # Red circle - extremely overbought
    elif rsi >= 70:
        return "⚠️"  # Warning - overbought
    elif rsi >= 60:
        return "🟡"  # Yellow - getting high
    elif rsi >= 40:
        return "🟢"  # Green - neutral zone
    elif rsi >= 30:
        return "💚"  # Green heart - getting low
    elif rsi >= 20:
        return "🛒"  # Shopping cart - oversold
    else:
        return "💎"  # Diamond - deep value

def get_market_cap_emoji(market_cap):
    """Get emoji based on market cap size"""
    if market_cap >= 1000000000000:  # $1T+
        return "👑"  # Crown - mega cap
    elif market_cap >= 200000000000:  # $200B+
        return "🏰"  # Castle - large cap
    elif market_cap >= 10000000000:   # $10B+
        return "🏢"  # Office building - mid cap
    elif market_cap >= 2000000000:    # $2B+
        return "🏠"  # House - small cap
    else:
        return "🏚️"  # Shack - micro cap

def get_sentiment_emoji(sentiment_score):
    """Get emoji based on news sentiment"""
    if sentiment_score >= 0.5:
        return "😍"  # Heart eyes - very positive
    elif sentiment_score >= 0.3:
        return "😊"  # Happy - positive
    elif sentiment_score >= 0.1:
        return "🙂"  # Slight smile - mildly positive
    elif sentiment_score >= -0.1:
        return "😐"  # Neutral face - neutral
    elif sentiment_score >= -0.3:
        return "😕"  # Worried - mildly negative
    elif sentiment_score >= -0.5:
        return "😞"  # Sad - negative
    else:
        return "😱"  # Screaming - very negative

def calculate_trading_prediction(hist, info=None):
    """
    Calculate trading prediction based on technical indicators
    This is for educational purposes only and not financial advice
    """
    if hist is None or hist.empty or len(hist) < 30:
        return {
            "signal": "INSUFFICIENT_DATA",
            "confidence": 0,
            "reasoning": "Not enough historical data for analysis",
            "prediction_emoji": "❓"
        }
    
    try:
        # Calculate indicators similar to the trading strategy
        close_prices = hist['Close']
        
        # EMA (20-period)
        ema_20 = close_prices.ewm(span=20).mean()
        
        # Triple EMA (TEMA) approximation using 30-period
        ema1 = close_prices.ewm(span=30).mean()
        ema2 = ema1.ewm(span=30).mean()
        ema3 = ema2.ewm(span=30).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        
        # RSI calculation
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Simple ADX approximation using price momentum
        high_low = hist['High'] - hist['Low']
        high_close = abs(hist['High'] - close_prices.shift())
        low_close = abs(hist['Low'] - close_prices.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean()
        
        # Get latest values
        current_ema = ema_20.iloc[-1] if not ema_20.empty else 0
        current_tema = tema.iloc[-1] if not tema.empty else 0
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        current_price = close_prices.iloc[-1]
        
        # Calculate price momentum
        if len(close_prices) >= 5:
            price_momentum = (current_price - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100
        else:
            price_momentum = 0
            
        # Prediction logic based on strategy conditions
        confidence = 0
        reasoning_parts = []
        
        # EMA > TEMA (upward trend)
        if current_ema > current_tema:
            confidence += 30
            reasoning_parts.append("Upward trend detected (EMA > TEMA)")
        else:
            reasoning_parts.append("Downward/sideways trend (EMA ≤ TEMA)")
            
        # RSI < 70 (not overbought)
        if current_rsi < 70:
            confidence += 25
            if current_rsi < 30:
                reasoning_parts.append("Oversold condition (RSI < 30) - potential bounce")
                confidence += 10
            else:
                reasoning_parts.append("RSI in healthy range (< 70)")
        else:
            reasoning_parts.append("Overbought condition (RSI > 70)")
            confidence -= 20
            
        # Price momentum
        if price_momentum > 2:
            confidence += 20
            reasoning_parts.append("Strong positive momentum")
        elif price_momentum > 0:
            confidence += 10
            reasoning_parts.append("Positive momentum")
        else:
            reasoning_parts.append("Negative momentum")
            confidence -= 15
            
        # Volume trend
        if len(hist) >= 10:
            recent_volume = hist['Volume'].iloc[-5:].mean()
            historical_volume = hist['Volume'].iloc[-20:-5].mean()
            if recent_volume > historical_volume * 1.2:
                confidence += 15
                reasoning_parts.append("Increasing volume")
            elif recent_volume < historical_volume * 0.8:
                confidence -= 10
                reasoning_parts.append("Decreasing volume")
                
        # Normalize confidence to 0-100
        confidence = max(0, min(100, confidence))
        
        # Determine signal
        if confidence >= 70:
            signal = "STRONG_BUY"
            prediction_emoji = "🚀"
        elif confidence >= 55:
            signal = "BUY" 
            prediction_emoji = "📈"
        elif confidence >= 45:
            signal = "HOLD"
            prediction_emoji = "➡️"
        elif confidence >= 30:
            signal = "SELL"
            prediction_emoji = "📉"
        else:
            signal = "STRONG_SELL"
            prediction_emoji = "💥"
            
        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": " • ".join(reasoning_parts[:3]),  # Limit to top 3 reasons
            "prediction_emoji": prediction_emoji,
            "rsi": current_rsi,
            "momentum": price_momentum
        }
        
    except Exception as e:
        return {
            "signal": "ERROR",
            "confidence": 0,
            "reasoning": "Unable to calculate prediction",
            "prediction_emoji": "❌"
        }

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
        
        # Stock search functionality
        st.markdown("### 🔍 Stock Search")
        search_ticker = st.text_input("Search any stock:", placeholder="Enter ticker (e.g., AAPL, MSFT)")
        
        if search_ticker and len(search_ticker) > 0:
            search_ticker = search_ticker.upper().strip()
            if st.button(f"📊 View {search_ticker}", key="search_btn"):
                st.session_state['selected_stock'] = search_ticker
                st.session_state['page_selection'] = "📈 Stock Analysis"
        
        st.markdown("---")
        
        page = st.selectbox(
            "Navigate to:",
            ["🏠 Dashboard", "📈 Stock Analysis", "📰 News & Sentiment", "🌍 Global Markets", "🎓 Learning Center"],
            index=0 if 'page_selection' not in st.session_state else 
                  ["🏠 Dashboard", "📈 Stock Analysis", "📰 News & Sentiment", "🌍 Global Markets", "🎓 Learning Center"].index(st.session_state.get('page_selection', "🏠 Dashboard"))
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
            perf_emoji = get_performance_emoji(change_pct)
            ticker_items.append(f'<span class="ticker-item" style="color: {color}">{perf_emoji} {name}: {current:.2f} {change_pct:+.2f}%</span>')

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
            perf_emoji = get_performance_emoji(change)
            st.metric(f"{perf_emoji} S&P 500 (SPY)", f"${current:.2f}", f"{change:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        vix_hist, _ = get_stock_data("^VIX", "5d")
        if vix_hist is not None and not vix_hist.empty:
            current = vix_hist['Close'].iloc[-1]
            vix_emoji = "😌" if current <= 20 else "😐" if current <= 25 else "😰" if current <= 30 else "😱"
            st.metric(f"{vix_emoji} Fear Index (VIX)", f"{current:.2f}", "Volatility Measure")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        gold_hist, _ = get_stock_data("GLD", "5d")
        if gold_hist is not None and not gold_hist.empty:
            current = gold_hist['Close'].iloc[-1]
            prev = gold_hist['Close'].iloc[-2] if len(gold_hist) > 1 else current
            change = ((current - prev) / prev) * 100
            gold_emoji = "💰" if change >= 0 else "📉"
            st.metric(f"{gold_emoji} Gold (GLD)", f"${current:.2f}", f"{change:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        dxy_hist, _ = get_stock_data("UUP", "5d")
        if dxy_hist is not None and not dxy_hist.empty:
            current = dxy_hist['Close'].iloc[-1]
            prev = dxy_hist['Close'].iloc[-2] if len(dxy_hist) > 1 else current
            change = ((current - prev) / prev) * 100
            dollar_emoji = "💵" if change >= 0 else "💸"
            st.metric(f"{dollar_emoji} USD Index (UUP)", f"${current:.2f}", f"{change:.2f}%")
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
        sector_df = pd.DataFrame(sector_data).sort_values("Change %", ascending=False)

    if not sector_df.empty:
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
    else:
        st.warning("No sector data available.")
else:
    st.warning("Sector performance data is missing.")


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
                perf_emoji = get_performance_emoji(row["Change %"])
                volume_emoji = get_volume_emoji(row["Volume Ratio"])
                rsi_emoji = get_rsi_emoji(row["RSI"])
                hist, _ = get_stock_data(row['Ticker'], "3mo")
                prediction = calculate_trading_prediction(hist)

                if st.button(f"{perf_emoji} {row['Ticker']}", key=f"gainer_{row['Ticker']}", help="Click to view detailed analysis"):
                    st.session_state['selected_stock'] = row['Ticker']
                    st.session_state['page_selection'] = "📈 Stock Analysis"
                    st.rerun()

                st.markdown(f"""
                    <div class="performance-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${row['Price']:.2f}</strong><br>
                                <span style="color: {change_color}; font-weight: bold;">
                                    {row['Change %']:.2f}%
                                </span><br>
                                <small>{volume_emoji} Vol: {row['Volume Ratio']:.1f}x | {rsi_emoji} RSI: {row['RSI']:.1f}</small>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.2rem;">{prediction['prediction_emoji']}</div>
                                <div style="font-size: 0.8rem; font-weight: bold; color: #64748b;">
                                    {prediction['signal'].replace('_', ' ')}
                                </div>
                                <div style="font-size: 0.7rem; color: #94a3b8;">
                                    {prediction['confidence']}% confidence
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #64748b; font-style: italic;">
                            ⚠️ Prediction only - not financial advice
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with col2:
            st.markdown("**🔴 Top Losers**")
            for _, row in losers.iterrows():
                change_color = "#10b981" if row["Change %"] >= 0 else "#ef4444"
                perf_emoji = get_performance_emoji(row["Change %"])
                volume_emoji = get_volume_emoji(row["Volume Ratio"])
                rsi_emoji = get_rsi_emoji(row["RSI"])
                hist, _ = get_stock_data(row['Ticker'], "3mo")
                prediction = calculate_trading_prediction(hist)

                if st.button(f"{perf_emoji} {row['Ticker']}", key=f"loser_{row['Ticker']}", help="Click to view detailed analysis"):
                    st.session_state['selected_stock'] = row['Ticker']
                    st.session_state['page_selection'] = "📈 Stock Analysis"
                    st.rerun()

                st.markdown(f"""
                    <div class="performance-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${row['Price']:.2f}</strong><br>
                                <span style="color: {change_color}; font-weight: bold;">
                                    {row['Change %']:.2f}%
                                </span><br>
                                <small>{volume_emoji} Vol: {row['Volume Ratio']:.1f}x | {rsi_emoji} RSI: {row['RSI']:.1f}</small>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.2rem;">{prediction['prediction_emoji']}</div>
                                <div style="font-size: 0.8rem; font-weight: bold; color: #64748b;">
                                    {prediction['signal'].replace('_', ' ')}
                                </div>
                                <div style="font-size: 0.7rem; color: #94a3b8;">
                                    {prediction['confidence']}% confidence
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #64748b; font-style: italic;">
                            ⚠️ Prediction only - not financial advice
                        </div>
                    </div>
                """, unsafe_allow_html=True)
