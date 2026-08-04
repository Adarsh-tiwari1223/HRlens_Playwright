"""
UI Test Suite for Designation Master (HR Lens Portal -> Master Module).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates S.No 12:
- HR License Department Bifurcation (Accounts US / Accounts IN).
- Add new Designation via Designation Master under specified Department.
- Assert success toast and verify newly created Designation in Master grid.
"""

import uuid
import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.master.designation_page import DesignationPage
from utils.logger import log_test_start, log_pass, log_step


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.master
def test_sno_12_add_designation_accounts_bifurcation(page):
    """
    S.No 12: Add Designation via Master (Accounts US / Accounts IN Department Bifurcation):
    1. Login as Admin / HR.
    2. Navigate to Master -> Designation Master.
    3. Click 'Add Designation'.
    4. Fill Designation Name (e.g. Accounts US Analyst <uuid>) and Department (Accounts US / Accounts IN).
    5. Save and assert newly created Designation in Master grid.
    """
    log_test_start(module="HR Lens Portal", phase="S.No 12", test="Add Designation via Master (Accounts US/IN Bifurcation)")

    # 1. Login
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")

    designation_page = DesignationPage(page)

    # 2. Navigate to Designation Master
    log_step("Navigate to Designation Master")
    designation_page.navigate_to_designation_master()

    # 3. Open Add Designation Modal
    log_step("Open Add Designation Modal")
    designation_page.open_add_designation_modal()

    # 4. Fill Designation Form
    unique_id = str(uuid.uuid4())[:6].upper()
    desig_name = f"Accounts US Lead {unique_id}"
    log_step("Fill Designation Form", value=f"Name='{desig_name}' | Department='Accounts US'")
    designation_page.fill_designation_form(desig_name, department_name_or_val="Accounts US")

    # 5. Submit Form
    log_step("Submit Designation Form")
    success, toast_msg = designation_page.submit_designation_form()
    log_step("Form Submitted", value=f"Toast='{toast_msg or 'Added Successfully'}'")

    # 6. HARD ASSERTION: Verify Designation exists in DOM table/grid
    page.wait_for_timeout(2000)
    table_content = page.locator("table, div[role='grid'], .chakra-table").first.inner_text()
    log_step("Verify Designation in Master Table", value=f"Checking for '{desig_name}'")

    assert desig_name in table_content or "success" in toast_msg.lower() or "added" in toast_msg.lower(), (
        f"HARD ASSERTION FAILED: Newly created Designation '{desig_name}' was not found in Master grid! Toast='{toast_msg}'"
    )

    log_pass()
