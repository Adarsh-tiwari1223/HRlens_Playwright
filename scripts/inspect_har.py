"""
CLI Tool for Inspecting Playwright HAR (HTTP Archive) files.
Usage:
    python scripts/inspect_har.py <har_file_path> [--errors] [--filter KEYWORD]
"""

import sys
import json
import argparse
from pathlib import Path


def inspect_har(har_path: str, errors_only: bool = False, filter_keyword: str = None):
    path = Path(har_path)
    if not path.exists():
        print(f"[ERROR] HAR file not found: {har_path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            har_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not parse HAR JSON: {e}")
        sys.exit(1)

    entries = har_data.get("log", {}).get("entries", [])
    print(f"\n=========================================================")
    print(f" HAR FILE SUMMARY: {path.name}")
    print(f" Total Network Requests Captured: {len(entries)}")
    print(f"=========================================================\n")

    displayed = 0
    for idx, entry in enumerate(entries, 1):
        req = entry.get("request", {})
        res = entry.get("response", {})
        method = req.get("method", "GET")
        url = req.get("url", "")
        status = res.get("status", 0)
        time_ms = round(entry.get("time", 0), 1)

        # Filters
        if errors_only and status < 400 and status != 0:
            continue
        if filter_keyword and filter_keyword.lower() not in url.lower():
            continue

        displayed += 1
        status_symbol = "🟢" if 200 <= status < 300 else ("🟡" if 300 <= status < 400 else "🔴")
        print(f"[{idx:03d}] {status_symbol} {status} | {method:<6} | {time_ms:>6.1f}ms | {url}")

        if status >= 400 or errors_only:
            # Print response snippet for errors
            res_content = res.get("content", {}).get("text", "")
            if res_content:
                snippet = res_content[:300].replace("\n", " ")
                print(f"      └── Response Error Payload: {snippet}")

    print(f"\n---------------------------------------------------------")
    print(f" Displayed {displayed} of {len(entries)} network entries.")
    print(f"---------------------------------------------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Playwright HAR network recordings.")
    parser.add_argument("har_file", help="Path to the .har file")
    parser.add_argument("--errors", action="store_true", help="Show only HTTP errors (>=400)")
    parser.add_argument("--filter", help="Filter network requests by URL keyword")

    args = parser.parse_args()
    inspect_har(args.har_file, errors_only=args.errors, filter_keyword=args.filter)
