import pytest
from pages.common.Login import LoginPage
from core.config import settings


@pytest.fixture
def login_page(page):
    page.goto(settings.BASE_URL)
    return LoginPage(page)


def test_valid_login(login_page):
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    assert login_page.is_visible("//div[contains(text(), 'Dashboard')]")  # Adjust the locator as needed


def test_login_empty_fields(login_page):
    login_page.click_login_button()
    assert login_page.is_email_error_visible()
    assert login_page.is_password_error_visible()
