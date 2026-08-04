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

    def add_manual_director_workflow(self, name: str, email: str, phone: str):
        """Workflow to add a manual director via inline 'Add New' form during company management."""
        logger.info(f"[WORKFLOW] Adding manual director: Name={name}, Email={email}, Phone={phone}")
        self.company_page.click_add_new_director_inline()
        self.company_page.fill_manual_director_form(name=name, email=email, phone=phone)
        self.company_page.click_add_manual_director_submit()
        self.page.wait_for_timeout(500)
