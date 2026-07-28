import pytest
import re
from datetime import datetime, timedelta
from playwright.sync_api import expect
from faker import Faker
fake = Faker()
from core.config import settings
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage

@pytest.mark.ui
def test_create_job_opening_manual(logged_in_page):
    """
    Test creating a new job opening using the JobOpeningPage POM.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    job_page = JobOpeningPage(page)
    
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
    
    job_page.create_job_opening(job_data)
    
    toast = page.locator(".Toastify__toast, .chakra-toast").first
    if toast.count() > 0:
        print(f"Toast message: {toast.inner_text()}")
        
    job_page.close_drawer_safely()
        
    latest_job_id = job_page.get_latest_job_id()
    print(f"SUCCESS: Newly created Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-")


@pytest.mark.ui
def test_auto_jd_generation(logged_in_page):
    """
    Test the 'Generate JD with AI' feature during Job Opening creation.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
    
    page.locator(job_page.BUSINESS_PROCESS).select_option(index=1)
    page.locator(job_page.PAYROLL_COMPANY).select_option(index=1)
    page.locator(job_page.BRANCH).select_option(index=1)
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.locator(job_page.JOB_TITLE).select_option(index=1)
    
    page.locator(job_page.NUM_OPENINGS).fill("5")
    page.locator(job_page.EMPLOYMENT_TYPE).select_option(index=1)
    page.locator(job_page.OPENING_DATE).fill("2026-07-11")
    page.locator(job_page.CLOSING_DATE).fill("2026-07-20")
    page.locator(job_page.SALARY_MIN).fill("20000")
    page.locator(job_page.SALARY_MAX).fill("30000")
    page.locator(job_page.URGENCY_LEVEL).select_option(index=1)
    page.locator(job_page.WORK_MODE).select_option(index=1)
    page.locator(job_page.EXPECTED_JOIN_DATE).fill("2026-07-30")
    
    page.locator(job_page.ADDITIONAL_DETAILS).click()
    page.locator(job_page.EXP_MIN).fill("1")
    page.locator(job_page.EXP_MAX).fill("3")
    
    auto_jd_btn = page.get_by_role("button", name="Generate JD with AI")
    expect(auto_jd_btn).to_be_visible()
    auto_jd_btn.click()
    
    summary_editor = page.locator("div.se-wrapper")
    page.locator(".chakra-button__spinner, .chakra-spinner").first.wait_for(state="hidden", timeout=30000)
    expect(summary_editor).not_to_have_text("", timeout=30000)
    
    summary_text = summary_editor.inner_text().strip()
    print(f"Auto-generated JD summary text: {summary_text}")
    assert len(summary_text) > 10, f"AI JD generation failed or returned empty text. Current text: '{summary_text}'"
    
    page.locator(job_page.PUBLISH_BTN).click()
    page.locator(job_page.CONFIRM_BTN).click()
    
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    job_page.close_drawer_safely()
    latest_job_id = job_page.get_latest_job_id()
    print(f"SUCCESS: Auto-generated Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-")
