from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from .config import DEFAULT_CATEGORY, DEFAULT_END, DEFAULT_SELLER, DEFAULT_START


def is_default_case(
    seller_id: str,
    start_date: str | date | datetime | pd.Timestamp,
    end_date: str | date | datetime | pd.Timestamp,
    category: str,
) -> bool:
    return (
        seller_id == DEFAULT_SELLER
        and pd.Timestamp(start_date).normalize() == pd.Timestamp(DEFAULT_START)
        and pd.Timestamp(end_date).normalize() == pd.Timestamp(DEFAULT_END)
        and category == DEFAULT_CATEGORY
    )


def investigation_directions(boundary: dict, peer: dict, sku: dict) -> list[dict[str, str]]:
    """Generate evidence-bounded actions from the current filter result."""
    directions: list[dict[str, str]] = []
    orders_change = boundary.get("orders_change")
    aov_change = boundary.get("aov_change")
    base_only_share = sku.get("base_only_gmv_share")

    if orders_change is not None and orders_change <= -0.10:
        directions.append(
            {
                "signal": f"订单量首尾月变化 {orders_change:.1%}",
                "direction": "优先核查交易基础变化",
                "action": "检查高贡献SKU的在售、库存、价格与流量状态，并按历史贡献排序核查。",
                "validation": "订单量、恢复SKU数、恢复SKU贡献GMV。",
            }
        )
    if aov_change is not None and abs(aov_change) >= 0.10:
        movement = "下移" if aov_change < 0 else "上移"
        directions.append(
            {
                "signal": f"客单价首尾月{movement} {abs(aov_change):.1%}",
                "direction": "核查成交商品与价格组合",
                "action": "区分单品价格变化与商品组合变化，检查促销、低价SKU占比及高价SKU成交情况。",
                "validation": "客单价、成交价格中位数、高价SKU成交占比。",
            }
        )
    if base_only_share is not None and base_only_share >= 0.30:
        directions.append(
            {
                "signal": f"仅首月成交SKU贡献首月GMV的 {base_only_share:.1%}",
                "direction": "优先核查SKU成交结构",
                "action": "建立首月高贡献但末月未成交SKU清单，逐项确认状态，不将未成交直接解释为缺货或下架。",
                "validation": "SKU恢复率、恢复SKU订单量与GMV贡献。",
            }
        )
    if peer.get("target") is not None and peer.get("median") is not None:
        gap = peer["target"] - peer["median"]
        if gap <= -0.10:
            directions.append(
                {
                    "signal": f"目标商家变化比同类中位数低 {abs(gap):.1%}",
                    "direction": "核查商家特有因素",
                    "action": "优先排查商家自身商品、运营和履约变化，再判断是否属于品类或平台共性波动。",
                    "validation": "目标商家与同类中位数差距、履约与评价护栏指标。",
                }
            )
    if not directions:
        directions.append(
            {
                "signal": "当前筛选范围未出现达到预设阈值的明显负向信号",
                "direction": "保持监控并复核口径",
                "action": "扩大观察周期或切换业务维度，避免在样本不足时作出机制判断。",
                "validation": "GMV、订单量、客单价及样本规模。",
            }
        )
    return directions[:3]
