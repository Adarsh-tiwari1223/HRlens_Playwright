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
