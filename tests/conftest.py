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
    parser.addoption(
        "--record-har", action="store_true", default=False,
        help="Record HAR (HTTP Archive) network logs into reports/network_<test_name>.har"
    )
    parser.addoption(
        "--employee", action="store", default=None,
        help="Pin a specific employee name for resignation E2E test (e.g. --employee='Uttam Kumar')"
    )
    parser.addoption(
        "--record-trace", action="store_true", default=False,
        help="Always record Playwright trace view (on both PASS and FAIL). When omitted, traces are saved on FAIL only."
    )
    parser.addoption(
        "--headed", action="store_true", default=False,
        help="Run browser in headed mode (visible GUI window)"
    )


def should_save_trace(request, failed: bool) -> bool:
    """
    Determines whether Playwright trace should be exported to disk.
    - If user passed `--record-trace`, `--trace`, or `--tracing=on`: captures on BOTH PASS and FAIL.
    - Otherwise (default): captures ONLY on FAIL.
    """
    if failed:
        return True
    try:
        if request.config.getoption("--record-trace", False):
            return True
    except Exception:
        pass
    try:
        tracing_opt = str(request.config.getoption("--tracing", "")).lower()
        if tracing_opt in ["on", "true", "1"]:
            return True
    except Exception:
        pass
    return False


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


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_auto_num_workers(config):
    """
    Parallel Worker Allocation:
    - Assigns 1 worker when --headed flag is passed or HEADLESS is False.
    - Assigns 1 worker when executing a single test file.
    - Scales workers to min(test_files, cpu_cores, 4) in headless mode.
    """
    is_headed = getattr(config.option, "headed", False) or not settings.HEADLESS
    if is_headed:
        return 1

    file_args = [arg for arg in config.args if arg.endswith('.py')]
    if len(file_args) == 1:
        return 1

    cpu_cores = os.cpu_count() or 4
    num_files = len(file_args) if file_args else cpu_cores
    return min(num_files, cpu_cores, 4)


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
        try:
            for ctx in list(browser_instance.contexts):
                for pg in list(ctx.pages):
                    try:
                        pg.close()
                    except Exception:
                        pass
                try:
                    ctx.close()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            browser_instance.close()
        except Exception:
            pass


@pytest.fixture(scope="function")
def page(browser, request):
    """
    Function-scoped isolated browser context and page.
    Enables Playwright tracing and saves trace artifacts only on test failure.
    """
    record_har = request.config.getoption("--record-har", False)
    har_path = f"reports/network_{request.node.name}.har" if record_har else None

    context = create_browser_context(browser, har_path=har_path)
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
    Function-scoped login factory fixture with session pooling.
    Maintains isolated browser contexts per user_key, reusing existing active sessions
    to prevent redundant re-logins during multi-role workflows.
    Automatically closes all contexts on test completion.
    """
    record_har = request.config.getoption("--record-har", False)
    contexts = []
    session_pool = {}

    def _login(user_key: str = settings.EMPLOYEE_USER, reuse: bool = True):
        # 1. Reuse existing logged-in session if available and active
        if reuse and user_key in session_pool:
            page, ctx = session_pool[user_key]
            try:
                if not page.is_closed():
                    logger.info(f"[SESSION POOL] Reusing active session for '{user_key}' (0s login time)")
                    page.bring_to_front()
                    return page, ctx
            except Exception:
                pass

        # 2. First time or fresh request: create isolated context & log in
        har_path = f"reports/network_{request.node.name}_{user_key}.har" if record_har else None
        context = create_browser_context(browser, har_path=har_path)
        start_tracing(context)
        page_instance = context.new_page()

        authenticate_user(page_instance, user_key=user_key)
        contexts.append((context, user_key))
        session_pool[user_key] = (page_instance, context)
        return page_instance, context

    yield _login

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    save_trace = should_save_trace(request, failed)
    safe_name = re.sub(r'[^\w\-_.]', '_', request.node.name)

    for context, user_key in contexts:
        if save_trace:
            trace_path = f"reports/trace_{safe_name}_{user_key}.zip"
            stop_tracing(context, output_path=trace_path)
            logger.info(f"[TRACE SAVED] Exported Playwright trace ({'FAILED' if failed else 'PASSED'}) -> {trace_path}")
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
    record_har = request.config.getoption("--record-har", False)
    har_path = f"reports/network_{request.node.name}.har" if record_har else None

    context = create_browser_context(browser, har_path=har_path)
    start_tracing(context)
    page_instance = context.new_page()

    authenticate_user(page_instance, user_key="admin")

    yield page_instance

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    save_trace = should_save_trace(request, failed)
    safe_name = re.sub(r'[^\w\-_.]', '_', request.node.name)

    if save_trace:
        trace_path = f"reports/trace_{safe_name}.zip"
        stop_tracing(context, output_path=trace_path)
        logger.info(f"[TRACE SAVED] Exported Playwright trace ({'FAILED' if failed else 'PASSED'}) -> {trace_path}")
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
