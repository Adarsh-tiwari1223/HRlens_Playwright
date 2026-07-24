import pytest
from datetime import datetime, timedelta
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.employee.onboarding_page import OnboardingPage

@pytest.fixture
def onboarding_page(page):
    """Fixture to log in and initialize the OnboardingPage object."""
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")
    return OnboardingPage(page)

@pytest.mark.ui
@pytest.mark.onboarding
def test_verify_and_send_offer(onboarding_page):
    """
    Test verifying candidate documents and generating the final Offer/Appointment Letter.
    NOTE: This test assumes the candidate has ALREADY manually accepted their LOI via OTP.
    """
    # Hardcoded to the user's manual trace for debugging the Network Error
    candidate_name = "Mannat Rajagopalan"
    
    # Calculate a valid DOJ (tomorrow)
    doj = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n[TEST START] Automating Onboarding for {candidate_name}")
    
    # 1. Navigate to Offers & Onboarding module
    onboarding_page.navigate_to_onboarding()
    
    # 2. Find Candidate and Open Verification Modal
    onboarding_page.open_verification_modal(candidate_name)
    
    # 3. Fill and Send Verification Form
    onboarding_page.fill_verification_form_and_send(candidate_name, doj=doj)
