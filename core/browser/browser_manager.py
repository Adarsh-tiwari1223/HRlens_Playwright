"""
Browser and Context lifecycle manager for Playwright.
"""

import logging
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
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
    print(f"\n=======================================================")
    print(f"[BROWSER LAUNCH] is_headed={is_headed} | settings.HEADLESS={settings.HEADLESS} | computed headless={headless}")
    print(f"=======================================================\n")
    logger.info(f"[BROWSER LAUNCH] is_headed={is_headed} | settings.HEADLESS={settings.HEADLESS} | computed headless={headless}")

    launch_kwargs = {
        "headless": headless,
        "args": ["--start-maximized", "--no-sandbox"],
    }
    if not headless:
        launch_kwargs["slow_mo"] = 1000  # 1 second between actions so user can inspect

    try:
        return playwright.chromium.launch(**launch_kwargs)
    except Exception as e:
        logger.warning(f"Chromium launch note: {e}")
        try:
            return playwright.chromium.launch(channel="chrome", **launch_kwargs)
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



def create_browser_context(browser: Browser, custom_options: dict = None, har_path: str = None) -> BrowserContext:
    """
    Creates an isolated BrowserContext with default timeout configured.
    Optionally records HAR (HTTP Archive) network traffic if har_path is specified.
    """
    options = dict(custom_options if custom_options is not None else get_context_options())
    if har_path:
        options["record_har_path"] = har_path
        options["record_har_mode"] = "full"

    if hasattr(browser, "new_context"):
        context = browser.new_context(**options)
    elif hasattr(browser, "browser") and browser.browser:
        context = browser.browser.new_context(**options)
    else:
        context = browser

    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    return context


def register_floating_alert_dismiss_handler(page: Page) -> None:
    """
    Registers an automatic background locator handler on the Page (Playwright 1.42+).
    Whenever any floating notification card (e.g. 'RESIGNATION UPDATE', 'Asset Alert', 'Return Approaching')
    appears (on login, refresh, or real-time event) and intercepts pointer events,
    Playwright automatically clicks its 'Dismiss' or '✕' button before continuing.
    """
    if getattr(page, "_has_alert_dismiss_handler", False):
        return
    try:
        alert_dismiss_loc = page.locator(
            "button:has-text('Dismiss'), "
            "div:has-text('Asset Alert') button:has-text('✕'), "
            "div:has-text('RESIGNATION UPDATE') button:has-text('✕'), "
            "div:has-text('Resignation Update') button:has-text('✕'), "
            "div:has-text('Return Approaching') button:has-text('✕')"
        ).first
        page.add_locator_handler(
            alert_dismiss_loc,
            lambda overlay: overlay.click()
        )
        page._has_alert_dismiss_handler = True
        logger.debug("[FLOATING ALERTS] Background auto-dismiss handler registered on page.")
    except Exception as ex:
        logger.debug(f"[FLOATING ALERTS] Note registering handler: {ex}")
