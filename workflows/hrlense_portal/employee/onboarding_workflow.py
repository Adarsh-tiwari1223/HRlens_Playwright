"""
Onboarding Workflow Layer for HR Lens Portal Employee Module.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.employee.onboarding_page import OnboardingPage

logger = logging.getLogger(__name__)

class OnboardingWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.onboarding_page = OnboardingPage(page)

    def execute_onboarding_wizard_workflow(self, onboarding_data: dict):
        logger.info(f"[WORKFLOW] Executing onboarding wizard for: {onboarding_data.get('name', 'N/A')}")
        self.onboarding_page.navigate_to_onboarding()
        self.onboarding_page.fill_wizard_steps(onboarding_data)
