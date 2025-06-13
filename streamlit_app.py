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
import warnings
warnings.filterwarnings('ignore')

# ---------- Configuration & Setup -----------
st.set_page_config(
    page_title="StockMood Pro - Smart Stock Analysis", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Initialize sentiment analyzer
@st.cache_resource
def get_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

analyzer = get_sentiment_analyzer()

# Clean, Professional CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #000000 !important;
    }
    
    .main {
        padding: 1rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
        color: #000000 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ensure all text is black and visible */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stMetric, [data-testid="metric-container"] {
        color: #000000 !important;
    }
    
    .stApp *, .stMetric *, [data-testid="metric-container"] * {
        color: #000000 !important;
    }
    
    .score-display {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white !important;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        animation: pulse 2s infinite;
    }
    
    .score-display * {
        color: white !important;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .score-number {
        font-size: 4rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        line-height: 1;
        color: white !important;
    }
    
    .score-label {
        font-size: 1.2rem;
        font-weight: 600;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: white !important;
    }
    
    .recommendation-card {
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        animation: fadeIn 0.6s ease-out;
    }
    
    .recommendation-card h3, .recommendation-card p {
        color: #000000 !important;
    }
    
    .buy-recommendation {
        background: linear-gradient(145deg, #d1fae5, #a7f3d0);
        border-left: 4px solid #059669;
    }
    
    .sell-recommendation {
        background: linear-gradient(145deg, #fee2e2, #fecaca);
        border-left: 4px solid #dc2626;
    }
    
    .hold-recommendation {
        background: linear-gradient(145deg, #fef3c7, #fde68a);
        border-left: 4px solid #d97706;
    }
    
    .stock-emoji {
        font-size: 3rem;
        margin-right: 1rem;
        vertical-align: middle;
    }
    
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
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
    
    .simplified-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        animation: fadeIn 0.6s ease-out;
    }
    
    .simplified-card h4, .simplified-card p {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helper Functions -----------

def get_stock_emoji(change_percent: float, overall_score: float = 50) -> str:
    """Get emoji based on stock performance."""
    if change_percent > 5:
        return "🚀"  # Rocket for big gains
    elif change_percent > 2:
        return "📈"  # Chart up for good gains
    elif change_percent > 0:
        return "💚"  # Green heart for small gains
    elif change_percent > -2:
        return "😐"  # Neutral face for small losses
    elif change_percent > -5:
        return "📉"  # Chart down for moderate losses
    else:
        return "💥"  # Explosion for big losses

def format_large_number(number: float) -> str:
    """Format large numbers simply."""
    try:
        if number >= 1e12:
            return f"${number/1e12:.1f}T"
        elif number >= 1e9:
            return f"${number/1e9:.1f}B"
        elif number >= 1e6:
            return f"${number/1e6:.1f}M"
        elif number >= 1e3:
            return f"${number/1e3:.0f}K"
        else:
            return f"${number:.0f}"
    except:
        return "N/A"

# ---------- Data Functions -----------

@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = '1y') -> pd.DataFrame:
    """Fetch stock data for a given symbol and period."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        
        if data.empty:
            return None
        
        data = data.dropna()
        data.index = pd.to_datetime(data.index)
        return data
        
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_company_info(symbol: str) -> dict:
    """Get simplified company information."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        company_data = {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', 'USD'),
        }
        
        return company_data
        
    except Exception as e:
        return {
            'name': symbol,
            'sector': 'N/A',
            'market_cap': 0,
            'currency': 'USD',
        }

# ---------- Analysis Functions -----------

def calculate_rsi(data: pd.DataFrame, window: int = 14) -> float:
    """Calculate RSI."""
    try:
        if len(data) < window + 1:
            return 50
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        
    except:
        return 50

def calculate_simple_score(stock_data: pd.DataFrame, sentiment_score: float = 0) -> dict:
    """Calculate a simplified investment score."""
    try:
        if stock_data is None or stock_data.empty:
            return {
                'overall_score': 50,
                'recommendation': 'Hold',
                'reason': 'Insufficient data'
            }
        
        # Simple scoring based on recent performance and RSI
        recent_returns = stock_data['Close'].pct_change().tail(10).mean()
        rsi = calculate_rsi(stock_data)
        
        # Base score from price momentum
        score = 50 + (recent_returns * 1000)  # Convert to percentage points
        
        # Adjust for RSI (avoid overbought/oversold)
        if 30 <= rsi <= 70:
            score += 10
        elif rsi < 30:
            score += 5  # Oversold might be good entry
        else:
            score -= 10  # Overbought is risky
        
        # Add sentiment influence
        score += sentiment_score * 20
        
        # Clamp between 0 and 100
        score = min(100, max(0, score))
        
        # Generate recommendation
        if score >= 70:
            recommendation = "Buy"
            reason = "Strong positive signals"
        elif score <= 40:
            recommendation = "Sell"
            reason = "Weak performance signals"
        else:
            recommendation = "Hold"
            reason = "Mixed signals, stay cautious"
        
        return {
            'overall_score': score,
            'recommendation': recommendation,
            'reason': reason
        }
        
    except:
        return {
            'overall_score': 50,
            'recommendation': 'Hold',
            'reason': 'Analysis error'
        }

@st.cache_data(ttl=900)
def get_simple_sentiment(symbol: str) -> dict:
    """Get simplified sentiment analysis."""
    try:
        # Try to get news from Yahoo Finance
        news_sources = [
            'https://feeds.finance.yahoo.com/rss/2.0/headline'
        ]
        
        articles = []
        for source_url in news_sources:
            try:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:10]:
                    title = entry.get('title', '')
                    if symbol.upper() in title.upper():
                        articles.append(title)
                time.sleep(0.1)
            except:
                continue
        
        if not articles:
            return {'sentiment_score': 0, 'article_count': 0}
        
        # Analyze sentiment
        sentiments = []
        for article in articles:
            sentiment = analyzer.polarity_scores(article)
            sentiments.append(sentiment['compound'])
        
        avg_sentiment = np.mean(sentiments) if sentiments else 0
        
        return {
            'sentiment_score': avg_sentiment,
            'article_count': len(articles)
        }
        
    except:
        return {'sentiment_score': 0, 'article_count': 0}

def create_simple_chart(stock_data: pd.DataFrame, symbol: str) -> go.Figure:
    """Create a clean, simple price chart."""
    try:
        if stock_data is None or stock_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            return fig
        
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name="Price",
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444'
            )
        )
        
        # Add simple moving average
        if len(stock_data) >= 20:
            sma_20 = stock_data['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=stock_data.index,
                    y=sma_20,
                    name="20-day Average",
                    line=dict(color="blue", width=2),
                    opacity=0.7
                )
            )
        
        fig.update_layout(
            title=f"{symbol} Price Chart",
            xaxis_rangeslider_visible=False,
            height=500,
            template="plotly_white",
            showlegend=True,
            font=dict(color='black')
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        return fig

# ---------- Main Application -----------

def main():
    """Simplified main application."""
    
    # Initialize session state
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = 'AAPL'
    
    # Header
    st.title("📊 StockMood ")
    st.markdown("**Smart Stock Analysis Made Simple**")
    st.markdown("*Get clear insights without the complexity*")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Analyze a Stock")
        
        stock_symbol = st.text_input(
            "Stock Symbol", 
            value=st.session_state.selected_stock,
            placeholder="e.g., AAPL, TSLA, MSFT"
        ).upper()
        
        timeframe = st.selectbox(
            "Time Period",
            options=['1mo', '3mo', '6mo', '1y'],
            index=3
        )
        
        if stock_symbol != st.session_state.selected_stock:
            st.session_state.selected_stock = stock_symbol
            st.rerun()
        
        st.markdown("---")
        st.markdown("**💡 Quick Picks**")
        popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA']
        
        for symbol in popular_stocks:
            if st.button(symbol, key=f"quick_{symbol}"):
                st.session_state.selected_stock = symbol
                st.rerun()
    
    if stock_symbol:
        try:
            # Load data
            with st.spinner(f"Analyzing {stock_symbol}..."):
                stock_data = get_stock_data(stock_symbol, timeframe)
                
                if stock_data is None or stock_data.empty:
                    st.error(f"❌ No data found for '{stock_symbol}'. Please check the symbol.")
                    return
            
            company_info = get_company_info(stock_symbol)
            
            # Calculate performance
            if len(stock_data) >= 2:
                current_price = stock_data['Close'].iloc[-1]
                previous_close = stock_data['Close'].iloc[-2]
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                
                # Get stock emoji
                stock_emoji = get_stock_emoji(change_percent)
                
                # Display header with emoji
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f'<div class="stock-emoji">{stock_emoji}</div>', unsafe_allow_html=True)
                
                with col2:
                    company_name = company_info.get('name', stock_symbol)
                    st.title(f"{company_name}")
                    st.caption(f"**{stock_symbol}** • {company_info.get('sector', 'N/A')}")
                
                # Key metrics - simplified
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    currency = company_info.get('currency', 'USD')
                    st.metric(
                        "Current Price",
                        f"{currency} {current_price:.2f}",
                        delta=f"{change:+.2f} ({change_percent:+.2f}%)"
                    )
                
                with col2:
                    day_high = stock_data['High'].iloc[-1]
                    day_low = stock_data['Low'].iloc[-1]
                    st.metric("Today's Range", f"{day_low:.2f} - {day_high:.2f}")
                
                with col3:
                    market_cap = company_info.get('market_cap', 0)
                    if market_cap > 0:
                        st.metric("Market Cap", format_large_number(market_cap))
                    else:
                        st.metric("Market Cap", "N/A")
                
                with col4:
                    volume = stock_data['Volume'].iloc[-1]
                    volume_formatted = f"{volume/1e6:.1f}M" if volume > 1e6 else f"{volume/1e3:.0f}K"
                    st.metric("Volume", volume_formatted)
                
                # Get sentiment and calculate score
                sentiment_data = get_simple_sentiment(stock_symbol)
                score_data = calculate_simple_score(stock_data, sentiment_data.get('sentiment_score', 0))
                
                # Investment Score Display
                st.subheader("🎯 Investment Score")
                
                overall_score = score_data.get('overall_score', 50)
                
                st.markdown(f"""
                <div class="score-display">
                    <div class="score-number">{overall_score:.0f}</div>
                    <div class="score-label">out of 100</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Recommendation
                recommendation = score_data.get('recommendation', 'Hold')
                reason = score_data.get('reason', 'Based on current analysis')
                
                if recommendation == 'Buy':
                    rec_class = "buy-recommendation"
                    rec_emoji = "🟢"
                elif recommendation == 'Sell':
                    rec_class = "sell-recommendation"
                    rec_emoji = "🔴"
                else:
                    rec_class = "hold-recommendation"
                    rec_emoji = "🟡"
                
                rec_html = f"""
                <div class="recommendation-card {rec_class}">
                    <h3 style="margin: 0; color: #000000;">{rec_emoji} {recommendation}</h3>
                    <p style="margin: 0.5rem 0 0 0; color: #000000;">{reason}</p>
                </div>
                """
                st.markdown(rec_html, unsafe_allow_html=True)
                
                # Score interpretation
                col1, col2 = st.columns(2)
                
                with col1:
                    if overall_score >= 70:
                        st.success("**Strong Score** - Positive outlook with good fundamentals")
                    elif overall_score >= 50:
                        st.info("**Neutral Score** - Mixed signals, proceed with caution")
                    else:
                        st.warning("**Weak Score** - Multiple negative indicators present")
                
                with col2:
                    sentiment_score = sentiment_data.get('sentiment_score', 0)
                    article_count = sentiment_data.get('article_count', 0)
                    
                    if sentiment_score > 0.1:
                        sentiment_label = "Positive News"
                        sentiment_color = "success"
                    elif sentiment_score < -0.1:
                        sentiment_label = "Negative News"
                        sentiment_color = "error"
                    else:
                        sentiment_label = "Neutral News"
                        sentiment_color = "info"
                    
                    if article_count > 0:
                        getattr(st, sentiment_color)(f"**{sentiment_label}** - {article_count} recent articles")
                    else:
                        st.info("**No Recent News** - Limited news coverage")
                
                # Price Chart
                st.subheader("📊 Price Chart")
                
                price_chart = create_simple_chart(stock_data, stock_symbol)
                st.plotly_chart(price_chart, use_container_width=True)
                
                # Simple analysis insights
                st.subheader("💡 Quick Insights")
                
                insights = []
                
                # Price trend insight
                if change_percent > 2:
                    insights.append("✅ Strong upward momentum today")
                elif change_percent < -2:
                    insights.append("⚠️ Significant decline today")
                else:
                    insights.append("➡️ Stable price movement today")
                
                # RSI insight
                rsi = calculate_rsi(stock_data)
                if rsi > 70:
                    insights.append("🔴 May be overbought - consider waiting")
                elif rsi < 30:
                    insights.append("🟢 May be oversold - potential opportunity")
                else:
                    insights.append("🟡 Technical indicators are balanced")
                
                # Volume insight
                if len(stock_data) >= 20:
                    avg_volume = stock_data['Volume'].tail(20).mean()
                    current_volume = stock_data['Volume'].iloc[-1]
                    if current_volume > avg_volume * 1.5:
                        insights.append("📈 High trading volume - increased interest")
                    elif current_volume < avg_volume * 0.5:
                        insights.append("📉 Low trading volume - reduced interest")
                
                for insight in insights:
                    st.markdown(f"• {insight}")
                
                # Disclaimer
                st.warning("⚠️ **Important:** This analysis is for educational purposes only. Always do your own research and consider consulting with financial professionals before making investment decisions.")
        
        except Exception as e:
            st.error(f"❌ An error occurred while analyzing {stock_symbol}: {str(e)}")
            st.info("💡 Please check your internet connection and try again.")
    
    else:
        st.info("👆 Enter a stock symbol in the sidebar to begin analysis")
        
        st.subheader("🌟 Popular Stocks")
        popular_with_emojis = [
            ("AAPL", "🍎"), ("MSFT", "💻"), ("GOOGL", "🔍"), 
            ("TSLA", "⚡"), ("AMZN", "📦"), ("NVDA", "🎮")
        ]
        
        cols = st.columns(3)
        for i, (symbol, emoji) in enumerate(popular_with_emojis):
            with cols[i % 3]:
                if st.button(f"{emoji} {symbol}", key=f"main_{symbol}"):
                    st.session_state.selected_stock = symbol
                    st.rerun()

if __name__ == "__main__":
    main()
