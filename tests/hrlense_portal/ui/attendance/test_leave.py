from core.config.settings import logger
import pytest
from datetime import date, timedelta
from pages.hrlense_portal.attendance.leave_page import LeavePage
from core.config import settings
from testdata.static.Leave import Leave


import random

EMPLOYEE_USERS = ["kumar_piyush", "uttam_kumar", "abhishek_singh"]



@pytest.fixture(scope="module")
def employee_context(logged_in_page):
    valid_users = [u for u in EMPLOYEE_USERS if settings.USERS.get(u, {}).get("username")]
    selected_user = random.choice(valid_users) if valid_users else settings.EMPLOYEE_USER
    page, context = logged_in_page(selected_user)
    yield page



@pytest.fixture(scope="module")
def approver_context(logged_in_page, submitted_leave):
    approver_key = settings.APPROVERS.get(submitted_leave["approver_name"])
    assert approver_key, f"No approver mapping for '{submitted_leave['approver_name']}' — add to settings.APPROVERS"
    page, context = logged_in_page(approver_key)
    yield page


@pytest.fixture(scope="module")
def submitted_leave(employee_context):
    from workflows.hrlense_portal.attendance.leave_workflow import LeaveWorkflow

    try:
        employee_context.goto(settings.BASE_URL)
    except Exception:
        pass

    workflow = LeaveWorkflow(employee_context)
    result = workflow.apply_leave_and_verify_status_tab_workflow(
        leave_type="Vacation Leave",
        from_offset=settings.LEAVE_FROM_OFFSET,
        to_offset=settings.LEAVE_TO_OFFSET
    )

    toast = result["toast"]
    from_date = result["from_date"]
    to_date = result["to_date"]

    if "already exists" in toast.lower():
        dates = workflow.leave_page.extract_dates_from_toast(toast)
        from_date, to_date = dates if dates else (from_date, to_date)
        if "approved" in toast.lower():
            workflow.handle_already_approved_leave(toast)
    elif "successfully" not in toast.lower():
        pytest.fail(f"Unexpected toast: {toast}")

    approver_name = workflow.leave_page.get_approver_name()

    return {
        "employee_name": workflow.leave_page.get_logged_in_employee_name(),
        "approver_name": approver_name,
        "from_date": from_date,
        "to_date": to_date,
    }


@pytest.fixture(scope="module")
def approver_login(approver_context, submitted_leave):
    leave = LeavePage(approver_context)
    leave.click_attendance()
    leave.click_leave_request(submitted_leave["employee_name"])
    return {
        "leave_page": leave,
        "employee_name": submitted_leave["employee_name"],
        "from_date": submitted_leave["from_date"],
        "to_date": submitted_leave["to_date"],
    }


from playwright.sync_api import expect


@pytest.fixture(autouse=False)
def leave_page(employee_context):
    employee_context.reload()
    leave = LeavePage(employee_context)
    leave.click_my_leave()
    expect(employee_context.locator("p:has-text('Leave Apply')")).to_be_visible()
    leave.click_leave_apply()
    return leave



# ─── Happy Path ───────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.smoke
@pytest.mark.regression
def test_full_leave_apply_and_approve_workflow(logged_in_page, employee_context):
    """
    Unified End-to-End Leave Workflow:
    1. Apply leave -> Capture raw toast -> Dynamically verify UI in matching status tab (Approved/Rejected/Pending).
    2. If raw toast status != 'approved':
       - Log in via Approver Manager (e.g. Vivek Singh).
       - Locate leave request & approve.
       - Capture approval toast notification & assert pass!
    """
    from workflows.hrlense_portal.attendance.leave_workflow import LeaveWorkflow

    employee_context.goto(settings.BASE_URL)
    leave_type = Leave.shuffled()[0]["leave_type"]

    workflow = LeaveWorkflow(employee_context)
    result = workflow.execute_full_leave_apply_and_approval_flow(
        logged_in_page_func=logged_in_page,
        leave_type=leave_type,
        from_offset=settings.LEAVE_FROM_OFFSET,
        to_offset=settings.LEAVE_TO_OFFSET
    )

    assert result["is_located"], f"Submitted leave request for '{leave_type}' was NOT found in target status tab UI"
    if "approved" not in result["toast"].lower():
        assert result.get("approved"), f"Leave approval failed for employee. Toast: '{result.get('approval_toast')}'"
        logger.info(f"[SUCCESS] E2E Leave Apply & Approve Flow completed successfully!")


# ─── Validation Tests ─────────────────────────────────────────────────────────

@pytest.mark.regression
@pytest.mark.leave_validation
def test_backdate_not_selectable(leave_page):
    back_date = date.today() - timedelta(days=1)
    try:
        leave_page._select_date_from_calendar(leave_page.FROM_DATE_TRIGGER, back_date)
        pytest.fail("Back date should not be selectable")
    except AssertionError as e:
        assert "not selectable" in str(e).lower()


@pytest.mark.regression
@pytest.mark.leave_validation
def test_duplicate_leave_shows_error(leave_page):
    from_date = date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)
    to_date = from_date + timedelta(days=settings.LEAVE_TO_OFFSET)

    leave_page._select_date_from_calendar(leave_page.FROM_DATE_TRIGGER, from_date)
    leave_page._select_date_from_calendar(leave_page.TO_DATE_TRIGGER, to_date)
    leave_page.select_leave_type("Vacation Leave")
    leave_page.enter_subject("Duplicate leave test")
    leave_page.fill_mail_body("Testing duplicate leave submission.")
    leave_page.click_submit()
    leave_page.click_confirm()

    toast = leave_page.wait_for_toast(leave_page.TOAST)
    assert "already exists" in toast.lower(), f"Expected duplicate error, got: {toast}"


@pytest.mark.regression
@pytest.mark.leave_validation
def test_blank_required_fields_shows_error(leave_page):
    leave_page.click_submit()
    leave_page.click_confirm()
    toasts = leave_page.get_all_toasts(leave_page.TOAST)
    assert any("required" in t.lower() for t in toasts), f"Expected validation errors, got: {toasts}"


@pytest.mark.regression
@pytest.mark.leave_validation
def test_blank_subject_shows_error(leave_page):
    from_date = date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)
    to_date = from_date + timedelta(days=settings.LEAVE_TO_OFFSET)

    leave_page._select_date_from_calendar(leave_page.FROM_DATE_TRIGGER, from_date)
    leave_page._select_date_from_calendar(leave_page.TO_DATE_TRIGGER, to_date)
    leave_page.select_leave_type("Vacation Leave")
    leave_page.click_submit()
    leave_page.click_confirm()

    # Capture all toast messages into an array
    toasts = leave_page.get_all_toasts(leave_page.TOAST)
    validations = leave_page.get_all_validation_messages()

    is_valid = (
        any("subject" in t.lower() or "required" in t.lower() or "correct" in t.lower() or "mail" in t.lower() or "body" in t.lower() for t in toasts) or
        any("subject" in v.lower() or "required" in v.lower() for v in validations.values()) or
        leave_page.page.locator(".chakra-form__error-message, [id*='feedback']").is_visible()
    )
    assert is_valid, f"Expected subject/mail body validation error in toasts: {toasts}, validations: {validations}"





@pytest.mark.regression
@pytest.mark.leave_validation
def test_single_day_leave(leave_page):
    from_date = date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)

    leave_page._select_date_from_calendar(leave_page.FROM_DATE_TRIGGER, from_date)
    leave_page._select_date_from_calendar(leave_page.TO_DATE_TRIGGER, from_date)
    leave_page.select_leave_type("Casual Leave")
    leave_page.enter_subject("Single day leave test")
    leave_page.fill_mail_body("Requesting single day leave.")
    leave_page.click_submit()
    leave_page.click_confirm()

    toast = leave_page.wait_for_toast(leave_page.TOAST)
    assert "successfully" in toast.lower() or "already exists" in toast.lower(), f"Unexpected toast: {toast}"
