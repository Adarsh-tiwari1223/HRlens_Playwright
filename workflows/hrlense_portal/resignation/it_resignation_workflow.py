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
        asset_condition: str = "Good Condition",
        remarks: str = "IT Asset clearance verified & completed"
    ) -> Dict[str, Union[bool, str]]:
        """
        Executes IT Person workflow to inspect employee's assigned assets and issue IT Clearance.
        Handles both cases dynamically:
        - If employee HAS assets: Processes asset inspection & return.
        - If employee has NO assets: Verifies and completes clearance task directly.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING DYNAMIC IT ASSET CLEARANCE WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        return self.res_page.process_it_person_asset_clearance(
            employee_name=employee_name,
            asset_condition=asset_condition,
            remarks=remarks
        )

