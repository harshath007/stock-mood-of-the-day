import streamlit as st

# Load CSS
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="StockMood", layout="wide")
load_css()

# Hero section
st.markdown("""
# StockMood
### Institutional-grade sentiment & market intelligence
""")

st.divider()

col1, col2, col3 = st.columns(3)

col1.metric("S&P 500", "+1.2%")
col2.metric("NASDAQ", "+0.8%")
col3.metric("Market Sentiment", "Bullish")

st.markdown("Use the sidebar to explore analytics.")
if __name__ == "__main__":
    main()
