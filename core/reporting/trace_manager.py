"""
Playwright Trace Management for Test Execution & Failure Analysis.
"""

import os
import logging
from playwright.sync_api import BrowserContext

logger = logging.getLogger(__name__)


def start_tracing(context: BrowserContext):
    """Starts Playwright execution tracing with screenshots, DOM snapshots, and sources."""
    try:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception as e:
        logger.debug(f"Could not start tracing: {e}")


def stop_tracing(context: BrowserContext, output_path: str = None):
    """
    Stops Playwright tracing.
    If output_path is provided, saves the trace archive to disk.
    Otherwise, stops and discards the trace to save disk space.
    """
    try:
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            context.tracing.stop(path=output_path)
        else:
            context.tracing.stop()
    except Exception as e:
        logger.debug(f"Could not stop tracing: {e}")
