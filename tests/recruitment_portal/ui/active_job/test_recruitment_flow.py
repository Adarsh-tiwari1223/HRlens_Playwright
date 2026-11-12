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
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "testdata", "static", "pdf", "sample-pdf-file-100kb.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


@pytest.mark.ui
@pytest.mark.e2e
@pytest.mark.regression
@pytest.mark.recruitment
@pytest.mark.recruitment_flow
@pytest.mark.parametrize("create_new_job", [
    pytest.param(False, id="existing_active_job"),
    pytest.param(True, id="new_job_opening")
])
def test_end_to_end_recruitment_flow(logged_in_page, dummy_resume_path, create_new_job):
    """
    Refined End-to-End Recruitment Lifecycle Workflow:
    1. Select an existing active job OR create a new job opening based on 'create_new_job'
    2. Add a Candidate for that specific Job Posting (Status: Applied)
    3. Shortlist the Candidate (Status: Shortlisted)
    4. Schedule an Interview for the Candidate (Status: Interview Scheduled)
    5. Generate and Send the Letter of Intent (LOI) / Offer (Status: LOI Shared)
    """
    page, context = logged_in_page("admin")
    job_workflow = JobOpeningWorkflow(page)
    candidate_workflow = CandidateWorkflow(page)
    candidate_page = CandidatePage(page)

    print("\n" + "=" * 70)
    print(f"  RECRUITMENT LIFECYCLE :: {'NEW JOB' if create_new_job else 'EXISTING ACTIVE JOB'}")
    print("=" * 70)

    # 1. Job Strategy: Select or Create Job Opening
    if create_new_job:
        print("[STEP 1/5] Creating a fresh Job Opening...")
        summary = f"Refined Automated Job Opening\n\n{fake.paragraph()}"
        target_job_id = job_workflow.create_manual_job_opening_workflow(summary_text=summary)
    else:
        print("[STEP 1/5] Resolving existing active Job Opening...")
        target_job_id = job_workflow.get_or_create_job_opening_workflow(create_new=False)

    print(f"  • Target Job ID: {target_job_id}")
    assert target_job_id and target_job_id.startswith("JOB_POSTING-"), f"Invalid Job ID: '{target_job_id}'"

    # 2. Add Candidate
    candidate_data = generate_candidate_data(is_experienced=False)
    candidate_name = candidate_data["name"]
    print(f"\n[STEP 2/5] Adding Candidate '{candidate_name}' ({candidate_data['email']}) to {target_job_id}...")
    candidate_workflow.add_candidate_for_specific_job(target_job_id, candidate_data, dummy_resume_path)
    print(f"  • Candidate successfully added to {target_job_id}.")

    # 3. Shortlist Candidate
    print(f"\n[STEP 3/5] Shortlisting Candidate '{candidate_name}'...")
    candidate_workflow.shortlist_candidate_workflow(candidate_name, status_option="Shortlisted")
    print(f"  • Candidate '{candidate_name}' moved to 'Shortlisted'.")

    # 4. Schedule Interview
    now = datetime.now()
    interview_date = now.strftime("%Y-%m-%d")
    interview_time = (now + timedelta(minutes=35)).strftime("%H:%M")

    print(f"\n[STEP 4/5] Scheduling Interview for '{candidate_name}' on {interview_date} at {interview_time}...")
    candidate_workflow.schedule_interview_workflow(
        candidate_name=candidate_name,
        date=interview_date,
        time=interview_time
    )
    print(f"  • Interview scheduled successfully for '{candidate_name}'.")

    # 5. Generate and Send Letter of Intent (LOI)
    print(f"\n[STEP 5/5] Generating and Sending LOI (Offer) for '{candidate_name}'...")
    offer_info = candidate_workflow.generate_and_send_offer_workflow(
        candidate_name=candidate_name,
        doj=interview_date,
        gross_salary="20000"
    )
    redirect_url = offer_info.get("candidate_form_url", "") if isinstance(offer_info, dict) else ""
    if redirect_url:
        print(f"  • Captured Candidate Details Form Link: {redirect_url}")
    print(f"  • Offer / LOI dispatched successfully for '{candidate_name}'.")

    print("\n" + "=" * 70)
    print(f"  [SUCCESS] Full Recruitment Flow Completed for '{candidate_name}' on '{target_job_id}'!")
    print("=" * 70 + "\n")
