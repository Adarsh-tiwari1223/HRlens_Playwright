"""
HRlens Portal — Accountant Resignation Flow Test Suite (Test Tier).
Contains test cases for Accountant / Finance clearance, buyout amount calculations, and offboarding settlement checks.
"""

import pytest
import logging
from core.config import settings
from workflows.hrlense_portal.resignation.accountant_resignation_workflow import AccountantResignationWorkflow

logger = logging.getLogger(__name__)


@pytest.fixture
def get_accountant_resignation_workflow(logged_in_page):
    """Factory fixture to initialize AccountantResignationWorkflow for an Accountant account."""
    def _create_workflow(user_key: str = "admin"):
        page, _ = logged_in_page(user_key)
        return AccountantResignationWorkflow(page)
    return _create_workflow


@pytest.mark.ui
@pytest.mark.accountant_clearance
@pytest.mark.resignation
def test_accountant_finance_clearance_inspection(get_accountant_resignation_workflow):
    """
    Accountant Finance Clearance Inspection Flow:
    1. Accountant logs in
    2. Navigates Offboarding -> Finance Clearance tab
    3. Inspects employee buyout settlement and pending dues status
    """
    acc_wf = get_accountant_resignation_workflow()
    target_employee_name = "Abhishek Singh"

    result = acc_wf.inspect_employee_buyout_settlement_workflow(employee_name=target_employee_name)
    logger.info(f"[PASS ACCOUNTANT] Finance Clearance inspection executed for '{target_employee_name}'! Result: {result}")


@pytest.mark.ui
@pytest.mark.accountant_process_buyout
@pytest.mark.resignation
@pytest.mark.parametrize("target_employee_name", ["Sanidhy Tiwari", "Adarsh Tiwari"], ids=["sanidhy", "adarsh_tiwari"])
def test_accountant_process_buyout_flow(get_accountant_resignation_workflow, target_employee_name):
    """
    Accountant Process Buyout Flow:
    1. Accountant logs in
    2. Navigates to https://stg-hrlense.jobvritta.com/accounts-buyout-processing
    3. Searches employee (target_employee_name) in table (status: 'HR Approved')
    4. Clicks Action icon to open 'Process Buyout' modal
    5. Reads Leave Balance, Leave Payout, Calculated Salary, Buyout Amount, Total Amount
    6. Validates financial formula: Total Amount = (Leave Payout + Calculated Salary) - Buyout Amount
    7. Fills Calculated Salary, toggles 'Recovery Confirmed' checkbox, enters Remarks
    8. Clicks 'Approve' button and captures success toast message!
    """
    acc_wf = get_accountant_resignation_workflow()

    result = acc_wf.process_accountant_buyout_workflow(
        employee_name=target_employee_name,
        calculated_salary="1000",
        remarks="Buyout Approved & Dues Cleared by Accountant",
        confirm_recovery=True,
        approve=True
    )


    assert result.get("success"), f"Failed to open Process Buyout modal for '{target_employee_name}'"
    toast_msg = str(result.get("toast", "")).strip()
    assert toast_msg != "", "Toast message must be captured after Accountant Buyout approval"
    assert "required" not in toast_msg.lower(), f"Accountant buyout approval failed with validation error toast: '{toast_msg}'"
    assert "approved" in toast_msg.lower() or "success" in toast_msg.lower() or "processed" in toast_msg.lower(), \
        f"Expected buyout approval success toast, got: '{toast_msg}'"
    logger.info(f"[PASS ACCOUNTANT] Accountant successfully processed Buyout for '{target_employee_name}'! Toast: '{toast_msg}'")




