"""
Asset Assignment Workflow Layer for HR Lens Portal.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage

logger = logging.getLogger(__name__)

class AssetAssignmentWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.assignment_page = AssetAssignmentPage(page)

    def assign_asset_workflow(self, assignment_data: dict):
        logger.info(f"[WORKFLOW] Assigning asset to employee: {assignment_data.get('employee_name', 'N/A')}")
        self.assignment_page.assign_asset_to_employee(assignment_data)
