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


CONTEXT_OPTIONS = {
    "permissions": ["clipboard-read", "clipboard-write"]
}

if settings.HEADLESS:
    CONTEXT_OPTIONS["viewport"] = {"width": 1920, "height": 1080}
else:
    CONTEXT_OPTIONS["no_viewport"] = True


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.HEADLESS, args=["--start-maximized"])
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, request):
    context = browser.new_context(**CONTEXT_OPTIONS)
    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    yield page
    context.tracing.stop(path=f"reports/trace_{request.node.name}.zip")
    context.close()


@pytest.fixture(scope="module")
def logged_in_page(browser):
    contexts = []

    def _login(user_key: str = settings.EMPLOYEE_USER):
        context = browser.new_context(**CONTEXT_OPTIONS)
        context.set_default_timeout(settings.DEFAULT_TIMEOUT)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.goto(settings.BASE_URL, timeout=60000)

        LoginPage(page).login(
            settings.USERS[user_key]["username"],
            settings.USERS[user_key]["password"]
        )
        page.wait_for_load_state("networkidle")
        contexts.append((context, user_key))
        return page, context

    yield _login

    for context, user_key in contexts:
        context.tracing.stop(path=f"reports/trace_{user_key}.zip")
        context.close()


@pytest.fixture(scope="module")
def admin_page(browser, request):
    context = browser.new_context(**CONTEXT_OPTIONS)
    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.goto(settings.BASE_URL, timeout=60000)
    page.get_by_label("Email").wait_for(state="visible", timeout=30000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    yield page
    try:
        context.tracing.stop(path=f"reports/trace_{request.node.name}.zip")
    except Exception:
        pass
    context.close()

