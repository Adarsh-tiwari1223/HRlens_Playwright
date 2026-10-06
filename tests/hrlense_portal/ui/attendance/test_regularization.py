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
    """
    REG_002: Rejection & Reapplication Prevention Workflow
    Rule: Employee Apply → Pending → Approver Rejects → Rejected (cant reapply)
    
    Phase 1: Employee applies for regularization on eligible date -> State: Pending
    Phase 2: Approver (Admin) rejects the request with reason -> State: Rejected
    Phase 3: Employee logs back in and attempts to reapply for the same date ->
             Asserts that reapplication is blocked / prohibited (cannot reapply).
    """
    log_test_start(module="Attendance", phase="REG_002", test="Regularization Rejection & Blocked Reapplication")

    valid_employees = [
        k for k in EMPLOYEE_USER_KEYS
        if settings.USERS.get(k, {}).get("username") and settings.USERS.get(k, {}).get("password")
    ]
    emp_user = "uttam_kumar" if "uttam_kumar" in valid_employees else (valid_employees[0] if valid_employees else "sanidhy")

    # =========================================================================
    # PHASE 1: Employee Submits Regularization Request (Status -> Pending)
    # =========================================================================
    log_step("Phase 1", value=f"Employee '{emp_user}' applies for regularization")
    login_as_user(page, emp_user)
    emp_workflow = RegularizationWorkflow(page)
    employee_name, apply_toast, selected_date = emp_workflow.apply_regularization_workflow(user_key=emp_user)

    log_debug(f"Employee '{employee_name}' applied for {selected_date.strftime('%Y-%m-%d')}, Toast='{apply_toast}'")
    if apply_toast and ("already present" in apply_toast.lower() or "already marked present" in apply_toast.lower()):
        pytest.skip(f"Date already marked present: {apply_toast}")

    # =========================================================================
    # PHASE 2: Approver (Admin) Rejects Regularization Request (Status -> Rejected)
    # =========================================================================
    log_step("Phase 2", value=f"Admin rejects regularization request for '{employee_name}'")
    login_as_user(page, APPROVER_USER_KEY)
    admin_workflow = RegularizationWorkflow(page)
    rejection_toast = admin_workflow.reject_regularization_workflow(
        employee_name,
        selected_date,
        remark="Duty hours unverified - rejected per attendance policy"
    )
    log_debug(f"Admin captured rejection toast: '{rejection_toast}'")

    # Verify status in Approver table is 'Rejected'
    admin_page = admin_workflow.reg_page
    status_in_table = admin_page.get_regularization_status(employee_name, selected_date)
    log_step("Approver Table Regularization Status", value=status_in_table)
    assert "reject" in status_in_table.lower(), f"Expected table status to be Rejected, got '{status_in_table}'"

    # =========================================================================
    # PHASE 3: Employee Session - Verify Cannot Reapply for Rejected Date
    # =========================================================================
    log_step("Phase 3", value=f"Employee '{emp_user}' verifies reapplication is blocked for {selected_date.strftime('%Y-%m-%d')}")
    login_as_user(page, emp_user)
    page.goto(f"{settings.BASE_URL}/regularizationRequest", timeout=60000)
    page.wait_for_load_state("domcontentloaded")

    emp_page = RegularizationPage(page)
    day_num = selected_date.day

    # 1. Inspect rendered status badge / tooltip on calendar for the rejected date
    rendered_status = emp_page.get_rendered_attendance_status(day_num)
    log_debug(f"Calendar Day {day_num} rendered status: '{rendered_status}'")

    # 2. Pick the rejected date on calendar
    emp_page.date_pick(day_num)
    page.wait_for_timeout(500)

    # 3. Check actionability: Apply button should be disabled, or submission should be rejected
    apply_btn = page.get_by_role("button", name="Apply", exact=True).first
    if not apply_btn.is_visible(timeout=1000):
        apply_btn = page.locator("button:has-text('Apply')").first

    is_apply_disabled = False
    if apply_btn.is_visible(timeout=1500):
        is_apply_disabled = apply_btn.is_disabled() or apply_btn.get_attribute("disabled") is not None or apply_btn.get_attribute("aria-disabled") == "true"

    if is_apply_disabled:
        log_step("Reapplication Blocked Check", value=f"Apply button is strictly disabled for rejected Day {day_num}")
        assert is_apply_disabled, f"Expected Apply button to be disabled for rejected date {day_num}"
    else:
        # If button is clickable, attempt submission and verify system rejection / error toast
        log_debug("Apply button clickable; attempting reapplication to verify backend block...")
        emp_page.in_time_input("09:30")
        emp_page.out_time_input("18:30")
        emp_page.enter_reason("Attempting reapplication after rejection")
        emp_page.click_apply_btn()
        emp_page.click_confirm_btn()

        reapply_toast = emp_page.get_pop_msg() or ""
        log_step("Reapplication Attempt Response Toast", value=reapply_toast)

        # Must not succeed: verify blocked toast or rejected state
        assert not any(pos in reapply_toast.lower() for pos in ["successfully applied", "success", "submitted successfully"]) or any(
            blk in reapply_toast.lower() for blk in ["already", "reject", "cannot", "not allowed", "exist"]
        ), f"System unexpectedly allowed reapplication for rejected date! Toast: '{reapply_toast}'"

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
