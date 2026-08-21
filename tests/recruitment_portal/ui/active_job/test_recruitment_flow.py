import os
import re
import pytest
from datetime import datetime, timedelta
from faker import Faker
from playwright.sync_api import expect
from core.config import settings
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from workflows.recruitment_portal.active_job.job_opening_workflow import JobOpeningWorkflow
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data

fake = Faker()

@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path

@pytest.mark.ui
@pytest.mark.e2e
@pytest.mark.regression
@pytest.mark.recruitment
@pytest.mark.recruitment_flow
@pytest.mark.meeting
@pytest.mark.interview
def test_end_to_end_recruitment_flow(logged_in_page, dummy_resume_path):
    """
    End-to-End Recruitment Workflow:
    1. Create a Job Opening (Job Posting) using JobOpeningWorkflow
    2. Get the generated Job ID
    3. Add a Candidate for that specific Job Posting using CandidateWorkflow
    4. Schedule an Interview for the Candidate
    5. Send the Letter of Intent (LOI)
    """
    page, context = logged_in_page("admin")
    job_workflow = JobOpeningWorkflow(page)
    job_page = JobOpeningPage(page)
    candidate_page = CandidatePage(page)

    # 1. Navigate to Active Jobs
    job_workflow.navigate_to_active_jobs()

    # 2. Fill mandatory fields and enter job description
    print("\n[ACTION] Creating Job Opening...")
    job_workflow.fill_mandatory_fields_except_jd()

    # Fill summary
    summary_text = f"Automated E2E Job Posting Description\n\n{fake.paragraph()}"
    job_page.set_job_summary(summary_text)

    # Publish
    job_workflow.publish_with_confirm()
    job_page.close_drawer_safely()

    latest_job_id = job_page.get_latest_job_id()
    print(f"SUCCESS: Newly created Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-")

    # 3. Add Candidate for the new Job
    candidate_data = generate_candidate_data(is_experienced=False)
    print(f"\n[DATA] Generated Candidate Name: {candidate_data['name']} | Email: {candidate_data['email']}")

    print(f"\n[ACTION] Adding Candidate to {latest_job_id}...")
    candidate_page.navigate_to_add_candidate_for_specific_job(latest_job_id)
    candidate_page.fill_candidate_form(candidate_data, dummy_resume_path)
    candidate_page.submit()

    # 4. Schedule Interview
    now = datetime.now()
    interview_date = now.strftime("%Y-%m-%d")
    interview_time = (now + timedelta(minutes=35)).strftime("%H:%M")

    print(f"\n[ACTION] Scheduling Interview for {candidate_data['name']}...")
    candidate_page.schedule_interview(
        candidate_name=candidate_data['name'],
        date=interview_date,
        time=interview_time
    )

    # 5. Validate Salary and Send Offer Letter (LOI)
    candidate_page.page.reload()
    candidate_page.page.wait_for_load_state("domcontentloaded")

    print(f"\n[ACTION] Generating and validating offer for {candidate_data['name']}...")
    offer_info = candidate_page.generate_and_validate_offer(
        candidate_name=candidate_data['name'],
        doj=interview_date,
        gross_salary="20000"
    )
    redirect_url = offer_info.get("candidate_form_url", "")
    if redirect_url:
        print(f"[API CHECK] Candidate Form Fill Redirect URL Captured: '{redirect_url}'")
    else:
        print("[API CHECK] Send LOI API executed successfully. No candidate form redirect URL string returned in JSON response payload.")

    print(f"\n[SUCCESS] E2E Recruitment flow completed successfully for candidate {candidate_data['name']}!")
