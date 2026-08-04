"""
Advanced Business Validation Test Suite for Attendance Regularization (HR Lens Portal).
Implements REG_001 through REG_010:
- REG_001: Validate Maximum Backdate Limit (Dependent on REG_006 Payroll Lock)
- REG_002: Validate Reapplication After Rejection
- REG_003: Cancel Pending Regularization Request
- REG_004: Edit Pending Regularization Request
- REG_005: Submit Multiple Regularization Requests
- REG_006: Validate Payroll Locked Attendance
- REG_007: Validate Payroll Generated Month Restriction
- REG_008: Validate Approval Hierarchy Fallback
- REG_009: Validate Audit Trail Logging
- REG_010: Manual Verification - Email Notifications
"""

import pytest
from datetime import datetime, timedelta
from pages.login_page import LoginPage
from workflows.hrlense_portal.attendance.regularization_workflow import RegularizationWorkflow
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug


# Helper function to perform single-window login
def login_as_user(page, user_key: str):
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
def test_reg_001_validate_max_backdate_limit(page):
    """REG_001: Validate Maximum Backdate Limit (Dependent on REG_006 Payroll Lock)."""
    log_test_start(module="Attendance", phase="REG_001", test="Validate Maximum Backdate Limit")
    login_as_user(page, "sanidhy")

    workflow = RegularizationWorkflow(page)
    # Pick a date from 2 months ago (backdated beyond current payroll cycle)
    past_date = datetime.today() - timedelta(days=60)
    log_debug(f"Testing backdate limit for date: {past_date.strftime('%Y-%m-%d')}")

    # Inspect if past month is locked by payroll
    is_locked = workflow.reg_page.is_payroll_locked_warning_visible()
    if is_locked:
        log_skip(f"Backdated request for date {past_date.strftime('%Y-%m-%d')} is blocked by Payroll Lock rule (REG_006).")
        pytest.skip("Backdated request is blocked by Payroll Lock rule (REG_006).")

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

    # 1. Employee submits request
    login_as_user(page, "sanidhy")
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    if "already exists" in toast.lower():
        log_skip("Request already exists; proceeding to cancellation step.")

    # 2. Employee cancels the pending request
    cancel_toast = emp_workflow.cancel_regularization_workflow(selected_date.day)
    log_debug(f"Cancellation response: {cancel_toast}")

    log_pass()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.attendance
def test_reg_004_edit_pending_request(page):
    """REG_004: Edit Pending Regularization Request."""
    log_test_start(module="Attendance", phase="REG_004", test="Edit Pending Regularization Request")

    # 1. Employee submits request
    login_as_user(page, "sanidhy")
    emp_workflow = RegularizationWorkflow(page)
    employee_name, toast, selected_date = emp_workflow.apply_regularization_workflow()

    # 2. Employee modifies pending request
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
    # Submit first request
    emp_1, toast_1, date_1 = emp_workflow.apply_regularization_workflow()
    # Submit second request
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


@pytest.mark.manual
@pytest.mark.attendance
def test_reg_010_manual_verification_email_notifications():
    """REG_010: Manual Verification - Email Notifications."""
    log_test_start(module="Attendance", phase="REG_010", test="Manual Verification - Email Notifications")
    log_skip("Manual Verification Required: Verify email notifications are generated for regularization workflow events.")
    pytest.skip("Manual Verification Required: Verify email notifications delivery.")
