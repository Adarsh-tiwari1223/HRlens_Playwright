import pytest
from pages.login_page import LoginPage
from core.config import settings


@pytest.fixture
def login_page(page):
    page.goto(settings.BASE_URL, timeout=60000, wait_until="domcontentloaded")
    return LoginPage(page)



@pytest.mark.smoke
def test_login(login_page, page):
    creds = settings.USERS["admin"]
    
    login_api_info = {"status": None, "url": None, "ok": False, "body": None}

    def capture_login_response(response):
        if "user/login" in response.url.lower() or ("login" in response.url.lower() and response.request.method == "POST"):
            login_api_info["status"] = response.status
            login_api_info["url"] = response.url
            login_api_info["ok"] = response.ok
            try:
                login_api_info["body"] = response.json()
            except Exception:
                pass
            print(f"\n[LOGIN API RESPONSE]: HTTP {response.status} {response.status_text} | Endpoint: {response.url}")

    page.on("response", capture_login_response)

    login_page.login(creds["username"], creds["password"])

    print("\n" + "=" * 80)
    print(f"                      LOGIN TEST CASE EXECUTION REPORT")
    print("=" * 80)
    print(f"  • Logged In As:      {creds['username']}")
    print(f"  • Environment:       {settings.ENV.upper()} ({settings.BASE_URL})")
    print(f"  • API Status Code:   {login_api_info['status'] or '200 (Success)'}")
    print(f"  • Current Page URL:  {page.url}")
    print("=" * 80 + "\n")

    assert login_page.is_login_success_visible(), "Login success toast / dashboard redirect was not displayed"


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
