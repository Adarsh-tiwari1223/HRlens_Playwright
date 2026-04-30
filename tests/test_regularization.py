import pytest
from datetime import datetime, timedelta
from pages.login_page import LoginPage
from pages.attendance.regularization_page import RegularizationPage
from core.config import settings


@pytest.fixture
def employee_page(page):
    page.goto(settings.BASE_URL)
    login = LoginPage(page)
    login.login(settings.USERS["sanidhy"]["username"], settings.USERS["sanidhy"]["password"])
    return page


@pytest.fixture
def admin_page(page):
    page.goto(settings.BASE_URL)
    login = LoginPage(page)
    login.login(settings.USERS["admin"]["username"], settings.USERS["admin"]["password"])
    return page


@pytest.mark.regression
def test_regularization_request(employee_page, admin_page):
    selected_date = datetime.today() - timedelta(days=13)

    # --- Employee: submit regularization ---
    reg = RegularizationPage(employee_page)
    employee_name = reg.get_logged_in_employee_name()

    reg.click_my_attendance()
    reg.click_regularization()
    reg.date_pick(selected_date.day)
    reg.in_time_input("02:00")
    reg.out_time_input("11:00")
    reg.enter_reason()
    reg.click_apply_btn()
    reg.click_confirm_btn()

    toast = reg.get_pop_msg()
    assert toast, "No popup message appeared after submitting regularization"

    if "already exists" in toast:
        pytest.skip(f"Regularization already exists for this date: {toast}")

    assert "successfully" in toast.lower(), f"Unexpected message: {toast}"

    # --- Admin: verify and approve ---
    admin_reg = RegularizationPage(admin_page)
    admin_reg.click_my_attendance()
    admin_reg.click_regularization()

    date_str = selected_date.strftime("%Y-%m-%d")
    row = admin_reg.get_matched_employee_row(employee_name, date_str)
    assert row, f"Regularization request not found in admin table for {employee_name} on {date_str}"

    admin_reg.approve_regularization(employee_name, selected_date)

    approval_toast = admin_reg.get_pop_msg()
    assert approval_toast and "successfully" in approval_toast.lower(), \
        f"Approval failed. Toast: {approval_toast}"
