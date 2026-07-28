import pytest
from core.config import settings
from pages.login_page import LoginPage
from workflows.hrlense_portal.increment.increment_workflow import IncrementWorkflow

def module_admin_login(page):
    """Module: Perform Admin Login"""
    page.goto(settings.BASE_URL)
    login_page = LoginPage(page)
    admin_creds = settings.USERS["admin"]
    login_page.login(admin_creds["username"], admin_creds["password"])
    page.wait_for_url("**/dashboard")


@pytest.mark.e2e
def test_full_increment_cycle(page):
    """Execute the complete E2E Increment workflow using IncrementWorkflow."""
    module_admin_login(page)
    workflow = IncrementWorkflow(page)
    
    increment_data = {
        "company": "TEK Inspirations LLC",
        "branch": "Varanasi",
        "department": "Developer",
        "employee_id": "EMP-001"
    }
    workflow.process_salary_increment_workflow(increment_data)
