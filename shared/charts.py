from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import seller_label


NAVY = "#16324F"
BLUE = "#2F6BFF"
TEAL = "#12A594"
RED = "#D9534F"
ORANGE = "#E58A2B"
GREY = "#8A97A6"
GRID = "#E8EDF3"


def _finish(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=54, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial, Microsoft YaHei, sans-serif", color=NAVY, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def overview_trend(monthly: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        x=monthly["month"], y=monthly["gmv"], name="GMV", marker_color=BLUE,
        hovertemplate="%{x}<br>GMV：%{y:,.0f} BRL<extra></extra>",
    )
    fig.add_scatter(
        x=monthly["month"], y=monthly["orders"], name="订单量", mode="lines+markers",
        line=dict(color=TEAL, width=3), marker=dict(size=7), secondary_y=True,
        hovertemplate="%{x}<br>订单量：%{y:,.0f}<extra></extra>",
    )
    fig.update_layout(title="经营规模如何随时间变化？")
    fig.update_yaxes(title_text="GMV（BRL）", secondary_y=False)
    fig.update_yaxes(title_text="订单量", secondary_y=True, showgrid=False)
    return _finish(fig, 380)


def contribution_bar(data: pd.DataFrame, dimension: str, title: str) -> go.Figure:
    shown = data.sort_values("gmv", ascending=True).copy()
    if dimension == "seller_id":
        shown["label"] = shown[dimension].map(seller_label)
    else:
        shown["label"] = shown[dimension].str.replace("_", " ").str.title()
    fig = px.bar(
        shown,
        x="gmv",
        y="label",
        orientation="h",
        text=shown["gmv_share"].map(lambda value: f"{value:.1%}"),
        color_discrete_sequence=[BLUE],
    )
    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>GMV：%{x:,.0f} BRL<extra></extra>")
    fig.update_layout(title=title, xaxis_title="GMV（BRL）", yaxis_title=None, showlegend=False)
    return _finish(fig, 380)


def negative_merchants(data: pd.DataFrame, limit: int = 10) -> go.Figure:
    shown = data.nsmallest(limit, "gmv_change").sort_values("gmv_change", ascending=False).copy()
    shown["label"] = shown["seller_id"].map(seller_label)
    colors = [RED if value < 0 else TEAL for value in shown["gmv_change"]]
    fig = go.Figure(
        go.Bar(
            x=shown["gmv_change"], y=shown["label"], orientation="h", marker_color=colors,
            text=shown["gmv_change"].map(lambda value: f"{value:.1%}"), textposition="outside",
            hovertemplate="%{y}<br>首尾月GMV变化：%{x:.1%}<extra></extra>",
        )
    )
    fig.update_layout(title="哪些商家需要优先关注？", xaxis_title="首尾月GMV变化", yaxis_title=None, showlegend=False)
    fig.update_xaxes(tickformat=".0%")
    return _finish(fig, 380)


def diagnostic_trend(monthly: pd.DataFrame) -> go.Figure:
    indexed = monthly.copy()
    for metric in ["gmv", "orders", "aov"]:
        first = indexed[metric].iloc[0]
        indexed[f"{metric}_index"] = indexed[metric] / first * 100 if first else 0
    fig = go.Figure()
    for metric, label, color in [
        ("gmv_index", "GMV指数", BLUE),
        ("orders_index", "订单量指数", TEAL),
        ("aov_index", "客单价指数", ORANGE),
    ]:
        fig.add_scatter(
            x=indexed["month"], y=indexed[metric], mode="lines+markers", name=label,
            line=dict(color=color, width=3), marker=dict(size=7),
            hovertemplate="%{x}<br>指数：%{y:.1f}<extra></extra>",
        )
    fig.add_hline(y=100, line_dash="dot", line_color=GREY)
    fig.update_layout(title="下滑从何时开始，订单量与客单价是否同步？", yaxis_title="首月=100", xaxis_title=None)
    return _finish(fig, 360)


def peer_distribution(peer: dict, target_seller: str) -> go.Figure:
    peers = peer["peers"].sort_values("gmv_change").reset_index(drop=True).copy()
    peers["position"] = range(1, len(peers) + 1)
    peers["is_target"] = peers["seller_id"].eq(target_seller)
    fig = go.Figure()
    fig.add_scatter(
        x=peers.loc[~peers["is_target"], "gmv_change"],
        y=peers.loc[~peers["is_target"], "position"],
        mode="markers", name="同类商家", marker=dict(color="#AAB5C2", size=9),
        hovertemplate="GMV变化：%{x:.1%}<extra></extra>",
    )
    target = peers.loc[peers["is_target"]]
    if not target.empty:
        fig.add_scatter(
            x=target["gmv_change"], y=target["position"], mode="markers+text", name=seller_label(target_seller),
            marker=dict(color=RED, size=15), text=[seller_label(target_seller)], textposition="middle right",
            hovertemplate="目标商家<br>GMV变化：%{x:.1%}<extra></extra>",
        )
    if peer.get("median") is not None:
        fig.add_vline(x=peer["median"], line_dash="dash", line_color=BLUE, annotation_text=f"同类中位数 {peer['median']:.1%}")
    fig.add_vline(x=0, line_color=GREY)
    fig.update_layout(title="目标商家是否显著弱于同类？", xaxis_title="首尾月GMV变化", yaxis_title="同类商家（按变化排序）")
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(showticklabels=False)
    return _finish(fig, 360)


def driver_waterfall(driver: pd.DataFrame, delta_gmv: float) -> go.Figure:
    fig = go.Figure(
        go.Waterfall(
            x=driver["driver"].tolist() + ["GMV净变化"],
            y=driver["effect"].tolist() + [delta_gmv],
            measure=["relative", "relative", "total"],
            connector={"line": {"color": GRID}},
            increasing={"marker": {"color": TEAL}},
            decreasing={"marker": {"color": RED}},
            totals={"marker": {"color": NAVY}},
            text=[f"{value:,.0f}" for value in driver["effect"]] + [f"{delta_gmv:,.0f}"],
            textposition="outside",
            hovertemplate="%{x}<br>影响：%{y:,.0f} BRL<extra></extra>",
        )
    )
    fig.update_layout(title="GMV变化主要由订单量还是客单价驱动？", yaxis_title="GMV影响（BRL）", showlegend=False)
    return _finish(fig, 360)


def sku_migration_chart(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=data["sku_group"], y=data["base_gmv"], name="首月GMV", marker_color=GREY)
    fig.add_bar(x=data["sku_group"], y=data["end_gmv"], name="末月GMV", marker_color=BLUE)
    fig.update_layout(title="哪些SKU成交结构变化值得优先核查？", barmode="group", yaxis_title="GMV（BRL）", xaxis_title=None)
    return _finish(fig, 360)


def price_mix_chart(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=data["period"], y=data["item_price_median"], name="成交价格中位数", marker_color=ORANGE)
    fig.add_bar(x=data["period"], y=data["active_sku_price_median"], name="成交SKU中位价", marker_color=TEAL)
    fig.update_layout(title="客单价变化是否伴随成交价格组合变化？", barmode="group", yaxis_title="价格（BRL）", xaxis_title=None)
    return _finish(fig, 360)
