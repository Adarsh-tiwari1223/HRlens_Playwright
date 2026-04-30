import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.increment.negotiation_page import NegotiationPage

@pytest.fixture
def employee_page(page):
    page.goto(settings.BASE_URL)
    login_page = LoginPage(page)
    # Using 'vivek' as a placeholder for employee login
    creds = settings.USERS["vivek"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_url("**/dashboard")
    return page

@pytest.mark.regression
def test_accept_offer(employee_page):
    negotiation_page = NegotiationPage(employee_page)
    negotiation_page.navigate_to_negotiation()
    negotiation_page.accept_offer()
    assert negotiation_page.is_success_visible()

@pytest.mark.regression
def test_reject_offer(employee_page):
    negotiation_page = NegotiationPage(employee_page)
    negotiation_page.navigate_to_negotiation()
    negotiation_page.reject_offer()
    # Need to verify state change after rejection

@pytest.mark.regression
def test_counter_offer(employee_page):
    negotiation_page = NegotiationPage(employee_page)
    negotiation_page.navigate_to_negotiation()
    negotiation_page.enter_counter_offer("10000")
    negotiation_page.submit()
    assert negotiation_page.is_success_visible()


@pytest.mark.smoke
def test_negotiation_page_loads(employee_page):
    negotiation_page = NegotiationPage(employee_page)
    negotiation_page.navigate_to_negotiation()
    assert negotiation_page.is_visible(negotiation_page.ACCEPT_BTN)
    assert negotiation_page.is_visible(negotiation_page.REJECT_BTN)
