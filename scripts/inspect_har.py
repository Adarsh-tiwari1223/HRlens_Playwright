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

    # Pre-filter entries
    filtered_entries = []
    for entry in entries:
        req = entry.get("request", {})
        res = entry.get("response", {})
        url = req.get("url", "")
        status = res.get("status", 0)

        if errors_only and status < 400 and status != 0:
            continue
        if filter_keyword and filter_keyword.lower() not in url.lower():
            continue

        filtered_entries.append(entry)

    print("\n" + "=" * 125)
    print(f" HAR FILE NETWORK SUMMARY: {path.name}")
    print(f" Total Requests Captured: {len(entries)} | Displayed Matching Entries: {len(filtered_entries)}")
    print("=" * 125)

    if not filtered_entries:
        print("\n No matching network requests found.\n")
        return

    # Render ASCII Table
    border = "+" + "-"*5 + "+" + "-"*10 + "+" + "-"*8 + "+" + "-"*12 + "+" + "-"*82 + "+"
    header = f"| {'#':<3} | {'Status':<8} | {'Method':<6} | {'Time (ms)':<10} | {'URL':<80} |"

    print(border)
    print(header)
    print(border)

    for idx, entry in enumerate(filtered_entries, 1):
        req = entry.get("request", {})
        res = entry.get("response", {})
        method = req.get("method", "GET")
        url = req.get("url", "")
        status = res.get("status", 0)
        time_ms = round(entry.get("time", 0), 1)

        status_tag = f"200 OK" if 200 <= status < 300 else (f"{status} 3XX" if 300 <= status < 400 else (f"{status} ERR" if status > 0 else "FAILED"))
        display_url = url if len(url) <= 80 else url[:77] + "..."

        print(f"| {idx:<3} | {status_tag:<8} | {method:<6} | {time_ms:>8.1f} ms | {display_url:<80} |")

        if status >= 400 or errors_only:
            res_content = res.get("content", {}).get("text", "")
            if res_content:
                snippet = res_content[:100].replace("\n", " ").strip()
                err_line = f"Payload/Error: {snippet}"
                display_err = err_line if len(err_line) <= 108 else err_line[:105] + "..."
                print(f"|     | └── {display_err:<109} |")

    print(border + "\n")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Playwright HAR network recordings.")
    parser.add_argument("har_file", nargs="?", default=None, help="Path to .har file or keyword matching filename")
    parser.add_argument("-k", "--key", help="Search and inspect .har file matching filename keyword")
    parser.add_argument("--errors", action="store_true", help="Show only HTTP errors (>=400)")
    parser.add_argument("--filter", help="Filter network requests by URL keyword")

    args = parser.parse_args()

    reports_dir = Path("reports")
    all_har_files = sorted(reports_dir.glob("*.har"), key=lambda p: p.stat().st_mtime, reverse=True)

    target_har = None
    search_keyword = args.key or args.har_file

    if search_keyword:
        # Check direct file path first
        direct_path = Path(search_keyword)
        if direct_path.exists() and direct_path.is_file():
            target_har = str(direct_path)
        else:
            # Search by filename keyword in reports/
            kw = search_keyword.lower()
            matches = [str(p) for p in all_har_files if kw in p.name.lower()]
            if matches:
                target_har = matches[0]
                print(f"[INFO] Matched HAR file by keyword '{search_keyword}': {target_har}")
            else:
                print(f"[ERROR] No HAR file matching keyword '{search_keyword}' found in reports/.")
                if all_har_files:
                    print("Available HAR files in reports/:")
                    for hf in all_har_files:
                        print(f"  • {hf.name}")
                sys.exit(1)
    else:
        # Auto-select latest if no file or -k keyword specified
        if all_har_files:
            target_har = str(all_har_files[0])
            print(f"[INFO] Auto-selected latest HAR file: {target_har}")
        else:
            print("[ERROR] No .har files found in reports/ directory.")
            print("Run pytest with --record-har flag to generate a HAR file, e.g.:")
            print("  python -m pytest tests/hrlense_portal/ui/master/test_company.py --record-har")
            sys.exit(1)

    inspect_har(target_har, errors_only=args.errors, filter_keyword=args.filter)


