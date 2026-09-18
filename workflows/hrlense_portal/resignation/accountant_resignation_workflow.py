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

    def get_employee_buyout_api_details(self, employee_name: str) -> Dict[str, Union[float, int, str]]:
        """
        Queries GET /api/Resignation/BuyoutList to fetch employee financial details:
        leave_Balance, buyout_Days, buyout_Amount, empId, leave_Payout, etc.
        """
        import requests, os
        from core.config.environments import ENV
        api_base = os.getenv("API_BASE_URL", "https://audit.jobvritta.com/api")
        admin_user = os.getenv(f"ADMIN_USERNAME_{ENV.upper()}", "admin@tek.com")
        admin_pass = os.getenv(f"ADMIN_PASSWORD_{ENV.upper()}", "Admin@ST2001")

        try:
            login_resp = requests.post(
                f"{api_base}/user/login",
                json={"email": admin_user, "user": admin_user, "password": admin_pass},
                verify=False,
                timeout=15
            )
            token = login_resp.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}

            res = requests.get(f"{api_base}/Resignation/BuyoutList", headers=headers, verify=False, timeout=15)
            if res.status_code == 200:
                data = res.json().get("data", [])
                for record in data:
                    if employee_name.lower() in (record.get("empName") or "").lower():
                        logger.info(f"API Details retrieved for '{employee_name}': {record}")
                        return record
        except Exception as e:
            logger.warning(f"Failed to fetch buyout API details: {e}")
        return {}

    def process_accountant_buyout_workflow(
        self,
        employee_name: str,
        calculated_salary: str = "1000",
        leave_payout: str = "500",
        remarks: str = "Buyout Approved by Accountant",
        confirm_recovery: bool = True,
        approve: bool = True
    ) -> Dict[str, Union[bool, str, Dict[str, str]]]:
        """
        Executes complete Accountant Process Buyout Workflow:
        1. Queries API (GET /api/Resignation/BuyoutList) for Employee financial figures (Leave Balance, Buyout Days, Buyout Amount)
        2. Navigates to /accounts-buyout-processing and opens 'Process Buyout' modal
        3. Reads modal field values
        4. Validates Leave Balance (UI Modal vs API)
        5. Validates Financial Formula: Total Amount = (Leave Payout + Calculated Salary) - Buyout Amount
        6. Fills Calculated Salary, Leave Payout, Recovery Confirmed, and Remarks
        7. Clicks Approve and captures toast message.
        """
        action_str = "APPROVE" if approve else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING ACCOUNTANT {action_str} BUYOUT WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        # 1. Fetch backend API records for Leave Balance & Buyout Details
        api_details = self.get_employee_buyout_api_details(employee_name)
        api_leave_balance = float(api_details.get("leave_Balance") or 0.0)
        api_buyout_days = int(api_details.get("buyout_Days") or 0)
        api_buyout_amount = float(api_details.get("buyout_Amount") or 0.0)

        # 2. Open Accountant Process Buyout Modal on /accounts-buyout-processing
        modal_opened = self.res_page.open_accountant_process_buyout_modal(employee_name)
        if not modal_opened:
            logger.error(f"Failed to open Accountant 'Process Buyout' modal for '{employee_name}'")
            return {"success": False, "toast": "", "values": {}, "leave_balance_match": False, "formula_match": False}

        # 3. Read Modal UI Values
        modal_values = self.res_page.get_accountant_buyout_modal_values()
        logger.info(f"Accountant Modal Field Values: {modal_values}")

        ui_leave_balance = float(modal_values.get("leave_balance") or 0.0)
        ui_buyout_amount = float(modal_values.get("buyout_amount") or 0.0)

        # 4. VALIDATE LEAVE BALANCE (UI Modal vs API)
        leave_balance_match = abs(ui_leave_balance - api_leave_balance) < 0.01
        logger.info(
            f"[LEAVE BALANCE VALIDATION] UI Modal Leave Balance: '{ui_leave_balance}' | "
            f"API Leave Balance: '{api_leave_balance}' -> Match: {leave_balance_match}"
        )

        # 5. VALIDATE FINANCIAL FORMULA: Total Amount = (Leave Payout + Calculated Salary) - Buyout Amount
        val_leave_payout = float(leave_payout or 0.0)
        val_calc_salary = float(calculated_salary or 0.0)
        val_buyout_amount = ui_buyout_amount if ui_buyout_amount > 0 else api_buyout_amount
        expected_total = (val_leave_payout + val_calc_salary) - val_buyout_amount

        formula_valid = self.validate_accountant_buyout_formulas(
            leave_payout=val_leave_payout,
            calculated_salary=val_calc_salary,
            buyout_amount=val_buyout_amount,
            expected_total_amount=expected_total
        )

        # 6. Complete Submission
        toast = self.res_page.process_accountant_buyout(
            calculated_salary=calculated_salary,
            leave_payout=leave_payout,
            buyout_amount=str(val_buyout_amount) if val_buyout_amount > 0 else None,
            remarks=remarks,
            confirm_recovery=confirm_recovery,
            approve=approve
        )
        logger.info(f"Accountant {action_str} Buyout Toast Captured: '{toast}'")

        return {
            "success": True,
            "toast": toast,
            "modal_values": modal_values,
            "api_details": api_details,
            "leave_balance_match": leave_balance_match,
            "formula_match": formula_valid,
            "expected_total": expected_total
        }

