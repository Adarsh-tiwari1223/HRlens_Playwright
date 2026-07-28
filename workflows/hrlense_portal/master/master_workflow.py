"""
Master Management Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for company setup, master configurations, and global settings.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.master.company_page import CompanyPage

logger = logging.getLogger(__name__)

class MasterWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.company_page = CompanyPage(page)

    def create_company_master_workflow(self, company_data: dict):
        """Workflow to configure and verify company master settings."""
        logger.info(f"[WORKFLOW] Setting up company master: {company_data.get('company_name', 'N/A')}")
        self.company_page.navigate_to_company_master()
        self.company_page.add_new_company(company_data)
        logger.info("[WORKFLOW] Company master created successfully")

    def verify_company_crud_workflow(self, company_name: str):
        """Workflow to execute company edit and validation checks."""
        logger.info(f"[WORKFLOW] Verifying company CRUD workflow for: '{company_name}'")
        self.company_page.navigate_to_company_master()
        self.company_page.edit_company(company_name)
        logger.info("[WORKFLOW] Company CRUD workflow executed")
