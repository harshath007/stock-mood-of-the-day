import plotly.graph_objects as go

def price_chart(df):

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"]
        )
    )

    fig.update_layout(
        height=500,
        template="plotly_dark"
    )

    return fig
