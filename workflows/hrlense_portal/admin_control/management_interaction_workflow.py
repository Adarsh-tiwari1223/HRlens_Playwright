"""
Management Interaction Workflow Layer for HR Lens Portal Admin Control.

Encapsulates reusable business workflows for case detail management, email dispatches,
and management interaction logging.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.admin_control.management_interaction_page import ManagementInteractionPage

logger = logging.getLogger(__name__)

class ManagementInteractionWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.interaction_page = ManagementInteractionPage(page)

    def log_management_interaction_workflow(self, interaction_data: dict):
        """Workflow to log management interaction and trigger notifications."""
        logger.info("[WORKFLOW] Logging management interaction")
        self.interaction_page.navigate_to_interactions()
        self.interaction_page.log_interaction(interaction_data)
        logger.info("[WORKFLOW] Management interaction logged successfully")
