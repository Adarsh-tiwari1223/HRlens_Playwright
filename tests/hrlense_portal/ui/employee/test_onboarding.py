import pytest
from datetime import datetime, timedelta
from core.config import settings
from workflows.hrlense_portal.employee.onboarding_workflow import OnboardingWorkflow


@pytest.fixture
def onboarding_workflow(admin_page):
    return OnboardingWorkflow(admin_page)


@pytest.mark.ui
@pytest.mark.e2e
@pytest.mark.regression
@pytest.mark.onboarding
def test_verify_and_send_offer(onboarding_workflow):
    """
    Test verifying candidate documents and generating the final Offer/Appointment Letter.
    NOTE: This test assumes the candidate has ALREADY manually accepted their LOI via OTP.
    """
    doj = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    onboarding_workflow.execute_onboarding_wizard_workflow({
        "name": "Mannat Rajagopalan",
        "doj": doj
    })
