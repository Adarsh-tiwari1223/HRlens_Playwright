import os
import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data

@pytest.fixture
def hr_candidate_workflow(page):
    """Fixture to log in as HR user (shiva) and initialize CandidateWorkflow."""
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["shiva"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    return CandidateWorkflow(page)

@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "testdata", "static", "pdf", "sample-pdf-file-100kb.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.regression
@pytest.mark.candidate
@pytest.mark.dependency(name="test_add_candidate")
def test_add_experienced_candidate(hr_candidate_workflow, dummy_resume_path):
    """
    Test generating and adding an EXPERIENCED candidate, scheduling interview, and sending offer.
    Must pass before candidate filter search is executed.
    """
    data = generate_candidate_data(is_experienced=True)
    print(f"\n[DATA] Generated Experienced Candidate: {data['name']} | Email: {data['email']} | City: {data['location']}")
    
    hr_candidate_workflow.end_to_end_candidate_onboarding_workflow(data, dummy_resume_path)


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.regression
@pytest.mark.candidate
@pytest.mark.dependency(depends=["test_add_candidate"])
def test_sno_02_candidate_filter_by_shared_loi(hr_candidate_workflow):
    """
    S.No 2: Candidate Filter by Shared LOI status for each Job Post.
    Executes AFTER test_add_candidate passes to ensure active candidate records exist.
    """
    from utils.logger import log_test_start, log_pass, log_skip, log_debug, log_step
    log_test_start(module="Recruitment Portal", phase="S.No 2", test="Candidate Filter by Shared LOI (HR Role)")

    cand_page = CandidatePage(hr_candidate_workflow.page)
    job_name, total_before = cand_page.find_job_opening_with_candidates(max_attempts=5)

    if not job_name or total_before == 0:
        log_skip("No job opening with >0 candidates found in 5 attempts.")
        pytest.skip("No job opening with candidates available for LOI filter test.")

    log_step("Target Job Opening Found", value=f"{job_name} | Candidates={total_before}")

    # Apply LOI status filter & verify status column
    loi_status = "LOI Shared"
    count, is_matching, details = cand_page.filter_and_verify_candidate_loi_status_column(loi_status)
    log_step("Candidates Count After LOI Filter", value=f"{count} (Filtered from {total_before})")
    log_debug(f"Row Details: {details}")

    assert is_matching, f"Status column verification failed for filter '{loi_status}'!"

    log_pass()
