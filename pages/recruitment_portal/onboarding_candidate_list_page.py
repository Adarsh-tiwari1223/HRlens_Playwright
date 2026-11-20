"""
Page Object for HRlens Recruitment Portal: Onboarding Candidate List Page.
URL: /onboardingCandidateList

Owns:
- Locators for header, search, filter popover, table columns, rows, status badges, and action buttons.
- Search and filtering operations.
- Candidate table verification and status retrieval.
"""

import logging
from typing import Optional
from playwright.sync_api import Page, Locator
from core.config import settings
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class OnboardingCandidateListPage(BasePage):
    """Page Object for Onboarding Candidate List (/onboardingCandidateList)."""

    def __init__(self, page: Page):
        super().__init__(page)
        # Header & Navigation
        self.page_heading = self.page.locator(".page_heading p, p:has-text('Onboarding Candidate List')")

        # Search & Filter
        self.search_input = self.page.locator("input[placeholder*='Search Candidates']")
        self.filter_btn = self.page.locator("img[alt='Filter'], #popover-trigger-_r_3l_")

        # Table & Rows
        self.table = self.page.locator("table.chakra-table")
        self.table_header = self.page.locator("table.chakra-table thead tr")
        self.table_rows = self.page.locator("table.chakra-table tbody tr")

    def navigate_to_onboarding_list(self):
        """Navigates directly to the Onboarding Candidate List page."""
        target_url = f"{settings.BASE_URL}/onboardingCandidateList"
        logger.info(f"[UI] Navigating to Onboarding Candidate List: {target_url}")
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.page_heading.first.wait_for(state="visible", timeout=15000)
        logger.info("[UI] Onboarding Candidate List page loaded successfully.")

    def search_candidate(self, candidate_name: str):
        """Searches for a candidate using the search box."""
        logger.info(f"[UI] Searching for candidate: '{candidate_name}'")
        self.search_input.first.wait_for(state="visible", timeout=10000)
        self.search_input.first.fill(candidate_name)
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("domcontentloaded")

    def get_candidate_row(self, candidate_name: str) -> Locator:
        """Returns the Locator for the table row corresponding to candidate_name."""
        return self.table_rows.filter(has_text=candidate_name).first

    def is_candidate_present(self, candidate_name: str, timeout: int = 10000) -> bool:
        """Checks if the candidate is visible in the table."""
        try:
            row = self.get_candidate_row(candidate_name)
            row.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_candidate_details(self, candidate_name: str) -> dict:
        """
        Extracts row data for candidate:
        Columns: [S.No, Name, Job Profile, Payroll Company, Branch, Department, DOJ, Status, Action]
        """
        row = self.get_candidate_row(candidate_name)
        row.wait_for(state="visible", timeout=10000)
        cells = row.locator("td").all()
        texts = [c.inner_text().strip() for c in cells]

        return {
            "s_no": texts[0] if len(texts) > 0 else "",
            "name": texts[1] if len(texts) > 1 else "",
            "job_profile": texts[2] if len(texts) > 2 else "",
            "payroll_company": texts[3] if len(texts) > 3 else "",
            "branch": texts[4] if len(texts) > 4 else "",
            "department": texts[5] if len(texts) > 5 else "",
            "doj": texts[6] if len(texts) > 6 else "",
            "status": texts[7] if len(texts) > 7 else "",
        }

    def get_candidate_status(self, candidate_name: str) -> str:
        """Extracts the status badge text for candidate (e.g. 'Accepted', 'Send LOI', 'Joined')."""
        details = self.get_candidate_details(candidate_name)
        status = details.get("status", "")
        logger.info(f"[UI] Candidate '{candidate_name}' Status in Onboarding List: '{status}'")
        return status

    def verify_candidate_status(self, candidate_name: str, expected_status: str = "Accepted") -> bool:
        """Verifies candidate appears in the list with expected_status."""
        actual_status = self.get_candidate_status(candidate_name)
        matches = actual_status.strip().lower() == expected_status.strip().lower()
        logger.info(f"[UI] Verification: Candidate='{candidate_name}', Expected='{expected_status}', Actual='{actual_status}' -> Matches={matches}")
        return matches

    def click_candidate_action(self, candidate_name: str):
        """Clicks the Action Arrow icon for the given candidate row."""
        row = self.get_candidate_row(candidate_name)
        action_btn = row.locator("img[alt='Action'], td:last-child img, td:last-child button, svg").first
        logger.info(f"[UI] Clicking Action Arrow for candidate: '{candidate_name}'")
        action_btn.click()
        self.page.wait_for_load_state("domcontentloaded")
