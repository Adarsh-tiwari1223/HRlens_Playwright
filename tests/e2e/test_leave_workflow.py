import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.increment.increment_page import IncrementPage
from pages.increment.increment_summary_page import IncrementSummaryPage
from pages.increment.negotiation_page import NegotiationPage

def module_admin_login(page):
    """Module: Perform Admin Login"""
    page.goto(settings.BASE_URL)
    login_page = LoginPage(page)
    admin_creds = settings.USERS["admin"]
    login_page.login(admin_creds["username"], admin_creds["password"])
    page.wait_for_url("**/dashboard")


def module_setup_assessment(page):
    """Module: Admin Setup Assessment"""
    increment_page = IncrementPage(page)
    increment_page.go_to_increment()
    increment_page.select_company("TEK Inspirations LLC")
    increment_page.select_branch("Varanasi")
    increment_page.select_department("Developer")
    increment_page.run_assessment()
    assert increment_page.is_assessment_open()


def module_view_summary(page):
    """Module: Admin View Summary & Assessment Form"""
    summary_page = IncrementSummaryPage(page)
    page.goto(f"{settings.BASE_URL}/increment/summary")
    summary_page.wait_for_grid()
    summary_page.select_tl("John Doe")
    summary_page.select_employee("Vivek")
    summary_page.open_assessment_form()


def module_employee_negotiation(page):
    """Module: Employee Login & Negotiation"""
    # Clear context or logout then login as employee
    page.context.clear_cookies()
    page.goto(settings.BASE_URL)
    
    login_page = LoginPage(page)
    emp_creds = settings.USERS["vivek"]
    login_page.login(emp_creds["username"], emp_creds["password"])
    page.wait_for_url("**/dashboard")

    negotiation_page = NegotiationPage(page)
    negotiation_page.navigate_to_negotiation()
    negotiation_page.enter_counter_offer("15000")
    negotiation_page.submit()
    assert negotiation_page.is_success_visible()


@pytest.mark.e2e
def test_full_increment_cycle(page):
    """Execute the complete E2E Increment workflow sequentially."""
    module_admin_login(page)
    module_setup_assessment(page)
    module_view_summary(page)
    module_employee_negotiation(page)
