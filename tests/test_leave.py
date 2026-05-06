import pytest
from datetime import date, timedelta
from pages.attendance.leave_page import LeavePage
from core.config import settings
from testdata.static.Leave import Leave


@pytest.fixture(scope="module")
def employee_context(logged_in_page):
    page, context = logged_in_page()
    yield page


@pytest.fixture(scope="module")
def approver_context(logged_in_page, submitted_leave):
    approver_key = settings.APPROVERS.get(submitted_leave["approver_name"])
    assert approver_key, f"No approver mapping for '{submitted_leave['approver_name']}' — add to settings.APPROVERS"
    page, context = logged_in_page(approver_key)
    yield page


@pytest.fixture(scope="module")
def submitted_leave(employee_context):
    leave = LeavePage(employee_context)
    leave.click_my_leave()
    leave.click_leave_apply()

    from_date = date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)
    to_date = from_date + timedelta(days=settings.LEAVE_TO_OFFSET)

    leave._select_date_from_calendar(leave.FROM_DATE_TRIGGER, from_date)
    leave._select_date_from_calendar(leave.TO_DATE_TRIGGER, to_date)
    leave.select_leave_type("Vacation Leave")
    leave.enter_subject("Leave for Vacation Leave")
    leave.fill_mail_body(
        f"Dear Sir/Ma'am,\n\n"
        f"I would like to request leave from {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')} "
        f"for Vacation Leave.\n\nKindly approve my leave request.\n\nThank you."
    )
    leave.click_submit()
    leave.click_confirm()

    toast = leave.wait_for_toast(leave.TOAST)

    if "already exists" in toast.lower():
        dates = leave.extract_dates_from_toast(toast)
        from_date, to_date = dates if dates else (from_date, to_date)
        if "approved" in toast.lower():
            pytest.fail(f"Leave already approved — cannot test approval flow: {toast}")
    elif "successfully" not in toast.lower():
        pytest.fail(f"Unexpected toast: {toast}")

    approver_name = leave.get_approver_name()

    return {
        "employee_name": leave.get_logged_in_employee_name(),
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


@pytest.fixture(autouse=False)
def leave_page(employee_context):
    employee_context.reload()
    employee_context.wait_for_load_state("networkidle")
    leave = LeavePage(employee_context)
    leave.click_my_leave()
    leave.click_leave_apply()
    return leave


# ─── Happy Path ───────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.dependency(name="test_apply_leave")
def test_apply_leave(employee_context):
    leave = LeavePage(employee_context)
    from_date = date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)
    to_date = from_date + timedelta(days=settings.LEAVE_TO_OFFSET)

    leave.click_my_leave()
    leave.click_leave_apply()
    leave._select_date_from_calendar(leave.FROM_DATE_TRIGGER, from_date)
    leave._select_date_from_calendar(leave.TO_DATE_TRIGGER, to_date)
    leave.get_approver_name()

    leave_type = Leave.shuffled()[0]["leave_type"]
    leave.select_leave_type(leave_type)
    leave.enter_subject(f"Leave for {leave_type}")
    leave.fill_mail_body(f"Leave for {leave_type}")
    leave.click_submit()
    leave.click_confirm()

    toast = leave.wait_for_toast(leave.TOAST)
    assert "successfully" in toast.lower() or "already exists" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.regression
@pytest.mark.dependency(depends=["test_apply_leave"])
def test_approve_leave(approver_login):
    leave = approver_login["leave_page"]
    approved = leave.approve_leave(
        approver_login["employee_name"],
        approver_login["from_date"],
        approver_login["to_date"]
    )
    assert approved, "Leave was not approved"


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

    toast = leave_page.wait_for_toast(leave_page.TOAST)
    assert toast, "Expected subject validation error but got nothing"


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
