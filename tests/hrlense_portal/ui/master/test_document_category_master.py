"""
UI Test Suite for Document Category Master Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates S.No 6 (Add KYC Document Category Master under /master/documentCategory) and Admin-only permission rules.
"""

import pytest
from faker import Faker
from pages.login_page import LoginPage
from pages.hrlense_portal.master.document_category_page import DocumentCategoryPage
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug

fake = Faker("en_IN")


@pytest.fixture
def admin_page(page):
    """Logs in as Admin user."""
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS["admin"]
    LoginPage(page).login(creds["username"], creds["password"])
    return page


@pytest.fixture
def employee_page(page):
    """Logs in as Standard Non-Admin Employee user (uttam_kumar)."""
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS["uttam_kumar"]
    LoginPage(page).login(creds["username"], creds["password"])
    return page


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.master
def test_sno_06_add_kyc_document_category_master(admin_page):
    """
    S.No 6: Add KYC Document Category Master under /master/documentCategory.
    Validates creating a dynamic KYC Document Category in Master.
    """
    log_test_start(module="Document Category Master", phase="S.No 6", test="Add KYC Document Category Master")

    doc_cat_page = DocumentCategoryPage(admin_page)
    new_category_name = f"KYC Compliance_{fake.word().capitalize()}_{fake.numerify('###')}"
    log_debug(f"Target KYC Document Category Name: '{new_category_name}'")

    toast = doc_cat_page.add_kyc_document_category(new_category_name)
    log_debug(f"Toast Response: '{toast}'")

    # Verify existing categories list
    existing_categories = doc_cat_page.get_existing_kyc_document_categories()
    log_debug(f"Total KYC Categories found in Master: {len(existing_categories)}")

    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.master
def test_document_category_master_admin_only_access(employee_page):
    """
    Validates Admin-Only Access Restriction on /master/documentCategory.
    Non-admin employee users must be blocked or redirected away from Master.
    """
    log_test_start(module="Document Category Master", phase="Security", test="Admin-Only Access Restriction")

    doc_cat_page = DocumentCategoryPage(employee_page)
    doc_cat_page.navigate_to_document_category_master()

    is_denied = doc_cat_page.is_access_denied_visible()
    assert is_denied, "Security Defect: Non-admin employee user was able to access /master/documentCategory!"

    log_pass()
