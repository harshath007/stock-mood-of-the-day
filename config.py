import os

FINNHUB_API_KEY = os.getenv("d1modnpr01qlvnp3nvbgd1modnpr01qlvnp3nvc0")

if not FINNHUB_API_KEY:
    raise ValueError("Missing FINNHUB_API_KEY environment variable")

FINNHUB_URL = "https://finnhub.io/api/v1"

POPULAR_STOCKS = [
"AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA",
"AMD","NFLX","CRM","INTC","ADBE"
]
