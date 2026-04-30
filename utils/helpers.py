import json
from pathlib import Path

BASE_DIR = Path("testdata/static").resolve()


def load_test_data(filename: str) -> dict:
    path = (BASE_DIR / Path(filename).name).resolve()
    if not str(path).startswith(str(BASE_DIR)):
        raise ValueError(f"Invalid filename — path traversal detected: {filename}")
    return json.loads(path.read_text(encoding="utf-8"))
