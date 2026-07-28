"""
Increment & Negotiation Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for salary increment proposals, negotiations, and summary reports.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.increment.increment_page import IncrementPage
from pages.hrlense_portal.increment.negotiation_page import NegotiationPage
from pages.hrlense_portal.increment.increment_summary_page import IncrementSummaryPage

logger = logging.getLogger(__name__)

class IncrementWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.increment_page = IncrementPage(page)
        self.negotiation_page = NegotiationPage(page)
        self.summary_page = IncrementSummaryPage(page)

    def process_salary_increment_workflow(self, increment_data: dict):
        """Workflow to initiate increment proposal, handle negotiation, and verify summary."""
        logger.info(f"[WORKFLOW] Initiating salary increment workflow for employee: {increment_data.get('employee_id', 'N/A')}")
        self.increment_page.go_to_increment()
        self.increment_page.select_company(increment_data.get("company", "TEK Inspirations LLC"))
        self.increment_page.select_branch(increment_data.get("branch", "Varanasi"))
        self.increment_page.select_department(increment_data.get("department", "Developer"))
        self.increment_page.run_assessment()
        logger.info("[WORKFLOW] Salary increment assessment executed")

    def execute_employee_negotiation_workflow(self, counter_offer: str = "15000"):
        """Workflow for employee login, counter-offer submission, and negotiation verification."""
        logger.info(f"[WORKFLOW] Submitting counter-offer of {counter_offer} in negotiation workflow")
        self.negotiation_page.navigate_to_negotiation()
        self.negotiation_page.enter_counter_offer(counter_offer)
        self.negotiation_page.submit()
        logger.info("[WORKFLOW] Counter offer submitted successfully")
