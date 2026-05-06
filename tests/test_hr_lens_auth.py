import pytest
from pages.login_page import LoginPage
from core.config import settings


@pytest.fixture
def login_page(page):
    page.goto(settings.BASE_URL)
    return LoginPage(page)


@pytest.mark.smoke
def test_login(login_page):
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    assert login_page.is_login_success_visible(), "Login success toast was not displayed"


@pytest.mark.regression
def test_error_handling_incorrect_password_negative_path(login_page):
    login_page.login(settings.USERS["admin"]["username"], "wrong_password")
    assert login_page.is_invalid_creds_visible(), "Invalid credentials error was not displayed"


@pytest.mark.smoke
def test_empty_fields_validation(login_page):
    login_page.click_login()
    assert login_page.is_email_required_visible(), "Email required message was not displayed"
    assert login_page.is_password_required_visible(), "Password required message was not displayed"


@pytest.mark.regression
def test_forgot_password_empty_email_validation(login_page):
    login_page.click_forgot_password()
    login_page.click_send_otp()
    assert login_page.is_otp_email_required_visible(), "OTP email required message was not displayed"
