import yfinance as yf
import streamlit as st

@st.cache_data(ttl=600)
def get_fundamentals(symbol):

    ticker = yf.Ticker(symbol)
    info = ticker.get_info()

    return {
        "market_cap": info.get("marketCap",0),
        "pe": info.get("trailingPE",0),
        "roe": info.get("returnOnEquity",0),
        "profit_margin": info.get("profitMargins",0),
        "revenue_growth": info.get("revenueGrowth",0),
        "debt_equity": info.get("debtToEquity",0)
    }
