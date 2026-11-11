"""Brand-aligned Plotly views, using only measured and explicitly modelled values."""
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from wealthrank.analytics import PERIODS

INK = "#000000"
IVORY = "#FEFFFA"
ORANGE = "#D23A00"
GRID = "rgba(254,255,250,0.10)"
MUTED = "rgba(254,255,250,0.55)"


def style_chart(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=24, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=IVORY, size=12),
        hoverlabel=dict(bgcolor="#211813", font_color=IVORY, font_size=12,
                        bordercolor="rgba(210,58,0,0.5)"),
        hovermode="x unified", showlegend=True,
        legend=dict(orientation="h", y=1.09, x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont=dict(color=MUTED)),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED)),
        transition=dict(duration=420, easing="cubic-in-out"),
    )
    return fig


def allocation_donut(table: pd.DataFrame, by: str = "Asset") -> go.Figure:
    values = table.groupby(by, dropna=False)["Value"].sum().sort_values(ascending=False)
    palette = [ORANGE, "#FEFFFA", "#B98A76", "#7C6461", "#66463B",
               "#3C322F", "#B24A24", "#8D8D8D", "#7E260D", "#DCA890"]
    fig = go.Figure(go.Pie(
        labels=values.index.tolist(), values=values.values, hole=.71,
        sort=False, marker=dict(colors=palette[:len(values)], line=dict(color=INK, width=3)),
        textinfo="none",
        hovertemplate="%{label}<br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=360, margin=dict(l=0, r=0, t=12, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=IVORY), showlegend=True,
        legend=dict(orientation="h", y=-.12, x=.02, font=dict(size=11)),
        annotations=[dict(text="ALLOCATION", x=.5, y=.52, showarrow=False,
                          font=dict(size=12, color=MUTED))],
    )
    return fig


def performance_chart(asset: dict, period: str) -> go.Figure:
    close = asset["close"]
    if period not in PERIODS:
        raise ValueError("Unsupported chart period.")
    cutoff = close.index[-1] - pd.Timedelta(days=PERIODS[period])
    data = close.loc[close.index >= cutoff]
    if len(data) < 2:
        raise ValueError(f"Not enough observed values for {period}.")
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=data.index, y=data.values, mode="lines", name="Price / NAV",
        line=dict(color=ORANGE, width=3),
        fill="tozeroy", fillcolor="rgba(210,58,0,0.12)",
        hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
    ))
    style_chart(figure, 365)
    figure.update_layout(showlegend=False)
    symbol = "₹" if asset["currency"] == "INR" else "$"
    figure.update_yaxes(tickprefix=symbol, tickformat=",.0f")
    return figure


def fire_projection_chart(projection: pd.DataFrame, retirement_age: int | None = None) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=projection["Age"], y=projection["Net worth"] / 100000,
        name="Projected net worth", mode="lines",
        line=dict(color=ORANGE, width=3),
        fill="tozeroy", fillcolor="rgba(210,58,0,0.14)",
        hovertemplate="Age %{x}<br>₹%{y:,.1f} lakh<extra></extra>",
    ))
    figure.add_trace(go.Scatter(
        x=projection["Age"], y=projection["Today's rupees"] / 100000,
        name="Today's purchasing power", mode="lines",
        line=dict(color=IVORY, width=2, dash="dot"),
        hovertemplate="Age %{x}<br>₹%{y:,.1f} lakh<extra></extra>",
    ))
    figure.add_trace(go.Scatter(
        x=projection["Age"], y=projection["FIRE target"] / 100000,
        name="Inflation-adjusted FIRE target", mode="lines",
        line=dict(color="#E49474", width=2, dash="dash"),
        hovertemplate="Age %{x}<br>₹%{y:,.1f} lakh<extra></extra>",
    ))
    style_chart(figure, 440)
    figure.update_yaxes(title_text="₹ lakh")
    figure.update_xaxes(title_text="Age", dtick=5)
    if retirement_age is not None:
        figure.add_vline(x=retirement_age, line_color="rgba(254,255,250,0.24)",
                         line_dash="dot")
    return figure


def comparison_chart(projection_a: pd.DataFrame, projection_b: pd.DataFrame,
                     label_a: str, label_b: str) -> go.Figure:
    figure = go.Figure()
    for projection, label, color, dash in (
        (projection_a, label_a, IVORY, "dash"),
        (projection_b, label_b, ORANGE, "solid"),
    ):
        figure.add_trace(go.Scatter(
            x=projection["Age"], y=projection["Net worth"] / 100000,
            mode="lines", name=label, line=dict(color=color, width=3, dash=dash),
            hovertemplate="Age %{x}<br>₹%{y:,.1f} lakh<extra></extra>",
        ))
    return style_chart(figure, 300)


def evaluation_chart(scores: dict) -> go.Figure:
    figure = go.Figure(go.Bar(
        x=list(scores), y=[100 * value for value in scores.values()],
        marker=dict(color=[ORANGE if name == "Hybrid" else "#82706A" for name in scores]),
        text=[f"{v:.1%}" for v in scores.values()], textposition="outside",
        textfont=dict(color=IVORY),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    style_chart(figure, 310)
    figure.update_layout(showlegend=False, bargap=.45)
    figure.update_yaxes(title_text="NDCG@5 (%)", range=[0, 115])
    return figure
