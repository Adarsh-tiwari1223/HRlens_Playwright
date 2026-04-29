import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.increment.increment_page import IncrementPage
from pages.increment.increment_summary_page import IncrementSummaryPage

@pytest.fixture
def admin_page(page):
    page.goto(settings.BASE_URL)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_selector("text=Logged in Successfully", state="visible")
    return page

@pytest.mark.regression
def test_filter_selections(admin_page):
    increment_page = IncrementPage(admin_page)
    increment_page.go_to_increment()
    # Mocking data selection
    increment_page.select_company("Tekinspirations")
    increment_page.select_branch("HQ")
    increment_page.select_department("Engineering")
    assert increment_page.is_visible(increment_page.DATE_RANGE)

@pytest.mark.regression
def test_run_assessment(admin_page):
    increment_page = IncrementPage(admin_page)
    increment_page.go_to_increment()
    # Fill required filters
    increment_page.select_date_range("15")
    increment_page.run_assessment()
    assert increment_page.is_assessment_open()

@pytest.mark.regression
def test_employee_drilldown(admin_page):
    summary_page = IncrementSummaryPage(admin_page)
    # Navigate to summary (assuming it's accessible or redirect happens)
    admin_page.goto(f"{settings.BASE_URL}/increment/summary") 
    summary_page.wait_for_grid()
    summary_page.select_tl("John Doe")
    summary_page.select_employee("Jane Smith")
    summary_page.open_assessment_form()
    # Assuming an assessment form modal or page appears
    assert summary_page.is_visible("text=Assessment Form")
