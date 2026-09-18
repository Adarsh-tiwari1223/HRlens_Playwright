"""
HRlens Portal — IT Person Resignation Flow Test Suite (Test Tier).
Contains test cases for IT Person-side offboarding clearance, asset recovery inspection, and IT clearance approval.
"""

import pytest
import logging
from core.config import settings
from workflows.hrlense_portal.resignation.it_resignation_workflow import ItResignationWorkflow

logger = logging.getLogger(__name__)


from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage


@pytest.fixture
def get_it_resignation_workflow(logged_in_page):
    """Factory fixture to initialize ItResignationWorkflow for a Branch IT Person account."""
    def _create_workflow(user_key: str = "it_varanasi_tejasav"):
        page, _ = logged_in_page(user_key)
        return ItResignationWorkflow(page)
    return _create_workflow


@pytest.mark.ui
@pytest.mark.asset_assignment
@pytest.mark.resignation
@pytest.mark.parametrize("target_employee_name", ["Uttam Kumar"], ids=["uttam_kumar"])
def test_admin_assign_asset_and_employee_accept_flow(logged_in_page, target_employee_name):
    """
    Direct Asset Assignment & Acceptance Flow:
    1. Admin logs in -> directly assigns an available asset to Uttam Kumar.
    2. Uttam Kumar logs in -> accepts the assigned asset on /asset-request.
    """
    logger.info(f"=== STEP 1: Admin Assigning Asset to '{target_employee_name}' ===")
    admin_page, _ = logged_in_page("admin")
    assign_page = AssetAssignmentPage(admin_page)
    assign_page.navigate_to_asset_assignment()
    assign_page.click_assign_asset()

    assigned_code = assign_page.fill_assignment_details(
        employee_name=target_employee_name,
        category="Audio Visual",
        sub_category="Conference Speakerphone",
        remarks="Asset assigned for offboarding clearance validation"
    )
    assign_page.click_submit_assignment()
    toast = assign_page.wait_for_toast_message()
    logger.info(f"Admin Assignment Toast: '{toast}' | Code: '{assigned_code}'")

    logger.info(f"=== STEP 2: '{target_employee_name}' Accepting Asset ===")
    emp_page, _ = logged_in_page("uttam_kumar")
    req_page = AssetRequestPage(emp_page)
    req_page.navigate_to_asset_request()
    accepted = req_page.accept_asset(assigned_code if assigned_code != "ASSET" else None)
    logger.info(f"Asset Acceptance Result: {accepted}")
    assert accepted, f"Failed to accept assigned asset for '{target_employee_name}'"


@pytest.mark.ui
@pytest.mark.it_clearance
@pytest.mark.resignation
@pytest.mark.parametrize("target_employee_name", ["Uttam Kumar"], ids=["uttam_kumar"])
def test_it_person_asset_clearance_inspection(get_it_resignation_workflow, target_employee_name):
    """
    IT Person Asset Clearance Flow:
    1. IT Person logs in (it_varanasi_ashutosh)
    2. Navigates Offboarding -> Resignation Approval / IT Task Clearance
    3. Searches resigning employee (target_employee_name)
    4. Dynamically processes IT Clearance:
       - If employee HAS assets: Inspects asset condition & confirms return.
       - If employee HAS NO assets: Verifies and completes task directly.
    """
    it_wf = get_it_resignation_workflow("it_varanasi_tejasav")

    result = it_wf.inspect_and_clear_employee_assets_workflow(
        employee_name=target_employee_name,
        asset_condition="Good Condition",
        remarks="IT Asset clearance verified & completed"
    )

    assert result.get("success"), f"Failed IT Clearance for '{target_employee_name}'"
    logger.info(f"[PASS IT] IT Asset Clearance executed for '{target_employee_name}'! Has Assets: {result.get('has_assets')}, Toast: '{result.get('toast')}'")



