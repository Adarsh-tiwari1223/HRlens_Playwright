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


def pytest_generate_tests(metafunc):
    """
    Dynamically generates test parameters for 'target_employee_name':
    - If user passed --employee="Name", generates [Name]
    - If user passed -k "Name", generates [Name] so -k matches the test id during collection!
    - Otherwise, generates ["auto"] with id "first_eligible" to pick dynamically at runtime.
    """
    if "target_employee_name" in metafunc.fixturenames:
        emp_cli = metafunc.config.getoption("--employee", default=None)
        if emp_cli:
            metafunc.parametrize("target_employee_name", [emp_cli], ids=[emp_cli.lower().replace(" ", "_")])
            return

        k_expr = (metafunc.config.getoption("-k", default="") or "").strip()
        ignored_keywords = {"test_", "accountant", "process", "buyout", "resignation", "ui", "and", "or", "not", "inspection", "finance", "clearance"}
        clean_parts = [p.replace('"', '').replace("'", "").strip() for p in k_expr.split() if p.lower() not in ignored_keywords and len(p) > 1]

        if clean_parts:
            target = " ".join(clean_parts)
            metafunc.parametrize("target_employee_name", [target], ids=[target.lower().replace(" ", "_")])
        else:
            metafunc.parametrize("target_employee_name", ["auto"], ids=["first_eligible"])


@pytest.mark.ui
@pytest.mark.accountant_process_buyout
@pytest.mark.resignation
def test_accountant_process_buyout_flow(target_employee_name, get_accountant_resignation_workflow):
    """
    Accountant Process Buyout Flow:
    1. If -k <employee_name> or --employee is provided, targets that specific employee.
    2. Otherwise ('auto'), dynamically discovers the first eligible employee waiting in 'HR Approved' status.
    3. Accountant logs in, searches employee on /accounts-buyout-processing, opens modal.
    4. Reads modal values, validates formula/deductions, confirms recovery, and approves.
    """
    acc_wf = get_accountant_resignation_workflow()

    if target_employee_name == "auto":
        resolved_name = acc_wf.get_first_eligible_buyout_employee()
        if not resolved_name:
            pytest.skip("No employees currently waiting in 'HR Approved' status for Accountant buyout processing.")
    else:
        resolved_name = target_employee_name

    logger.info(f"[EXECUTION] Processing Accountant Buyout for employee: '{resolved_name}'")
    result = acc_wf.process_accountant_buyout_workflow(
        employee_name=resolved_name,
        calculated_salary="0",
        remarks="Buyout Approved & Dues Cleared by Accountant",
        confirm_recovery=True,
        approve=True
    )

    assert result.get("success"), f"Failed to process Buyout modal for '{resolved_name}'"
    toast_msg = str(result.get("toast", "")).strip()
    assert toast_msg != "", "Toast message must be captured after Accountant Buyout approval"
    assert "required" not in toast_msg.lower(), f"Accountant buyout approval failed with validation error toast: '{toast_msg}'"
    assert "approved" in toast_msg.lower() or "success" in toast_msg.lower() or "processed" in toast_msg.lower(), \
        f"Expected buyout approval success toast, got: '{toast_msg}'"
    logger.info(f"[PASS ACCOUNTANT] Accountant successfully processed Buyout for '{resolved_name}'! Toast: '{toast_msg}'")




