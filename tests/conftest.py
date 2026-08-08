import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from core.config import settings
from testdata.static.companies import COMPANIES

def pytest_addoption(parser):
    parser.addoption(
        "--company", action="store", default="Code Crewzs Private Limited", 
        help="Specify company to test against, or 'all' to run against all companies"
    )

def pytest_generate_tests(metafunc):
    if "template_company" in metafunc.fixturenames:
        company_opt = metafunc.config.getoption("--company")
        if company_opt.lower() == "all":
            metafunc.parametrize("template_company", COMPANIES)
        else:
            metafunc.parametrize("template_company", [company_opt])

import logging

logger = logging.getLogger(__name__)

def pytest_configure(config):
    """Log active configuration at start of test session."""
    logger.info("==================================================")
    logger.info("HRlens Playwright - Active Configuration")
    logger.info("==================================================")
    logger.info(f"ENV:        {settings.ENV}")
    logger.info(f"API URL:    {settings.API_BASE_URL}")
    logger.info("==================================================")


def pytest_collection_modifyitems(items):
    """Reorder test collection so that authentication and login tests always run FIRST."""
    login_items = []
    other_items = []
    for item in items:
        if "auth" in item.nodeid.lower() or "login" in item.nodeid.lower():
            login_items.append(item)
        else:
            other_items.append(item)
    items[:] = login_items + other_items


def pytest_xdist_auto_num_workers(config):
    """
    Parallel Worker Allocation:
    - Assign 1 worker when --headed flag is passed or HEADLESS is False (for step-by-step visual execution).
    - Assign 1 worker when executing a single test file.
    - Scale to max 4 workers only when running multiple test files in headless mode.
    """
    import os
    is_headed = getattr(config.option, "headed", False) or not settings.HEADLESS
    if is_headed:
        return 1

    file_args = [arg for arg in config.args if arg.endswith('.py')]
    if len(file_args) == 1:
        return 1
    cpu_cores = os.cpu_count() or 4
    return min(cpu_cores, 4)


CONTEXT_OPTIONS = {
    "permissions": ["clipboard-read", "clipboard-write"]
}

if settings.HEADLESS:
    CONTEXT_OPTIONS["viewport"] = {"width": 1920, "height": 1080}
else:
    CONTEXT_OPTIONS["no_viewport"] = True


import os

CHROME_USER_DATA_DIR = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")

@pytest.fixture(scope="session")
def browser(pytestconfig):
    is_headed = getattr(pytestconfig.option, "headed", False) or not settings.HEADLESS
    with sync_playwright() as p:
        browser_instance = p.chromium.launch(headless=not is_headed, args=["--start-maximized"])
        yield browser_instance
        browser_instance.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to attach test call status to item for conditional failure actions."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def page(browser, request):
    if hasattr(browser, "new_context"):
        context = browser.new_context(**CONTEXT_OPTIONS)
        should_close_context = True
    elif hasattr(browser, "browser") and browser.browser:
        context = browser.browser.new_context(**CONTEXT_OPTIONS)
        should_close_context = True
    else:
        context = browser
        should_close_context = False

    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    try:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        pass
    page = context.new_page()
    
    yield page
    
    # Save trace ONLY if the test failed!
    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        try:
            context.tracing.stop(path=f"reports/trace_{request.node.name}.zip")
        except Exception:
            pass
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass

    # Close test page tab so tab bar does not accumulate open tabs
    try:
        page.close()
    except Exception:
        pass

    if should_close_context:
        try:
            context.close()
        except Exception:
            pass


@pytest.fixture(scope="module")
def logged_in_page(browser):
    contexts = []

    def _login(user_key: str = settings.EMPLOYEE_USER):
        user_info = settings.USERS.get(user_key)
        assert user_info and user_info.get("username") and user_info.get("password"), \
            f"User '{user_key}' missing valid credentials in environment settings."

        if hasattr(browser, "new_context"):
            context = browser.new_context(**CONTEXT_OPTIONS)
        elif hasattr(browser, "browser") and browser.browser:
            context = browser.browser.new_context(**CONTEXT_OPTIONS)
        else:
            context = browser

        context.set_default_timeout(settings.DEFAULT_TIMEOUT)
        try:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception:
            pass
        page = context.new_page()
        page.goto(settings.BASE_URL, timeout=60000)
        try:
            page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="visible", timeout=30000)
        except Exception:
            pass

        LoginPage(page).login(
            user_info["username"],
            user_info["password"]
        )
        try:
            page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="hidden", timeout=15000)
        except Exception:
            # Safeguard: Re-click Login if network latency or toast overlay delayed initial submission
            if page.get_by_text("Please enter your Login Details", exact=True).is_visible():
                page.get_by_role("button", name="Login").click()
                page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="hidden", timeout=20000)
        contexts.append((context, user_key))
        return page, context


    yield _login

    for context, user_key in contexts:
        try:
            context.tracing.stop(path=f"reports/trace_{user_key}.zip")
        except Exception:
            pass
        try:
            for p in context.pages:
                try:
                    p.close()
                except Exception:
                    pass
            if hasattr(browser, "new_context") or (hasattr(browser, "browser") and browser.browser):
                context.close()
        except Exception:
            pass


@pytest.fixture(scope="module")
def admin_page(browser, request):
    if hasattr(browser, "new_context"):
        context = browser.new_context(**CONTEXT_OPTIONS)
    elif hasattr(browser, "browser") and browser.browser:
        context = browser.browser.new_context(**CONTEXT_OPTIONS)
    else:
        context = browser
    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.goto(settings.BASE_URL, timeout=60000)
    page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="visible", timeout=30000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.get_by_text("Please enter your Login Details", exact=True).wait_for(state="hidden", timeout=30000)
    yield page
    try:
        context.tracing.stop(path=f"reports/trace_{request.node.name}.zip")
    except Exception:
        pass
    try:
        page.close()
    except Exception:
        pass
    if hasattr(browser, "new_context") or (hasattr(browser, "browser") and browser.browser):
        context.close()


@pytest.fixture(autouse=True)
def clean_page_state_after_test(request):
    """
    Autouse fixture executed for every test.
    Teardown: Closes open dialogs, clears overlays, and safely resets page state
    so subsequent tests never encounter sticky modal overlays or wrong tab state.
    """
    yield
    page = request.node.funcargs.get("admin_page") or request.node.funcargs.get("page")
    if page and not page.is_closed():
        try:
            modal_close = page.locator("[role='dialog'] .chakra-modal__close-btn, [role='dialog'] button:has-text('Cancel')").first
            if modal_close.is_visible():
                modal_close.click(force=True)
                page.wait_for_timeout(300)
        except Exception:
            pass
        try:
            page.evaluate("() => window.scrollTo(0, 0)")
        except Exception:
            pass
