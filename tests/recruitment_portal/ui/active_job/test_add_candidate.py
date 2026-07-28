import os
import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data

@pytest.fixture
def candidate_workflow(page):
    """Fixture to log in and initialize the CandidateWorkflow object."""
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    return CandidateWorkflow(page)

@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


@pytest.mark.ui
@pytest.mark.candidate
def test_add_fresher_candidate(candidate_workflow, dummy_resume_path):
    """
    Test generating and adding a FRESHER candidate, scheduling interview, and sending offer.
    """
    data = generate_candidate_data(is_experienced=False)
    print(f"\n[DATA] Generated Fresher Candidate: {data['name']} | Email: {data['email']} | City: {data['location']}")
    
    candidate_workflow.end_to_end_candidate_onboarding_workflow(data, dummy_resume_path)


@pytest.mark.ui
@pytest.mark.candidate
def test_add_experienced_candidate(candidate_workflow, dummy_resume_path):
    """
    Test generating and adding an EXPERIENCED candidate, scheduling interview, and sending offer.
    """
    data = generate_candidate_data(is_experienced=True)
    print(f"\n[DATA] Generated Experienced Candidate: {data['name']} | Email: {data['email']} | City: {data['location']}")
    
    candidate_workflow.end_to_end_candidate_onboarding_workflow(data, dummy_resume_path)
