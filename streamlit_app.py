import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Page configuration
st.set_page_config(
    page_title="StockMood Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS styling
st.markdown("""
<style>
    /* Hide Streamlit header and menu */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main layout */
    .main > div {
        padding: 0;
    }
    
    /* Header styling */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px 0;
        text-align: center;
        margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 10px 0 0 0;
    }
    
    /* Quotron ticker */
    .quotron {
        background: #1a1a1a;
        color: #00ff00;
        padding: 15px;
        margin: 20px 0;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 18px;
        font-weight: bold;
        overflow: hidden;
        position: relative;
        border: 2px solid #333;
    }
    
    .quotron-content {
        white-space: nowrap;
        animation: scroll-left 60s linear infinite;
    }
    
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .quotron-item {
        display: inline-block;
        margin-right: 50px;
        padding: 5px 15px;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .quotron-item:hover {
        background: rgba(0,255,0,0.1);
        transform: scale(1.05);
    }
    
    .quotron-item.positive {
        color: #00ff00;
        background: rgba(0,255,0,0.1);
    }
    
    .quotron-item.negative {
        color: #ff4444;
        background: rgba(255,68,68,0.1);
    }
    
    .quotron-item.neutral {
        color: #ffff00;
        background: rgba(255,255,0,0.1);
    }
    
    /* Cards */
    .popup-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin: 15px 0;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .popup-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    
    .popup-card h4 {
        color: #1f2937;
        margin: 0 0 10px 0;
        font-size: 1.2rem;
    }
    
    .popup-card p {
        color: #6b7280;
        margin: 5px 0;
        font-size: 1rem;
    }
    
    /* Stock symbol and emoji */
    .stock-symbol {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-left: 10px;
    }
    
    .stock-emoji {
        font-size: 3rem;
        margin-right: 15px;
    }
    
    /* Metric cards with proper contrast */
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
    
    /* Search styling */
    .search-section {
        background: #f8fafc;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        border: 1px solid #e5e7eb;
    }
    
    .search-title {
        color: #1f2937;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* Stock analysis badges */
    .buy-badge {
        background: #22c55e;
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(34, 197, 94, 0.3);
    }
    
    .sell-badge {
        background: #ef4444;
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
    }
    
    .hold-badge {
        background: #f59e0b;
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(245, 158, 11, 0.3);
    }
    
    /* Score card */
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .score-number {
        font-size: 4rem;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    .score-label {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 10px 0 0 0;
    }
    
    .recommendation-badge {
        padding: 20px 40px;
        border-radius: 25px;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
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
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 15px;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Hide Streamlit branding and empty containers */
    .viewerBadge_container__1QSob {
        display: none !important;
    }
    
    /* Hide any iframe or component containers that might show as black spots */
    iframe[title=""] {
        display: none !important;
        height: 0 !important;
        width: 0 !important;
    }
    
    /* Hide empty component containers */
    .stComponentBlock {
        display: none !important;
    }
    
    /* Hide html component containers */
    .element-container:has(iframe[title=""]) {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'AAPL'
if 'quotron_stocks' not in st.session_state:
    st.session_state.quotron_stocks = []

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

# Sentiment analyzer
@st.cache_resource
def get_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

def get_stock_emoji(percent_change):
    """Get emoji based on stock mood (percent change)"""
    if percent_change > 5:
        return "🚀"  # Rocket for big gains
    elif percent_change > 2:
        return "📈"  # Chart up for good gains
    elif percent_change > 0:
        return "💚"  # Green heart for small gains
    elif percent_change == 0:
        return "➡️"  # Arrow for no change
    elif percent_change > -2:
        return "❤️"  # Red heart for small losses
    elif percent_change > -5:
        return "📉"  # Chart down for moderate losses
    else:
        return "💥"  # Explosion for big losses

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
            current_price = data['c']
            change = data['d']
            percent_change = data['dp']
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': change,
                'percent_change': percent_change,
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
    quotron_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
    
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
        ticker_item = f'<span class="quotron-item {color_class}">{mood_emoji} {symbol} ${price:.2f} {sign}{percent_change:.2f}%</span>'
        ticker_content += ticker_item
    
    # Repeat content for continuous scrolling
    full_content = ticker_content * 3
    
    # Create the quotron ticker
    ticker_html = f"""
    <div class="quotron">
        <div class="quotron-content">
            {full_content}
        </div>
    </div>
    """
    
    st.markdown(ticker_html, unsafe_allow_html=True)

def get_stock_info(symbol: str) -> Dict:
    """Get comprehensive stock information from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1y")
        
        if hist.empty:
            return None
        
        # Get current price data
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close != 0 else 0
        
        # Calculate technical indicators
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line
            return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
        
        # Calculate week change
        week_ago_price = hist['Close'].iloc[-7] if len(hist) > 7 else current_price
        week_change = ((current_price - week_ago_price) / week_ago_price) * 100 if week_ago_price != 0 else 0
        
        # Get additional metrics
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0) or 0
        profit_margin = info.get('profitMargins', 0) or 0
        debt_to_equity = info.get('debtToEquity', 0) or 0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'change': change,
            'percent_change': percent_change,
            'week_change': week_change,
            'day_high': hist['High'].iloc[-1],
            'day_low': hist['Low'].iloc[-1],
            'volume': hist['Volume'].iloc[-1],
            'market_cap': market_cap,
            'pe_ratio': pe_ratio,
            'profit_margin': profit_margin,
            'debt_to_equity': debt_to_equity,
            '52_week_high': hist['High'].max(),
            '52_week_low': hist['Low'].min(),
            'avg_volume': hist['Volume'].tail(30).mean(),
            'previous_close': previous_close,
            'rsi': calculate_rsi(hist['Close']),
            'macd': calculate_macd(hist['Close'])
        }
    except Exception as e:
        st.error(f"Error getting stock info for {symbol}: {str(e)}")
        return None

def calculate_comprehensive_score(stock_info: Dict, news_sentiment: float) -> int:
    """Calculate comprehensive financial score out of 100"""
    score = 50  # Base score
    
    # Price momentum (20 points)
    if stock_info['percent_change'] > 5:
        score += 20
    elif stock_info['percent_change'] > 2:
        score += 15
    elif stock_info['percent_change'] > 0:
        score += 10
    elif stock_info['percent_change'] < -5:
        score -= 20
    elif stock_info['percent_change'] < -2:
        score -= 15
    else:
        score -= 10
    
    # Week performance (15 points)
    if stock_info['week_change'] > 5:
        score += 15
    elif stock_info['week_change'] > 0:
        score += 10
    elif stock_info['week_change'] < -5:
        score -= 15
    else:
        score -= 10
    
    # RSI analysis (10 points)
    rsi = stock_info.get('rsi', 50)
    if 30 <= rsi <= 70:
        score += 10
    elif rsi < 30:
        score += 5  # Oversold, potential buy
    else:
        score -= 5  # Overbought
    
    # Profit margin (10 points)
    if stock_info['profit_margin'] > 0.2:
        score += 10
    elif stock_info['profit_margin'] > 0.1:
        score += 5
    elif stock_info['profit_margin'] < 0:
        score -= 10
    
    # Debt to equity (10 points)
    if stock_info['debt_to_equity'] < 0.5:
        score += 10
    elif stock_info['debt_to_equity'] < 1.0:
        score += 5
    elif stock_info['debt_to_equity'] > 2.0:
        score -= 10
    
    # News sentiment (15 points)
    if news_sentiment > 0.1:
        score += 15
    elif news_sentiment > -0.1:
        score += 5
    else:
        score -= 15
    
    # Volume analysis (10 points)
    volume_ratio = stock_info['volume'] / stock_info['avg_volume']
    if volume_ratio > 1.5:
        score += 10
    elif volume_ratio > 1.2:
        score += 5
    elif volume_ratio < 0.8:
        score -= 5
    
    # P/E ratio (10 points)
    if 10 <= stock_info['pe_ratio'] <= 25:
        score += 10
    elif 5 <= stock_info['pe_ratio'] <= 35:
        score += 5
    elif stock_info['pe_ratio'] > 50:
        score -= 10
    
    return max(0, min(100, score))

def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of text using VADER"""
    analyzer = get_sentiment_analyzer()
    return analyzer.polarity_scores(text)

def calculate_sentiment_score(news_data: List[Dict]) -> float:
    """Calculate overall sentiment score from news data"""
    if not news_data:
        return 0.0
    
    total_sentiment = 0.0
    for article in news_data:
        headline_sentiment = analyze_sentiment(article['headline'])
        summary_sentiment = analyze_sentiment(article['summary'])
        
        # Weight headline more than summary
        article_sentiment = (headline_sentiment['compound'] * 0.6 + 
                           summary_sentiment['compound'] * 0.4)
        total_sentiment += article_sentiment
    
    return total_sentiment / len(news_data)

def display_home_page():
    """Display the main home page"""
    # Header
    st.markdown("""
    <div class="header">
        <h1>📈 StockMood Pro</h1>
        <p>Advanced Stock Analysis with Real-Time Market Sentiment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create quotron ticker (display only)
    create_quotron_ticker()
    
    # Search section
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    st.markdown('<div class="search-title">🔍 Search Any Stock</div>', unsafe_allow_html=True)
    
    # Search input
    search_symbol = st.text_input("Enter stock symbol (e.g., AAPL, GOOGL, TSLA):", key="stock_search")
    
    # Quick select buttons
    st.markdown("**Quick Select:**")
    cols = st.columns(4)
    quick_stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
    
    for i, symbol in enumerate(quick_stocks):
        with cols[i % 4]:
            if st.button(symbol, key=f"quick_{symbol}"):
                st.session_state.selected_stock = symbol
                st.session_state.current_page = 'stock_analysis'
                st.rerun()
    
    # Handle search
    if search_symbol:
        if st.button("Analyze Stock"):
            st.session_state.selected_stock = search_symbol.upper()
            st.session_state.current_page = 'stock_analysis'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    # Validate symbol
    if not symbol:
        st.error("Please select a stock symbol")
        if st.button("← Back to Home"):
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
        st.error(f"Could not retrieve data for {symbol}. Please check the symbol and try again.")
        return
    
    # Display essential metrics in card format
    st.markdown("## 📊 Essential Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    current_price = stock_info['current_price']
    daily_high = stock_info['day_high']
    daily_low = stock_info['day_low']
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Current Price</h4>
            <p class="metric-value">${current_price:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Daily Change</h4>
            <p class="metric-value">{stock_info['change']:+.2f} ({stock_info['percent_change']:+.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Daily Range</h4>
            <p class="metric-value">${stock_info['day_low']:.2f} - ${stock_info['day_high']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Volume</h4>
            <p class="metric-value">{stock_info['volume']:,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Week Change</h4>
            <p class="metric-value">{stock_info['week_change']:+.2f}%</p>
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
    
    # Display additional metrics
    st.markdown("## 💰 Additional Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Market Cap</h4>
            <p class="metric-value">${stock_info['market_cap']/1e9:.1f}B</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pe_text = f"{stock_info['pe_ratio']:.1f}" if stock_info['pe_ratio'] else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h4>P/E Ratio</h4>
            <p class="metric-value">{pe_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Debt/Equity</h4>
            <p class="metric-value">{stock_info['debt_to_equity']:.1f}</p>
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
                sentiment_badge = "🟢 Positive"
            elif avg_sentiment <= -0.1:
                sentiment_badge = "🔴 Negative"
            else:
                sentiment_badge = "🟡 Neutral"
            
            with st.expander(f"{sentiment_badge} {article['headline'][:80]}..."):
                st.markdown(f"**Source:** {article['source']}")
                st.markdown(f"**Date:** {article['datetime'].strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Summary:** {article['summary']}")
                if article['url']:
                    st.markdown(f"[Read full article]({article['url']})")
    else:
        st.info("No recent news available for this stock")
    
    # Display price chart
    st.markdown("## 📈 Price Chart")
    
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

# Main application logic
def main():
    if st.session_state.current_page == 'home':
        display_home_page()
    elif st.session_state.current_page == 'stock_analysis':
        display_stock_analysis()

if __name__ == "__main__":
    main()
