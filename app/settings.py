"""Where the app keeps its data.

The working data lives in data/store/ and is created from data/examples/
the first time the app starts. Set CARRENTAL_DATA_DIR to use another folder,
for example in tests.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "data" / "examples"


def data_dir() -> Path:
    return Path(os.environ.get("CARRENTAL_DATA_DIR", PROJECT_ROOT / "data" / "store"))
