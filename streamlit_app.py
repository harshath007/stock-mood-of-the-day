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
from typing import Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="StockMood Pro",
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

# Initialize sentiment analyzer
@st.cache_resource
def get_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

analyzer = get_sentiment_analyzer()

# Fun, interactive styling inspired by "not boring software" design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #ffffff;
        min-height: 100vh;
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
    
    /* Clean Quotron Ticker */
    .quotron {
        background: #000000;
        border-radius: 10px;
        margin: 15px 0;
        overflow: hidden;
        position: relative;
        height: 60px;
        border: 1px solid #333333;
    }
    
    .quotron-content {
        display: flex;
        animation: scroll 90s linear infinite;
        height: 100%;
        align-items: center;
        white-space: nowrap;
        padding: 0 20px;
    }
    
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .quotron-item {
        color: #ffffff;
        font-family: 'Inter', monospace;
        font-weight: 600;
        font-size: 14px;
        margin-right: 30px;
        cursor: pointer;
        transition: all 0.2s ease;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid transparent;
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
    
    /* Info Modal */
    .info-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    
    .info-modal.show {
        display: flex;
    }
    
    .info-modal-content {
        background: white;
        border-radius: 20px;
        padding: 30px;
        max-width: 500px;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
        animation: modalSlide 0.3s ease;
    }
    
    @keyframes modalSlide {
        from {
            opacity: 0;
            transform: translateY(-50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .close-modal {
        position: absolute;
        top: 15px;
        right: 20px;
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
    }
    
    .close-modal:hover {
        color: #000;
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
    
    .score-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 4s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .score-number {
        font-size: 5rem;
        font-weight: 900;
        margin: 1rem 0;
        position: relative;
        z-index: 1;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        background: linear-gradient(45deg, #ffffff, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
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
    
    .recommendation-badge:hover {
        transform: scale(1.1);
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
    
    /* Interactive components */
    .component-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 15px;
        transition: all 0.3s ease;
        border-left: 4px solid transparent;
    }
    
    .component-bar:hover {
        transform: translateX(10px);
        border-left-color: #667eea;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
    }
    
    /* Fun news cards */
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
    
    /* Animated elements */
    .bounce {
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-15px);
        }
        60% {
            transform: translateY(-8px);
        }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    /* Clean buttons */
    .stButton > button {
        background: #000000;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 1rem;
        transition: all 0.2s ease;
        border: 1px solid #000000;
    }
    
    .stButton > button:hover {
        background: #333333;
        transform: translateY(-1px);
    }
    
    /* Clean selectbox */
    .stSelectbox > div > div {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #000000;
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
    
    /* Loading animations */
    .loading {
        display: inline-block;
        position: relative;
        width: 80px;
        height: 80px;
    }
    
    .loading div {
        position: absolute;
        top: 33px;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background: #667eea;
        animation-timing-function: cubic-bezier(0, 1, 1, 0);
    }
    
    .loading div:nth-child(1) {
        left: 8px;
        animation: loading1 0.6s infinite;
    }
    
    @keyframes loading1 {
        0% {
            transform: scale(0);
        }
        100% {
            transform: scale(1);
        }
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def format_large_number(number: float) -> str:
    """Format large numbers for easy reading."""
    try:
        if pd.isna(number) or number == 0:
            return "N/A"
        
        if number >= 1e12:
            return f"${number/1e12:.1f}T"
        elif number >= 1e9:
            return f"${number/1e9:.1f}B"
        elif number >= 1e6:
            return f"${number/1e6:.1f}M"
        elif number >= 1e3:
            return f"${number/1e3:.0f}K"
        else:
            return f"${number:.2f}"
    except:
        return "N/A"

def format_percentage(value: float) -> str:
    """Format percentage values."""
    try:
        if pd.isna(value):
            return "N/A"
        return f"{value:+.2f}%"
    except:
        return "N/A"

def get_stock_emoji(change_percent: float) -> str:
    """Get emoji based on daily stock performance."""
    if change_percent >= 5:
        return "🚀"
    elif change_percent >= 2:
        return "📈"
    elif change_percent >= 0:
        return "⬆️"
    elif change_percent >= -2:
        return "⬇️"
    elif change_percent >= -5:
        return "📉"
    else:
        return "💥"

def get_sentiment_emoji(score: float) -> str:
    """Get emoji for sentiment score."""
    if score > 0.3:
        return "😄"
    elif score > 0.1:
        return "🙂"
    elif score > -0.1:
        return "😐"
    elif score > -0.3:
        return "😟"
    else:
        return "😨"

# Data Fetching Functions
@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
    """Fetch stock data for a given symbol and period."""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        if data.empty:
            return None
        return data
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None

# Quotron Functions
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_quotron_stocks() -> list:
    """Get a rotating list of major stocks for the quotron."""
    from datetime import datetime
    
    # Major stocks organized by categories
    all_stocks = {
        'tech': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'CRM', 'ORCL', 'ADBE', 'INTC', 'AMD', 'UBER', 'LYFT'],
        'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'V', 'MA', 'PYPL', 'SQ', 'BRK-B'],
        'healthcare': ['JNJ', 'PFE', 'ABT', 'MRK', 'TMO', 'UNH', 'ABBV', 'BMY', 'CVS', 'ANTM'],
        'consumer': ['PG', 'KO', 'PEP', 'WMT', 'TGT', 'HD', 'MCD', 'SBUX', 'NKE', 'DIS'],
        'energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'KMI', 'OXY'],
        'industrial': ['BA', 'CAT', 'GE', 'MMM', 'UPS', 'FDX', 'LMT', 'RTX']
    }
    
    # Rotate stocks based on day of year to get fresh selection
    day_of_year = datetime.now().timetuple().tm_yday
    selected_stocks = []
    
    for category, stocks in all_stocks.items():
        # Rotate through stocks in each category
        start_idx = (day_of_year * 2) % len(stocks)
        category_count = min(6, len(stocks))  # 6 stocks per category max
        
        for i in range(category_count):
            idx = (start_idx + i) % len(stocks)
            selected_stocks.append(stocks[idx])
    
    return selected_stocks[:35]  # Return 35 stocks total

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_quotron_data(symbols: list) -> list:
    """Get current price and change data for quotron stocks."""
    quotron_data = []
    
    # Process stocks in batches to avoid overwhelming yfinance
    batch_size = 10
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        try:
            # Fetch data for batch
            tickers = yf.Tickers(' '.join(batch))
            
            for symbol in batch:
                try:
                    ticker = tickers.tickers[symbol]
                    hist = ticker.history(period='2d')
                    info = ticker.info
                    
                    if not hist.empty and len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2]
                        change = current_price - prev_price
                        change_pct = (change / prev_price) * 100
                        
                        quotron_data.append({
                            'symbol': symbol,
                            'price': current_price,
                            'change': change,
                            'change_pct': change_pct,
                            'name': info.get('shortName', symbol)[:20]  # Truncate long names
                        })
                except Exception:
                    continue
        except Exception:
            continue
        
        time.sleep(0.1)  # Rate limiting
    
    return quotron_data

def create_quotron_html(quotron_data: list) -> str:
    """Create HTML for the quotron ticker."""
    items = []
    for stock in quotron_data:
        change_class = "positive" if stock['change'] >= 0 else "negative"
        change_sign = "+" if stock['change'] >= 0 else ""
        
        # Real ticker styling with arrows
        if stock['change'] >= 0:
            color = "#22c55e"
            arrow = "▲"
        else:
            color = "#ef4444"
            arrow = "▼"
        
        item_html = f"""
        <span class="quotron-item" onclick="selectStock('{stock['symbol']}')" style="color: {color};">
            <strong>{stock['symbol']}</strong> ${stock['price']:.2f} {arrow} {change_sign}{stock['change']:.2f} ({change_sign}{stock['change_pct']:.1f}%)
        </span>
        """
        items.append(item_html)
    
    quotron_html = f"""
    <div class="quotron">
        <div class="quotron-content">
            {''.join(items * 3)}  <!-- Repeat 3 times for smooth scrolling -->
        </div>
    </div>
    """
    
    return quotron_html

@st.cache_data(ttl=300)
def get_company_info(symbol: str) -> Dict:
    """Get company information and key metrics."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 1),
            'profit_margins': info.get('profitMargins', 0),
            'debt_to_equity': info.get('debtToEquity', 0),
            'current_price': info.get('currentPrice', 0)
        }
    except Exception as e:
        return {
            'name': symbol,
            'sector': 'Unknown',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'beta': 1,
            'profit_margins': 0,
            'debt_to_equity': 0,
            'current_price': 0
        }

# Technical Analysis Functions
def calculate_rsi(prices: pd.Series, window: int = 14) -> float:
    """Calculate RSI (Relative Strength Index)."""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    except:
        return 50

def calculate_macd(prices: pd.Series) -> Dict[str, float]:
    """Calculate MACD indicators."""
    try:
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'macd': macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0,
            'signal': signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0,
            'histogram': histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0
        }
    except:
        return {'macd': 0, 'signal': 0, 'histogram': 0}

def calculate_bollinger_bands(prices: pd.Series, window: int = 20) -> Dict[str, float]:
    """Calculate Bollinger Bands."""
    try:
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * 2)
        lower_band = rolling_mean - (rolling_std * 2)
        
        current_price = prices.iloc[-1]
        bb_position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
        
        return {
            'upper': upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else current_price * 1.1,
            'lower': lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else current_price * 0.9,
            'position': bb_position if not pd.isna(bb_position) else 0.5
        }
    except:
        return {'upper': 0, 'lower': 0, 'position': 0.5}

# Investment Scoring Function
def calculate_comprehensive_score(stock_data: pd.DataFrame, company_info: Dict, sentiment_score: float = 0) -> Dict:
    """Calculate a sophisticated investment score using multiple time horizons and company history."""
    try:
        scores = {}
        
        # 1. Multi-timeframe Performance Score (35% weight)
        returns_1d = stock_data['Close'].pct_change(periods=1).iloc[-1] * 100 if len(stock_data) > 1 else 0
        returns_1w = stock_data['Close'].pct_change(periods=5).iloc[-1] * 100 if len(stock_data) > 5 else 0
        returns_1m = stock_data['Close'].pct_change(periods=21).iloc[-1] * 100 if len(stock_data) > 21 else 0
        
        performance_score = 50
        if not pd.isna(returns_1d):
            performance_score += min(max(returns_1d * 2, -30), 30)
        if not pd.isna(returns_1w):
            performance_score += min(max(returns_1w * 1.5, -20), 20)
        if not pd.isna(returns_1m):
            performance_score += min(max(returns_1m * 1, -15), 15)
        
        scores['performance'] = max(0, min(100, performance_score))
        
        # 2. Technical Analysis Score (25% weight)
        prices = stock_data['Close']
        rsi = calculate_rsi(prices)
        macd_data = calculate_macd(prices)
        bb_data = calculate_bollinger_bands(prices)
        
        technical_score = 50
        
        # RSI scoring
        if 30 <= rsi <= 70:
            technical_score += 10
        elif rsi < 30:
            technical_score += 5  # Oversold, potential buy
        elif rsi > 70:
            technical_score -= 5  # Overbought, potential sell
        
        # MACD scoring
        if macd_data['macd'] > macd_data['signal']:
            technical_score += 8
        else:
            technical_score -= 3
        
        # Bollinger Bands scoring
        if 0.2 <= bb_data['position'] <= 0.8:
            technical_score += 7
        
        # Volume and volatility analysis
        if len(stock_data) > 20:
            recent_volatility = stock_data['Close'].pct_change().rolling(20).std().iloc[-1]
            if recent_volatility < 0.02:
                technical_score += 5  # Low volatility is good for stability
            elif recent_volatility > 0.05:
                technical_score -= 5  # High volatility increases risk
        
        scores['technical'] = max(0, min(100, technical_score))
        
        # 3. Company Fundamentals & History Score (25% weight)
        fundamental_score = 50
        
        # Market cap scoring (company size and stability)
        market_cap = company_info.get('market_cap', 0)
        if market_cap > 100e9:
            fundamental_score += 10  # Large cap
        elif market_cap > 10e9:
            fundamental_score += 7   # Mid cap
        elif market_cap > 1e9:
            fundamental_score += 3   # Small cap
        else:
            fundamental_score -= 5   # Micro cap (higher risk)
        
        # Profitability
        profit_margins = company_info.get('profit_margins', 0)
        if profit_margins > 0.15:
            fundamental_score += 8
        elif profit_margins > 0.05:
            fundamental_score += 4
        elif profit_margins < 0:
            fundamental_score -= 10
        
        # P/E ratio analysis
        pe_ratio = company_info.get('pe_ratio', 0)
        if 10 <= pe_ratio <= 25:
            fundamental_score += 6   # Reasonable valuation
        elif pe_ratio > 40:
            fundamental_score -= 8   # Potentially overvalued
        
        # Debt management
        debt_to_equity = company_info.get('debt_to_equity', 0)
        if debt_to_equity < 0.3:
            fundamental_score += 5   # Low debt
        elif debt_to_equity > 1.0:
            fundamental_score -= 8   # High debt
        
        # Dividend yield
        dividend_yield = company_info.get('dividend_yield', 0)
        if dividend_yield and dividend_yield > 0.02:
            fundamental_score += 3   # Decent dividend
        
        scores['fundamental'] = max(0, min(100, fundamental_score))
        
        # 4. Market Sentiment & News Score (15% weight) - Reduced impact
        sentiment_adjusted = 65 + (sentiment_score * 15)  # Minimal impact for stability
        scores['sentiment'] = max(0, min(100, sentiment_adjusted))
        
        # Calculate weighted overall score with new weights
        overall_score = (
            scores['performance'] * 0.35 +  # Multi-timeframe performance
            scores['technical'] * 0.25 +    # Technical indicators
            scores['fundamental'] * 0.25 +  # Company fundamentals & history
            scores['sentiment'] * 0.15      # Market sentiment
        )
        
        # Generate recommendation
        if overall_score >= 80:
            recommendation = "Strong Buy"
            reason = "Excellent fundamentals, strong technical signals, and positive momentum across all timeframes."
        elif overall_score >= 65:
            recommendation = "Buy"
            reason = "Good overall performance with solid fundamentals and positive technical indicators."
        elif overall_score >= 50:
            recommendation = "Hold"
            reason = "Mixed signals suggest maintaining current position while monitoring developments."
        elif overall_score >= 35:
            recommendation = "Weak Hold"
            reason = "Below-average performance with some concerning indicators. Consider reducing position."
        else:
            recommendation = "Sell"
            reason = "Poor fundamentals and negative technical signals suggest high risk."
        
        return {
            'overall_score': round(overall_score, 1),
            'recommendation': recommendation,
            'reason': reason,
            'components': {
                'Performance': round(scores['performance'], 1),
                'Technical': round(scores['technical'], 1),
                'Fundamental': round(scores['fundamental'], 1),
                'Sentiment': round(scores['sentiment'], 1)
            },
            'daily_return': returns_1d,
            'weekly_return': returns_1w,
            'monthly_return': returns_1m
        }
        
    except Exception as e:
        st.error(f"Score calculation error: {str(e)}")
        return {
            'overall_score': 50,
            'recommendation': 'Hold',
            'reason': 'Cannot calculate score',
            'components': {},
            'daily_return': 0,
            'weekly_return': 0,
            'monthly_return': 0
        }

# News and Sentiment Functions
@st.cache_data(ttl=1800)
def get_stock_sentiment(symbol: str) -> Dict:
    """Get sentiment analysis from Finnhub API with reliable news sources."""
    try:
        analyzer = get_sentiment_analyzer()
        articles = []
        
        # Use Finnhub API with the user's key
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            try:
                url = f"https://finnhub.io/api/v1/company-news"
                params = {
                    'symbol': symbol,
                    'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'to': datetime.now().strftime('%Y-%m-%d'),
                    'token': finnhub_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data[:15]:
                        if article.get('headline') and article.get('summary'):
                            articles.append({
                                'title': article['headline'],
                                'content': f"{article['headline']} {article['summary']}",
                                'source': article.get('source', 'Financial News'),
                                'published': datetime.fromtimestamp(article.get('datetime', 0)).strftime('%B %d, %Y') if article.get('datetime') else 'Recent',
                                'url': article.get('url', '#')
                            })
                elif response.status_code == 401:
                    return {
                        'sentiment_score': 0,
                        'article_count': 0,
                        'sentiment_label': 'API Error',
                        'articles': [],
                        'message': 'Invalid API key. Please check your Finnhub API key.'
                    }
                time.sleep(0.1)
            except Exception as e:
                return {
                    'sentiment_score': 0,
                    'article_count': 0,
                    'sentiment_label': 'Error',
                    'articles': [],
                    'message': f'News API error: {str(e)}'
                }
        
        # If no articles found, return neutral
        if not articles:
            return {
                'sentiment_score': 0,
                'article_count': 0,
                'sentiment_label': 'Neutral',
                'articles': [],
                'message': 'No recent news found for this stock'
            }
        
        # Analyze sentiment
        sentiments = []
        analyzed_articles = []
        
        for article in articles[:15]:
            try:
                sentiment = analyzer.polarity_scores(article['content'])
                sentiments.append(sentiment['compound'])
                
                # Categorize sentiment in simple terms
                if sentiment['compound'] > 0.1:
                    sentiment_label = 'Good News'
                elif sentiment['compound'] < -0.1:
                    sentiment_label = 'Bad News'
                else:
                    sentiment_label = 'Neutral'
                
                analyzed_articles.append({
                    'title': article['title'][:120] + '...' if len(article['title']) > 120 else article['title'],
                    'sentiment_score': sentiment['compound'],
                    'sentiment_label': sentiment_label,
                    'source': article['source'],
                    'published': article['published'],
                    'url': article['url']
                })
            except:
                continue
        
        avg_sentiment = np.mean(sentiments) if sentiments else 0
        
        # Overall sentiment label in simple terms
        if avg_sentiment > 0.1:
            overall_sentiment = 'Good News'
        elif avg_sentiment < -0.1:
            overall_sentiment = 'Bad News'
        else:
            overall_sentiment = 'Mixed News'
        
        return {
            'sentiment_score': avg_sentiment,
            'article_count': len(analyzed_articles),
            'sentiment_label': overall_sentiment,
            'articles': analyzed_articles[:8],
            'message': f'Found {len(analyzed_articles)} recent news articles'
        }
        
    except Exception as e:
        return {
            'sentiment_score': 0,
            'article_count': 0,
            'sentiment_label': 'Error',
            'articles': [],
            'message': f'Error fetching news: {str(e)}'
        }

# Chart Creation Function
def create_price_chart(stock_data: pd.DataFrame, symbol: str) -> go.Figure:
    """Create a clean, informative price chart."""
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        mode='lines',
        name='Price',
        line=dict(color='#667eea', width=3),
        hovertemplate='<b>%{y:.2f}</b><br>%{x}<extra></extra>'
    ))
    
    # Add volume bar chart (secondary y-axis)
    fig.add_trace(go.Bar(
        x=stock_data.index,
        y=stock_data['Volume'],
        name='Volume',
        yaxis='y2',
        opacity=0.3,
        marker_color='#764ba2',
        hovertemplate='Volume: %{y:,.0f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{symbol.upper()} Stock Price & Volume',
        title_font_size=20,
        title_font_color='#374151',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=12, color="#374151")
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig

# Main Application
def main():
    """Main application function."""
    
    # Hero Section with Quotron
    st.markdown("""
    <div class="main-container">
        <div class="hero-section">
            <h1 class="hero-title">StockMood Pro</h1>
            <p class="hero-subtitle">Smart stock analysis that's actually fun to use! 📈✨</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Add Quotron Ticker
    st.markdown("### 📊 Live Market Quotron")
    st.markdown("*Click any stock to analyze it instantly!*", unsafe_allow_html=True)
    
    try:
        quotron_stocks = get_quotron_stocks()
        with st.spinner("Loading live market data..."):
            quotron_data = get_quotron_data(quotron_stocks)
        
        if quotron_data:
            quotron_html = create_quotron_html(quotron_data)
            st.markdown(quotron_html, unsafe_allow_html=True)
            
            # JavaScript for quotron interaction and modals
            st.markdown("""
            <script>
            function selectStock(symbol) {
                // Store in session storage for Streamlit to pick up
                sessionStorage.setItem('selected_stock', symbol);
                
                // Trigger a rerun by clicking the refresh button
                setTimeout(() => {
                    const buttons = parent.document.querySelectorAll('button');
                    const analyzeBtn = Array.from(buttons).find(btn => 
                        btn.textContent.includes('Refresh') || 
                        btn.textContent.includes('🔄')
                    );
                    if (analyzeBtn) analyzeBtn.click();
                }, 100);
            }
            
            function showArticleInfo(articleId) {
                const modal = document.getElementById('modal_' + articleId);
                if (modal) {
                    modal.classList.add('show');
                }
            }
            
            function closeModal(articleId) {
                const modal = document.getElementById('modal_' + articleId);
                if (modal) {
                    modal.classList.remove('show');
                }
            }
            
            // Close modal when clicking outside
            window.onclick = function(event) {
                if (event.target.classList.contains('info-modal')) {
                    event.target.classList.remove('show');
                }
            }
            
            // Check for selected stock from quotron
            const selectedStock = sessionStorage.getItem('selected_stock');
            if (selectedStock) {
                sessionStorage.removeItem('selected_stock');
                // This will be handled by Streamlit's session state
            }
            </script>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.info("Quotron temporarily unavailable - select a stock from the sidebar!")
    
    # Add refresh button (hidden but accessible via JS)
    if st.button("🔄 Refresh", key="hidden_refresh", help="Refresh quotron data"):
        st.rerun()

    # Clean sidebar for stock search
    with st.sidebar:
        st.markdown("## 📈 **Stock Analysis**")
        
        # Stock search input
        custom_symbol = st.text_input(
            "Enter stock symbol:",
            placeholder="e.g., AAPL, GOOGL, TSLA",
            help="Enter any valid stock ticker symbol",
            key="stock_search"
        )
        
        if st.button("Analyze Stock", use_container_width=True, type="primary"):
            if custom_symbol:
                st.session_state.selected_stock = custom_symbol.upper()
        
        st.markdown("---")
        
        # Analysis settings
        time_period = st.selectbox(
            "Analysis Period:",
            ["1mo", "3mo", "6mo", "1y", "2y"],
            index=3,
            help="Select the time period for analysis"
        )
        
        st.markdown("---")
        
        # Quotron refresh
        if st.button("🔄 Refresh Market Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main content area
    if 'selected_stock' in st.session_state and st.session_state.selected_stock:
        symbol = st.session_state.selected_stock
        
        # Show loading animation
        with st.spinner("🔮 Analyzing your stock..."):
            # Fetch data
            stock_data = get_stock_data(symbol, time_period)
            
            if stock_data is not None and not stock_data.empty:
                company_info = get_company_info(symbol)
                sentiment_data = get_stock_sentiment(symbol)
                
                # Calculate comprehensive analysis
                analysis = calculate_comprehensive_score(
                    stock_data, 
                    company_info, 
                    sentiment_data.get('sentiment_score', 0)
                )
                
                # Get daily performance emoji
                current_price = stock_data['Close'].iloc[-1] if not stock_data.empty else 0
                price_change = stock_data['Close'].pct_change().iloc[-1] * 100 if len(stock_data) > 1 else 0
                performance_emoji = get_stock_emoji(price_change)
                
                # Stock Header with fun popup style
                st.markdown(f"""
                <div class="popup-card">
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                        <span class="bounce" style="font-size: 3rem;">{performance_emoji}</span>
                        <div>
                            <h2 class="stock-symbol">{symbol}</h2>
                            <p style="color: #6b7280; margin: 0; font-size: 1.1em;">{company_info['name']}</p>
                        </div>
                    </div>
                    <p style="color: #6b7280; margin: 0; font-size: 1.1em; text-align: center;">Ready for some stock magic? Let's dive in! ✨</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Investment Score Card with animation
                score = analysis['overall_score']
                score_color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
                
                st.markdown(f"""
                <div class="score-card pulse">
                    <div class="score-number">{score:.0f}</div>
                    <div class="score-label">Investment Score</div>
                    <div style="margin-top: 1rem; font-size: 1.1rem; opacity: 0.9;">
                        {"🚀 Looking Amazing!" if score >= 80 else "🎯 Pretty Good!" if score >= 65 else "⚡ Proceed with Caution" if score >= 50 else "⚠️ High Risk Zone"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Fun Recommendation Badge
                rec = analysis['recommendation']
                if "Strong Buy" in rec:
                    rec_class, rec_emoji = "buy-badge", "🚀"
                elif "Buy" in rec:
                    rec_class, rec_emoji = "buy-badge", "📈"
                elif "Sell" in rec:
                    rec_class, rec_emoji = "sell-badge", "📉"
                else:
                    rec_class, rec_emoji = "hold-badge", "⏸️"
                
                st.markdown(f"""
                <div class="recommendation-badge {rec_class}">
                    {rec_emoji} {rec} {rec_emoji}
                </div>
                """, unsafe_allow_html=True)
                
                # Reason in popup card
                st.markdown(f"""
                <div class="popup-card">
                    <h4 style="color: #374151; margin-bottom: 1rem;">💡 Why this recommendation?</h4>
                    <p style="color: #6b7280; margin: 0; font-size: 1.1em; line-height: 1.6;">{analysis['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                daily_change = analysis.get('daily_return', 0)
                weekly_change = analysis.get('weekly_return', 0)
                monthly_change = analysis.get('monthly_return', 0)
                
                with col1:
                    st.metric("Today", f"{daily_change:+.2f}%", delta=None)
                with col2:
                    st.metric("This Week", f"{weekly_change:+.2f}%", delta=None)
                with col3:
                    st.metric("This Month", f"{monthly_change:+.2f}%", delta=None)
                
                # Score Breakdown with interactive bars
                if analysis['components']:
                    st.markdown("### 🔍 **What Makes This Score?**")
                    st.markdown(f"""
                    <div class="popup-card">
                        <div style="text-align: center; margin-bottom: 2rem;">
                            <h4 style="color: #374151; margin: 0;">Here's how we calculated this score</h4>
                            <p style="color: #6b7280; margin: 0.5rem 0;">Each piece of the puzzle matters! 🧩</p>
                        </div>
                        <div class="component-bar">
                            <span style="font-size: 1.1em; font-weight: 600;">📊 Multi-timeframe Performance (35%)</span>
                            <span style="font-weight: 800; color: #667eea; font-size: 1.2em;">{analysis['components']['Performance']:.0f}/100</span>
                        </div>
                        <div class="component-bar">
                            <span style="font-size: 1.1em; font-weight: 600;">⚙️ Technical Analysis (25%)</span>
                            <span style="font-weight: 800; color: #764ba2; font-size: 1.2em;">{analysis['components']['Technical']:.0f}/100</span>
                        </div>
                        <div class="component-bar">
                            <span style="font-size: 1.1em; font-weight: 600;">💼 Company Health (25%)</span>
                            <span style="font-weight: 800; color: #22c55e; font-size: 1.2em;">{analysis['components']['Fundamental']:.0f}/100</span>
                        </div>
                        <div class="component-bar">
                            <span style="font-size: 1.1em; font-weight: 600;">📰 News Sentiment (15%)</span>
                            <span style="font-weight: 800; color: #f59e0b; font-size: 1.2em;">{analysis['components']['Sentiment']:.0f}/100</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Stock Chart
                st.markdown("### 📊 **Price Chart**")
                chart = create_price_chart(stock_data, symbol)
                st.plotly_chart(chart, use_container_width=True)
                
                # News Section with fun cards
                if sentiment_data and sentiment_data.get('articles'):
                    st.markdown("### 📰 **What's Everyone Talking About?**")
                    
                    # Overall sentiment popup
                    sentiment_score = sentiment_data.get('sentiment_score', 0)
                    sentiment_emoji = get_sentiment_emoji(sentiment_score)
                    sentiment_label = sentiment_data.get('sentiment_label', 'Neutral')
                    
                    sentiment_color = "#22c55e" if sentiment_score > 0.1 else "#ef4444" if sentiment_score < -0.1 else "#6b7280"
                    
                    st.markdown(f"""
                    <div class="popup-card" style="text-align: center; background: linear-gradient(135deg, {sentiment_color}10, {sentiment_color}05);">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">{sentiment_emoji}</div>
                        <h4 style="color: {sentiment_color}; margin: 0; font-weight: 700;">Overall News Mood: {sentiment_label}</h4>
                        <p style="color: #6b7280; margin: 0.5rem 0;">Based on {sentiment_data.get('article_count', 0)} recent articles from financial news sources</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display articles in fun cards with info popups
                    st.markdown("#### 📋 **Recent Headlines**")
                    for i, article in enumerate(sentiment_data['articles'][:5], 1):
                        if article['sentiment_label'] == 'Good News':
                            news_color, news_emoji = "#22c55e", "📈"
                        elif article['sentiment_label'] == 'Bad News':
                            news_color, news_emoji = "#ef4444", "📉"
                        else:
                            news_color, news_emoji = "#6b7280", "📊"
                        
                        # Create unique ID for each article
                        article_id = f"article_{i}"
                        
                        st.markdown(f"""
                        <div class="news-card" style="border-left-color: {news_color}; margin: 10px 0;" onclick="showArticleInfo('{article_id}')">
                            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                                <span style="font-size: 1.3rem;">{news_emoji}</span>
                                <span class="sentiment-{article['sentiment_label'].lower().replace(' ', '-').replace('news', '').strip()}">{article['sentiment_label']}</span>
                                <span style="color: #6b7280; font-size: 0.85em;">• {article.get('source', 'News')} • {article.get('published', 'Recent')}</span>
                            </div>
                            <h5 style="margin: 0.5rem 0; color: #374151; line-height: 1.4; font-weight: 600; font-size: 1em;">{article['title']}</h5>
                            <p style="color: #667eea; font-size: 0.85em; margin: 0; font-weight: 500;">Click for summary & link →</p>
                        </div>
                        
                        <!-- Article Info Modal -->
                        <div id="modal_{article_id}" class="info-modal">
                            <div class="info-modal-content">
                                <button class="close-modal" onclick="closeModal('{article_id}')">&times;</button>
                                <div style="text-align: center; margin-bottom: 1rem;">
                                    <span style="font-size: 2rem;">{news_emoji}</span>
                                    <h3 style="color: {news_color}; margin: 0.5rem 0;">{article['sentiment_label']}</h3>
                                </div>
                                <h4 style="color: #374151; margin: 1rem 0; line-height: 1.4;">{article['title']}</h4>
                                <div style="background: #f8fafc; padding: 15px; border-radius: 10px; margin: 1rem 0;">
                                    <p style="color: #6b7280; margin: 0; font-size: 0.9em;"><strong>Source:</strong> {article.get('source', 'Unknown')}</p>
                                    <p style="color: #6b7280; margin: 0.5rem 0 0 0; font-size: 0.9em;"><strong>Published:</strong> {article.get('published', 'Recent')}</p>
                                </div>
                                <div style="text-align: center; margin-top: 1.5rem;">
                                    <a href="{article.get('url', '#')}" target="_blank" style="background: {news_color}; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: 600;">
                                        Read Full Article →
                                    </a>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                elif sentiment_data and sentiment_data.get('message'):
                    st.markdown(f"""
                    <div class="popup-card" style="text-align: center; background: linear-gradient(135deg, #f59e0b10, #f59e0b05);">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">📰</div>
                        <h4 style="color: #f59e0b; margin: 0; font-weight: 700;">News Update</h4>
                        <p style="color: #6b7280; margin: 0.75rem 0; font-size: 1.1em;">{sentiment_data['message']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="popup-card" style="text-align: center;">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                        <h4 style="color: #6b7280; margin: 0; font-weight: 700;">No Recent News</h4>
                        <p style="color: #9ca3af; margin: 0.75rem 0; font-size: 1.1em;">We couldn't find recent news for this stock. Try a different symbol!</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # How we calculate explanation
                st.markdown("---")
                st.markdown(f"""
                <div class="popup-card" style="background: linear-gradient(135deg, #667eea10, #764ba210);">
                    <h4 style="color: #374151; margin-bottom: 1.5rem;">🤓 How We Calculate Your Score</h4>
                    <p style="color: #6b7280; margin-bottom: 1rem; font-size: 1.1em;">We analyze this stock using a sophisticated system that looks at:</p>
                    <ul style="color: #6b7280; line-height: 1.8; font-size: 1.05em;">
                        <li><strong>Performance (35%):</strong> How the stock did today, this week, and this month</li>
                        <li><strong>Technical Analysis (25%):</strong> Advanced math signals that predict price movements</li>
                        <li><strong>Company Health (25%):</strong> The company's size, profits, debt, and track record</li>
                        <li><strong>News Mood (15%):</strong> What people are saying about the company lately</li>
                    </ul>
                    <p style="color: #6b7280; margin-top: 1rem; font-size: 1.05em;">The emoji next to the stock shows how it performed today specifically.</p>
                    <p style="color: #9ca3af; margin-top: 1.5rem; font-style: italic; font-size: 1em;"><strong>Remember:</strong> This is just our analysis to help you learn. Always do more research before investing!</p>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.markdown(f"""
                <div class="popup-card" style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">😅</div>
                    <h4 style="color: #ef4444; margin: 0;">Oops! Stock Not Found</h4>
                    <p style="color: #6b7280; margin: 1rem 0;">We couldn't find data for <strong>{symbol}</strong>. Make sure it's a valid stock symbol!</p>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        # Clean welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; margin: 2rem 0;">
            <div style="margin-bottom: 2rem;">
                <h2 style="color: #000000; margin-bottom: 1rem; font-weight: 600;">Welcome to StockMood Pro</h2>
                <p style="color: #6b7280; font-size: 1.1em; max-width: 500px; margin: 0 auto;">
                    Get intelligent stock analysis with real-time news sentiment. 
                    Enter any stock symbol in the sidebar to begin.
                </p>
            </div>
            <div style="border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.5rem; max-width: 400px; margin: 0 auto; background: #f9fafb;">
                <p style="color: #374151; margin: 0; font-weight: 500;">Ready to analyze?</p>
                <p style="color: #6b7280; margin: 0.5rem 0 0 0; font-size: 0.9em;">Click any stock in the quotron above or use the search in the sidebar</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close main container
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
