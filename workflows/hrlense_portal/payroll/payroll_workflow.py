"""
Payroll Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for payroll processing, verification, and API/UI comparison.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.payroll.payroll_page import PayrollPage

logger = logging.getLogger(__name__)

class PayrollWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.payroll_page = PayrollPage(page)

    def process_monthly_payroll_workflow(self, branch_filter: str = "Varanasi - Inf"):
        """Workflow to navigate to payroll, apply branch filter, and trigger payroll calculation."""
        logger.info(f"[WORKFLOW] Processing monthly payroll with branch filter: '{branch_filter}'")
        self.payroll_page.navigate_to_payroll()
        self.payroll_page.apply_branch_filter(branch_filter)
        self.payroll_page.run_payroll()
        logger.info("[WORKFLOW] Monthly payroll processing executed")
        return self.payroll_page

    def get_payroll_ui_rows_workflow(self) -> list:
        """Workflow to retrieve table rows from the payroll UI."""
        return self.payroll_page.get_table_rows()
