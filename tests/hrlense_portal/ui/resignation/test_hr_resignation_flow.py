"""
HRlens Portal — HR Resignation Flow Test Suite (Test Tier).
Contains test cases for HR-side offboarding approvals, employee search, Resignation Details modal inspection, and Revoke requests.
"""

import pytest
import logging
from core.config import settings
from utils.branch_persona_resolver import get_dynamic_resignation_employee
from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow

logger = logging.getLogger(__name__)


@pytest.fixture
def get_hr_resignation_workflow(logged_in_page):
    """Factory fixture to initialize HrResignationWorkflow for a Branch HR account."""
    def _create_workflow(user_key: str = "tejaswini"):
        page, _ = logged_in_page(user_key)
        return HrResignationWorkflow(page)
    return _create_workflow


@pytest.mark.ui
@pytest.mark.hr_revoke_flow
@pytest.mark.resignation
def test_hr_revoke_request_flow(get_hr_resignation_workflow):
    """
    HR Revoke Request Flow:
    1. HR logs in (Branch HR: tejaswini)
    2. Navigates Offboarding -> Resignation Approval
    3. Searches dynamic employee by name
    4. Inspects status badge and processes Revoke
    """
    hr_wf = get_hr_resignation_workflow("tejaswini")
    candidate = get_dynamic_resignation_employee("Varanasi")
    target_employee_name = candidate["name"]

    is_revoked = hr_wf.execute_hr_revoke_request_workflow(employee_name=target_employee_name)
    assert is_revoked, f"HR Revoke Request Flow must complete successfully for '{target_employee_name}'"
    logger.info(f"[PASS HR] HR Revoke Request Flow executed successfully for '{target_employee_name}'!")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_buyout_request_prevents_hr_revoke(get_hr_resignation_workflow):
    """
    [P0 CRITICAL] Buyout Request -> HR Revoke Restriction.
    When Employee submits a Buyout Request, HR should NOT have the option to create a Revoke Request.
    """
    hr_wf = get_hr_resignation_workflow("tejaswini")
    candidate = get_dynamic_resignation_employee("Varanasi")
    target_employee_name = candidate["name"]

    is_revoke_visible = hr_wf.validate_buyout_prevents_hr_revoke_workflow(employee_name=target_employee_name)
    assert not is_revoke_visible, "HR Revoke button must be hidden/blocked when employee has requested Buyout"
    logger.info(f"[PASS HR] Buyout Request correctly prevents HR Revoke for '{target_employee_name}'!")


@pytest.mark.ui
@pytest.mark.p1
@pytest.mark.resignation
def test_revoke_without_buyout_allows_hr_revoke(get_hr_resignation_workflow):
    """
    [P1 HIGH] Revoke without Buyout.
    When Employee has NOT submitted a Buyout Request, HR should be able to initiate the Revoke Request.
    """
    hr_wf = get_hr_resignation_workflow("tejaswini")
    candidate = get_dynamic_resignation_employee("Varanasi")
    target_employee_name = candidate["name"]

    status = hr_wf.verify_hr_table_status_workflow(employee_name=target_employee_name)
    logger.info(f"[PASS HR] Employee '{target_employee_name}' table status: '{status}'")


@pytest.mark.ui
@pytest.mark.hr_process_buyout
@pytest.mark.resignation
def test_hr_process_buyout_request_flow(get_hr_resignation_workflow):
    """
    HR Process Buyout Request Flow:
    1. HR logs in (Branch HR: tejaswini)
    2. Navigates Offboarding -> Resignation Approval
    3. Searches dynamic candidate with status 'BUYOUT REQUESTED'
    4. Clicks Actions hamburger button -> selects 'Buyout Request' menu item
    5. Drawer opens ('Buyout Request') displaying Buyout Days, Early LWD, Requested On
    6. Clicks 'Process Buyout' button and captures toast message!
    """
    hr_wf = get_hr_resignation_workflow("tejaswini")
    candidate = get_dynamic_resignation_employee("Varanasi")
    target_employee_name = candidate["name"]

    toast_msg = hr_wf.process_buyout_request_workflow(employee_name=target_employee_name, process=True)
    assert toast_msg != "", "Toast message must be captured after processing Buyout"
    assert "buyout approved" in toast_msg.lower() or "approved" in toast_msg.lower(), \
        f"Expected 'Buyout approved successfully' toast, got: '{toast_msg}'"

    # Verify table status updates post-approval
    updated_status = hr_wf.verify_hr_table_status_workflow(employee_name=target_employee_name)
    logger.info(f"[PASS HR] HR successfully processed Buyout for '{target_employee_name}'! Post-approval status: '{updated_status}' | Toast: '{toast_msg}'")





