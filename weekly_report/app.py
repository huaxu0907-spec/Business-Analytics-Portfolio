import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["STREAMLIT_APP_MODE"] = "自动经营周报"

import app_core  # noqa: E402


app_core.main()
