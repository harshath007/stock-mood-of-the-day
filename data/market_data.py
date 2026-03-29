import yfinance as yf
import requests
import streamlit as st
from config import FINNHUB_API_KEY, FINNHUB_URL

@st.cache_data(ttl=60)
def get_quote(symbol):

    url = f"{FINNHUB_URL}/quote"

    params = {
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    }

    r = requests.get(url, params=params)
    data = r.json()

    return {
        "price": data["c"],
        "change": data["d"],
        "percent": data["dp"]
    }


@st.cache_data(ttl=300)
def get_price_history(symbol):

    ticker = yf.Ticker(symbol)

    return ticker.history(period="3mo")
