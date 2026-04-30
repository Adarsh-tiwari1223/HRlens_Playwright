import pytest
from pages.login_page import LoginPage
from core.config import settings


@pytest.fixture
def login_page(page):
    page.goto(settings.BASE_URL)
    return LoginPage(page)


@pytest.mark.smoke
def test_valid_login(login_page):
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    assert login_page.is_visible("text=Logged in Successfully")


@pytest.mark.smoke
def test_empty_fields(login_page):
    login_page.click_login()
    assert login_page.is_visible(LoginPage.EMAIL_REQUIRED)
    assert login_page.is_visible(LoginPage.PWD_REQUIRED)


@pytest.mark.regression
def test_invalid_credentials(login_page):
    login_page.login("admin@gmail.com", "wrongpwd")
    assert login_page.is_visible(LoginPage.INVALID_CREDS)


@pytest.mark.regression
def test_forgot_password_empty_email(login_page):
    login_page.click_forgot_password()
    login_page.click_send_otp()
    assert login_page.is_visible(LoginPage.OTP_EMAIL_REQUIRED)
