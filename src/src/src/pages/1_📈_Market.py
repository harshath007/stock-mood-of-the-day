import streamlit as st
from src.data import get_stock_data
from src.charts import price_chart

st.title("Market Dashboard")

ticker = st.text_input("Enter ticker", "AAPL")

if st.button("Analyze"):
    try:
        df = get_stock_data(ticker)
        fig = price_chart(df, ticker)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")
