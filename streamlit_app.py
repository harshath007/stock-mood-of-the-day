import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import time
import re
import requests
from urllib.parse import quote

# ---------- Configuration & Setup -----------
st.set_page_config(
    page_title="StockMood Pro - Professional Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Professional CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
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
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .score-display {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-lg);
        margin: 1rem 0;
    }
    
    .score-number {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: black;
        background-clip: text;
        margin: 0;
        line-height: 1;
    }
    
    .score-label {
        font-size: 1.2rem;
        color: var(--text-medium);
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .recommendation-card {
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-md);
        margin: 1rem 0;
    }
    
    .buy-recommendation {
        background: linear-gradient(145deg, #d1fae5, #a7f3d0);
        border-left: 4px solid var(--success-green);
    }
    
    .sell-recommendation {
        background: linear-gradient(145deg, #fee2e2, #fecaca);
        border-left: 4px solid var(--danger-red);
    }
    
    .hold-recommendation {
        background: linear-gradient(145deg, #fef3c7, #fde68a);
        border-left: 4px solid var(--warning-orange);
    }
    
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
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .news-card {
        background: var(--bg-white);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-blue);
    }
    
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
    
    .factor-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid var(--border-light);
        border-left: 4px solid var(--primary-blue);
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .factor-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .confidence-meter {
        height: 10px;
        background: linear-gradient(90deg, #dc2626, #d97706, #059669);
        border-radius: 5px;
        position: relative;
        overflow: hidden;
    }
    
    .confidence-indicator {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Utility Functions -----------

@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = '1y') -> tuple:
    """Fetch stock data and company information"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        info = ticker.info
        
        if data.empty:
            return None, None
        
        data = data.dropna()
        data.index = pd.to_datetime(data.index)
        
        return data, info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

def calculate_article_relevance(title: str, summary: str, symbol: str) -> float:
    """Calculate relevance score for news articles with enhanced accuracy"""
    try:
        relevance = 0
        symbol_upper = symbol.upper()
        
        # Direct symbol mentions (highest weight)
        title_upper = title.upper()
        if symbol_upper in title_upper:
            relevance += 0.7
            # Bonus for symbol being prominent in title
            words = title_upper.split()
            if words and words[0] == symbol_upper:
                relevance += 0.2
        
        # Summary mentions
        summary_upper = summary.upper()
        if symbol_upper in summary_upper:
            relevance += 0.4
        
        # Enhanced financial keywords with weights
        high_relevance_keywords = [
            'EARNINGS', 'QUARTERLY', 'ANNUAL', 'REVENUE', 'PROFIT', 'LOSS',
            'GUIDANCE', 'FORECAST', 'BEAT', 'MISS', 'ESTIMATE', 'OUTLOOK'
        ]
        
        medium_relevance_keywords = [
            'STOCK', 'SHARES', 'TRADING', 'PRICE', 'TARGET', 'UPGRADE',
            'DOWNGRADE', 'ANALYST', 'RATING', 'DIVIDEND', 'SPLIT'
        ]
        
        low_relevance_keywords = [
            'MARKET', 'INVESTOR', 'INVESTMENT', 'ACQUISITION', 'MERGER',
            'IPO', 'BUYBACK', 'ACQUISITION', 'PARTNERSHIP'
        ]
        
        text_upper = f"{title_upper} {summary_upper}"
        
        # Count high-value keywords
        high_count = sum(1 for keyword in high_relevance_keywords if keyword in text_upper)
        medium_count = sum(1 for keyword in medium_relevance_keywords if keyword in text_upper)
        low_count = sum(1 for keyword in low_relevance_keywords if keyword in text_upper)
        
        relevance += min(0.3, high_count * 0.1)
        relevance += min(0.2, medium_count * 0.05)
        relevance += min(0.1, low_count * 0.02)
        
        # Company-specific terms boost
        company_terms = get_company_terms(symbol_upper)
        company_mentions = sum(1 for term in company_terms if term in text_upper)
        if company_mentions > 0:
            relevance += min(0.3, company_mentions * 0.1)
        
        return min(1.0, max(0.0, relevance))
    except:
        return 0.3

def get_company_terms(symbol: str) -> list:
    """Get company-specific terms for better relevance detection"""
    terms_map = {
        'AAPL': ['APPLE', 'IPHONE', 'IPAD', 'MAC', 'MACBOOK', 'AIRPODS', 'WATCH'],
        'MSFT': ['MICROSOFT', 'WINDOWS', 'AZURE', 'OFFICE', 'XBOX', 'TEAMS'],
        'GOOGL': ['GOOGLE', 'ALPHABET', 'SEARCH', 'YOUTUBE', 'ANDROID', 'CHROME'],
        'GOOG': ['GOOGLE', 'ALPHABET', 'SEARCH', 'YOUTUBE', 'ANDROID', 'CHROME'],
        'AMZN': ['AMAZON', 'AWS', 'PRIME', 'ALEXA', 'KINDLE', 'WAREHOUSE'],
        'TSLA': ['TESLA', 'ELECTRIC', 'MUSK', 'AUTOPILOT', 'MODEL', 'CHARGING'],
        'META': ['META', 'FACEBOOK', 'INSTAGRAM', 'WHATSAPP', 'METAVERSE'],
        'NVDA': ['NVIDIA', 'GPU', 'AI', 'CHIP', 'GAMING', 'DATACENTER'],
        'NFLX': ['NETFLIX', 'STREAMING', 'SUBSCRIBER', 'CONTENT', 'SERIES']
    }
    return terms_map.get(symbol, [symbol])

@st.cache_data(ttl=900)
def get_enhanced_news_sentiment(symbol: str, days_back: int = 7) -> dict:
    """Enhanced news sentiment analysis with better source handling"""
    try:
        # Multiple reliable news sources
        news_sources = [
            {
                'url': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'name': 'Yahoo Finance',
                'weight': 1.0
            },
            {
                'url': 'https://feeds.marketwatch.com/marketwatch/realtimeheadlines/',
                'name': 'MarketWatch',
                'weight': 0.9
            },
            {
                'url': f'https://news.google.com/rss/search?q={quote(symbol)}+stock+earnings+financial&hl=en&gl=US&ceid=US:en',
                'name': 'Google News (Financial)',
                'weight': 0.8
            }
        ]
        
        all_articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for source in news_sources:
            try:
                feed = feedparser.parse(source['url'])
                
                if not feed.entries:
                    continue
                
                for entry in feed.entries[:25]:
                    title = entry.get('title', '').strip()
                    summary = entry.get('summary', entry.get('description', '')).strip()
                    link = entry.get('link', '')
                    
                    # Clean HTML tags and entities
                    title = re.sub(r'<[^>]+>', '', title)
                    title = re.sub(r'&[^;]+;', ' ', title)
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = re.sub(r'&[^;]+;', ' ', summary)
                    
                    # Calculate relevance with enhanced algorithm
                    relevance_score = calculate_article_relevance(title, summary, symbol)
                    
                    if relevance_score > 0.4:  # Higher threshold for better quality
                        # Enhanced date parsing
                        pub_date = parse_article_date(entry)
                        
                        if pub_date and pub_date >= cutoff_date:
                            all_articles.append({
                                'title': title[:250].strip(),
                                'summary': summary[:600].strip(),
                                'date': pub_date,
                                'source': source['name'],
                                'link': link,
                                'relevance': relevance_score,
                                'weight': source['weight']
                            })
                
                time.sleep(0.3)  # Respectful delay
            except Exception as e:
                continue
        
        if not all_articles:
            return create_empty_sentiment_result()
        
        # Sort by relevance and date, prioritize recent high-relevance articles
        all_articles.sort(key=lambda x: (x['relevance'] * x['weight'], x['date']), reverse=True)
        
        # Analyze sentiment with weighted scoring
        return analyze_weighted_sentiment(all_articles[:15], symbol)
        
    except Exception as e:
        return create_empty_sentiment_result()

def parse_article_date(entry) -> datetime:
    """Enhanced date parsing for news articles"""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        elif entry.get('published'):
            # Try multiple date formats
            date_str = entry.get('published')
            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        return datetime.now() - timedelta(hours=1)  # Default to 1 hour ago
    except:
        return datetime.now() - timedelta(hours=1)

def create_empty_sentiment_result() -> dict:
    """Create empty sentiment result structure"""
    return {
        'sentiment_score': 0,
        'article_count': 0,
        'positive_articles': 0,
        'negative_articles': 0,
        'neutral_articles': 0,
        'confidence': 0,
        'articles': [],
        'sentiment_trend': [],
        'source_distribution': {}
    }

def analyze_weighted_sentiment(articles: list, symbol: str) -> dict:
    """Analyze sentiment with weighted scoring and enhanced metrics"""
    try:
        if not articles:
            return create_empty_sentiment_result()
        
        sentiments = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_weight = 0
        source_distribution = {}
        
        for article in articles:
            text = f"{article['title']} {article['summary']}"
            sentiment_scores = analyzer.polarity_scores(text)
            
            sentiment = sentiment_scores['compound']
            weight = article['weight'] * article['relevance']
            
            sentiments.append(sentiment * weight)
            total_weight += weight
            
            # Count articles by sentiment
            if sentiment > 0.05:
                positive_count += 1
            elif sentiment < -0.05:
                negative_count += 1
            else:
                neutral_count += 1
            
            # Track source distribution
            source = article['source']
            source_distribution[source] = source_distribution.get(source, 0) + 1
            
            # Add individual scores to articles
            article['sentiment'] = sentiment
            article['sentiment_label'] = get_sentiment_label(sentiment)[0]
            article['confidence'] = abs(sentiment) * article['relevance']
        
        # Calculate weighted overall sentiment
        overall_sentiment = sum(sentiments) / total_weight if total_weight > 0 else 0
        
        # Calculate confidence based on multiple factors
        confidence = calculate_sentiment_confidence(articles, overall_sentiment)
        
        # Create sentiment trend
        sentiment_trend = create_sentiment_trend(articles)
        
        return {
            'sentiment_score': overall_sentiment,
            'article_count': len(articles),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'confidence': confidence,
            'articles': articles,
            'sentiment_trend': sentiment_trend,
            'source_distribution': source_distribution
        }
        
    except Exception as e:
        return create_empty_sentiment_result()

def calculate_sentiment_confidence(articles: list, overall_sentiment: float) -> float:
    """Calculate confidence score for sentiment analysis"""
    try:
        if not articles:
            return 0
        
        base_confidence = min(len(articles) * 10, 60)  # Up to 60% from article count
        
        # Relevance boost
        avg_relevance = sum(article['relevance'] for article in articles) / len(articles)
        relevance_boost = avg_relevance * 25  # Up to 25% from relevance
        
        # Consistency boost (how much articles agree)
        sentiments = [article['sentiment'] for article in articles]
        sentiment_std = np.std(sentiments) if len(sentiments) > 1 else 0
        consistency_boost = max(0, 15 - sentiment_std * 30)  # Up to 15% from consistency
        
        total_confidence = base_confidence + relevance_boost + consistency_boost
        return min(100, max(0, total_confidence))
        
    except:
        return 50

def create_sentiment_trend(articles: list) -> list:
    """Create sentiment trend data from articles"""
    try:
        if not articles:
            return []
        
        # Group articles by date
        daily_sentiments = {}
        for article in articles:
            date_key = article['date'].date()
            if date_key not in daily_sentiments:
                daily_sentiments[date_key] = []
            daily_sentiments[date_key].append(article['sentiment'])
        
        # Calculate daily averages
        trend_data = []
        for date, sentiments in sorted(daily_sentiments.items()):
            avg_sentiment = np.mean(sentiments)
            trend_data.append({
                'date': date.isoformat(),
                'sentiment': avg_sentiment,
                'article_count': len(sentiments)
            })
        
        return trend_data
    except:
        return []

def calculate_rsi(data: pd.DataFrame, window: int = 14) -> float:
    """Calculate Relative Strength Index with enhanced accuracy"""
    try:
        if len(data) < window + 1:
            return 50
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        # Avoid division by zero
        loss = loss.replace(0, 0.0001)
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    except:
        return 50

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD with enhanced signal detection"""
    try:
        if len(data) < slow + signal:
            return {'macd': 0, 'signal_line': 0, 'histogram': 0, 'signal': 0, 'strength': 0}
        
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        # Calculate signal strength
        recent_histogram = histogram.tail(5)
        signal_strength = abs(recent_histogram.mean()) / data['Close'].iloc[-1] * 1000
        
        return {
            'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0,
            'signal_line': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0,
            'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0,
            'signal': 1 if histogram.iloc[-1] > 0 else -1,
            'strength': min(100, max(0, signal_strength))
        }
    except:
        return {'macd': 0, 'signal_line': 0, 'histogram': 0, 'signal': 0, 'strength': 0}

def calculate_bollinger_bands(data: pd.DataFrame, window: int = 20, num_std: float = 2) -> dict:
    """Calculate Bollinger Bands with position analysis"""
    try:
        if len(data) < window:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'position': 0.5, 'squeeze': False}
        
        middle_band = data['Close'].rolling(window=window).mean()
        std_dev = data['Close'].rolling(window=window).std()
        
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        current_price = data['Close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Calculate position within bands
        if current_upper != current_lower:
            bb_position = (current_price - current_lower) / (current_upper - current_lower)
        else:
            bb_position = 0.5
        
        # Detect squeeze (low volatility)
        band_width = (current_upper - current_lower) / middle_band.iloc[-1]
        is_squeeze = band_width < 0.1  # Less than 10% width indicates squeeze
        
        return {
            'upper': float(current_upper) if not pd.isna(current_upper) else 0,
            'middle': float(middle_band.iloc[-1]) if not pd.isna(middle_band.iloc[-1]) else 0,
            'lower': float(current_lower) if not pd.isna(current_lower) else 0,
            'position': float(bb_position),
            'squeeze': is_squeeze
        }
    except:
        return {'upper': 0, 'middle': 0, 'lower': 0, 'position': 0.5, 'squeeze': False}

def calculate_enhanced_technical_score(data: pd.DataFrame) -> dict:
    """Enhanced technical analysis with multiple indicators and confidence scoring"""
    try:
        if len(data) < 20:
            return {'score': 50, 'confidence': 0, 'signals': [], 'strength': 'Weak'}
        
        signals = []
        score = 50  # Start neutral
        
        # RSI Analysis (25% weight)
        rsi = calculate_rsi(data)
        if 30 <= rsi <= 70:
            score += 15
            signals.append(f"RSI Healthy ({rsi:.1f})")
        elif rsi < 30:
            score += 20
            signals.append(f"RSI Oversold - Buy Signal ({rsi:.1f})")
        elif rsi > 70:
            score -= 15
            signals.append(f"RSI Overbought - Caution ({rsi:.1f})")
        
        # MACD Analysis (25% weight)
        macd_data = calculate_macd(data)
        if macd_data['signal'] > 0:
            boost = min(20, macd_data['strength'] / 5)
            score += boost
            signals.append(f"MACD Bullish (Strength: {macd_data['strength']:.1f})")
        else:
            penalty = min(20, macd_data['strength'] / 5)
            score -= penalty
            signals.append(f"MACD Bearish (Strength: {macd_data['strength']:.1f})")
        
        # Bollinger Bands Analysis (20% weight)
        bb_data = calculate_bollinger_bands(data)
        bb_position = bb_data['position']
        if 0.2 <= bb_position <= 0.8:
            score += 10
            signals.append("Price in BB Normal Range")
        elif bb_position < 0.2:
            score += 15
            signals.append("Price Near BB Lower Band - Buy Signal")
        else:
            score -= 10
            signals.append("Price Near BB Upper Band - Caution")
        
        if bb_data['squeeze']:
            signals.append("Bollinger Squeeze Detected - Breakout Expected")
        
        # Moving Average Analysis (20% weight)
        if len(data) >= 50:
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                score += 15
                signals.append("Strong Uptrend (Price > SMA20 > SMA50)")
            elif current_price < sma_20 < sma_50:
                score -= 15
                signals.append("Strong Downtrend (Price < SMA20 < SMA50)")
            elif current_price > sma_20:
                score += 5
                signals.append("Short-term Uptrend (Price > SMA20)")
        
        # Volume Analysis (10% weight)
        if len(data) >= 20:
            recent_volume = data['Volume'].tail(5).mean()
            avg_volume = data['Volume'].tail(20).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > 1.5:
                score += 10
                signals.append(f"High Volume Confirmation ({volume_ratio:.1f}x)")
            elif volume_ratio < 0.7:
                score -= 5
                signals.append(f"Low Volume - Weak Signal ({volume_ratio:.1f}x)")
        
        # Volatility penalty
        if len(data) >= 30:
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std()
            if volatility > 0.05:  # Very high volatility
                penalty = min(15, (volatility - 0.05) * 300)
                score -= penalty
                signals.append(f"High Volatility Risk ({volatility*100:.1f}%)")
        
        final_score = min(100, max(0, score))
        
        # Calculate confidence based on data quality and signal strength
        confidence = min(100, len(data) * 2 + len(signals) * 5)
        
        # Determine overall strength
        if final_score >= 75:
            strength = "Very Strong"
        elif final_score >= 60:
            strength = "Strong"
        elif final_score >= 40:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        return {
            'score': final_score,
            'confidence': confidence,
            'signals': signals,
            'strength': strength,
            'rsi': rsi,
            'macd': macd_data,
            'bollinger': bb_data
        }
    except Exception as e:
        return {'score': 50, 'confidence': 0, 'signals': [f"Error: {str(e)}"], 'strength': 'Unknown'}

def calculate_enhanced_sentiment_score(sentiment_data: dict) -> dict:
    """Enhanced sentiment scoring with confidence weighting"""
    try:
        if not sentiment_data or sentiment_data.get('article_count', 0) == 0:
            return {'score': 50, 'confidence': 0, 'factors': []}
        
        factors = []
        base_sentiment = sentiment_data.get('sentiment_score', 0)
        article_count = sentiment_data.get('article_count', 0)
        confidence = sentiment_data.get('confidence', 0)
        
        # Convert sentiment (-1 to 1) to score (0 to 100)
        base_score = (base_sentiment + 1) * 50
        
        # Article count factor
        count_factor = min(1.0, article_count / 10)
        factors.append(f"Article Count: {article_count} (Factor: {count_factor:.2f})")
        
        # Confidence factor
        conf_factor = confidence / 100
        factors.append(f"Confidence: {confidence:.1f}% (Factor: {conf_factor:.2f})")
        
        # Sentiment distribution factor
        pos_articles = sentiment_data.get('positive_articles', 0)
        neg_articles = sentiment_data.get('negative_articles', 0)
        
        if article_count > 0:
            pos_ratio = pos_articles / article_count
            neg_ratio = neg_articles / article_count
            
            if pos_ratio > 0.6:
                base_score += 10
                factors.append(f"Strong Positive Bias ({pos_ratio:.1%})")
            elif neg_ratio > 0.6:
                base_score -= 10
                factors.append(f"Strong Negative Bias ({neg_ratio:.1%})")
        
        # Apply confidence weighting
        final_score = 50 + (base_score - 50) * conf_factor * count_factor
        final_score = min(100, max(0, final_score))
        
        return {
            'score': final_score,
            'confidence': confidence,
            'factors': factors
        }
    except:
        return {'score': 50, 'confidence': 0, 'factors': ['Error in sentiment calculation']}

def calculate_comprehensive_score(data: pd.DataFrame, sentiment_data: dict, risk_tolerance: str = 'Moderate') -> dict:
    """Enhanced comprehensive scoring with detailed breakdown"""
    try:
        if data is None or data.empty:
            return create_empty_score_result()
        
        # Calculate enhanced component scores
        technical_result = calculate_enhanced_technical_score(data)
        sentiment_result = calculate_enhanced_sentiment_score(sentiment_data)
        volume_result = calculate_volume_score(data)
        trend_result = calculate_trend_score(data)
        
        # Enhanced weights based on data quality and confidence
        base_weights = {
            'technical': 0.40,
            'sentiment': 0.25,
            'volume': 0.20,
            'trend': 0.15
        }
        
        # Adjust weights based on confidence levels
        tech_confidence = technical_result.get('confidence', 50) / 100
        sent_confidence = sentiment_result.get('confidence', 50) / 100
        
        # Rebalance weights based on confidence
        if sent_confidence < 0.3:  # Low sentiment confidence
            base_weights['technical'] += 0.15
            base_weights['sentiment'] -= 0.15
        elif tech_confidence < 0.3:  # Low technical confidence
            base_weights['sentiment'] += 0.15
            base_weights['technical'] -= 0.15
        
        # Risk tolerance adjustments
        risk_adjustments = {
            'Conservative': {'volatility_penalty': 1.5, 'trend_weight': 0.8, 'safety_bonus': 5},
            'Moderate': {'volatility_penalty': 1.0, 'trend_weight': 1.0, 'safety_bonus': 0},
            'Aggressive': {'volatility_penalty': 0.5, 'trend_weight': 1.2, 'safety_bonus': -5}
        }
        
        risk_adj = risk_adjustments.get(risk_tolerance, risk_adjustments['Moderate'])
        
        # Calculate weighted score
        overall_score = (
            technical_result['score'] * base_weights['technical'] +
            sentiment_result['score'] * base_weights['sentiment'] +
            volume_result['score'] * base_weights['volume'] +
            trend_result['score'] * base_weights['trend'] * risk_adj['trend_weight']
        )
        
        # Apply risk adjustments
        overall_score += risk_adj['safety_bonus']
        
        # Apply volatility penalty
        if len(data) >= 20:
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std()
            volatility_penalty = min(20, volatility * 1000 * risk_adj['volatility_penalty'])
            overall_score = max(0, overall_score - volatility_penalty)
        
        overall_score = min(100, max(0, overall_score))
        
        # Calculate overall confidence
        overall_confidence = (
            technical_result.get('confidence', 50) * base_weights['technical'] +
            sentiment_result.get('confidence', 50) * base_weights['sentiment'] +
            50 * (base_weights['volume'] + base_weights['trend'])  # Default confidence for volume/trend
        )
        
        # Generate enhanced recommendation
        recommendation = generate_enhanced_recommendation(
            overall_score, overall_confidence, risk_tolerance, 
            technical_result, sentiment_result
        )
        
        return {
            'overall_score': overall_score,
            'technical_score': technical_result['score'],
            'sentiment_score': sentiment_result['score'],
            'volume_score': volume_result['score'],
            'trend_score': trend_result['score'],
            'confidence': overall_confidence,
            'recommendation': recommendation['action'],
            'recommendation_reason': recommendation['reason'],
            'technical_signals': technical_result.get('signals', []),
            'sentiment_factors': sentiment_result.get('factors', []),
            'risk_factors': identify_risk_factors(data, technical_result, sentiment_data),
            'score_breakdown': {
                'weights_used': base_weights,
                'risk_adjustments': risk_adj,
                'confidence_levels': {
                    'technical': technical_result.get('confidence', 50),
                    'sentiment': sentiment_result.get('confidence', 50)
                }
            }
        }
    except Exception as e:
        return create_empty_score_result()

def calculate_volume_score(data: pd.DataFrame) -> dict:
    """Enhanced volume analysis scoring"""
    try:
        if len(data) < 20:
            return {'score': 50, 'signals': ['Insufficient data for volume analysis']}
        
        signals = []
        score = 50
        
        recent_volume = data['Volume'].tail(5).mean()
        avg_volume = data['Volume'].tail(20).mean()
        
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        # Volume trend analysis
        if volume_ratio > 2.0:
            score = 85
            signals.append(f"Exceptional Volume ({volume_ratio:.1f}x average)")
        elif volume_ratio > 1.5:
            score = 70
            signals.append(f"High Volume Confirmation ({volume_ratio:.1f}x average)")
        elif volume_ratio > 1.2:
            score = 60
            signals.append(f"Above Average Volume ({volume_ratio:.1f}x average)")
        elif volume_ratio > 0.8:
            score = 50
            signals.append(f"Normal Volume ({volume_ratio:.1f}x average)")
        else:
            score = 35
            signals.append(f"Low Volume - Weak Signal ({volume_ratio:.1f}x average)")
        
        # Price-volume relationship
        if len(data) >= 2:
            price_change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
            
            if abs(price_change) > 0.02 and volume_ratio > 1.2:
                score += 10
                signals.append("Volume Confirms Price Movement")
            elif abs(price_change) > 0.03 and volume_ratio < 0.8:
                score -= 10
                signals.append("Price Movement Not Confirmed by Volume")
        
        return {'score': min(100, max(0, score)), 'signals': signals}
    except:
        return {'score': 50, 'signals': ['Error in volume calculation']}

def calculate_trend_score(data: pd.DataFrame) -> dict:
    """Enhanced trend analysis with multiple timeframes"""
    try:
        if len(data) < 20:
            return {'score': 50, 'signals': ['Insufficient data for trend analysis']}
        
        signals = []
        
        # Calculate trend strength for different timeframes
        short_trend = calculate_trend_strength(data, 5)
        medium_trend = calculate_trend_strength(data, 10)
        long_trend = calculate_trend_strength(data, 20)
        
        # Weighted trend score with recency bias
        trend_score = (short_trend * 0.5 + medium_trend * 0.3 + long_trend * 0.2)
        
        # Convert to 0-100 scale
        score = 50 + (trend_score * 50)
        
        # Add trend strength signals
        if short_trend > 0.5:
            signals.append("Strong Short-term Uptrend")
        elif short_trend < -0.5:
            signals.append("Strong Short-term Downtrend")
        
        if medium_trend > 0.3:
            signals.append("Medium-term Uptrend")
        elif medium_trend < -0.3:
            signals.append("Medium-term Downtrend")
        
        if long_trend > 0.2:
            signals.append("Long-term Uptrend")
        elif long_trend < -0.2:
            signals.append("Long-term Downtrend")
        
        # Trend consistency bonus
        trends = [short_trend, medium_trend, long_trend]
        if all(t > 0 for t in trends):
            score += 15
            signals.append("All Timeframes Bullish")
        elif all(t < 0 for t in trends):
            score -= 15
            signals.append("All Timeframes Bearish")
        
        return {'score': min(100, max(0, score)), 'signals': signals}
    except:
        return {'score': 50, 'signals': ['Error in trend calculation']}

def calculate_trend_strength(data: pd.DataFrame, window: int) -> float:
    """Calculate trend strength using linear regression"""
    try:
        if len(data) < window:
            return 0
        
        prices = data['Close'].tail(window)
        x = np.arange(len(prices))
        
        # Linear regression
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalize slope relative to price
        trend_strength = slope / prices.mean() * 100
        
        # Cap the trend strength
        return min(1, max(-1, trend_strength))
    except:
        return 0

def generate_enhanced_recommendation(overall_score: float, confidence: float, 
                                   risk_tolerance: str, technical_result: dict, 
                                   sentiment_result: dict) -> dict:
    """Generate detailed investment recommendation"""
    try:
        # Dynamic thresholds based on confidence and risk tolerance
        base_thresholds = {
            'Conservative': {'buy': 70, 'sell': 35},
            'Moderate': {'buy': 65, 'sell': 40},
            'Aggressive': {'buy': 60, 'sell': 45}
        }
        
        thresholds = base_thresholds.get(risk_tolerance, base_thresholds['Moderate'])
        
        # Adjust thresholds based on confidence
        confidence_factor = confidence / 100
        if confidence_factor < 0.5:
            # Lower confidence = more conservative thresholds
            thresholds['buy'] += 5
            thresholds['sell'] -= 5
        
        # Generate recommendation
        if overall_score >= thresholds['buy']:
            if overall_score >= 85:
                action = 'Strong Buy'
                reason = f"Exceptional score ({overall_score:.0f}) with strong technical and fundamental indicators"
            else:
                action = 'Buy'
                reason = f"Positive outlook ({overall_score:.0f}) aligns with {risk_tolerance.lower()} risk profile"
        elif overall_score <= thresholds['sell']:
            if overall_score <= 25:
                action = 'Strong Sell'
                reason = f"Poor fundamentals ({overall_score:.0f}) suggest significant downside risk"
            else:
                action = 'Sell'
                reason = f"Negative outlook ({overall_score:.0f}) warrants position reduction"
        else:
            action = 'Hold'
            reason = f"Mixed signals ({overall_score:.0f}) suggest maintaining current position"
        
        # Add confidence qualifier
        if confidence < 50:
            reason += f" (Low confidence: {confidence:.0f}%)"
        elif confidence < 70:
            reason += f" (Moderate confidence: {confidence:.0f}%)"
        else:
            reason += f" (High confidence: {confidence:.0f}%)"
        
        return {'action': action, 'reason': reason}
    except:
        return {'action': 'Hold', 'reason': 'Unable to generate recommendation due to insufficient data'}

def identify_risk_factors(data: pd.DataFrame, technical_result: dict, sentiment_data: dict) -> list:
    """Identify potential risk factors"""
    risk_factors = []
    
    try:
        # High volatility risk
        if len(data) >= 20:
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std()
            if volatility > 0.04:  # 4% daily volatility
                risk_factors.append(f"High volatility detected ({volatility*100:.1f}% daily)")
        
        # Technical risks
        rsi = technical_result.get('rsi', 50)
        if rsi > 80:
            risk_factors.append("Extremely overbought conditions (RSI > 80)")
        elif rsi < 20:
            risk_factors.append("Extremely oversold conditions (RSI < 20)")
        
        # Sentiment risks
        if sentiment_data and sentiment_data.get('confidence', 0) < 30:
            risk_factors.append("Low confidence in sentiment analysis")
        
        neg_articles = sentiment_data.get('negative_articles', 0)
        total_articles = sentiment_data.get('article_count', 0)
        if total_articles > 0 and neg_articles / total_articles > 0.7:
            risk_factors.append("Predominantly negative news sentiment")
        
        # Volume risks
        if len(data) >= 5:
            recent_volume = data['Volume'].tail(5).mean()
            if recent_volume == 0:
                risk_factors.append("Zero or very low trading volume")
        
        # Price trend risks
        if len(data) >= 10:
            recent_change = (data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10]
            if abs(recent_change) > 0.25:  # 25% move in 10 days
                risk_factors.append(f"Extreme price movement ({recent_change*100:+.1f}% in 10 days)")
        
        if not risk_factors:
            risk_factors.append("No significant risk factors identified")
        
        return risk_factors
    except:
        return ["Unable to assess risk factors"]

def create_empty_score_result() -> dict:
    """Create empty score result structure"""
    return {
        'overall_score': 0,
        'technical_score': 0,
        'sentiment_score': 0,
        'volume_score': 0,
        'trend_score': 0,
        'confidence': 0,
        'recommendation': 'Hold',
        'recommendation_reason': 'Insufficient data for analysis',
        'technical_signals': [],
        'sentiment_factors': [],
        'risk_factors': ['Insufficient data'],
        'score_breakdown': {}
    }

def create_enhanced_price_chart(data: pd.DataFrame, symbol: str) -> go.Figure:
    """Create comprehensive technical analysis chart"""
    try:
        if data.empty:
            return create_empty_chart("No data available for charting")
        
        # Create subplots with custom spacing
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(
                f'{symbol} Price Action with Technical Indicators',
                'Volume Analysis',
                'RSI (Relative Strength Index)',
                'MACD Convergence Divergence'
            ),
            row_heights=[0.5, 0.2, 0.15, 0.15]
        )
        
        # Main price chart with candlesticks
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Price",
                increasing_line_color='#00C851',
                decreasing_line_color='#FF4444',
                increasing_fillcolor='#00C851',
                decreasing_fillcolor='#FF4444'
            ),
            row=1, col=1
        )
        
        # Moving averages
        if len(data) >= 20:
            sma_20 = data['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_20,
                    name="SMA 20",
                    line=dict(color="orange", width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        if len(data) >= 50:
            sma_50 = data['Close'].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_50,
                    name="SMA 50",
                    line=dict(color="blue", width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        # Bollinger Bands
        if len(data) >= 20:
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=upper_band,
                    name="BB Upper",
                    line=dict(color="gray", width=1, dash="dash"),
                    opacity=0.5
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=lower_band,
                    name="BB Lower",
                    line=dict(color="gray", width=1, dash="dash"),
                    opacity=0.5,
                    fill='tonexty',
                    fillcolor='rgba(128, 128, 128, 0.1)'
                ),
                row=1, col=1
            )
        
        # Enhanced volume chart
        colors = ['#00C851' if close >= open else '#FF4444' 
                 for close, open in zip(data['Close'], data['Open'])]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Volume moving average
        if len(data) >= 20:
            volume_ma = data['Volume'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=volume_ma,
                    name="Volume MA (20)",
                    line=dict(color="purple", width=2)
                ),
                row=2, col=1
            )
        
        # RSI chart
        if len(data) >= 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=rsi,
                    name="RSI",
                    line=dict(color="purple", width=2)
                ),
                row=3, col=1
            )
            
            # RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=3)
            
            fig.update_yaxes(range=[0, 100], row=3, col=1)
        
        # MACD chart
        if len(data) >= 26:
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=macd_line,
                    name="MACD",
                    line=dict(color="blue", width=2)
                ),
                row=4, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=signal_line,
                    name="Signal",
                    line=dict(color="red", width=2)
                ),
                row=4, col=1
            )
            
            # MACD histogram
            colors = ['green' if val >= 0 else 'red' for val in histogram]
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=histogram,
                    name="Histogram",
                    marker_color=colors,
                    opacity=0.6
                ),
                row=4, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - Comprehensive Technical Analysis",
            xaxis_rangeslider_visible=False,
            height=1000,
            showlegend=True,
            template="plotly_white",
            hovermode='x unified'
        )
        
        # Style the chart
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
        
        return fig
    except Exception as e:
        return create_empty_chart(f"Error creating chart: {str(e)}")

def create_empty_chart(message: str) -> go.Figure:
    """Create empty chart with error message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig

def format_large_number(number: float) -> str:
    """Format large numbers with appropriate suffixes"""
    try:
        if number >= 1e12:
            return f"{number/1e12:.2f}T"
        elif number >= 1e9:
            return f"{number/1e9:.2f}B"
        elif number >= 1e6:
            return f"{number/1e6:.2f}M"
        elif number >= 1e3:
            return f"{number/1e3:.2f}K"
        else:
            return f"{number:.0f}"
    except:
        return "N/A"

def get_market_status() -> dict:
    """Get current market status"""
    try:
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        
        is_weekend = weekday >= 5
        is_market_hours = 9 <= hour < 16
        
        is_open = not is_weekend and is_market_hours
        
        return {
            'is_open': is_open,
            'status': 'Open' if is_open else 'Closed',
            'next_open': 'Next trading day' if is_weekend else 'Tomorrow 9:30 AM EST' if not is_market_hours else 'Currently open'
        }
    except:
        return {
            'is_open': False,
            'status': 'Unknown',
            'next_open': 'Unable to determine'
        }

def get_sentiment_label(score: float) -> tuple:
    """Get sentiment label and CSS class"""
    if score > 0.1:
        return "Positive", "sentiment-positive"
    elif score < -0.1:
        return "Negative", "sentiment-negative"
    else:
        return "Neutral", "sentiment-neutral"

# ---------- Main Application -----------

def main():
    # Header with enhanced branding
    st.title("📊 StockMood Pro")
    st.markdown("**Professional Stock Analysis Platform with Multi-Factor Predictive Scoring**")
    st.markdown("*Designed for independent investors - Complex analysis, simple insights*")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Stock Analysis Center")
        
        # Stock search with enhanced UX
        stock_symbol = st.text_input(
            "Enter Stock Symbol", 
            value="AAPL",
            placeholder="e.g., AAPL, MSFT, GOOGL",
            help="Enter a stock ticker symbol to analyze"
        ).upper()
        
        # Timeframe selection
        timeframe = st.selectbox(
            "Analysis Timeframe",
            options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
            index=3,
            help="Select the time period for historical data analysis"
        )
        
        # Risk tolerance with enhanced descriptions
        st.subheader("⚖️ Investment Profile")
        risk_tolerance = st.select_slider(
            "Risk Tolerance",
            options=['Conservative', 'Moderate', 'Aggressive'],
            value='Moderate',
            help="Conservative: Lower risk, higher quality stocks | Moderate: Balanced approach | Aggressive: Higher risk, growth-focused"
        )
        
        # Analysis features
        st.subheader("📊 Analysis Features")
        show_technical = st.checkbox("Technical Analysis", value=True, help="RSI, MACD, Bollinger Bands, Moving Averages")
        show_sentiment = st.checkbox("News Sentiment", value=True, help="AI-powered sentiment analysis of financial news")
        show_prediction = st.checkbox("Predictive Score", value=True, help="Multi-factor predictive scoring algorithm")
        
        # Market status with enhanced display
        market_status = get_market_status()
        if market_status['is_open']:
            st.success(f"🟢 Market {market_status['status']}")
        else:
            st.info(f"🔴 Market {market_status['status']}")
        st.caption(f"Next: {market_status['next_open']}")
        
        # Quick stats section
        st.subheader("📈 Quick Stats")
        st.caption("Analysis powered by:")
        st.caption("• Yahoo Finance API")
        st.caption("• VADER Sentiment Analysis")
        st.caption("• Multi-source news feeds")
        st.caption("• Advanced technical indicators")
    
    # Main content area
    if stock_symbol:
        try:
            # Load data with progress indicator
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text(f"Loading data for {stock_symbol}...")
            progress_bar.progress(25)
            
            stock_data, company_info = get_stock_data(stock_symbol, timeframe)
            progress_bar.progress(50)
            
            if stock_data is None or stock_data.empty:
                st.error(f"❌ No data found for symbol '{stock_symbol}'. Please check the symbol and try again.")
                st.info("💡 **Tips:**\n- Make sure the stock symbol is correct\n- Try popular symbols like AAPL, MSFT, GOOGL\n- Check if the market is open")
                return
            
            # Company header with enhanced information
            company_name = company_info.get('longName', stock_symbol) if company_info else stock_symbol
            
            # Create header with metrics
            col1, col2 = st.columns([3, 1])
            with col1:
                st.header(f"{company_name} ({stock_symbol})")
                if company_info:
                    sector = company_info.get('sector', 'N/A')
                    industry = company_info.get('industry', 'N/A')
                    exchange = company_info.get('exchange', 'N/A')
                    st.caption(f"**Sector:** {sector} | **Industry:** {industry} | **Exchange:** {exchange}")
            
            with col2:
                if company_info and company_info.get('marketCap'):
                    market_cap = company_info.get('marketCap', 0)
                    st.metric("Market Cap", f"{format_large_number(market_cap)}")
            
            progress_bar.progress(75)
            
            # Current price section with enhanced metrics
            if len(stock_data) >= 2:
                current_price = stock_data['Close'].iloc[-1]
                previous_close = stock_data['Close'].iloc[-2]
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                
                # Price metrics
                price_col1, price_col2, price_col3, price_col4, price_col5 = st.columns(5)
                
                with price_col1:
                    currency = company_info.get('currency', 'USD') if company_info else 'USD'
                    st.metric(
                        "Current Price",
                        f"{currency} {current_price:.2f}",
                        delta=f"{change:+.2f} ({change_percent:+.2f}%)"
                    )
                
                with price_col2:
                    day_high = stock_data['High'].iloc[-1]
                    day_low = stock_data['Low'].iloc[-1]
                    st.metric("Day Range", f"{day_low:.2f} - {day_high:.2f}")
                
                with price_col3:
                    volume = stock_data['Volume'].iloc[-1]
                    st.metric("Volume", f"{format_large_number(volume)}")
                
                with price_col4:
                    if len(stock_data) >= 20:
                        avg_volume = stock_data['Volume'].tail(20).mean()
                        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
                        st.metric("Vol Ratio", f"{volume_ratio:.1f}x")
                    else:
                        st.metric("Vol Ratio", "N/A")
                
                with price_col5:
                    if len(stock_data) >= 30:
                        returns = stock_data['Close'].pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252) * 100
                        st.metric("Volatility", f"{volatility:.1f}%")
                    else:
                        st.metric("Volatility", "N/A")
            
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()
            
            # Main prediction score (enhanced)
            if show_prediction:
                st.subheader("🎯 Enhanced StockMood Prediction Score")
                
                with st.spinner("Performing comprehensive analysis..."):
                    # Get enhanced sentiment data
                    sentiment_data = get_enhanced_news_sentiment(stock_symbol) if show_sentiment else {}
                    
                    # Calculate comprehensive score
                    score_data = calculate_comprehensive_score(
                        stock_data, sentiment_data, risk_tolerance
                    )
                
                # Main score display with enhanced visualization
                score_col1, score_col2, score_col3 = st.columns([2, 1, 1])
                
                with score_col1:
                    overall_score = score_data.get('overall_score', 0)
                    
                    # Enhanced score display
                    score_html = f"""
                    <div class="score-display">
                        <div class="score-number">{overall_score:.0f}</div>
                        <div class="score-label">Investment Score</div>
                        <div style="margin-top: 1rem;">
                            <div class="confidence-meter">
                                <div class="confidence-indicator" style="width: {overall_score}%;"></div>
                            </div>
                        </div>
                        <p style="margin-top: 1rem; color: #64748b; font-size: 0.9rem;">
                            Score combines technical analysis, sentiment, volume, and trend factors
                        </p>
                    </div>
                    """
                    st.markdown(score_html, unsafe_allow_html=True)
                
                with score_col2:
                    confidence = score_data.get('confidence', 0)
                    st.metric("Analysis Confidence", f"{confidence:.0f}%")
                    
                    # Confidence explanation
                    if confidence >= 80:
                        st.success("Very High")
                    elif confidence >= 60:
                        st.info("High")
                    elif confidence >= 40:
                        st.warning("Medium")
                    else:
                        st.error("Low")
                
                with score_col3:
                    # Data quality metrics
                    data_points = len(stock_data)
                    sentiment_articles = sentiment_data.get('article_count', 0) if sentiment_data else 0
                    st.metric("Data Quality", "Excellent" if data_points > 100 else "Good" if data_points > 50 else "Fair")
                    st.caption(f"Price Data: {data_points} days")
                    st.caption(f"News Articles: {sentiment_articles}")
                
                # Enhanced score breakdown
                st.subheader("📋 Detailed Score Analysis")
                
                # Component scores with detailed metrics
                breakdown_cols = st.columns(4)
                
                components = [
                    ("Technical", score_data.get('technical_score', 0), "📊", "RSI, MACD, Bollinger Bands"),
                    ("Sentiment", score_data.get('sentiment_score', 0), "💭", "News sentiment analysis"),
                    ("Volume", score_data.get('volume_score', 0), "📈", "Trading volume patterns"),
                    ("Trend", score_data.get('trend_score', 0), "📉", "Price trend analysis")
                ]
                
                for i, (component, score, emoji, description) in enumerate(components):
                    with breakdown_cols[i]:
                        st.metric(f"{emoji} {component}", f"{score:.0f}/100")
                        
                        # Enhanced color coding
                        if score >= 75:
                            st.success("Very Strong")
                        elif score >= 60:
                            st.info("Strong")
                        elif score >= 40:
                            st.warning("Neutral")
                        else:
                            st.error("Weak")
                        
                        st.caption(description)
                
                # Technical signals display
                technical_signals = score_data.get('technical_signals', [])
                if technical_signals:
                    st.subheader("🔍 Technical Analysis Signals")
                    for signal in technical_signals[:5]:  # Show top 5 signals
                        st.info(f"• {signal}")
                
                # Enhanced recommendation with detailed reasoning
                st.subheader("💡 Investment Recommendation")
                recommendation = score_data.get('recommendation', 'Hold')
                recommendation_reason = score_data.get('recommendation_reason', 'Based on current analysis')
                
                # Enhanced recommendation styling
                if recommendation in ['Strong Buy', 'Buy']:
                    rec_class = "buy-recommendation"
                    rec_emoji = "🟢"
                    action_color = "#059669"
                elif recommendation in ['Strong Sell', 'Sell']:
                    rec_class = "sell-recommendation"
                    rec_emoji = "🔴"
                    action_color = "#dc2626"
                else:
                    rec_class = "hold-recommendation"
                    rec_emoji = "🟡"
                    action_color = "#d97706"
                
                rec_html = f"""
                <div class="recommendation-card {rec_class}">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <h2 style="margin: 0; color: {action_color}; font-size: 1.5rem;">{rec_emoji} {recommendation}</h2>
                        <div style="margin-left: auto; background: rgba(255,255,255,0.8); padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600;">
                            Score: {overall_score:.0f}/100
                        </div>
                    </div>
                    <p style="margin: 0; color: #334155; font-size: 1rem; line-height: 1.5;">
                        {recommendation_reason}
                    </p>
                </div>
                """
                st.markdown(rec_html, unsafe_allow_html=True)
                
                # Risk factors with enhanced display
                risk_factors = score_data.get('risk_factors', [])
                if risk_factors and risk_factors != ['No significant risk factors identified']:
                    st.subheader("⚠️ Risk Assessment")
                    for risk in risk_factors[:5]:  # Show top 5 risks
                        st.warning(f"• {risk}")
                
                # Score breakdown details in expander
                with st.expander("🔧 Advanced Analysis Details", expanded=False):
                    score_breakdown = score_data.get('score_breakdown', {})
                    if score_breakdown:
                        st.write("**Weights Used:**")
                        weights = score_breakdown.get('weights_used', {})
                        for factor, weight in weights.items():
                            st.write(f"• {factor.title()}: {weight:.1%}")
                        
                        st.write("**Confidence Levels:**")
                        conf_levels = score_breakdown.get('confidence_levels', {})
                        for factor, conf in conf_levels.items():
                            st.write(f"• {factor.title()}: {conf:.0f}%")
                
                # Risk disclaimer with enhanced styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-left: 4px solid #d97706; padding: 1rem; border-radius: 8px; margin: 2rem 0;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #92400e;">⚠️ Important Disclaimer</h4>
                    <p style="margin: 0; color: #92400e; font-size: 0.9rem;">
                        This analysis is for educational purposes only and should not be considered as financial advice. 
                        Stock markets are inherently risky and past performance does not guarantee future results. 
                        Always conduct your own research and consult with qualified financial professionals before making investment decisions.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Technical Analysis Section
            if show_technical:
                st.subheader("📊 Advanced Technical Analysis")
                
                # Get technical analysis results
                technical_result = calculate_enhanced_technical_score(stock_data)
                
                # Technical summary
                tech_summary_cols = st.columns(4)
                
                with tech_summary_cols[0]:
                    rsi = technical_result.get('rsi', 50)
                    st.metric(
                        "RSI (14)",
                        f"{rsi:.1f}",
                        delta="Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                    )
                
                with tech_summary_cols[1]:
                    macd_data = technical_result.get('macd', {})
                    macd_signal = "Bullish" if macd_data.get('signal', 0) > 0 else "Bearish"
                    st.metric(
                        "MACD Signal",
                        macd_signal,
                        delta=f"Strength: {macd_data.get('strength', 0):.0f}"
                    )
                
                with tech_summary_cols[2]:
                    bb_data = technical_result.get('bollinger', {})
                    bb_position = bb_data.get('position', 0.5)
                    bb_signal = "Upper" if bb_position > 0.8 else "Lower" if bb_position < 0.2 else "Middle"
                    st.metric(
                        "Bollinger Position",
                        bb_signal,
                        delta=f"{bb_position:.2f}"
                    )
                
                with tech_summary_cols[3]:
                    tech_strength = technical_result.get('strength', 'Unknown')
                    tech_score = technical_result.get('score', 50)
                    st.metric(
                        "Technical Strength",
                        tech_strength,
                        delta=f"Score: {tech_score:.0f}"
                    )
                
                # Enhanced price chart
                price_chart = create_enhanced_price_chart(stock_data, stock_symbol)
                st.plotly_chart(price_chart, use_container_width=True)
                
                # Technical signals in organized format
                tech_signals = technical_result.get('signals', [])
                if tech_signals:
                    st.subheader("📈 Technical Signals Summary")
                    signal_cols = st.columns(2)
                    
                    for i, signal in enumerate(tech_signals):
                        with signal_cols[i % 2]:
                            if "Buy" in signal or "Bullish" in signal or "Uptrend" in signal:
                                st.success(f"✅ {signal}")
                            elif "Sell" in signal or "Bearish" in signal or "Downtrend" in signal:
                                st.error(f"❌ {signal}")
                            else:
                                st.info(f"ℹ️ {signal}")
            
            # Enhanced Sentiment Analysis
            if show_sentiment:
                st.subheader("💭 Advanced Market Sentiment Analysis")
                
                sentiment_data = get_enhanced_news_sentiment(stock_symbol)
                
                if sentiment_data and sentiment_data.get('article_count', 0) > 0:
                    # Enhanced sentiment overview
                    sent_cols = st.columns(4)
                    
                    with sent_cols[0]:
                        overall_sentiment = sentiment_data.get('sentiment_score', 0)
                        sentiment_label = "Positive" if overall_sentiment > 0.1 else "Negative" if overall_sentiment < -0.1 else "Neutral"
                        st.metric(
                            "Overall Sentiment",
                            sentiment_label,
                            delta=f"{overall_sentiment:.3f}"
                        )
                    
                    with sent_cols[1]:
                        article_count = sentiment_data.get('article_count', 0)
                        confidence = sentiment_data.get('confidence', 0)
                        st.metric("News Articles", f"{article_count}")
                        st.caption(f"Confidence: {confidence:.0f}%")
                    
                    with sent_cols[2]:
                        positive_articles = sentiment_data.get('positive_articles', 0)
                        negative_articles = sentiment_data.get('negative_articles', 0)
                        
                        if positive_articles > negative_articles:
                            st.metric("Sentiment Bias", "📈 Positive", delta=f"+{positive_articles}")
                        elif negative_articles > positive_articles:
                            st.metric("Sentiment Bias", "📉 Negative", delta=f"-{negative_articles}")
                        else:
                            st.metric("Sentiment Bias", "➡️ Neutral", delta="0")
                    
                    with sent_cols[3]:
                        source_dist = sentiment_data.get('source_distribution', {})
                        primary_source = max(source_dist.items(), key=lambda x: x[1])[0] if source_dist else "N/A"
                        st.metric("Primary Source", primary_source)
                        st.caption(f"{len(source_dist)} sources")
                    
                    # Sentiment distribution chart
                    if sentiment_data.get('sentiment_trend'):
                        trend_data = sentiment_data['sentiment_trend']
                        
                        sentiment_chart = go.Figure()
                        
                        dates = [item['date'] for item in trend_data]
                        sentiments = [item['sentiment'] for item in trend_data]
                        
                        sentiment_chart.add_trace(
                            go.Scatter(
                                x=dates,
                                y=sentiments,
                                mode='lines+markers',
                                name='Sentiment Trend',
                                line=dict(width=3, color='#2563eb'),
                                marker=dict(size=8),
                                fill='tonexty'
                            )
                        )
                        
                        sentiment_chart.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5)
                        sentiment_chart.add_hline(y=0.1, line_dash="dash", line_color="green", opacity=0.3)
                        sentiment_chart.add_hline(y=-0.1, line_dash="dash", line_color="red", opacity=0.3)
                        
                        sentiment_chart.update_layout(
                            title="News Sentiment Trend Over Time",
                            xaxis_title="Date",
                            yaxis_title="Sentiment Score",
                            template="plotly_white",
                            height=400
                        )
                        
                        st.plotly_chart(sentiment_chart, use_container_width=True)
                    
                    # Enhanced news articles display
                    st.subheader("📰 Recent News Analysis")
                    articles = sentiment_data.get('articles', [])
                    
                    for i, article in enumerate(articles[:8]):  # Show more articles
                        sentiment_score = article.get('sentiment', 0)
                        sentiment_label, sentiment_class = get_sentiment_label(sentiment_score)
                        relevance = article.get('relevance', 0)
                        
                        article_html = f"""
                        <div class="news-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                                <h4 style="margin: 0; color: #0f172a; flex: 1; line-height: 1.3;">{article['title']}</h4>
                                <div style="margin-left: 1rem; flex-shrink: 0; text-align: right;">
                                    <span class="{sentiment_class}">{sentiment_label}</span>
                                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                                        Relevance: {relevance:.1%}
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <span style="color: #64748b; font-size: 0.9rem;">
                                    📅 {article['date'].strftime('%Y-%m-%d %H:%M')}
                                </span>
                                <span style="color: #64748b; font-size: 0.9rem;">
                                    🏢 {article['source']}
                                </span>
                            </div>
                            <p style="margin: 0.5rem 0 0 0; color: #334155; line-height: 1.5;">
                                {article.get('summary', '')[:300]}{'...' if len(article.get('summary', '')) > 300 else ''}
                            </p>
                        </div>
                        """
                        st.markdown(article_html, unsafe_allow_html=True)
                        
                        if i < len(articles) - 1 and i < 7:  # Add separator
                            st.divider()
                    
                else:
                    st.info(f"📰 No recent news found for {stock_symbol}. Sentiment analysis requires recent news articles mentioning the stock.")
                    
                    # Suggest related searches
                    st.subheader("💡 Suggestions")
                    st.write("• Check if the company name or ticker symbol is correct")
                    st.write("• Try searching for a more widely covered stock")
                    st.write("• The company might not be frequently mentioned in financial news")
            
            # Company Information (Enhanced)
            if company_info:
                with st.expander("🏢 Detailed Company Information", expanded=False):
                    company_col1, company_col2 = st.columns(2)
                    
                    with company_col1:
                        st.write("**📊 Financial Metrics**")
                        
                        pe_ratio = company_info.get('trailingPE', 0)
                        if pe_ratio and pe_ratio > 0:
                            st.write(f"• **P/E Ratio:** {pe_ratio:.2f}")
                        
                        beta = company_info.get('beta', 0)
                        if beta and beta > 0:
                            st.write(f"• **Beta:** {beta:.2f}")
                        
                        dividend_yield = company_info.get('dividendYield', 0)
                        if dividend_yield and dividend_yield > 0:
                            st.write(f"• **Dividend Yield:** {dividend_yield * 100:.2f}%")
                        
                        profit_margin = company_info.get('profitMargins', 0)
                        if profit_margin and profit_margin > 0:
                            st.write(f"• **Profit Margin:** {profit_margin * 100:.2f}%")
                        
                        debt_to_equity = company_info.get('debtToEquity', 0)
                        if debt_to_equity and debt_to_equity > 0:
                            st.write(f"• **Debt-to-Equity:** {debt_to_equity:.2f}")
                    
                    with company_col2:
                        st.write("**📈 Performance Metrics**")
                        
                        week_52_high = company_info.get('fiftyTwoWeekHigh', 0)
                        week_52_low = company_info.get('fiftyTwoWeekLow', 0)
                        if week_52_high > 0 and week_52_low > 0:
                            st.write(f"• **52-Week High:** ${week_52_high:.2f}")
                            st.write(f"• **52-Week Low:** ${week_52_low:.2f}")
                        
                        employees = company_info.get('fullTimeEmployees', 0)
                        if employees > 0:
                            st.write(f"• **Employees:** {format_large_number(employees)}")
                        
                        recommendation = company_info.get('recommendationKey', 'N/A')
                        if recommendation != 'N/A':
                            st.write(f"• **Analyst Rating:** {recommendation.title()}")
                        
                        target_price = company_info.get('targetMeanPrice', 0)
                        if target_price > 0:
                            st.write(f"• **Target Price:** ${target_price:.2f}")
                    
                    # Company description with better formatting
                    description = company_info.get('longBusinessSummary', '')
                    if description:
                        st.write("**📋 Company Description**")
                        # Truncate and format description
                        if len(description) > 800:
                            description = description[:800] + "..."
                        st.write(description)
                        
                        # Additional company details
                        website = company_info.get('website', '')
                        if website:
                            st.write(f"**🌐 Website:** [{website}]({website})")
        
        except Exception as e:
            st.error(f"❌ An error occurred while analyzing {stock_symbol}: {str(e)}")
            st.info("💡 **Possible solutions:**\n- Check your internet connection\n- Verify the stock symbol is correct\n- Try again in a few moments\n- Some features may be temporarily unavailable")
    
    else:
        # Enhanced welcome screen
        st.info("👆 Please enter a stock symbol in the sidebar to begin comprehensive analysis.")
        
        # Featured analysis section
        st.subheader("🌟 Featured Analysis Tools")
        
        feature_cols = st.columns(3)
        
        with feature_cols[0]:
            st.markdown("""
            **📊 Technical Analysis**
            - RSI, MACD, Bollinger Bands
            - Moving averages and trend analysis
            - Volume confirmation signals
            - Support and resistance levels
            """)
        
        with feature_cols[1]:
            st.markdown("""
            **💭 Sentiment Analysis**
            - Multi-source news aggregation
            - AI-powered sentiment scoring
            - Relevance-weighted analysis
            - Real-time sentiment trends
            """)
        
        with feature_cols[2]:
            st.markdown("""
            **🎯 Predictive Scoring**
            - Multi-factor algorithm
            - Risk-adjusted recommendations
            - Confidence-weighted results
            - Personalized risk profiles
            """)
        
        # Popular stocks with enhanced display
        st.subheader("💡 Popular Stocks to Analyze")
        
        popular_categories = {
            "🏛️ Blue Chip Stocks": ['AAPL', 'MSFT', 'JNJ', 'WMT'],
            "🚀 Growth Stocks": ['TSLA', 'NVDA', 'AMZN', 'GOOGL'],
            "💰 Financial Sector": ['JPM', 'BAC', 'WFC', 'GS'],
            "🏥 Healthcare": ['PFE', 'UNH', 'ABBV', 'MRK']
        }
        
        for category, stocks in popular_categories.items():
            st.write(f"**{category}**")
            cols = st.columns(len(stocks))
            for i, symbol in enumerate(stocks):
                with cols[i]:
                    if st.button(symbol, key=f"popular_{symbol}_{category}"):
                        st.experimental_set_query_params(symbol=symbol)
                        st.rerun()
        
        # Educational content
        with st.expander("📚 How StockMood Pro Works", expanded=False):
            st.markdown("""
            **Our Analysis Process:**
            
            1. **Data Collection:** We gather real-time stock prices, historical data, and financial news from multiple reliable sources.
            
            2. **Technical Analysis:** Advanced algorithms calculate key indicators like RSI, MACD, and Bollinger Bands to identify trends and signals.
            
            3. **Sentiment Analysis:** AI-powered natural language processing analyzes news sentiment to gauge market mood.
            
            4. **Multi-Factor Scoring:** Our proprietary algorithm combines technical, sentiment, volume, and trend factors into a single predictive score.
            
            5. **Risk Assessment:** Personalized recommendations based on your risk tolerance and current market conditions.
            
            **Key Features:**
            - ✅ Real-time data from Yahoo Finance
            - ✅ Multi-source news sentiment analysis
            - ✅ Advanced technical indicators
            - ✅ Risk-adjusted scoring
            - ✅ Professional-grade visualizations
            - ✅ Beginner-friendly insights
            """)

if __name__ == "__main__":
    main()
