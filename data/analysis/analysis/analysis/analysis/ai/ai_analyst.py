import openai

def ai_stock_summary(symbol, score, sentiment):

    prompt = f"""

You are a professional equity analyst.

Analyze stock {symbol}.

Investment score: {score}/100
News sentiment: {sentiment}

Explain:

1. strengths
2. weaknesses
3. short term outlook
4. long term outlook

"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content
