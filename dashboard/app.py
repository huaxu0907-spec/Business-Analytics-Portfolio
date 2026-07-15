import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["STREAMLIT_APP_MODE"] = "经营分析 Dashboard"

import app_core  # noqa: E402


app_core.main()
