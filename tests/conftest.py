"""
Pytest configuration, CLI options, hooks, and core fixture composition for HRlens Playwright tests.
"""

import os
import re
import logging
import pytest
from playwright.sync_api import sync_playwright

from core.config import settings
from core.browser.browser_manager import get_context_options, launch_browser, create_browser_context
from core.reporting.trace_manager import start_tracing, stop_tracing
from core.auth.auth_manager import authenticate_user
from testdata.static.companies import COMPANIES

logger = logging.getLogger(__name__)

# Preserved for backward compatibility
CONTEXT_OPTIONS = get_context_options()


# ══════════════════════════════════════════════════════════════════════════════
# PYTEST CLI OPTIONS & PARAMETRIZATION HOOKS
# ══════════════════════════════════════════════════════════════════════════════

def pytest_addoption(parser):
    """Adds CLI options for customizing test runs."""
    parser.addoption(
        "--company", action="store", default="Code Crewzs Private Limited",
        help="Specify company to test against, or 'all' to run against all companies"
    )


def pytest_generate_tests(metafunc):
    """Dynamically parametrizes tests requesting the 'template_company' fixture."""
    if "template_company" in metafunc.fixturenames:
        company_opt = metafunc.config.getoption("--company")
        if company_opt.lower() == "all":
            metafunc.parametrize("template_company", COMPANIES)
        else:
            metafunc.parametrize("template_company", [company_opt])


def pytest_configure(config):
    """Logs active configuration at start of test session."""
    logger.info("==================================================")
    logger.info("HRlens Playwright - Active Configuration")
    logger.info("==================================================")
    logger.info(f"ENV:        {settings.ENV}")
    logger.info(f"API URL:    {settings.API_BASE_URL}")
    logger.info("==================================================")


def pytest_collection_modifyitems(items):
    """Reorders test collection so authentication/login tests always execute first."""
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
    - Assigns 1 worker when --headed flag is passed or HEADLESS is False.
    - Assigns 1 worker when executing a single test file.
    - Scales up to max 4 workers when running multiple test files in headless mode.
    """
    is_headed = getattr(config.option, "headed", False) or not settings.HEADLESS
    if is_headed:
        return 1

    file_args = [arg for arg in config.args if arg.endswith('.py')]
    if len(file_args) == 1:
        return 1

    cpu_cores = os.cpu_count() or 4
    return min(cpu_cores, 4)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attaches test outcome report to item for conditional failure actions."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ══════════════════════════════════════════════════════════════════════════════
# DEDICATED PER-TEST LOGGING HOOK (hrlense_portal & recruitment_portal)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def per_test_logger(request):
    """
    Creates a dedicated log file for each test case organized into portal subfolders:
    - tests/hrlense_portal/...     -> logs/hrlense_portal/{test_name}.log
    - tests/recruitment_portal/... -> logs/recruitment_portal/{test_name}.log
    """
    test_path = str(request.node.fspath).replace("\\", "/")

    if "hrlense_portal" in test_path:
        subfolder = "hrlense_portal"
    elif "recruitment_portal" in test_path:
        subfolder = "recruitment_portal"
    else:
        subfolder = "general"

    logs_dir = os.path.join(os.getcwd(), "logs", subfolder)
    os.makedirs(logs_dir, exist_ok=True)

    test_name = request.node.name
    safe_name = re.sub(r'[^\w\-_.]', '_', test_name)
    log_file_path = os.path.join(logs_dir, f"{safe_name}.log")

    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s  →  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    logger.info("================================================================================")
    logger.info(f"[TEST START] {test_name}")
    logger.info("================================================================================")

    yield

    rep_call = getattr(request.node, "rep_call", None)
    status = "PASSED" if (rep_call and rep_call.passed) else ("FAILED" if (rep_call and rep_call.failed) else "COMPLETED")

    logger.info("================================================================================")
    logger.info(f"[TEST END] {test_name} → {status}")
    logger.info("================================================================================")

    root_logger.removeHandler(file_handler)
    file_handler.close()


# ══════════════════════════════════════════════════════════════════════════════
# CORE BROWSER & PAGE FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser(pytestconfig):
    """
    Session-scoped Chromium browser instance.
    Configured with start-maximized and proper headed/headless mode.
    """
    is_headed = getattr(pytestconfig.option, "headed", False) or not settings.HEADLESS
    with sync_playwright() as p:
        browser_instance = launch_browser(p, is_headed=is_headed)
        yield browser_instance
        browser_instance.close()


@pytest.fixture(scope="function")
def page(browser, request):
    """
    Function-scoped isolated browser context and page.
    Enables Playwright tracing and saves trace artifacts only on test failure.
    """
    context = create_browser_context(browser)
    start_tracing(context)
    page_instance = context.new_page()

    yield page_instance

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        stop_tracing(context, output_path=f"reports/trace_{request.node.name}.zip")
    else:
        stop_tracing(context)

    try:
        page_instance.close()
    except Exception:
        pass

    if hasattr(browser, "new_context") or (hasattr(browser, "browser") and browser.browser):
        try:
            context.close()
        except Exception:
            pass


@pytest.fixture(scope="function")
def logged_in_page(browser, request):
    """
    Function-scoped login factory fixture.
    Supports user_key selection (defaults to settings.EMPLOYEE_USER).
    Returns (page, context) tuple and automatically closes all pages/contexts on test completion.
    """
    contexts = []

    def _login(user_key: str = settings.EMPLOYEE_USER):
        context = create_browser_context(browser)
        start_tracing(context)
        page_instance = context.new_page()

        authenticate_user(page_instance, user_key=user_key)
        contexts.append((context, user_key))
        return page_instance, context

    yield _login

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    for context, user_key in contexts:
        if failed:
            stop_tracing(context, output_path=f"reports/trace_{request.node.name}_{user_key}.zip")
        else:
            stop_tracing(context)
        try:
            for p in context.pages:
                try:
                    p.close()
                except Exception:
                    pass
            context.close()
        except Exception:
            pass


@pytest.fixture(scope="function")
def admin_page(browser, request):
    """
    Function-scoped pre-authenticated Admin page fixture.
    Automatically closes context on test completion.
    """
    context = create_browser_context(browser)
    start_tracing(context)
    page_instance = context.new_page()

    authenticate_user(page_instance, user_key="admin")

    yield page_instance

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        stop_tracing(context, output_path=f"reports/trace_{request.node.name}.zip")
    else:
        stop_tracing(context)
    try:
        page_instance.close()
    except Exception:
        pass
    try:
        context.close()
    except Exception:
        pass
