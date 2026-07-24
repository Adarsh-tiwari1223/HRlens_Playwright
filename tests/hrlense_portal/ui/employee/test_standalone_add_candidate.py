import os
import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.employee.candidate_page import CandidatePage
from testdata.dynamic.candidate_data import generate_candidate_data

@pytest.fixture(scope="session")
def dummy_resume_path():
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path

@pytest.mark.ui
@pytest.mark.standalone
def test_create_candidate_only(page, dummy_resume_path):
    """
    STANDALONE TEST: Only generates and adds a candidate.
    It stops immediately after the candidate is successfully added.
    """
    # Setup login
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    candidate_page = CandidatePage(page)
    
    # Generate dynamic data
    data = generate_candidate_data(is_experienced=False)
    print(f"\n[DATA] Generated Standalone Candidate: {data['name']} | Email: {data['email']}")
    
    # Navigate, Fill, and Submit
    job_name = candidate_page.navigate_to_add_candidate_for_job()
    candidate_page.fill_candidate_form(data, dummy_resume_path)
    candidate_page.submit()
    
    print(f"\n[SUCCESS] Candidate {data['name']} was successfully added to job '{job_name}'. Stopping script.")
