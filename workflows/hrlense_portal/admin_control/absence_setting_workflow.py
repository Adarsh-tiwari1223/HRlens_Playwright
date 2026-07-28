"""
Absence Setting Workflow Layer for HR Lens Portal Admin Control.

Encapsulates reusable business workflows for absence settings configuration,
branch overrides, and metric verification.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.admin_control.absence_setting_page import AbsenceSettingPage

logger = logging.getLogger(__name__)

class AbsenceSettingWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.absence_setting_page = AbsenceSettingPage(page)

    def configure_absence_settings_workflow(self, setting_data: dict):
        """Workflow to update and verify absence settings."""
        logger.info("[WORKFLOW] Configuring absence settings")
        self.absence_setting_page.navigate_to_settings()
        self.absence_setting_page.update_settings(setting_data)
        logger.info("[WORKFLOW] Absence settings updated successfully")
