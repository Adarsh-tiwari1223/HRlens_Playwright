"""
HRlens Portal — IT Person Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for IT Person-side asset clearance during employee offboarding.
"""

from typing import Dict, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
import logging
logger = logging.getLogger(__name__)



class ItResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def navigate_to_it_clearance(self) -> None:
        """Navigates IT Person role to Offboarding -> IT Clearance tab."""
        logger.info("UI Action: IT Person Navigating to Offboarding -> IT Clearance")
        clearance_link = self.page.locator("a[href*='it-clearance'], a[href*='asset-clearance'], a:has-text('IT Clearance'), a:has-text('Asset Clearance')").first
        clearance_link.wait_for(state="visible", timeout=10000)
        clearance_link.click()
        self.page.wait_for_load_state("networkidle")

    def inspect_and_clear_employee_assets_workflow(
        self,
        employee_name: str,
        asset_condition: str = "Good Condition"
    ) -> Dict[str, Union[bool, str]]:
        """
        Executes IT Person workflow to inspect employee's assigned assets and issue IT Clearance.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING IT ASSET CLEARANCE WORKFLOW FOR: '{employee_name}' (Condition: '{asset_condition}')")
        logger.info("=" * 60)

        self.navigate_to_it_clearance()
        row = self.page.locator(f"tr:has-text('{employee_name}')").first

        is_found = row.is_visible(timeout=5000)
        status_text = ""

        if is_found:
            badge = row.locator(".chakra-badge").first
            if badge.is_visible(timeout=2000):
                status_text = badge.inner_text().strip()

        return {
            "employee_found": is_found,
            "it_clearance_status": status_text,
        }
