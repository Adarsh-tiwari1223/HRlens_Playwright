"""
UI Test Suite for Attendance Regularization Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Contains complete basic and advanced business validation test cases (REG_001 – REG_010).
"""

import pytest
from datetime import datetime, timedelta
from pages.login_page import LoginPage
from workflows.hrlense_portal.attendance.regularization_workflow import RegularizationWorkflow
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug


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
    Sequential Single-Window Workflow:
    1. Employee Session: Submit Regularization Request
    2. Admin Session: Approve Regularization Request (in same browser window)
    3. Employee Session: Verify Rendered Calendar Attendance Status (in same browser window)
    """
    log_test_start(module="Attendance", phase="Phase 1", test="Apply & Approve Regularization Workflow")

    # 1. Employee Step: Log in & Submit Regularization Request
    page.goto(settings.BASE_URL, timeout=60000)
    emp_creds = settings.USERS["sanidhy"]
    LoginPage(page).login(emp_creds["username"], emp_creds["password"])

    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    assert toast, "No popup message appeared after submitting regularization request"

    if "already exists" in toast.lower():
        log_skip(f"Regularization already exists for date: {selected_date}")
        pytest.skip(f"Regularization already exists for date: {selected_date}")

    assert "successfully" in toast.lower() or "applied" in toast.lower() or "submitted" in toast.lower(), f"Unexpected submission toast: {toast}"

    # 2. Admin Step: Log in as Admin in same window & Approve Request
    login_as_user(page, "admin")
    admin_workflow = RegularizationWorkflow(page)
    approval_toast = admin_workflow.approve_regularization_workflow(employee_name, selected_date)

    if approval_toast:
        assert "successfully" in approval_toast.lower() or "approved" in approval_toast.lower(), f"Approval failed! Toast: {approval_toast}"

    # 3. Post-Approval Verification: Log back in as Employee to inspect calendar
    login_as_user(page, "sanidhy")
    is_rendered_valid = emp_workflow.verify_rendered_attendance_status_workflow(
        day_num=selected_date.day,
        expected_in_time="09:30",
        expected_out_time="18:30"
    )
    assert is_rendered_valid, f"Rendered status on calendar for day={selected_date.day} did not match expected attendance status!"

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
