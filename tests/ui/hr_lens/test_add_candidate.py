import os
import pytest
from datetime import datetime, timedelta
from core.config import settings
from pages.login_page import LoginPage
from pages.employee.candidate_page import CandidatePage
from testdata.dynamic.candidate_data import generate_candidate_data

@pytest.fixture
def candidate_page(page):
    """Fixture to log in and initialize the CandidatePage object."""
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    
    # We assume the user is now on the page where JOB_POSTING buttons are visible.
    # If a specific navigation step is required, it should be added here.
    return CandidatePage(page)

@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


@pytest.mark.ui
@pytest.mark.candidate
def test_add_fresher_candidate(candidate_page, dummy_resume_path):
    """
    Test generating and adding a FRESHER candidate.
    Verifies that the conditional 'Experience' logic accurately handles the 'false' state.
    """
    # 1. Generate dynamic fresher data (is_experienced=False)
    data = generate_candidate_data(is_experienced=False)
    print(f"\n[DATA] Generated Fresher Candidate: {data['name']} | Email: {data['email']} | City: {data['location']}")
    
    # 2. Navigate and Open Add Candidate Form
    candidate_page.navigate_to_add_candidate_for_job()
    
    # 3. Fill the form with the dynamic data
    candidate_page.fill_candidate_form(data, dummy_resume_path)
    
    # 4. Submit and Assert success
    candidate_page.submit()

    # 5. Schedule Interview for the newly created candidate
    now = datetime.now()
    interview_date = now.strftime("%Y-%m-%d")
    interview_time = (now + timedelta(minutes=35)).strftime("%H:%M")
    
    print(f"\n[ACTION] Scheduling interview for {data['name']} at {interview_date} {interview_time}...")
    candidate_page.schedule_interview(
        candidate_name=data['name'],
        date=interview_date,
        time=interview_time
    )
    
    # 6. Validate Salary and Send Offer Letter
    # 6. Validate Salary and Send Offer Letter
    candidate_page.page.reload()
    candidate_page.page.wait_for_load_state("networkidle")
    
    print(f"\n[ACTION] Generating and validating offer for {data['name']}...")
    candidate_page.generate_and_validate_offer(
        candidate_name=data['name'],
        doj=interview_date,
        gross_salary="20000"
    )


@pytest.mark.ui
@pytest.mark.candidate
def test_add_experienced_candidate(candidate_page, dummy_resume_path):
    """
    Test generating and adding an EXPERIENCED candidate.
    Verifies that the conditional 'Experience' logic accurately handles the 'true' state
    and successfully fills the dynamically revealed fields.
    """
    # 1. Generate dynamic experienced data (is_experienced=True)
    data = generate_candidate_data(is_experienced=True)
    print(f"\n[DATA] Generated Experienced Candidate: {data['name']} | Email: {data['email']} | City: {data['location']}")
    
    # 2. Navigate and Open Add Candidate Form
    candidate_page.navigate_to_add_candidate_for_job()
    
    # 3. Fill the form with the dynamic data
    candidate_page.fill_candidate_form(data, dummy_resume_path)
    
    # 4. Submit and Assert success
    candidate_page.submit()

    # 5. Schedule Interview for the newly created candidate
    now = datetime.now()
    interview_date = now.strftime("%Y-%m-%d")
    interview_time = (now + timedelta(minutes=35)).strftime("%H:%M")
    
    print(f"\n[ACTION] Scheduling interview for {data['name']} at {interview_date} {interview_time}...")
    candidate_page.schedule_interview(
        candidate_name=data['name'],
        date=interview_date,
        time=interview_time
    )
    
    # 6. Validate Salary and Send Offer Letter
    # We do not reload the page here. Reloading breaks the frontend state and causes email=null bugs.
    
    print(f"\n[ACTION] Generating and validating offer for {data['name']}...")
    candidate_page.generate_and_validate_offer(
        candidate_name=data['name'],
        doj=interview_date,
        gross_salary="15000"
    )
