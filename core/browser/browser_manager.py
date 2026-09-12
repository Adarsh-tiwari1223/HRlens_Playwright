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
    Launches Chromium or system Chrome browser instance with start-maximized flag.
    Gracefully falls back to headless if headed mode is requested but no X-server/display is available.
    """
    headless = not (is_headed or not settings.HEADLESS)
    try:
        return playwright.chromium.launch(
            headless=headless,
            channel="chrome",
            args=["--start-maximized"]
        )
    except Exception:
        try:
            return playwright.chromium.launch(
                headless=headless,
                args=["--start-maximized"]
            )
        except Exception as launch_err:
            # When headed mode is requested in container or CI without an X display, fall back to headless
            if not headless and ("Missing X server" in str(launch_err) or "Target page, context or browser has been closed" in str(launch_err)):
                logger.warning(
                    "Headed mode requested (HEADLESS=False) but no GUI display ($DISPLAY / X server) is available in container. "
                    "Falling back to headless mode to allow execution."
                )
                print(
                    "\n[WARNING] Headed mode requested (HEADLESS=False) but no GUI display ($DISPLAY / X server) is available in this environment.\n"
                    "          Falling back to headless mode so tests can execute without crashing.\n"
                )
                return playwright.chromium.launch(
                    headless=True,
                    args=["--start-maximized"]
                )
            raise launch_err



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
