"""
HRlens Portal — HR Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for HR-side resignation actions.
"""

from typing import Dict, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
import logging
logger = logging.getLogger(__name__)



class HrResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def execute_hr_revoke_request_workflow(self, employee_name: str) -> bool:
        """
        Executes HR Revoke Request Flow:
        1. Navigates Offboarding -> • Resignation Request (p:has-text('Resignation Requests'))
        2. Types dynamic employee_name in input[placeholder="Search employee by name..."]
        3. Inspects status badge (.chakra-badge) in tr:has-text(employee_name)
        4. If status is 'Resignation Requested' (or 'Applied'), clicks employee name to open modal (header:has-text('Resignation Details'))
        5. Verifies button:has-text('Revoke') is visible -> clicks Revoke -> clicks Confirm / Yes
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR REVOKE REQUEST WORKFLOW FOR EMPLOYEE: '{employee_name}'")
        logger.info("=" * 60)

        is_success = self.res_page.hr_revoke_request_flow(employee_name=employee_name)
        logger.info(f"HR Revoke Request Workflow Result for '{employee_name}': {is_success}")
        return is_success

    def verify_hr_table_status_workflow(self, employee_name: str) -> str:
        """
        Searches employee in HR Resignation table and reads status badge.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR TABLE STATUS VERIFICATION FOR EMPLOYEE: '{employee_name}'")
        logger.info("=" * 60)

        self.res_page.navigate_to_hr_resignation_approval()
        self.res_page.search_employee_in_hr_table(employee_name)
        status = self.res_page.get_hr_table_employee_status(employee_name)
        logger.info(f"HR Table Status for '{employee_name}': '{status}'")
        return status

    def validate_buyout_prevents_hr_revoke_workflow(self, employee_name: str) -> bool:
        """
        Verifies that when an Employee has applied for Buyout Request, HR's Revoke option is BLOCKED.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR BUYOUT REVOKE RESTRICTION WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        self.res_page.navigate_to_hr_resignation_approval()
        self.res_page.search_employee_in_hr_table(employee_name)
        status = self.res_page.get_hr_table_employee_status(employee_name)

        if "buyout" in status.lower():
            logger.info(f"Status is '{status}': Revoke option is BLOCKED as expected!")
            return False

        modal_opened = self.res_page.open_hr_resignation_details_modal(employee_name)
        if modal_opened:
            is_revoke_visible = self.res_page.is_modal_revoke_button_visible()
            return is_revoke_visible
        return False

    def process_buyout_request_workflow(self, employee_name: str, process: bool = True) -> str:
        """
        Executes HR Process Buyout Request Workflow:
        1. Navigates to Offboarding -> Resignation Approval
        2. Searches employee_name in table
        3. Clicks Actions hamburger button -> selects 'Buyout Request' menu item to open drawer
        4. Clicks 'Process Buyout' (or 'Reject Buyout') button and returns toast message!
        """
        action_str = "PROCESS" if process else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING HR {action_str} BUYOUT REQUEST WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        drawer_opened = self.res_page.open_hr_buyout_request_drawer(employee_name)
        if not drawer_opened:
            logger.error(f"Failed to open 'Buyout Request' drawer for '{employee_name}'")
            return ""

        toast = self.res_page.process_or_reject_hr_buyout(process=process)
        logger.info(f"HR {action_str} Buyout Toast Captured: '{toast}'")
        return toast

