from __future__ import annotations

import numpy as np
import pandas as pd


ANOMALY_COLUMNS = [
    "seller_id",
    "current_month",
    "baseline_month",
    "orders",
    "gmv",
    "gmv_change",
    "orders_change",
    "late_rate",
    "low_review_rate",
    "severity_score",
    "severity",
    "priority",
    "signals",
    "observable_evidence",
    "investigation_direction",
    "recommended_action",
]


def seller_month_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Build one explainable monitoring row per seller and month."""
    if frame.empty:
        return pd.DataFrame(
            columns=["seller_id", "month", "orders", "gmv", "late_rate", "low_review_rate"]
        )
    working = frame.copy()
    working["is_low_review"] = working["review_score"].le(2).fillna(False)
    return (
        working.groupby(["seller_id", "month"], observed=True)
        .agg(
            orders=("order_id", "nunique"),
            gmv=("price", "sum"),
            late_rate=("is_late", "mean"),
            low_review_rate=("is_low_review", "mean"),
        )
        .reset_index()
        .sort_values(["seller_id", "month"])
    )


def detect_seller_anomalies(
    frame: pd.DataFrame,
    minimum_orders: int = 10,
    decline_threshold: float = 0.30,
    late_rate_threshold: float = 0.20,
    low_review_threshold: float = 0.20,
) -> pd.DataFrame:
    """Detect seller-month signals using transparent thresholds.

    A row enters the list when the current and previous active month both meet
    the order floor and at least one business rule is triggered. The result is
    a prioritisation aid, not causal proof.
    """
    monthly = seller_month_metrics(frame)
    if monthly.empty:
        return pd.DataFrame(columns=ANOMALY_COLUMNS)

    previous = monthly.groupby("seller_id", observed=True).shift(1)
    candidates = monthly.copy()
    candidates["baseline_month"] = previous["month"]
    candidates["orders_base"] = previous["orders"]
    candidates["gmv_base"] = previous["gmv"]
    candidates["gmv_change"] = np.where(
        candidates["gmv_base"].gt(0), candidates["gmv"] / candidates["gmv_base"] - 1, np.nan
    )
    candidates["orders_change"] = np.where(
        candidates["orders_base"].gt(0),
        candidates["orders"] / candidates["orders_base"] - 1,
        np.nan,
    )
    candidates = candidates.loc[
        candidates["orders"].ge(minimum_orders)
        & candidates["orders_base"].ge(minimum_orders)
    ].copy()

    rows: list[dict] = []
    for row in candidates.itertuples(index=False):
        signals: list[str] = []
        directions: list[str] = []
        score = 0
        if row.gmv_change <= -decline_threshold:
            signals.append(f"GMV环比下降{abs(row.gmv_change):.1%}")
            directions.append("核查订单规模与成交结构")
            score += 2 if row.gmv_change <= -(decline_threshold + 0.20) else 1
        if row.orders_change <= -decline_threshold:
            signals.append(f"订单量环比下降{abs(row.orders_change):.1%}")
            directions.append("核查订单流失集中对象")
            score += 2 if row.orders_change <= -(decline_threshold + 0.20) else 1
        if row.late_rate >= late_rate_threshold:
            signals.append(f"延迟率{row.late_rate:.1%}")
            directions.append("核查履约时效与延迟订单")
            score += 2 if row.late_rate >= late_rate_threshold + 0.20 else 1
        if row.low_review_rate >= low_review_threshold:
            signals.append(f"低评分率{row.low_review_rate:.1%}")
            directions.append("核查评价、商品描述与服务体验")
            score += 2 if row.low_review_rate >= low_review_threshold + 0.20 else 1
        if not signals:
            continue
        severity = "高" if score >= 4 else "中" if score >= 2 else "低"
        priority = "P0｜立即核查" if score >= 4 else "P1｜重点复核" if score >= 2 else "P2｜持续观察"
        evidence = (
            f"当前月{int(row.orders)}单、GMV {row.gmv:,.0f} BRL；"
            f"GMV环比{row.gmv_change:+.1%}、订单量环比{row.orders_change:+.1%}；"
            f"延迟率{row.late_rate:.1%}、低评分率{row.low_review_rate:.1%}"
        )
        if score >= 4:
            action = "优先核查触发信号对应的订单与商家明细，并在本周期内确认待验证原因。"
        elif score >= 2:
            action = "建议复核异常对象及前后月份差异，确认是否需要进入专项核查。"
        else:
            action = "保持持续观察；若下一周期再次触发，升级为重点复核。"
        rows.append(
            {
                "seller_id": row.seller_id,
                "current_month": row.month,
                "baseline_month": row.baseline_month,
                "orders": int(row.orders),
                "gmv": float(row.gmv),
                "gmv_change": float(row.gmv_change),
                "orders_change": float(row.orders_change),
                "late_rate": float(row.late_rate),
                "low_review_rate": float(row.low_review_rate),
                "severity_score": score,
                "severity": severity,
                "priority": priority,
                "signals": "；".join(signals),
                "observable_evidence": evidence,
                "investigation_direction": "；".join(dict.fromkeys(directions)),
                "recommended_action": action,
            }
        )
    if not rows:
        return pd.DataFrame(columns=ANOMALY_COLUMNS)
    return (
        pd.DataFrame(rows, columns=ANOMALY_COLUMNS)
        .sort_values(["severity_score", "gmv"], ascending=[False, False])
        .reset_index(drop=True)
    )


def anomaly_summary(anomalies: pd.DataFrame) -> dict:
    if anomalies.empty:
        return {"events": 0, "sellers": 0, "high": 0, "gmv": 0.0}
    return {
        "events": int(len(anomalies)),
        "sellers": int(anomalies["seller_id"].nunique()),
        "high": int(anomalies["severity"].eq("高").sum()),
        "gmv": float(anomalies["gmv"].sum()),
    }
