"""
Authentication Manager for HRlens Portal.
Handles user credential resolution, login execution, session verification,
and Playwright storage state (including sessionStorage) caching per user role.
"""

import os
import json
import logging
from datetime import datetime
from playwright.sync_api import Browser, BrowserContext, Page
from core.config import settings
from core.browser.browser_manager import create_browser_context
from pages.login_page import LoginPage

logger = logging.getLogger(__name__)

AUTH_DIR = os.path.join(os.getcwd(), ".auth")


def get_auth_state_path(user_key: str) -> str:
    """Returns absolute path to cached storage state JSON file for a given user key."""
    return os.path.join(AUTH_DIR, f"{user_key}.json")


def get_user_credentials(user_key: str) -> dict:
    """
    Resolves username and password for a user key from settings.USERS.
    Raises AssertionError if credentials are not configured.
    """
    user_info = settings.USERS.get(user_key)
    assert user_info and user_info.get("username") and user_info.get("password"), \
        f"User '{user_key}' missing valid credentials in environment settings."
    return user_info


def save_storage_state(context: BrowserContext, user_key: str) -> None:
    """Saves browser context storage state (including sessionStorage) to .auth/<user_key>.json."""
    os.makedirs(AUTH_DIR, exist_ok=True)
    auth_path = get_auth_state_path(user_key)
    try:
        state_dict = context.storage_state()

        # Capture sessionStorage from active page using explicit Storage key iteration
        session_storage = {}
        for p in context.pages:
            try:
                session_storage = p.evaluate("""() => {
                    const res = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        res[key] = sessionStorage.getItem(key);
                    }
                    return res;
                }""")
                if session_storage:
                    break
            except Exception:
                pass

        state_dict["sessionStorage"] = session_storage

        with open(auth_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

        logger.info(f"Saved session storage state (with {len(session_storage)} sessionStorage items) for user '{user_key}' to {auth_path}")
    except Exception as e:
        logger.warning(f"Failed to save storage state for user '{user_key}': {e}")



def authenticate_user(page: Page, user_key: str = "admin", save_state: bool = True) -> Page:
    """
    Navigates to portal base URL and authenticates with credentials of the specified user_key.
    Includes safeguards for modal dismissal and submission latency.
    Optionally saves storage state upon successful authentication.
    """
    creds = get_user_credentials(user_key)

    try:
        page.goto(settings.BASE_URL, timeout=30000, wait_until="domcontentloaded")
    except Exception:
        page.goto(settings.BASE_URL, timeout=30000, wait_until="commit")

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

    if save_state and user_key == "admin" and page.context:
        save_storage_state(page.context, user_key)

    return page


def is_auth_state_fresh(auth_path: str, max_age_hours: int = 12) -> bool:
    """
    Validates if cached auth state is from today and not expired due to daily session timeout.
    A new day requires a fresh initial authentication.
    """
    if not os.path.exists(auth_path) or os.path.getsize(auth_path) == 0:
        return False
    try:
        mtime = os.path.getmtime(auth_path)
        file_dt = datetime.fromtimestamp(mtime)
        now = datetime.now()
        # Session timeout across days: require new day initial login
        if file_dt.date() != now.date():
            logger.info(f"Cached auth state for '{os.path.basename(auth_path)}' is from a previous day ({file_dt.strftime('%Y-%m-%d')}). New day initial login required.")
            return False
        if (now - file_dt).total_seconds() > max_age_hours * 3600:
            logger.info(f"Cached auth state for '{os.path.basename(auth_path)}' exceeded {max_age_hours}h session limit. Fresh login required.")
            return False
        return True
    except Exception as e:
        logger.warning(f"Error checking cache freshness for '{auth_path}': {e}")
        return False


def get_authenticated_context(
    browser: Browser,
    user_key: str = "admin",
    har_path: str = None
) -> tuple[Page, BrowserContext]:
    """
    Retrieves or creates a browser context.
    - 'admin': Reuses cached session storage state if fresh.
    - Normal employees & IT persons: Always perform full UI authentication without cached session state.
    Returns (page, context) tuple.
    """
    # Only admin is permitted to use cached session storage state
    if user_key == "admin":
        auth_path = get_auth_state_path(user_key)
        state_exists = is_auth_state_fresh(auth_path)

        if state_exists:
            try:
                with open(auth_path, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)

                session_storage_data = saved_data.get("sessionStorage", {})

                logger.info(f"Reusing cached storage state for '{user_key}' from {auth_path}")
                context = create_browser_context(browser, custom_options={"storage_state": auth_path}, har_path=har_path)

                if session_storage_data:
                    ss_json = json.dumps(session_storage_data)
                    context.add_init_script(f"""
                        try {{
                            const data = {ss_json};
                            for (const [k, v] of Object.entries(data)) {{
                                sessionStorage.setItem(k, v);
                            }}
                        }} catch (e) {{}}
                    """)

                page = context.new_page()
                try:
                    page.goto(settings.BASE_URL, timeout=30000, wait_until="domcontentloaded")
                except Exception:
                    page.goto(settings.BASE_URL, timeout=30000, wait_until="commit")

                # Check if login modal/prompt is present or URL has /login
                has_login_modal = False
                try:
                    has_login_modal = page.get_by_text("Please enter your Login Details", exact=True).is_visible(timeout=2500)
                except Exception:
                    pass

                is_logged_in = ("/login" not in page.url) and not has_login_modal

                if is_logged_in:
                    logger.info(f"Cached session state for '{user_key}' is active (URL: {page.url}).")
                    return page, context

                logger.info(f"Cached session for '{user_key}' expired/invalid. Performing full UI re-authentication...")
                try:
                    context.close()
                except Exception:
                    pass
            except Exception as err:
                logger.warning(f"Error loading auth state for '{user_key}': {err}")

    # For normal employees, IT persons, or admin cache miss: perform full UI authentication
    logger.info(f"Performing direct UI login for user: '{user_key}' (cached session disabled)")
    context = create_browser_context(browser, har_path=har_path)
    page = context.new_page()
    authenticate_user(page, user_key=user_key, save_state=(user_key == "admin"))
    return page, context


