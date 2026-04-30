import pytest
from pages.login_page import LoginPage
from core.config import settings

@pytest.fixture
def login_page(page):
    """Fixture to navigate to the base URL and return LoginPage instance."""
    page.goto(settings.BASE_URL)
    return LoginPage(page)


@pytest.mark.smoke
def test_successful_login_happy_path(login_page):
    """
    Test Case 1: Successful Login (Happy Path)
    Objective: Verify that a user with valid credentials can successfully log into the HRlens application.
    """
    # Use valid credentials from settings
    creds = settings.USERS["admin"]
    
    # Perform login
    login_page.login(creds["username"], creds["password"])
    
    # Verify expected result
    login_page.page.wait_for_url("**/dashboard")
    assert "/dashboard" in login_page.page.url, "User was not authenticated successfully"


@pytest.mark.regression
def test_error_handling_incorrect_password_negative_path(login_page):
    """
    Test Case 2: Error Handling for Incorrect Passwords (Negative Path)
    Objective: Verify that the system properly rejects login attempts with incorrect passwords.
    """
    # Use valid username but incorrect password
    valid_username = settings.USERS["admin"]["username"]
    wrong_credential = "this_is_an_invalid_credential"
    
    # Perform login attempt
    login_page.login(valid_username, wrong_credential)
    
    # Verify expected result
    assert login_page.is_visible(LoginPage.INVALID_CREDS), "Error message for invalid credentials was not displayed"


@pytest.mark.smoke
def test_empty_fields_validation(login_page):
    """
    Test Case 3: Empty Fields Validation
    Objective: Verify that the system prompts the user when login is attempted with empty fields.
    """
    # Attempt login without entering credentials
    login_page.click_login()
    
    # Verify expected result
    assert login_page.is_visible(LoginPage.EMAIL_REQUIRED), "Email required validation message was not displayed"
    assert login_page.is_visible(LoginPage.PWD_REQUIRED), "Password required validation message was not displayed"


@pytest.mark.regression
def test_forgot_password_empty_email_validation(login_page):
    """
    Test Case 4: Forgot Password Empty Email Validation
    Objective: Verify that the system prompts the user when attempting to send OTP without providing an email.
    """
    # Navigate to forgot password and attempt to send OTP
    login_page.click_forgot_password()
    login_page.click_send_otp()
    
    # Verify expected result
    assert login_page.is_visible(LoginPage.OTP_EMAIL_REQUIRED), "OTP email required validation message was not displayed"
