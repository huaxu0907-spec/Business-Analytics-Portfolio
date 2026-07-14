from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import FACT_PATH, METADATA_PATH


def load_fact(path: Path = FACT_PATH) -> pd.DataFrame:
    """Load the prepared item-level fact table through DuckDB when available."""
    try:
        import duckdb

        fact = duckdb.sql(
            "SELECT * FROM read_csv_auto(?, header = true)", params=[str(path)]
        ).df()
        fact["purchase_date"] = pd.to_datetime(fact["purchase_date"])
    except ImportError:
        # Keeps metric tests runnable in a minimal Python environment.
        fact = pd.read_csv(path, compression="gzip", parse_dates=["purchase_date"])
    for column in ["order_id", "seller_id", "product_id", "customer_unique_id", "month", "category"]:
        fact[column] = fact[column].astype("string")
    return fact


def load_metadata(path: Path = METADATA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
