import pytest
from datetime import datetime, timedelta
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.employee.candidate_page import CandidatePage

@pytest.mark.ui
@pytest.mark.standalone
def test_schedule_and_loi_only(page):
    """
    STANDALONE TEST: Only schedules an interview and sends the LOI.
    Assumes the candidate ALREADY exists and is in the 'Applied' state.
    """
    # 🛑 UPDATE THIS WITH THE EXACT CANDIDATE NAME BEFORE RUNNING 🛑
    candidate_name = "REPLACE_WITH_CANDIDATE_NAME"
    
    if candidate_name == "REPLACE_WITH_CANDIDATE_NAME":
        pytest.fail("You must update the 'candidate_name' variable in the script before running this standalone test!")
        
    # Setup login
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    candidate_page = CandidatePage(page)
    
    # 1. Schedule Interview
    now = datetime.now()
    interview_date = now.strftime("%Y-%m-%d")
    interview_time = (now + timedelta(minutes=35)).strftime("%H:%M")
    
    print(f"\n[ACTION] Scheduling interview for {candidate_name} at {interview_date} {interview_time}...")
    candidate_page.schedule_interview(
        candidate_name=candidate_name,
        date=interview_date,
        time=interview_time
    )
    
    # 2. Validate Salary and Send Offer Letter
    print(f"\n[ACTION] Generating and validating offer for {candidate_name}...")
    candidate_page.generate_and_validate_offer(
        candidate_name=candidate_name,
        doj=interview_date,
        gross_salary="15000"
    )
    
    print(f"\n[SUCCESS] LOI sent successfully to {candidate_name}!")
