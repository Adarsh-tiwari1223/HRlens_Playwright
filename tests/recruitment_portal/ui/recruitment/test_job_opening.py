import pytest
from playwright.sync_api import expect
from faker import Faker
fake = Faker()
from core.config import settings
from pages.recruitment_portal.recruitment.job_opening_page import JobOpeningPage

@pytest.mark.ui
def test_create_job_opening_manual(logged_in_page):
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
        "summary": f"This is manual test case\n\n{fake.paragraph()}"
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


@pytest.mark.ui
def test_auto_jd_generation(logged_in_page):
    """
    Test the 'Generate JD with AI' feature during Job Opening creation.
    """
    page, context = logged_in_page("admin")
    
    # Navigate to Recruitment Portal -> Job Openings -> Active Jobs
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    job_page = JobOpeningPage(page)
    
    # 1. Open the modal
    page.locator(job_page.CREATE_JOB_BTN).click()
    page.wait_for_load_state("networkidle")
    
    # 2. Select Job details (essential for JD generation context) - Using index=1 to avoid stale hardcoded ID conflicts
    page.locator(job_page.BUSINESS_PROCESS).select_option(index=1)
    page.locator(job_page.PAYROLL_COMPANY).select_option(index=1)
    page.locator(job_page.BRANCH).select_option(index=1)
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.locator(job_page.JOB_TITLE).select_option(index=1)
    
    # Fill remaining mandatory fields
    page.locator(job_page.NUM_OPENINGS).fill("5")
    page.locator(job_page.EMPLOYMENT_TYPE).select_option(index=1)
    page.locator(job_page.OPENING_DATE).fill("2026-07-11")
    page.locator(job_page.CLOSING_DATE).fill("2026-07-20")
    page.locator(job_page.SALARY_MIN).fill("20000")
    page.locator(job_page.SALARY_MAX).fill("30000")
    page.locator(job_page.URGENCY_LEVEL).select_option(index=1)
    page.locator(job_page.WORK_MODE).select_option(index=1)
    page.locator(job_page.EXPECTED_JOIN_DATE).fill("2026-07-30")
    
    # Expand and fill Additional Details
    page.locator(job_page.ADDITIONAL_DETAILS).click()
    page.locator(job_page.EXP_MIN).fill("1")
    page.locator(job_page.EXP_MAX).fill("3")
    
    # 3. Locate the Auto JD button
    auto_jd_btn = page.get_by_role("button", name="Generate JD with AI")
    expect(auto_jd_btn).to_be_visible()
    
    # 4. Click the 'Generate JD with AI' button
    auto_jd_btn.click()
    
    # 5. Wait for the generation to complete and summary to populate
    import re
    summary_editor = page.locator("div.se-wrapper")
    
    # Wait for the AI loading spinner to disappear and button to complete its spin
    page.locator(".chakra-button__spinner, .chakra-spinner").first.wait_for(state="hidden", timeout=15000)
    
    # Wait dynamically for the AI generation service to complete and populate the editor
    expect(summary_editor).not_to_have_text("", timeout=15000)
    
    summary_text = summary_editor.inner_text().strip()
    print(f"Auto-generated JD summary text: {summary_text}")
    
    # Assert that a JD description has been generated and populated
    assert len(summary_text) > 10, f"AI JD generation failed or returned empty text. Current text: '{summary_text}'"
    
    # 6. Publish and save the newly created job with generated JD
    page.locator(job_page.PUBLISH_BTN).click()
    page.locator(job_page.CONFIRM_BTN).click()
    
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    # Close modal if it didn't close automatically
    close_btn = page.get_by_role("button", name="Close")
    if close_btn.count() > 0:
        close_btn.first.click()
        
    # Verify the newly created job shows up on the grid
    latest_job_id = job_page.get_latest_job_id()
    print(f"SUCCESS: Auto-generated Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-")
