"""
Employee Management Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for employee onboarding, profile updates,
salary settings, and offer/appointment letter template management.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.employee.employee_page import EmployeePage
from pages.hrlense_portal.employee.onboarding_page import OnboardingPage
from pages.hrlense_portal.employee.salary_settings_page import SalarySettingsPage
from pages.hrlense_portal.employee.offer_letter_template_page import OfferLetterTemplatePage
from pages.hrlense_portal.employee.appointment_letter_template_page import AppointmentLetterTemplatePage

logger = logging.getLogger(__name__)

class EmployeeWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.employee_page = EmployeePage(page)
        self.onboarding_page = OnboardingPage(page)
        self.salary_settings_page = SalarySettingsPage(page)
        self.offer_template_page = OfferLetterTemplatePage(page)
        self.appointment_template_page = AppointmentLetterTemplatePage(page)

    def onboard_new_employee_workflow(self, employee_data: dict):
        """Workflow for onboarding a new employee."""
        logger.info(f"[WORKFLOW] Onboarding new employee: {employee_data.get('name', 'N/A')}")
        self.employee_page.navigate_to_employee_list()
        self.employee_page.open_add_employee_modal()
        self.employee_page.fill_employee_details(employee_data)
        self.employee_page.save_employee()
        logger.info("[WORKFLOW] Employee onboarded successfully")

    def configure_salary_settings_workflow(self, salary_data: dict):
        """Workflow to configure employee salary settings and slab parameters."""
        logger.info("[WORKFLOW] Configuring employee salary settings")
        self.salary_settings_page.navigate_to_salary_settings()
        self.salary_settings_page.update_salary_parameters(salary_data)
        logger.info("[WORKFLOW] Salary settings configured successfully")

    def create_offer_letter_section_workflow(self, company_name: str, section_title: str, content: str):
        """Workflow to create an offer letter template section."""
        logger.info(f"[WORKFLOW] Creating offer letter section '{section_title}' for company '{company_name}'")
        self.offer_template_page.navigate_to_templates()
        self.offer_template_page.select_company(company_name)
        self.offer_template_page.add_section(title=section_title, content=content)
        logger.info("[WORKFLOW] Offer letter section created successfully")
