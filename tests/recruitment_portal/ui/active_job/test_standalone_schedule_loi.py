import pytest
from core.config import settings
from pages.login_page import LoginPage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow

@pytest.mark.ui
@pytest.mark.standalone
def test_schedule_and_loi_only(page):
    """
    STANDALONE TEST: Only schedules an interview and sends the LOI using CandidateWorkflow.
    Assumes the candidate ALREADY exists and is in the 'Applied' state.
    """
    # 🛑 UPDATE THIS WITH THE EXACT CANDIDATE NAME BEFORE RUNNING 🛑
    candidate_name = "REPLACE_WITH_CANDIDATE_NAME"

    if candidate_name == "REPLACE_WITH_CANDIDATE_NAME":
        pytest.fail("You must update the 'candidate_name' variable in the script before running this standalone test!")

    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")

    workflow = CandidateWorkflow(page)

    # 1. Schedule Interview
    workflow.schedule_interview_workflow(candidate_name)

    # 2. Generate and Send Offer Letter (LOI)
    workflow.generate_and_send_offer_workflow(candidate_name, gross_salary="15000")

    print(f"\n[SUCCESS] LOI sent successfully to {candidate_name}!")
