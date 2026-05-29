import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from core.config import settings


def pytest_configure(config):
    """Print active configuration at start of test session."""
    print("\n" + "="*50)
    print("HRlens Playwright - Active Configuration")
    print("="*50)
    print("ENV:        " + settings.ENV)
    print("API URL:    " + settings.API_BASE_URL)
    print("="*50 + "\n")

CONTEXT_OPTIONS = {
    "no_viewport": True,
    "permissions": ["clipboard-read", "clipboard-write"]
}


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
        page.goto(settings.BASE_URL)
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
