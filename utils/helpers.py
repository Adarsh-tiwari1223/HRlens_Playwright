import json
from pathlib import Path


def load_test_data(filename: str) -> dict:
    path = Path("testdata/static") / filename
    with open(path, "r") as f:
        return json.load(f)
