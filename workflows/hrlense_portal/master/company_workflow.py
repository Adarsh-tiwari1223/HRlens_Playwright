"""
Company Master Workflow Layer for HR Lens Portal Master Module.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.master.company_page import CompanyPage

logger = logging.getLogger(__name__)

class CompanyWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.company_page = CompanyPage(page)

    def create_company_workflow(self, company_data: dict):
        logger.info(f"[WORKFLOW] Creating company master: {company_data.get('company_name', 'N/A')}")
        self.company_page.navigate_to_company_master()
        self.company_page.add_new_company(company_data)

    def create_company_with_manual_director_from_scratch(self, company_data: dict, director_data: dict) -> str:
        """
        ADD Operation:
        1. Open Add Company modal
        2. Fill company form from scratch (Name, Code, Address, Zip Code)
        3. Click 'Add New' -> click 'Director Name' label -> fill manual director form -> click 'Add'
        4. Submit/Save new company
        """
        logger.info(f"[WORKFLOW] Creating company from scratch: {company_data.get('company_name')} with manual director: {director_data.get('name')}")
        self.company_page.navigate_to_company_master()
        self.company_page.click_add_new_company()
        self.company_page.fill_company_details(
            name=company_data.get("company_name"),
            address=company_data.get("address"),
            zip_code=company_data.get("zip_code"),
            country=company_data.get("country"),
            state=company_data.get("state"),
            city=company_data.get("city"),
            code=company_data.get("code")
        )
        self.company_page.add_manual_director(
            name=director_data.get("name"),
            email=director_data.get("email"),
            phone=director_data.get("phone")
        )
        self.company_page.click_add_company()
        self.page.wait_for_timeout(1000)
        return self.company_page.wait_for_toast_message()

    def edit_company_add_manual_director_only(self, company_name: str, director_data: dict) -> str:
        """
        EDIT Operation:
        1. Open existing company in edit mode
        2. Click 'Add New' -> click 'Director Name' label -> fill manual director form -> click 'Add'
        3. Click 'Update Company' to submit
        """
        logger.info(f"[WORKFLOW] Editing company '{company_name}' to add manual director: {director_data.get('name')}")
        self.company_page.navigate_to_company_master()
        self.company_page.edit_company(company_name)
        self.company_page.add_manual_director(
            name=director_data.get("name"),
            email=director_data.get("email"),
            phone=director_data.get("phone")
        )
        self.company_page.click_update_company()
        self.page.wait_for_timeout(1000)
        return self.company_page.wait_for_toast_message()
