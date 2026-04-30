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
    assert login_page.is_visible("text=Logged in Successfully"), "User was not authenticated successfully"


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
