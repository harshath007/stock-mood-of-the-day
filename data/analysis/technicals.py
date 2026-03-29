import pandas as pd

def calculate_rsi(prices, period=14):

    delta = prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(prices):

    ema12 = prices.ewm(span=12).mean()
    ema26 = prices.ewm(span=26).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()

    return macd, signal


def moving_averages(prices):

    ma50 = prices.rolling(50).mean()
    ma200 = prices.rolling(200).mean()

    return ma50, ma200
