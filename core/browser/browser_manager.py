"""
Browser and Context lifecycle manager for Playwright.
"""

import logging
from playwright.sync_api import Playwright, Browser, BrowserContext
from core.config import settings

logger = logging.getLogger(__name__)


def get_context_options() -> dict:
    """
    Returns standard browser context options for HRlens tests.
    Includes clipboard permissions and responsive viewport configurations.
    """
    options = {
        "permissions": ["clipboard-read", "clipboard-write"]
    }
    if settings.HEADLESS:
        options["viewport"] = {"width": 1920, "height": 1080}
    else:
        options["no_viewport"] = True
    return options


def launch_browser(playwright: Playwright, is_headed: bool = False) -> Browser:
    """
    Launches Chromium browser instance with start-maximized flag.
    """
    headless = not (is_headed or not settings.HEADLESS)
    return playwright.chromium.launch(
        headless=headless,
        args=["--start-maximized"]
    )


def create_browser_context(browser: Browser, custom_options: dict = None) -> BrowserContext:
    """
    Creates an isolated BrowserContext with default timeout configured.
    """
    options = custom_options if custom_options is not None else get_context_options()
    if hasattr(browser, "new_context"):
        context = browser.new_context(**options)
    elif hasattr(browser, "browser") and browser.browser:
        context = browser.browser.new_context(**options)
    else:
        context = browser

    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    return context
