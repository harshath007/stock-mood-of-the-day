import yfinance as yf
import streamlit as st

@st.cache_data
def get_stock_data(ticker):
    return yf.download(ticker, period="3mo", interval="1d")
