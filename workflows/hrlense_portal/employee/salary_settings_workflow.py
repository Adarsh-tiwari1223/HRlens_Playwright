"""
Salary Settings Workflow Layer for HR Lens Portal Employee Module.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.employee.salary_settings_page import SalarySettingsPage

logger = logging.getLogger(__name__)

class SalarySettingsWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.salary_settings_page = SalarySettingsPage(page)

    def configure_employee_salary_slab_workflow(self, salary_data: dict):
        logger.info("[WORKFLOW] Configuring employee salary slab settings")
        self.salary_settings_page.navigate_to_salary_settings()
        self.salary_settings_page.update_salary_parameters(salary_data)
