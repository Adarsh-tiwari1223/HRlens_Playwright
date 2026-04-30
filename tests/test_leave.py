import pytest
from datetime import date, timedelta
from pages.login_page import LoginPage
from pages.attendance.leave_page import LeavePage
from core.config import settings


@pytest.fixture(scope="module")
def employee_context(browser):
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto(settings.BASE_URL)
    LoginPage(page).login(
        settings.USERS["sanidhy"]["username"],
        settings.USERS["sanidhy"]["password"]
    )
    yield page
    context.close()


@pytest.fixture(scope="module")
def approver_context(browser):
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="module")
def submitted_leave(employee_context):
    leave = LeavePage(employee_context)
    leave.click_my_leave()
    leave.click_leave_apply()

    from_date = date.today() + timedelta(days=1)
    to_date = from_date + timedelta(days=1)

    toast = leave.apply_leave_and_get_message(from_date, to_date, "Vacation")

    if "already exists" in toast.lower() and "pending" in toast.lower():
        dates = leave.extract_dates_from_toast(toast)
        from_date, to_date = dates if dates else (from_date, to_date)
    elif "already exists" in toast.lower():
        pytest.skip(f"Leave already exists, cannot apply: {toast}")
    elif "successfully" not in toast.lower():
        pytest.fail(f"Unexpected toast message: {toast}")

    return {
        "employee_name": leave.get_logged_in_employee_name(),
        "approver_name": leave.get_approver_name(),
        "from_date": from_date,
        "to_date": to_date,
    }


@pytest.fixture(scope="module")
def approver_login(approver_context, submitted_leave):
    approver_name = submitted_leave["approver_name"]

    # Resolve approver credentials from settings by matching name
    approver_user = next(
        (key for key, val in settings.USERS.items() if approver_name.lower() in key.lower()),
        "vivek"  # fallback
    )

    approver_context.goto(settings.BASE_URL)
    LoginPage(approver_context).login(
        settings.USERS[approver_user]["username"],
        settings.USERS[approver_user]["password"]
    )

    leave = LeavePage(approver_context)
    leave.click_attendance()
    leave.click_leave_request()

    return {
        "leave_page": leave,
        "employee_name": submitted_leave["employee_name"],
        "from_date": submitted_leave["from_date"],
        "to_date": submitted_leave["to_date"],
    }


@pytest.mark.regression
def test_approve_leave(approver_login):
    leave = approver_login["leave_page"]
    employee_name = approver_login["employee_name"]
    from_date = approver_login["from_date"]
    to_date = approver_login["to_date"]

    approved = leave.approve_leave(employee_name, from_date, to_date)
    assert approved, f"Leave for {employee_name} from {from_date} to {to_date} was not approved"
