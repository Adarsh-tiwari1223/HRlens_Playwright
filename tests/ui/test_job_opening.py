import pytest
from core.config import settings
from pages.recruitment.job_opening_page import JobOpeningPage

@pytest.mark.ui
def test_create_job_opening(logged_in_page):
    """
    Test creating a new job opening using the JobOpeningPage POM.
    """
    # 1. Log in (handled by fixture) and get the page
    page, context = logged_in_page("admin")
    
    # 2. Navigate to Recruitment Portal -> Job Openings -> Active Jobs
    # Click the Recruitment Portal module on the dashboard
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    # But for now, we assume the direct URL works.
    
    # 3. Instantiate POM
    job_page = JobOpeningPage(page)
    
    # 4. Define dummy data
    job_data = {
        "business_process": "4",
        "payroll_company": "10",
        "branch": "1",
        "department": "1",
        "job_title": "32",
        "openings": "10",
        "employment_type": "1",
        "opening_date": "2026-05-30",
        "closing_date": "2026-05-31",
        "salary_min": "15000",
        "salary_max": "20000",
        "urgency": "2",
        "work_mode": "4",
        "expected_join": "2026-06-06",
        "exp_min": "0",
        "exp_max": "1",
        "summary": "This is an automated test JD."
    }
    
    # 5. Create Job Opening
    job_page.create_job_opening(job_data)
    
    # 6. Verify and Extract Job ID
    toast = page.locator(".Toastify__toast, .chakra-toast").first
    if toast.count() > 0:
        print(f"Toast message: {toast.inner_text()}")
        
    # Close modal if it didn't close automatically
    close_btn = page.get_by_role("button", name="Close")
    if close_btn.count() > 0:
        close_btn.first.click()
        
    latest_job_id = job_page.get_latest_job_id()
    print(f"SUCCESS: Newly created Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-")
