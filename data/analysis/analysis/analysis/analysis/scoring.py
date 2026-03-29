def investment_score(fund, rsi, sentiment):

    score = 0

    # fundamentals 40 pts
    if fund["profit_margin"] > .2:
        score += 10

    if fund["roe"] > .15:
        score += 10

    if fund["revenue_growth"] > .1:
        score += 10

    if fund["debt_equity"] < 50:
        score += 10

    # valuation 20 pts
    pe = fund["pe"]

    if 10 <= pe <= 25:
        score += 20
    elif pe < 40:
        score += 10

    # technicals 20 pts
    if 40 <= rsi <= 60:
        score += 20
    elif 30 <= rsi <= 70:
        score += 10

    # sentiment 20 pts
    score += int((sentiment + 1) * 10)

    return max(0, min(score,100))
