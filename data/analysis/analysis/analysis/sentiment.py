from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

analyzer = SentimentIntensityAnalyzer()

def sentiment_score(news):

    score = 0
    weight_sum = 0

    for article in news:

        days_old = (datetime.now() - article["datetime"]).days

        weight = 1 / (1 + days_old)

        s = analyzer.polarity_scores(article["headline"])["compound"]

        score += s * weight
        weight_sum += weight

    if weight_sum == 0:
        return 0

    return score / weight_sum
