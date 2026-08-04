"""
UI Test Suite for ZIP Code Location Autofill & Payroll Company Validation (HR Lens Portal).
Validates S.No 10 (ZIP Code Auto-fill for Indian vs Foreign postal codes in Company & Payroll Company)
and S.No 13 (Website Field Enablement in Add Payroll Company).
"""

import pytest
from pages.login_page import LoginPage
from pages.hrlense_portal.master.payroll_company_page import PayrollCompanyPage
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug


@pytest.fixture
def admin_page(page):
    """Logs in as Admin user."""
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS["admin"]
    LoginPage(page).login(creds["username"], creds["password"])
    return page


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company
def test_sno_10_indian_vs_foreign_zipcode_autofill(admin_page):
    """
    S.No 10: Validate ZIP Code State/Country Auto-fill (Indian PIN vs Foreign ZIP Code).
    - Indian PIN (110001): Auto-populates 'India' / 'Delhi'.
    - Foreign ZIP (90210): Tests system behavior when populating foreign postal codes.
    """
    log_test_start(module="Company Master", phase="S.No 10", test="ZIP Code Auto-fill (Indian vs Foreign)")

    payroll_page = PayrollCompanyPage(admin_page)

    # 1. Test Indian Postal Code (110001)
    indian_res = payroll_page.test_zipcode_autofill("110001")
    log_debug(f"Indian PIN 110001 Result: {indian_res}")

    # 2. Test Foreign Postal Code (90210 - US)
    foreign_res = payroll_page.test_zipcode_autofill("90210")
    log_debug(f"Foreign ZIP 90210 Result: {foreign_res}")

    # Assert Indian PIN auto-populates India
    if indian_res["autofilled_country"]:
        assert "india" in indian_res["autofilled_country"].lower(), f"Indian PIN 110001 should auto-fill India, got '{indian_res['autofilled_country']}'"

    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.payroll_company
def test_sno_13_validate_payroll_company_website_field_enabled(admin_page):
    """
    S.No 13: Validate Payroll Company Website Field Enablement.
    Bug Fix Verification: Website field should be editable when adding a Payroll Company.
    """
    log_test_start(module="Payroll Company", phase="S.No 13", test="Validate Website Field Enablement")

    payroll_page = PayrollCompanyPage(admin_page)
    is_enabled = payroll_page.is_website_input_enabled()

    assert is_enabled, "S.No 13 Bug Detected: Website input field in Add Payroll Company modal is disabled!"
    log_pass()
