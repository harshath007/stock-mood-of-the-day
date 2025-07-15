import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os
import time
from typing import Dict, Optional, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="StockMood",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit branding and warnings
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
.stDeployButton {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stAlert > div {display: none;}
</style>
""", unsafe_allow_html=True)

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'quotron_stocks' not in st.session_state:
    st.session_state.quotron_stocks = []

# Initialize sentiment analyzer
@st.cache_resource
def get_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

analyzer = get_sentiment_analyzer()

# Finnhub API configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "default_key")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Major market indices and popular stocks
MAJOR_INDICES = [
    "^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX", "^TNX"  # S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX, 10-Year Treasury
]

POPULAR_STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", 
    "ORCL", "CRM", "ADBE", "INTC", "AMD", "UBER", "LYFT", "SHOP",
    "PYPL", "SQ", "ROKU", "ZOOM", "SNOW", "PLTR", "COIN", "HOOD"
]

def get_stock_emoji(percent_change):
    """Get emoji based on stock mood (percent change)"""
    if percent_change > 3:
        return "🚀"  # Very positive
    elif percent_change > 1:
        return "😊"  # Positive
    elif percent_change > 0:
        return "🙂"  # Slightly positive
    elif percent_change == 0:
        return "😐"  # Neutral
    elif percent_change > -1:
        return "🙁"  # Slightly negative
    elif percent_change > -3:
        return "😟"  # Negative
    else:
        return "💥"  # Very negative

# Fun, interactive styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #f8fafc;
        min-height: 100vh;
        color: #1f2937;
    }
    
    /* Clean container */
    .main-container {
        background: white;
        border-radius: 20px;
        margin: 10px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        color: #1f2937;
    }
    
    .main-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #22c55e, #000000, #ef4444);
        border-radius: 20px 20px 0 0;
    }
    
    /* Clean hero section */
    .hero-section {
        text-align: center;
        padding: 30px 20px;
        background: #000000;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: rotate(0deg) translate(0, 0); }
        50% { transform: rotate(180deg) translate(20px, -20px); }
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        margin: 1rem 0;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    /* Clean Quotron Ticker */
    .quotron {
        background: #000000;
        border-radius: 10px;
        margin: 15px 0;
        overflow: hidden;
        position: relative;
        height: 50px;
        border: 1px solid #333333;
    }
    
    .quotron-content {
        display: flex;
        animation: scroll 90s linear infinite;
        height: 100%;
        align-items: center;
        white-space: nowrap;
        padding: 0 20px;
        gap: 40px;
    }
    
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .quotron-item {
        color: #ffffff;
        font-family: 'Inter', monospace;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.2s ease;
        padding: 10px 16px;
        border-radius: 6px;
        border: 1px solid transparent;
        white-space: nowrap;
        display: inline-block;
    }
    
    .quotron-item:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #ffffff;
        transform: scale(1.05);
    }
    
    .quotron-item.positive {
        color: #22c55e;
    }
    
    .quotron-item.negative {
        color: #ef4444;
    }
    
    .quotron-item.neutral {
        color: #ffffff;
    }
    
    /* Fun popup cards */
    .popup-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.08);
        margin: 15px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(0,0,0,0.05);
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    
    .popup-card:hover {
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 20px 40px rgba(0,0,0,0.12);
    }
    
    /* Clean score display */
    .score-card {
        background: #000000;
        color: white;
        padding: 30px 25px;
        border-radius: 15px;
        text-align: center;
        margin: 15px 0;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        border: 2px solid #e5e7eb;
    }
    
    .score-card:hover {
        transform: scale(1.05) rotate(1deg);
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
    }
    
    .score-number {
        font-size: 5rem;
        font-weight: 900;
        margin: 1rem 0;
        position: relative;
        z-index: 1;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .score-label {
        font-size: 1.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 3px;
        position: relative;
        z-index: 1;
    }
    
    /* Fun recommendation badges */
    .recommendation-badge {
        padding: 20px 30px;
        border-radius: 50px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
        margin: 20px 0;
        font-size: 1.2rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .buy-badge {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
        box-shadow: 0 15px 30px rgba(34, 197, 94, 0.4);
    }
    
    .sell-badge {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        box-shadow: 0 15px 30px rgba(239, 68, 68, 0.4);
    }
    
    .hold-badge {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        box-shadow: 0 15px 30px rgba(245, 158, 11, 0.4);
    }
    
    /* Clean buttons with white text */
    .stButton > button {
        background: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid #000000 !important;
    }
    
    .stButton > button:hover {
        background: #333333 !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        background: #000000 !important;
        color: #ffffff !important;
    }
    
    .stButton > button:focus {
        background: #000000 !important;
        color: #ffffff !important;
        outline: none !important;
    }
    
    /* Force all button text elements to be white */
    .stButton > button, 
    .stButton > button span,
    .stButton > button div,
    .stButton > button p {
        color: #ffffff !important;
    }
    
    /* Fix general text visibility */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        color: #1f2937 !important;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        margin: 10px 0;
        border: 1px solid #cbd5e1;
    }
    
    .metric-card h4 {
        color: #374151 !important;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: 600;
    }
    
    .metric-value {
        color: #1f2937 !important;
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    
    /* Selectbox styling */
    .stSelectbox label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    .stSelectbox > div > div {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px;
        color: #1f2937 !important;
    }
    
    /* Clickable news links */
    .news-link {
        color: #2563eb !important;
        text-decoration: underline;
        cursor: pointer;
        transition: color 0.2s ease;
    }
    
    .news-link:hover {
        color: #1d4ed8 !important;
    }
    
    /* Company info cards */
    .company-info {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        margin-top: 5px;
    }
    
    /* Stock emoji display */
    .stock-emoji {
        font-size: 2rem;
        margin-right: 10px;
    }
    
    /* Stock symbol styling */
    .stock-symbol {
        font-weight: 800;
        font-size: 2rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sentiment badges */
    .sentiment-positive {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9em;
        text-transform: uppercase;
    }
    
    .sentiment-negative {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9em;
        text-transform: uppercase;
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, #6b7280, #4b5563);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9em;
        text-transform: uppercase;
    }
    
    /* News cards */
    .news-card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-left: 4px solid #667eea;
        cursor: pointer;
    }
    
    .news-card:hover {
        transform: translateX(10px) scale(1.02);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        border-left-width: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Finnhub API functions
def get_stock_quote(symbol: str) -> Optional[Dict]:
    """Get real-time stock quote from Finnhub API"""
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'c' in data and data['c'] is not None:
            return {
                'symbol': symbol,
                'current_price': data['c'],
                'change': data['d'],
                'percent_change': data['dp'],
                'high': data['h'],
                'low': data['l'],
                'open': data['o'],
                'previous_close': data['pc']
            }
        return None
    except Exception as e:
        st.error(f"Error fetching quote for {symbol}: {str(e)}")
        return None

def get_stock_news(symbol: str, days: int = 7) -> List[Dict]:
    """Get stock news from Finnhub API"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        news_data = response.json()
        
        # Filter and sort news
        filtered_news = []
        for article in news_data[:20]:  # Limit to 20 articles
            if article.get('headline') and article.get('summary'):
                filtered_news.append({
                    'headline': article['headline'],
                    'summary': article['summary'],
                    'url': article.get('url', ''),
                    'datetime': datetime.fromtimestamp(article['datetime']),
                    'source': article.get('source', 'Unknown')
                })
        
        return sorted(filtered_news, key=lambda x: x['datetime'], reverse=True)
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {str(e)}")
        return []

def get_quotron_data() -> List[Dict]:
    """Get real-time data for quotron ticker using Yahoo Finance"""
    quotron_data = []
    
    # Use cached data if available and recent
    if (st.session_state.quotron_stocks and 
        'last_update' in st.session_state and 
        time.time() - st.session_state.last_update < 60):  # 1 minute cache
        return st.session_state.quotron_stocks
    
    # Use a subset of popular stocks for quotron
    quotron_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ORCL", "CRM", "ADBE", "INTC", "AMD", "UBER", "LYFT", "SHOP",
    "PYPL", "SQ", "ROKU", "ZOOM", "SNOW", "PLTR", "COIN", "HOOD"]
    
    with st.spinner("Loading market data..."):
        for symbol in quotron_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - prev_price
                    percent_change = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    quotron_data.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'change': change,
                        'percent_change': percent_change
                    })
            except Exception as e:
                print(f"Error getting data for {symbol}: {e}")
                continue
    
    st.session_state.quotron_stocks = quotron_data
    st.session_state.last_update = time.time()
    return quotron_data

def create_quotron_ticker():
    """Create the quotron ticker with real stock data"""
    quotron_data = get_quotron_data()
    
    if not quotron_data:
        st.markdown("""
        <div class="quotron">
            <div class="quotron-content">
                <span class="quotron-item">Market data temporarily unavailable</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create ticker items as a single string
    ticker_content = ""
    for stock in quotron_data:
        symbol = stock['symbol']
        price = stock['current_price']
        change = stock['change']
        percent_change = stock['percent_change']
        
        # Determine color and sign
        if change > 0:
            color_class = "positive"
            sign = "+"
        elif change < 0:
            color_class = "negative"
            sign = ""
        else:
            color_class = "neutral"
            sign = ""
        
        # Get mood emoji
        mood_emoji = get_stock_emoji(percent_change)
        
        # Format: EMOJI SYMBOL $PRICE +/-CHANGE%
        ticker_item = f'<span class="quotron-item {color_class}" data-symbol="{symbol}" style="cursor: pointer;">{mood_emoji} {symbol} ${price:.2f} {sign}{percent_change:.2f}%</span>'
        ticker_content += ticker_item
    
    # Repeat content for continuous scrolling
    full_content = ticker_content * 3
    
    # Create the quotron ticker with click handling
    ticker_html = f"""
    <div class="quotron">
        <div class="quotron-content">
            {full_content}
        </div>
    </div>
    """
    
    st.markdown(ticker_html, unsafe_allow_html=True)
    
    # Note: Quotron is display-only, use search or quick select buttons to analyze stocks

def get_stock_info(symbol: str) -> Dict:
    """Get comprehensive stock information from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1y")
        
        # Calculate technical indicators
        close_prices = hist['Close']
        
        # RSI calculation
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        
        # MACD calculation
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal).mean()
            return macd.iloc[-1] - signal_line.iloc[-1] if not macd.empty else 0
        
        # Get week data
        week_data = hist.tail(7)
        week_high = week_data['High'].max()
        week_low = week_data['Low'].min()
        week_change = ((close_prices.iloc[-1] - close_prices.iloc[-7]) / close_prices.iloc[-7]) * 100 if len(close_prices) > 7 else 0
        
        rsi = calculate_rsi(close_prices)
        macd = calculate_macd(close_prices)
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'summary': info.get('longBusinessSummary', 'No summary available'),
            'current_price': info.get('currentPrice', close_prices.iloc[-1]),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'debt_to_equity': info.get('debtToEquity', 0),
            'profit_margin': info.get('profitMargins', 0),
            'roe': info.get('returnOnEquity', 0),
            'revenue_growth': info.get('revenueGrowth', 0),
            'rsi': rsi,
            'macd': macd,
            'week_high': week_high,
            'week_low': week_low,
            'week_change': week_change,
            'volume': info.get('volume', 0),
            'avg_volume': info.get('averageVolume', 0),
            'dividend_yield': info.get('dividendYield', 0) or 0,
            'beta': info.get('beta', 1.0),
            'price_to_book': info.get('priceToBook', 0),
            'earnings_growth': info.get('earningsGrowth', 0)
        }
    except Exception as e:
        st.error(f"Error fetching stock info for {symbol}: {str(e)}")
        return None

def calculate_comprehensive_score(stock_info: Dict, news_sentiment: float) -> int:
    """Calculate comprehensive financial score out of 100"""
    if not stock_info:
        return 50
    
    score = 0
    
    # Financial Health (30 points)
    # Profit Margin (10 points)
    profit_margin = stock_info.get('profit_margin', 0)
    if profit_margin > 0.2:  # >20%
        score += 10
    elif profit_margin > 0.1:  # 10-20%
        score += 7
    elif profit_margin > 0.05:  # 5-10%
        score += 5
    elif profit_margin > 0:  # 0-5%
        score += 3
    
    # Debt to Equity (10 points)
    debt_to_equity = stock_info.get('debt_to_equity', 100)
    if debt_to_equity < 30:
        score += 10
    elif debt_to_equity < 50:
        score += 7
    elif debt_to_equity < 100:
        score += 5
    elif debt_to_equity < 200:
        score += 3
    
    # ROE (10 points)
    roe = stock_info.get('roe', 0)
    if roe > 0.15:  # >15%
        score += 10
    elif roe > 0.1:  # 10-15%
        score += 7
    elif roe > 0.05:  # 5-10%
        score += 5
    elif roe > 0:  # 0-5%
        score += 3
    
    # Technical Indicators (30 points)
    # RSI (15 points)
    rsi = stock_info.get('rsi', 50)
    if 40 <= rsi <= 60:  # Neutral zone
        score += 15
    elif 30 <= rsi <= 70:  # Good zone
        score += 12
    elif 20 <= rsi <= 80:  # Acceptable zone
        score += 8
    else:  # Overbought/Oversold
        score += 5
    
    # MACD (15 points)
    macd = stock_info.get('macd', 0)
    if macd > 0:  # Bullish
        score += 15
    elif macd > -0.5:  # Slightly bearish
        score += 10
    else:  # Bearish
        score += 5
    
    # Valuation (20 points)
    # P/E Ratio (10 points)
    pe_ratio = stock_info.get('pe_ratio', 25)
    if pe_ratio and pe_ratio > 0:
        if 10 <= pe_ratio <= 20:  # Good value
            score += 10
        elif 5 <= pe_ratio <= 30:  # Acceptable
            score += 7
        elif pe_ratio <= 40:  # High but reasonable
            score += 5
        else:  # Overvalued
            score += 2
    
    # Price to Book (10 points)
    ptb = stock_info.get('price_to_book', 3)
    if ptb and ptb > 0:
        if ptb <= 1.5:  # Undervalued
            score += 10
        elif ptb <= 3:  # Fair value
            score += 7
        elif ptb <= 5:  # High but acceptable
            score += 5
        else:  # Overvalued
            score += 2
    
    # Growth & Sentiment (20 points)
    # Revenue Growth (10 points)
    revenue_growth = stock_info.get('revenue_growth', 0)
    if revenue_growth > 0.15:  # >15%
        score += 10
    elif revenue_growth > 0.1:  # 10-15%
        score += 7
    elif revenue_growth > 0.05:  # 5-10%
        score += 5
    elif revenue_growth > 0:  # 0-5%
        score += 3
    
    # News Sentiment (10 points)
    if news_sentiment > 0.3:
        score += 10
    elif news_sentiment > 0.1:
        score += 7
    elif news_sentiment > -0.1:
        score += 5
    elif news_sentiment > -0.3:
        score += 3
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))

def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of text using VADER"""
    scores = analyzer.polarity_scores(text)
    
    # Determine overall sentiment
    if scores['compound'] >= 0.05:
        sentiment = 'positive'
    elif scores['compound'] <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'compound': scores['compound'],
        'positive': scores['pos'],
        'negative': scores['neg'],
        'neutral': scores['neu']
    }

def calculate_sentiment_score(news_data: List[Dict]) -> float:
    """Calculate overall sentiment score from news data"""
    if not news_data:
        return 0.0
    
    total_score = 0.0
    for article in news_data:
        headline_sentiment = analyze_sentiment(article['headline'])
        summary_sentiment = analyze_sentiment(article['summary'])
        
        # Weight headline more than summary
        article_score = (headline_sentiment['compound'] * 0.6 + 
                        summary_sentiment['compound'] * 0.4)
        total_score += article_score
    
    return total_score / len(news_data)

def get_recommendation(sentiment_score: float, price_change: float) -> str:
    """Get investment recommendation based on sentiment and price movement"""
    if sentiment_score > 0.3 and price_change > 0:
        return "BUY"
    elif sentiment_score < -0.3 and price_change < 0:
        return "SELL"
    else:
        return "HOLD"

def display_home_page():
    """Display the main home page"""
    st.markdown("""
    <div class="main-container">
        <div class="hero-section">
            <div class="hero-title">StockMood Pro</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create quotron ticker
    create_quotron_ticker()
    
    # Add click instructions
    st.markdown("---")
    
    # Stock selection
    st.markdown("### 📊 Analyze Any Stock")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Text input for any stock symbol
        stock_input = st.text_input(
            "Enter any stock symbol (e.g., AAPL, GOOGL, TSLA):",
            placeholder="Type stock symbol here...",
            help="Enter any valid stock symbol to get comprehensive analysis"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align button
        if st.button("Analyze Stock", type="primary"):
            if stock_input:
                st.session_state.selected_stock = stock_input.upper()
                st.session_state.current_page = 'stock_analysis'
                st.rerun()
            else:
                st.warning("Please enter a stock symbol")
    
    # Quick select from popular stocks
    st.markdown("### 🔥 Popular Stocks")
    
    # Create clickable stock cards
    cols = st.columns(6)
    for i, symbol in enumerate(POPULAR_STOCKS[:12]):  # Show first 12 popular stocks
        with cols[i % 6]:
            # Get stock data for mood emoji
            quote = get_stock_quote(symbol)
            if quote:
                mood_emoji = get_stock_emoji(quote['percent_change'])
                change_color = "🟢" if quote['change'] > 0 else "🔴" if quote['change'] < 0 else "⚪"
                
                if st.button(f"{mood_emoji} {symbol}", key=f"quick_{symbol}"):
                    st.session_state.selected_stock = symbol
                    st.session_state.current_page = 'stock_analysis'
                    st.rerun()
    
    # Display major market indices
    st.markdown("### 📈 Major Market Indices")
    
    # Get major indices data
    indices_data = []
    with st.spinner("Loading market indices..."):
        for symbol in MAJOR_INDICES:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - prev_price
                    percent_change = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    # Map symbols to readable names
                    name_map = {
                        "^GSPC": "S&P 500",
                        "^DJI": "Dow Jones",
                        "^IXIC": "NASDAQ",
                        "^RUT": "Russell 2000",
                        "^VIX": "VIX",
                        "^TNX": "10-Year Treasury"
                    }
                    
                    indices_data.append({
                        'symbol': symbol,
                        'name': name_map.get(symbol, symbol),
                        'current_price': current_price,
                        'change': change,
                        'percent_change': percent_change
                    })
            except:
                continue
    
    if indices_data:
        cols = st.columns(3)
        for i, index in enumerate(indices_data[:6]):
            with cols[i % 3]:
                change_color = "🟢" if index['change'] > 0 else "🔴" if index['change'] < 0 else "⚪"
                mood_emoji = get_stock_emoji(index['percent_change'])
                
                # Make market indices clickable
                if st.button(f"{mood_emoji} {index['name']}", key=f"index_{index['symbol']}"):
                    st.session_state.selected_stock = index['symbol']
                    st.session_state.current_page = 'stock_analysis'
                    st.rerun()
                
                st.markdown(f"""
                <div class="popup-card">
                    <p><strong>{index['current_price']:.2f}</strong></p>
                    <p>{change_color} {index['change']:+.2f} ({index['percent_change']:+.2f}%)</p>
                </div>
                """, unsafe_allow_html=True)

def display_stock_analysis():
    """Display detailed stock analysis page"""
    symbol = st.session_state.selected_stock
    if not symbol:
        st.session_state.current_page = 'home'
        st.rerun()
        return
    
    # Get current stock quote for mood emoji
    current_quote = get_stock_quote(symbol)
    if current_quote:
        emoji = get_stock_emoji(current_quote['percent_change'])
    else:
        emoji = "📈"
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Home"):
            st.session_state.current_page = 'home'
            st.rerun()
    
    with col2:
        st.markdown(f"<h1><span class='stock-emoji'>{emoji}</span><span class='stock-symbol'>{symbol}</span></h1>", unsafe_allow_html=True)
    
    # Get comprehensive stock data
    with st.spinner(f"Loading comprehensive analysis for {symbol}..."):
        stock_info = get_stock_info(symbol)
        stock_news = get_stock_news(symbol)
        
        if not stock_info:
            st.error(f"Unable to fetch data for {symbol}")
            return
    
    # Display company information
    st.markdown("## 🏢 Company Information")
    st.markdown(f"""
    <div class="company-info">
        <h3>{stock_info['name']}</h3>
        <p><strong>Sector:</strong> {stock_info['sector']} | <strong>Industry:</strong> {stock_info['industry']}</p>
        <p><strong>Summary:</strong> {stock_info['summary'][:400]}...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display key metrics - only essential upfront metrics
    st.markdown("## 📊 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${stock_info['current_price']:.2f}</div>
            <div class="metric-label">Current Price</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Get daily high/low from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            today_data = ticker.history(period="1d")
            daily_high = today_data['High'].iloc[-1] if not today_data.empty else stock_info['week_high']
            daily_low = today_data['Low'].iloc[-1] if not today_data.empty else stock_info['week_low']
        except:
            daily_high = stock_info['week_high']
            daily_low = stock_info['week_low']
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${daily_high:.2f}</div>
            <div class="metric-label">Daily High</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${daily_low:.2f}</div>
            <div class="metric-label">Daily Low</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        change_color = "🟢" if stock_info['week_change'] >= 0 else "🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{change_color} {stock_info['week_change']:.2f}%</div>
            <div class="metric-label">Week Change</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stock_info['profit_margin']*100:.1f}%</div>
            <div class="metric-label">Profit Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Calculate comprehensive score
    sentiment_score = calculate_sentiment_score(stock_news)
    comprehensive_score = calculate_comprehensive_score(stock_info, sentiment_score)
    
    # Display comprehensive analysis
    st.markdown("## 🧠 Comprehensive Financial Analysis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="score-card">
            <div class="score-number">{comprehensive_score}</div>
            <div class="score-label">Investment Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Get recommendation based on score
        if comprehensive_score >= 80:
            recommendation = "STRONG BUY"
            badge_class = "buy-badge"
        elif comprehensive_score >= 60:
            recommendation = "BUY"
            badge_class = "buy-badge"
        elif comprehensive_score >= 40:
            recommendation = "HOLD"
            badge_class = "hold-badge"
        elif comprehensive_score >= 20:
            recommendation = "SELL"
            badge_class = "sell-badge"
        else:
            recommendation = "STRONG SELL"
            badge_class = "sell-badge"
        
        st.markdown(f"""
        <div class="recommendation-badge {badge_class}">
            {recommendation}
        </div>
        """, unsafe_allow_html=True)
    
    # Display only debt/equity as additional upfront metric
    st.markdown("## 💰 Additional Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stock_info['debt_to_equity']:.1f}</div>
            <div class="metric-label">Debt/Equity Ratio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stock_info['market_cap']/1e9:.1f}B</div>
            <div class="metric-label">Market Cap</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stock_info['pe_ratio']:.1f}</div>
            <div class="metric-label">P/E Ratio</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display news analysis
    st.markdown("## 📰 Recent News & Analysis")
    
    if stock_news:
        for article in stock_news[:5]:  # Show top 5 articles
            # Analyze article sentiment
            headline_sentiment = analyze_sentiment(article['headline'])
            summary_sentiment = analyze_sentiment(article['summary'])
            
            # Determine sentiment badge
            avg_sentiment = (headline_sentiment['compound'] + summary_sentiment['compound']) / 2
            
            if avg_sentiment >= 0.1:
                sentiment_badge = '<span class="sentiment-positive">Positive</span>'
            elif avg_sentiment <= -0.1:
                sentiment_badge = '<span class="sentiment-negative">Negative</span>'
            else:
                sentiment_badge = '<span class="sentiment-neutral">Neutral</span>'
            
            st.markdown(f"""
            <div class="news-card">
                <h4>{article['headline']}</h4>
                <p><strong>Source:</strong> {article['source']} | <strong>Date:</strong> {article['datetime'].strftime('%Y-%m-%d %H:%M')} | {sentiment_badge}</p>
                <p>{article['summary'][:300]}...</p>
                <a href="{article['url']}" target="_blank" class="news-link">Read full article →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news available for this stock")
    
    # Display price chart using yfinance
    st.markdown("### 📊 Price Chart")
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#ffffff', width=2)
            ))
            
            fig.update_layout(
                title=f"{symbol} - 1 Month Price History",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=500,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0.8)',
                paper_bgcolor='rgba(0,0,0,0.8)',
                font=dict(color='white', size=12),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)', 
                    color='white',
                    showgrid=True,
                    tickformat='%m/%d'
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)', 
                    color='white',
                    showgrid=True,
                    tickformat='$,.2f'
                ),
                hovermode='x unified'
            )
            
            # Add hover template for better price display
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Unable to load price chart data")
    except Exception as e:
        st.error(f"Error loading price chart: {str(e)}")

# Handle stock selection from URL parameters (quotron clicks)
try:
    query_params = st.query_params
    if 'stock' in query_params:
        selected_stock = query_params['stock']
        if selected_stock:
            st.session_state.selected_stock = selected_stock
            st.session_state.current_page = 'stock_analysis'
            # Clear the query parameter
            st.query_params.clear()
            st.rerun()
except:
    pass

# Check if any quotron stock was clicked
if 'quotron_clicked_stock' in st.session_state and st.session_state.quotron_clicked_stock:
    st.session_state.selected_stock = st.session_state.quotron_clicked_stock
    st.session_state.current_page = 'stock_analysis'
    st.session_state.quotron_clicked_stock = None
    st.rerun()

# Main application logic
def main():
    # Check for stock selection via URL parameters
    query_params = st.query_params
    if 'stock' in query_params:
        st.session_state.selected_stock = query_params['stock']
        st.session_state.current_page = 'stock_analysis'
    
    # Display appropriate page
    if st.session_state.current_page == 'home':
        display_home_page()
    elif st.session_state.current_page == 'stock_analysis':
        display_stock_analysis()

if __name__ == "__main__":
    main()
