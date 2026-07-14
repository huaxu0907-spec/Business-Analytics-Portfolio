import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["STREAMLIT_APP_MODE"] = "BI经营看板"

import app_core  # noqa: E402,F401
