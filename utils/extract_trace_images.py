"""
HRlens Playwright — Trace Viewer Image & Action Extractor Utility.

Unpacks Playwright traceview zip files (reports/trace_*.zip), extracts screencast
frames and action snapshots from the archive, and generates a structured image catalog
ready for automatic inclusion into User Manual documents.
"""

import os
import sys
import glob
import json
import zipfile
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def find_latest_trace(pattern: str = "reports/trace_*employee*.zip") -> Optional[str]:
    """Finds the most recently modified trace zip matching the pattern."""
    traces = glob.glob(pattern)
    if not traces:
        # Fallback to any trace
        traces = glob.glob("reports/trace_*.zip")
    if not traces:
        return None
    traces.sort(key=os.path.getmtime, reverse=True)
    return traces[0]


def extract_trace_frames(
    trace_zip_path: str,
    output_dir: str = "reports/trace_extracted"
) -> Dict[str, any]:
    """
    Extracts screencast frames and action timeline from a Playwright trace zip.

    Args:
        trace_zip_path: Path to the Playwright trace.zip file.
        output_dir: Directory where extracted images will be saved.

    Returns:
        dict containing:
            - 'trace_file': source zip path
            - 'total_frames': number of screencast frames extracted
            - 'frames': list of {frame_idx, filename, path, timestamp}
            - 'actions': list of action events parsed from trace.trace
    """
    if not os.path.exists(trace_zip_path):
        raise FileNotFoundError(f"Trace file not found: {trace_zip_path}")

    os.makedirs(output_dir, exist_ok=True)
    extracted_frames = []
    actions = []

    with zipfile.ZipFile(trace_zip_path, 'r') as z:
        namelist = z.namelist()

        # 1. Parse trace.trace events
        trace_events = []
        if 'trace.trace' in namelist:
            trace_content = z.open('trace.trace').read().decode('utf-8', errors='ignore')
            for line in trace_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    trace_events.append(json.loads(line))
                except Exception:
                    pass

        # 2. Extract screencast frames
        screencast_events = [ev for ev in trace_events if ev.get("type") == "screencast-frame"]
        
        # Sort by timestamp
        screencast_events.sort(key=lambda x: x.get("timestamp", 0))

        for idx, sc in enumerate(screencast_events):
            sha1_filename = sc.get("sha1")
            if not sha1_filename:
                continue
            
            # The resource in the zip is inside resources/
            resource_key = f"resources/{sha1_filename}"
            if resource_key in namelist:
                dest_filename = f"frame_{idx:03d}_{sha1_filename.replace('/', '_')}"
                dest_path = os.path.join(output_dir, dest_filename)
                
                with open(dest_path, "wb") as f_out:
                    f_out.write(z.open(resource_key).read())
                
                extracted_frames.append({
                    "frame_idx": idx,
                    "filename": dest_filename,
                    "path": os.path.abspath(dest_path),
                    "timestamp": sc.get("timestamp", 0),
                    "width": sc.get("width"),
                    "height": sc.get("height")
                })

        # 3. Collect high-level UI actions
        for ev in trace_events:
            if ev.get("type") == "before" and ev.get("apiName"):
                api_name = ev.get("apiName")
                params = ev.get("params", {})
                actions.append({
                    "apiName": api_name,
                    "selector": params.get("selector"),
                    "url": params.get("url"),
                    "startTime": ev.get("startTime", 0)
                })

    return {
        "trace_file": os.path.abspath(trace_zip_path),
        "total_frames": len(extracted_frames),
        "frames": extracted_frames,
        "actions_count": len(actions),
        "actions": actions[:25]
    }


if __name__ == "__main__":
    target_trace = sys.argv[1] if len(sys.argv) > 1 else find_latest_trace()
    if not target_trace:
        print("No trace zip file found in reports/.")
        sys.exit(1)

    print(f"Extracting frames from: {target_trace}")
    result = extract_trace_frames(target_trace)
    print(f"Extracted {result['total_frames']} screencast frames to reports/trace_extracted/")
    print(f"Parsed {result['actions_count']} action events from trace timeline.")
