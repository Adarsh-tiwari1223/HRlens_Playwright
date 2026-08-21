"""
Payroll Company Master Workflow Layer for HR Lens Portal Master Module.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.master.payroll_company_page import PayrollCompanyPage

logger = logging.getLogger(__name__)


class PayrollCompanyWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.payroll_company_page = PayrollCompanyPage(page)

    def create_payroll_company_with_manual_director_from_scratch(self, company_data: dict, director_data: dict) -> str:
        """
        ADD Operation:
        1. Open Add Payroll Company modal
        2. Fill Payroll Company form from scratch (1-12 strict field sequence)
        3. Click 'Add New' -> click 'Director Name' label -> fill manual director form -> click 'Add'
        4. Submit/Save new Payroll Company
        """
        logger.info(f"[WORKFLOW] Creating Payroll Company from scratch: {company_data.get('company_name')} with manual director: {director_data.get('name')}")
        self.payroll_company_page.open_add_payroll_company_modal()
        self.payroll_company_page.fill_payroll_company_details(
            name=company_data.get("company_name"),
            address=company_data.get("address"),
            zip_code=company_data.get("zip_code"),
            country=company_data.get("country"),
            state=company_data.get("state"),
            city=company_data.get("city"),
            code=company_data.get("code")
        )
        self.payroll_company_page.add_manual_director(
            name=director_data.get("name"),
            email=director_data.get("email"),
            phone=director_data.get("phone")
        )
        self.payroll_company_page.click_submit()
        return self.payroll_company_page.get_form_error_or_toast()

    def edit_payroll_company_add_manual_director_only(self, company_name: str, director_data: dict) -> str:
        """
        EDIT Operation:
        1. Open existing Payroll Company in edit mode
        2. Click 'Add New' -> click 'Director Name' label -> fill manual director form -> click 'Add'
        3. Submit/Update Payroll Company
        """
        logger.info(f"[WORKFLOW] Editing Payroll Company '{company_name}' to add manual director: {director_data.get('name')}")
        self.payroll_company_page.edit_payroll_company(company_name)
        self.payroll_company_page.add_manual_director(
            name=director_data.get("name"),
            email=director_data.get("email"),
            phone=director_data.get("phone")
        )
        self.payroll_company_page.click_submit()
        return self.payroll_company_page.get_form_error_or_toast()
