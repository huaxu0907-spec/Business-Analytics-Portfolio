from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
FACT_PATH = DATA_DIR / "dashboard_fact.csv.gz"
METADATA_PATH = DATA_DIR / "metadata.json"
CASE_SUMMARY_PATH = DATA_DIR / "analysis_summary.json"
RAW_ZIP_PATH = DATA_DIR / "raw" / "olist_brazilian_ecommerce.zip"

DEFAULT_SELLER = "da8622b14eb17ae2831f4ac5b9dab84a"
DEFAULT_START = "2018-04-01"
DEFAULT_END = "2018-07-31"
DEFAULT_CATEGORY = "全部品类"

VALID_ORDER_STATUS = "delivered"
GMV_CURRENCY = "BRL"


def seller_label(seller_id: str) -> str:
    """Return a stable, interview-friendly masked label."""
    if not seller_id:
        return "未知商家"
    return f"S-{seller_id[:6].upper()}"
