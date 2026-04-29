import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.increment.increment_page import IncrementPage
from pages.increment.increment_summary_page import IncrementSummaryPage
from pages.increment.negotiation_page import NegotiationPage

@pytest.mark.e2e
def test_full_increment_cycle(page):
    # 1. Admin Login
    page.goto(settings.BASE_URL)
    login_page = LoginPage(page)
    admin_creds = settings.USERS["admin"]
    login_page.login(admin_creds["username"], admin_creds["password"])
    page.wait_for_selector("text=Logged in Successfully", state="visible")

    # 2. Setup Assessment
    increment_page = IncrementPage(page)
    increment_page.go_to_increment()
    increment_page.select_company("Tekinspirations")
    increment_page.select_branch("HQ")
    increment_page.select_department("Engineering")
    increment_page.select_date_range("15")
    increment_page.run_assessment()
    assert increment_page.is_assessment_open()

    # 3. View Summary (Admin assigns increment - simulated/simplified)
    summary_page = IncrementSummaryPage(page)
    page.goto(f"{settings.BASE_URL}/increment/summary")
    summary_page.wait_for_grid()
    summary_page.select_tl("John Doe")
    summary_page.select_employee("Vivek")
    summary_page.open_assessment_form()

    # 4. Employee Login & Negotiation
    # Clear context or logout then login as employee
    page.context.clear_cookies()
    page.goto(settings.BASE_URL)
    emp_creds = settings.USERS["vivek"]
    login_page.login(emp_creds["username"], emp_creds["password"])
    page.wait_for_selector("text=Logged in Successfully", state="visible")

    negotiation_page = NegotiationPage(page)
    negotiation_page.navigate_to_negotiation()
    negotiation_page.enter_counter_offer("15000")
    negotiation_page.submit()
    assert negotiation_page.is_success_visible()
