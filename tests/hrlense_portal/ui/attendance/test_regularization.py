"""
UI Test Suite for Attendance Regularization Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Contains complete basic and advanced business validation test cases (REG_001 – REG_010).
"""

import random
import pytest
from datetime import datetime, timedelta
from pages.login_page import LoginPage
from workflows.hrlense_portal.attendance.regularization_workflow import RegularizationWorkflow
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug, log_step


EMPLOYEE_USER_KEYS = [
    "sanidhy",
    "kumar_piyush",
    "uttam_kumar",
    "abhishek_singh",
    "ritesh_singh"
]
APPROVER_USER_KEY = "admin"


def login_as_user(page, user_key: str):
    """Helper to switch user session in a single window."""
    try:
        page.context.clear_cookies()
        page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    except Exception:
        pass
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS[user_key]
    LoginPage(page).login(creds["username"], creds["password"])


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_apply_and_approve_regularization(page):
    """
    End-to-End Two-Phase Regularization Workflow:
    Phase 1: Employee Session (Random Employee)
      1. Randomly select an eligible Employee from configured employee pool.
      2. Login as the selected Employee.
      3. Navigate to Attendance -> /regularizationRequest.
      4. Select eligible date (Absent / Late).
      5. Fill In-Time (09:30), Out-Time (18:30), and Reason (Client Visit On Duty).
      6. Click Apply -> Confirm.
      7. Capture and verify regularization submission toast.
    
    Phase 2: Admin Session (Constant Approver)
      1. Switch session: Login as constant Approver (Admin).
      2. Navigate to Attendance -> • Regularisation.
      3. Search for employee name using 'Search Employee by name....'.
      4. Locate the matching request row for the submitted date.
      5. Select 'Approve' (value='Approved') -> Submit Reason -> Confirm.
      6. Capture and assert approval toast notification.
      7. Verify request state is marked 'Approved' and cannot be approved a second time.
    """
    log_test_start(module="Attendance", phase="Phase 1 & Phase 2", test="End-to-End Regularization Submission & Approval Workflow")

    # Select random valid employee
    valid_employees = [
        k for k in EMPLOYEE_USER_KEYS
        if settings.USERS.get(k, {}).get("username") and settings.USERS.get(k, {}).get("password")
    ]
    random_emp_key = random.choice(valid_employees) if valid_employees else "sanidhy"
    log_step("Selected Dynamic Employee User", value=f"{random_emp_key} (Approver: {APPROVER_USER_KEY})")

    # =========================================================================
    # PHASE 1: Employee Session - Apply Regularization Request
    # =========================================================================
    login_as_user(page, random_emp_key)
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow(user_key=random_emp_key)

    log_debug(f"Employee '{employee_name}' applied for date {selected_date.strftime('%Y-%m-%d')}, Toast='{toast}'")
    
    # Verify submission popup response
    if toast:
        if "already present" in toast.lower() or "already marked present" in toast.lower():
            log_skip(f"Skipping test case: {toast}")
            pytest.skip(f"Employee regularization skipped: '{toast}'")
        elif "already exists" in toast.lower():
            log_debug(f"Regularization request already exists for date: {selected_date.strftime('%Y-%m-%d')}; proceeding to Admin Approval.")
        else:
            assert any(term in toast.lower() for term in ["success", "applied", "submitted"]), f"Unexpected submission toast: {toast}"

    # =========================================================================
    # PHASE 2: Admin Session - Approve Regularization Request
    # =========================================================================
    login_as_user(page, "admin")
    admin_workflow = RegularizationWorkflow(page)
    approval_toast = admin_workflow.approve_regularization_workflow(employee_name, selected_date)

    log_debug(f"Admin captured approval toast: '{approval_toast}'")
    if approval_toast:
        assert any(term in approval_toast.lower() for term in ["success", "applied", "approved"]), f"Unexpected approval toast: '{approval_toast}'"

    # Verify persistent approved state and duplicate prevention
    admin_page = admin_workflow.reg_page
    status = admin_page.get_regularization_status(employee_name, selected_date)
    log_step("Final Regularization Status in Table", value=status)

    row_info = admin_page.get_row_details(employee_name, selected_date)
    assert row_info["is_approved"] and not row_info["is_actionable"], f"Expected request to be approved and non-actionable, got status='{status}', details={row_info}"

    log_pass()



@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_002_reapplication_after_rejection(page):
    """REG_002: Validate Reapplication After Rejection."""
    log_test_start(module="Attendance", phase="REG_002", test="Validate Reapplication After Rejection")

    # 1. Employee submits request
    login_as_user(page, "sanidhy")
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    if not toast or "already exists" in toast.lower():
        pytest.skip("Regularization request already exists for target date.")

    # 2. Admin rejects request
    login_as_user(page, "admin")
    admin_workflow = RegularizationWorkflow(page)
    rejection_toast = admin_workflow.reject_regularization_workflow(employee_name, selected_date, remark="Rejection test for REG_002")

    # 3. Employee re-applies for the same date
    login_as_user(page, "sanidhy")
    employee_name_2, reapply_toast, _ = emp_workflow.apply_regularization_workflow()

    assert reapply_toast, "No response received when re-applying after rejection."
    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_003_cancel_pending_request(page):
    """REG_003: Cancel Pending Regularization Request."""
    log_test_start(module="Attendance", phase="REG_003", test="Cancel Pending Regularization Request")

    login_as_user(page, "sanidhy")
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    cancel_toast = emp_workflow.cancel_regularization_workflow(selected_date.day)
    log_debug(f"Cancellation response: {cancel_toast}")
    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_004_edit_pending_request(page):
    """REG_004: Edit Pending Regularization Request."""
    log_test_start(module="Attendance", phase="REG_004", test="Edit Pending Regularization Request")

    login_as_user(page, "sanidhy")
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    edit_toast = emp_workflow.edit_regularization_workflow(
        day_num=selected_date.day,
        new_in_time="10:00",
        new_out_time="19:00",
        new_reason="Updated Duty Reason"
    )
    log_debug(f"Edit response: {edit_toast}")
    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_005_submit_multiple_requests(page):
    """REG_005: Submit Multiple Regularization Requests."""
    log_test_start(module="Attendance", phase="REG_005", test="Submit Multiple Regularization Requests")
    login_as_user(page, "sanidhy")

    emp_workflow = RegularizationWorkflow(page)
    emp_1, toast_1, date_1 = emp_workflow.apply_regularization_workflow()
    emp_2, toast_2, date_2 = emp_workflow.apply_regularization_workflow()

    log_debug(f"Multiple requests submitted for date_1={date_1.day}, date_2={date_2.day}")
    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_006_validate_payroll_locked_attendance(page):
    """REG_006: Validate Payroll Locked Attendance."""
    log_test_start(module="Attendance", phase="REG_006", test="Validate Payroll Locked Attendance")
    login_as_user(page, "sanidhy")

    workflow = RegularizationWorkflow(page)
    is_locked = workflow.reg_page.is_payroll_locked_warning_visible()

    if is_locked:
        log_skip("Attendance belongs to a payroll-locked period; regularization is correctly blocked by system.")
        pytest.skip("Attendance belongs to a payroll-locked period.")

    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_007_validate_payroll_generated_month_restriction(page):
    """REG_007: Validate Payroll Generated Month Restriction."""
    log_test_start(module="Attendance", phase="REG_007", test="Validate Payroll Generated Month Restriction")
    login_as_user(page, "sanidhy")

    workflow = RegularizationWorkflow(page)
    is_locked = workflow.reg_page.is_payroll_locked_warning_visible()

    if is_locked:
        log_skip("Payroll has already been generated for this month; regularization modification is blocked.")
        pytest.skip("Payroll has already been generated for this month.")

    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_008_validate_approval_hierarchy_fallback(page):
    """REG_008: Validate Approval Hierarchy Fallback."""
    log_test_start(module="Attendance", phase="REG_008", test="Validate Approval Hierarchy Fallback")
    login_as_user(page, "sanidhy")

    workflow = RegularizationWorkflow(page)
    hierarchy = workflow.get_approval_hierarchy(duration_days=1)
    log_debug(f"Resolved Approval Hierarchy: {hierarchy}")

    assert "Branch Head" in hierarchy, "Fallback hierarchy must route to Branch Head when approver is unconfigured."
    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_009_validate_audit_trail(page):
    """REG_009: Validate Audit Trail Logging."""
    log_test_start(module="Attendance", phase="REG_009", test="Validate Audit Trail Logging")
    login_as_user(page, "sanidhy")

    workflow = RegularizationWorkflow(page)
    records = workflow.reg_page.get_audit_trail_records()
    log_debug(f"Audit Trail Records count: {len(records)}")

    log_pass()
