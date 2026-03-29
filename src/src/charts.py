import plotly.graph_objects as go

def price_chart(df, ticker):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode='lines',
        name=ticker
    ))

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0),
        height=500
    )

    return fig
