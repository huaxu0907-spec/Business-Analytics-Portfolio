"""Build the lightweight dashboard fact table from the archived Olist zip."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from shared.config import DATA_DIR, FACT_PATH, METADATA_PATH, RAW_ZIP_PATH  # noqa: E402


def build_dashboard_fact() -> pd.DataFrame:
    with zipfile.ZipFile(RAW_ZIP_PATH) as archive:
        orders = pd.read_csv(
            archive.open("olist_orders_dataset.csv"),
            usecols=[
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
            parse_dates=[
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )
        items = pd.read_csv(
            archive.open("olist_order_items_dataset.csv"),
            usecols=["order_id", "order_item_id", "product_id", "seller_id", "price"],
        )
        products = pd.read_csv(
            archive.open("olist_products_dataset.csv"),
            usecols=["product_id", "product_category_name"],
        )
        translations = pd.read_csv(archive.open("product_category_name_translation.csv"))
        customers = pd.read_csv(
            archive.open("olist_customers_dataset.csv"),
            usecols=["customer_id", "customer_unique_id"],
        )
        reviews = pd.read_csv(
            archive.open("olist_order_reviews_dataset.csv"),
            usecols=["order_id", "review_score", "review_creation_date"],
            parse_dates=["review_creation_date"],
        )

    products = products.merge(translations, on="product_category_name", how="left")
    reviews = (
        reviews.sort_values("review_creation_date")
        .drop_duplicates("order_id", keep="last")
        .drop(columns="review_creation_date")
    )
    fact = (
        items.merge(
            products[["product_id", "product_category_name_english"]],
            on="product_id",
            how="left",
        )
        .merge(orders, on="order_id", how="inner")
        .merge(customers, on="customer_id", how="left")
        .merge(reviews, on="order_id", how="left")
    )
    fact = fact.loc[
        (fact["order_status"] == "delivered")
        & (fact["order_purchase_timestamp"] >= "2017-01-01")
        & (fact["order_purchase_timestamp"] < "2018-08-01")
    ].copy()

    fact["category"] = fact["product_category_name_english"].fillna("unknown")
    fact["purchase_date"] = fact["order_purchase_timestamp"].dt.normalize()
    fact["month"] = fact["order_purchase_timestamp"].dt.to_period("M").astype(str)
    fact["delivery_delay_days"] = (
        fact["order_delivered_customer_date"] - fact["order_estimated_delivery_date"]
    ).dt.days
    fact["is_late"] = fact["delivery_delay_days"].gt(0).astype("int8")

    output_columns = [
        "order_id",
        "order_item_id",
        "seller_id",
        "product_id",
        "customer_unique_id",
        "purchase_date",
        "month",
        "category",
        "price",
        "review_score",
        "delivery_delay_days",
        "is_late",
    ]
    return fact[output_columns].sort_values(["purchase_date", "order_id", "order_item_id"])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fact = build_dashboard_fact()
    fact.to_csv(FACT_PATH, index=False, compression="gzip", encoding="utf-8")
    metadata = {
        "rows": int(len(fact)),
        "orders": int(fact["order_id"].nunique()),
        "sellers": int(fact["seller_id"].nunique()),
        "start_date": str(fact["purchase_date"].min().date()),
        "end_date": str(fact["purchase_date"].max().date()),
        "gmv_definition": "delivered order item price sum, excluding freight",
        "currency": "BRL",
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
