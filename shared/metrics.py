from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

import numpy as np
import pandas as pd


ALL_CATEGORIES = "全部品类"
ALL_SELLERS = "全部商家"


@dataclass(frozen=True)
class KpiResult:
    gmv: float
    orders: int
    aov: float
    active_sellers: int


def _timestamp(value: str | date | datetime | pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def filter_fact(
    fact: pd.DataFrame,
    start_date: str | date | datetime | pd.Timestamp,
    end_date: str | date | datetime | pd.Timestamp,
    seller_ids: Iterable[str] | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """Apply every user-controlled filter to the same fact table."""
    start = _timestamp(start_date)
    end = _timestamp(end_date)
    if start > end:
        return fact.iloc[0:0].copy()
    mask = fact["purchase_date"].between(start, end, inclusive="both")
    if seller_ids:
        selected = list(seller_ids)
        mask &= fact["seller_id"].isin(selected)
    if category and category != ALL_CATEGORIES:
        mask &= fact["category"].eq(category)
    return fact.loc[mask].copy()


def previous_period(
    start_date: str | date | datetime | pd.Timestamp,
    end_date: str | date | datetime | pd.Timestamp,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = _timestamp(start_date)
    end = _timestamp(end_date)
    duration = end - start
    previous_end = start - timedelta(days=1)
    return previous_end - duration, previous_end


def summarize_kpis(frame: pd.DataFrame) -> KpiResult:
    if frame.empty:
        return KpiResult(0.0, 0, 0.0, 0)
    gmv = float(frame["price"].sum())
    orders = int(frame["order_id"].nunique())
    return KpiResult(
        gmv=gmv,
        orders=orders,
        aov=gmv / orders if orders else 0.0,
        active_sellers=int(frame["seller_id"].nunique()),
    )


def safe_change(current: float, baseline: float) -> float | None:
    if baseline == 0 or pd.isna(baseline):
        return None
    return float(current / baseline - 1)


def monthly_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["month", "gmv", "orders", "aov", "active_sellers"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    result = (
        frame.groupby("month", observed=True)
        .agg(
            gmv=("price", "sum"),
            orders=("order_id", "nunique"),
            active_sellers=("seller_id", "nunique"),
        )
        .reset_index()
        .sort_values("month")
    )
    result["aov"] = result["gmv"] / result["orders"]
    return result[columns]


def contribution(frame: pd.DataFrame, dimension: str, limit: int = 10) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=[dimension, "gmv", "gmv_share", "orders"])
    result = (
        frame.groupby(dimension, observed=True)
        .agg(gmv=("price", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("gmv", ascending=False)
    )
    total = result["gmv"].sum()
    result["gmv_share"] = result["gmv"] / total if total else 0.0
    return result.head(limit).reset_index(drop=True)


def boundary_months(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    if frame.empty:
        return None, None
    months = sorted(frame["month"].dropna().unique())
    if len(months) < 2:
        return months[0], None
    return months[0], months[-1]


def boundary_metrics(frame: pd.DataFrame) -> dict:
    first_month, last_month = boundary_months(frame)
    empty = {
        "first_month": first_month,
        "last_month": last_month,
        "base": KpiResult(0.0, 0, 0.0, 0),
        "end": KpiResult(0.0, 0, 0.0, 0),
        "gmv_change": None,
        "orders_change": None,
        "aov_change": None,
    }
    if not first_month or not last_month:
        return empty
    base = summarize_kpis(frame.loc[frame["month"].eq(first_month)])
    end = summarize_kpis(frame.loc[frame["month"].eq(last_month)])
    return {
        "first_month": first_month,
        "last_month": last_month,
        "base": base,
        "end": end,
        "gmv_change": safe_change(end.gmv, base.gmv),
        "orders_change": safe_change(end.orders, base.orders),
        "aov_change": safe_change(end.aov, base.aov),
    }


def merchant_change_table(frame: pd.DataFrame, minimum_orders: int = 5) -> pd.DataFrame:
    first_month, last_month = boundary_months(frame)
    output_columns = [
        "seller_id",
        "orders_base",
        "orders_end",
        "gmv_base",
        "gmv_end",
        "gmv_change",
    ]
    if not first_month or not last_month:
        return pd.DataFrame(columns=output_columns)
    grouped = (
        frame.loc[frame["month"].isin([first_month, last_month])]
        .groupby(["seller_id", "month"], observed=True)
        .agg(orders=("order_id", "nunique"), gmv=("price", "sum"))
        .reset_index()
    )
    pivot = grouped.pivot(index="seller_id", columns="month", values=["orders", "gmv"]).dropna()
    if pivot.empty:
        return pd.DataFrame(columns=output_columns)
    pivot.columns = [f"{metric}_{'base' if month == first_month else 'end'}" for metric, month in pivot.columns]
    pivot = pivot.reset_index()
    pivot = pivot.loc[
        (pivot["orders_base"] >= minimum_orders) & (pivot["orders_end"] >= minimum_orders)
    ].copy()
    pivot["gmv_change"] = pivot["gmv_end"] / pivot["gmv_base"] - 1
    return pivot[output_columns].sort_values("gmv_change").reset_index(drop=True)


def main_category(frame: pd.DataFrame) -> str | None:
    if frame.empty:
        return None
    category_gmv = frame.groupby("category", observed=True)["price"].sum().sort_values(ascending=False)
    return str(category_gmv.index[0]) if len(category_gmv) else None


def peer_benchmark(
    scoped_fact: pd.DataFrame,
    seller_id: str,
    minimum_orders: int = 5,
) -> dict:
    seller_frame = scoped_fact.loc[scoped_fact["seller_id"].eq(seller_id)]
    category = main_category(seller_frame)
    if not category:
        return {"category": None, "peers": pd.DataFrame(), "median": None, "q1": None, "q3": None, "target": None, "rank": None}
    peers = merchant_change_table(
        scoped_fact.loc[scoped_fact["category"].eq(category)], minimum_orders=minimum_orders
    )
    if peers.empty or seller_id not in set(peers["seller_id"]):
        return {"category": category, "peers": peers, "median": None, "q1": None, "q3": None, "target": None, "rank": None}
    target = float(peers.loc[peers["seller_id"].eq(seller_id), "gmv_change"].iloc[0])
    return {
        "category": category,
        "peers": peers,
        "median": float(peers["gmv_change"].median()),
        "q1": float(peers["gmv_change"].quantile(0.25)),
        "q3": float(peers["gmv_change"].quantile(0.75)),
        "target": target,
        "rank": int(peers["gmv_change"].rank(method="min", ascending=True).loc[peers["seller_id"].eq(seller_id)].iloc[0]),
    }


def driver_decomposition(boundary: dict) -> pd.DataFrame:
    columns = ["driver", "effect"]
    if boundary.get("last_month") is None:
        return pd.DataFrame(columns=columns)
    base: KpiResult = boundary["base"]
    end: KpiResult = boundary["end"]
    order_effect = (end.orders - base.orders) * (base.aov + end.aov) / 2
    aov_effect = (end.aov - base.aov) * (base.orders + end.orders) / 2
    return pd.DataFrame(
        [{"driver": "订单量影响", "effect": order_effect}, {"driver": "客单价影响", "effect": aov_effect}]
    )


def sku_migration(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    first_month, last_month = boundary_months(frame)
    columns = ["sku_group", "sku_count", "base_gmv", "end_gmv"]
    if not first_month or not last_month:
        return pd.DataFrame(columns=columns), {"base_only_gmv_share": None}
    base = frame.loc[frame["month"].eq(first_month)]
    end = frame.loc[frame["month"].eq(last_month)]
    base_skus, end_skus = set(base["product_id"]), set(end["product_id"])
    groups = {
        "持续成交SKU": base_skus & end_skus,
        "仅首月成交SKU": base_skus - end_skus,
        "末月新增成交SKU": end_skus - base_skus,
    }
    rows = []
    for label, sku_set in groups.items():
        rows.append(
            {
                "sku_group": label,
                "sku_count": len(sku_set),
                "base_gmv": float(base.loc[base["product_id"].isin(sku_set), "price"].sum()),
                "end_gmv": float(end.loc[end["product_id"].isin(sku_set), "price"].sum()),
            }
        )
    result = pd.DataFrame(rows)
    base_total = float(base["price"].sum())
    base_only = float(result.loc[result["sku_group"].eq("仅首月成交SKU"), "base_gmv"].sum())
    return result, {"base_only_gmv_share": base_only / base_total if base_total else None}


def price_mix(frame: pd.DataFrame) -> pd.DataFrame:
    first_month, last_month = boundary_months(frame)
    columns = ["period", "item_price_median", "active_sku_price_median"]
    if not first_month or not last_month:
        return pd.DataFrame(columns=columns)
    rows = []
    for month in [first_month, last_month]:
        month_frame = frame.loc[frame["month"].eq(month)]
        rows.append(
            {
                "period": month,
                "item_price_median": float(month_frame["price"].median()),
                "active_sku_price_median": float(
                    month_frame.groupby("product_id", observed=True)["price"].median().median()
                ),
            }
        )
    return pd.DataFrame(rows)
