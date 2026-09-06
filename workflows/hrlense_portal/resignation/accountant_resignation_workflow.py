"""
HRlens Portal — Accountant Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for Accountant / Finance clearance actions during employee offboarding.
"""

from typing import Dict, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
import logging
logger = logging.getLogger(__name__)



class AccountantResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def navigate_to_finance_clearance(self) -> None:
        """Navigates Accountant / Finance role to Offboarding -> Finance Clearance tab."""
        logger.info("UI Action: Accountant Navigating to Finance Clearance")
        clearance_link = self.page.locator("a[href*='finance-clearance'], a:has-text('Finance Clearance')").first
        clearance_link.wait_for(state="visible", timeout=10000)
        clearance_link.click()
        self.page.wait_for_load_state("networkidle")

    def inspect_employee_buyout_settlement_workflow(self, employee_name: str) -> Dict[str, Union[bool, str]]:
        """
        Executes Accountant workflow to inspect employee buyout amount and pending dues clearance.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING ACCOUNTANT BUYOUT SETTLEMENT WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        self.navigate_to_finance_clearance()
        row = self.page.locator(f"tr:has-text('{employee_name}')").first

        is_found = row.is_visible(timeout=5000)
        status_text = row.locator(".chakra-badge").first.inner_text().strip() if is_found else ""

        return {
            "employee_found": is_found,
            "finance_status": status_text,
        }

    def validate_accountant_buyout_formulas(
        self,
        leave_payout: float,
        calculated_salary: float,
        buyout_amount: float,
        expected_total_amount: float
    ) -> bool:
        """
        Validates the Accountant financial formula:
        Total Amount = (Leave Payout + Calculated Salary) - Buyout Amount
        """
        calculated_total = (leave_payout + calculated_salary) - buyout_amount
        is_correct = abs(calculated_total - expected_total_amount) < 0.01
        logger.info(f"Formula Validation: ({leave_payout} + {calculated_salary}) - {buyout_amount} = {calculated_total:.2f} (Expected: {expected_total_amount:.2f}) -> Match: {is_correct}")
        return is_correct

    def process_accountant_buyout_workflow(
        self,
        employee_name: str,
        calculated_salary: str = "0",
        remarks: str = "Buyout Approved by Accountant",
        confirm_recovery: bool = True,
        approve: bool = True
    ) -> Dict[str, Union[bool, str, Dict[str, str]]]:
        """
        Executes complete Accountant Process Buyout Workflow:
        1. Navigates to /accounts-buyout-processing
        2. Searches employee_name ('Adarsh Tiwari')
        3. Clicks Action icon/button to open 'Process Buyout' modal
        4. Reads and validates modal values (Leave Balance, Leave Payout, Calculated Salary, Buyout Amount, Total Amount)
        5. Fills Calculated Salary, Recovery Confirmed, and Remarks
        6. Clicks Approve/Reject and captures toast message.
        """
        action_str = "APPROVE" if approve else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING ACCOUNTANT {action_str} BUYOUT WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        modal_opened = self.res_page.open_accountant_process_buyout_modal(employee_name)
        if not modal_opened:
            logger.error(f"Failed to open Accountant 'Process Buyout' modal for '{employee_name}'")
            return {"success": False, "toast": "", "values": {}}

        modal_values = self.res_page.get_accountant_buyout_modal_values()
        logger.info(f"Accountant Modal Field Values: {modal_values}")

        toast = self.res_page.process_accountant_buyout(
            calculated_salary=calculated_salary,
            remarks=remarks,
            confirm_recovery=confirm_recovery,
            approve=approve
        )
        logger.info(f"Accountant {action_str} Buyout Toast Captured: '{toast}'")

        return {
            "success": True,
            "toast": toast,
            "modal_values": modal_values
        }

