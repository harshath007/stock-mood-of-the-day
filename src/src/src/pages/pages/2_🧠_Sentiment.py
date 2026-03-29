import streamlit as st
from src.sentiment import get_sentiment

st.title("Sentiment Analysis")

text = st.text_area("Paste news or text")

if st.button("Analyze Sentiment"):
    score = get_sentiment(text)

    if score > 0:
        st.success(f"Bullish ({score})")
    elif score < 0:
        st.error(f"Bearish ({score})")
    else:
        st.warning("Neutral")
