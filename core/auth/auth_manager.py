"""
Authentication Manager for HRlens Portal.
Handles user credential resolution, login execution, and session verification.
"""

import logging
from playwright.sync_api import Page
from core.config import settings
from core.browser.browser_manager import register_floating_alert_dismiss_handler
from pages.login_page import LoginPage

logger = logging.getLogger(__name__)


def get_user_credentials(user_key: str) -> dict:
    """
    Resolves username and password for a user key from settings.USERS.
    Raises AssertionError if credentials are not configured.
    """
    user_info = settings.USERS.get(user_key)
    assert user_info and user_info.get("username") and user_info.get("password"), \
        f"User '{user_key}' missing valid credentials in environment settings."
    return user_info


def authenticate_user(page: Page, user_key: str = "admin") -> Page:
    """
    Navigates to portal base URL and authenticates with credentials of the specified user_key.
    Includes safeguards for modal dismissal and submission latency.
    """
    register_floating_alert_dismiss_handler(page)
    creds = get_user_credentials(user_key)

    page.goto(settings.BASE_URL, timeout=60000)
    try:
        page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="visible", timeout=30000)
    except Exception:
        pass

    login_page = LoginPage(page)
    login_page.login(creds["username"], creds["password"])

    try:
        page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="hidden", timeout=15000)
    except Exception:
        # Safeguard: Re-click Login button if network latency delayed initial submission
        try:
            if page.get_by_text("Please enter your Login Details", exact=True).is_visible(timeout=2000):
                page.get_by_role("button", name="Login").click()
                page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="hidden", timeout=20000)
        except Exception:
            pass

    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass

    dismiss_post_login_cards(page)

    return page


def dismiss_post_login_cards(page: Page) -> int:
    """
    Dismisses all floating notification cards (e.g. Asset Alert, Resignation Update, Return Approaching)
    that appear after successful login.
    Clicks the card's '✕' close button or 'Dismiss' button.
    """
    dismissed_count = 0
    try:
        alert_buttons = page.locator(
            "div:has-text('Asset Alert') button:has-text('✕'), "
            "div:has-text('Asset Alert') button:has-text('Dismiss'), "
            "div:has-text('Resignation Update') button:has-text('✕'), "
            "div:has-text('Return Approaching') button:has-text('✕'), "
            "button:has-text('Dismiss')"
        )
        if not alert_buttons.first.is_visible(timeout=1000):
            return 0

        for _ in range(5):
            btns = alert_buttons.all()
            if not btns:
                break
            clicked = False
            for btn in btns:
                try:
                    if btn.is_visible(timeout=300):
                        btn.click(force=True)
                        dismissed_count += 1
                        clicked = True
                        page.wait_for_timeout(200)
                except Exception:
                    pass
            if not clicked:
                break

        if dismissed_count > 0:
            logger.info(f"[POST-LOGIN] Successfully dismissed {dismissed_count} notification card(s).")
    except Exception as ex:
        logger.debug(f"Note dismissing post-login cards: {ex}")

    return dismissed_count

