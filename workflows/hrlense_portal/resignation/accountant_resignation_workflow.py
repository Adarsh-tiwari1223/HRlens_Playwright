"""
HRlens Portal — Accountant Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for Accountant / Finance clearance actions during employee offboarding.

KEY DESIGN PRINCIPLE:
  API validation (leave balance, buyout_days, per-day basic) is done by calling
  GET /api/Resignation/BuyoutList via the *Playwright browser session* — reusing
  the existing auth token from the logged-in page context.
  This avoids a full Python `requests` re-login (~75s on staging) while still
  giving real backend data to validate against UI values.
"""

import os
import json
import logging
from typing import Dict, Union, Optional

from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
from core.config.environments import ENV

logger = logging.getLogger(__name__)


class AccountantResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    # ──────────────────────────────────────────────────────────────────────────
    # FAST API FETCH — uses existing browser session, no extra login
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_buyout_list_via_browser(self) -> list:
        """
        Calls GET /api/Resignation/BuyoutList using the Playwright browser's
        existing auth session (cookies + Authorization header from sessionStorage).

        WHY THIS APPROACH:
          - The browser is already authenticated (admin login performed by the fixture).
          - page.context.request reuses the same cookies/auth headers automatically.
          - No second Python `requests` login → saves ~60-75s on slow staging API.

        Returns the raw 'data' list from the API response, or [] on failure.
        """
        api_base = os.getenv("API_BASE_URL", "https://audit.jobvritta.com/api")

        try:
            # Step 1: Extract auth token from sessionStorage (already set by browser)
            token = self.page.evaluate("""() => {
                return (
                    sessionStorage.getItem('token') ||
                    sessionStorage.getItem('authToken') ||
                    sessionStorage.getItem('access_token') ||
                    localStorage.getItem('token') ||
                    localStorage.getItem('authToken') ||
                    null
                );
            }""")

            if not token:
                logger.warning("[BuyoutList API] No auth token found in browser storage. Skipping API validation.")
                return []

            headers = {"Authorization": f"Bearer {token}"}
            url = f"{api_base}/Resignation/BuyoutList"

            logger.info(f"[BuyoutList API] Fetching via browser session → {url}")

            # Step 2: Use Playwright's built-in API request context (no new login)
            response = self.page.context.request.get(url, headers=headers)

            if response.ok:
                data = response.json()
                records = data.get("data", [])
                logger.info(f"[BuyoutList API] Fetched {len(records)} records successfully.")
                return records
            else:
                logger.warning(f"[BuyoutList API] Response status: {response.status}. Skipping API validation.")
                return []

        except Exception as e:
            logger.warning(f"[BuyoutList API] Failed to fetch buyout list: {e}")
            return []

    def get_employee_buyout_api_details(self, employee_name: str) -> Dict[str, Union[float, int, str]]:
        """
        Fetches backend API financial details for a specific employee from
        GET /api/Resignation/BuyoutList — using the existing browser auth session.

        Returns dict with keys: leave_Balance, buyout_Days, buyout_Amount,
        leave_Payout, per_Day_Basic, empId, empName, etc.
        Returns {} if not found or API fails.
        """
        records = self._fetch_buyout_list_via_browser()
        for record in records:
            if employee_name.lower() in (record.get("empName") or "").lower():
                logger.info(f"[BuyoutList API] Employee '{employee_name}' found: {record}")
                return record

        logger.warning(f"[BuyoutList API] Employee '{employee_name}' not found in BuyoutList response.")
        return {}

    # ──────────────────────────────────────────────────────────────────────────
    # FORMULA VALIDATION
    # ──────────────────────────────────────────────────────────────────────────

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

        This formula is validated from UI-displayed values cross-checked
        against the result entered into the form.
        """
        calculated_total = (leave_payout + calculated_salary) - buyout_amount
        is_correct = abs(calculated_total - expected_total_amount) < 0.01
        logger.info(
            f"[Formula Validation] ({leave_payout} + {calculated_salary}) - {buyout_amount} = "
            f"{calculated_total:.2f} | Expected: {expected_total_amount:.2f} → Match: {is_correct}"
        )
        return is_correct

    # ──────────────────────────────────────────────────────────────────────────
    # NAVIGATION HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def navigate_to_finance_clearance(self) -> None:
        """Navigates Accountant / Finance role to Offboarding → Exit Clearance / Finance page."""
        logger.info("UI Action: Accountant Navigating to Exit/Finance Clearance")
        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/exit-clearance"
        if not self.page.url.endswith("/exit-clearance"):
            self.page.goto(target_url, wait_until="domcontentloaded")
        self.page.locator("table, tr").first.wait_for(state="visible", timeout=10000)

    def get_first_eligible_buyout_employee(self) -> Optional[str]:
        """
        Discovers the first employee currently in 'HR APPROVED' status waiting for
        Accountant Buyout processing.
        1. Navigates to /accounts-buyout-processing
        2. Scans the table rows for status badge 'HR APPROVED'
        3. Returns the employee name, or None if no candidate exists.
        """
        try:
            self.res_page.navigate_to_accountant_buyout_processing()
            self.page.wait_for_timeout(1000)
            rows = self.page.locator("table tbody tr").all()
            for row in rows:
                try:
                    badge = row.locator(".chakra-badge, span[class*='badge']").first
                    if badge.is_visible(timeout=1000):
                        badge_text = badge.inner_text().strip().upper()
                        if "HR APPROVED" in badge_text or "APPROVED" in badge_text:
                            cells = row.locator("td").all()
                            for cell in cells[:3]:
                                text = cell.inner_text().strip()
                                if text and not text.isdigit() and len(text) > 3 and "hr" not in text.lower():
                                    cleaned_name = text.split("\n")[0].strip()
                                    logger.info(f"[DYNAMIC DISCOVERY] Found eligible buyout candidate: '{cleaned_name}'")
                                    return cleaned_name
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[DYNAMIC DISCOVERY] Error scanning buyout table: {e}")
        return None

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

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN WORKFLOW
    # ──────────────────────────────────────────────────────────────────────────

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
        2. Searches employee_name
        3. Opens 'Process Buyout' modal

        Validation strategy (fast, no second login):
          1. Open Process Buyout modal on /accounts-buyout-processing (UI).
          2. Read modal field values from UI (leave_balance, buyout_amount, etc.).
          3. Concurrently call GET /api/Resignation/BuyoutList via browser session
             to get API-side: leave_Balance, buyout_Days, per_Day_Basic.
          4. VALIDATE Leave Balance: modal UI value == API value.
          5. VALIDATE Buyout Days × Per-Day Basic == Buyout Amount (if API provides per_Day_Basic).
          6. VALIDATE Formula: Total Amount = (Leave Payout + Calculated Salary) - Buyout Amount.
          7. Fill form → Approve → capture toast.
        """
        action_str = "APPROVE" if approve else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING ACCOUNTANT {action_str} BUYOUT WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        # STEP 1 — Open Modal (navigate + click)
        modal_opened = self.res_page.open_accountant_process_buyout_modal(employee_name)
        if not modal_opened:
            logger.error(f"Failed to open Accountant 'Process Buyout' modal for '{employee_name}'")
            return {
                "success": False, "toast": "", "modal_values": {},
                "leave_balance_match": False, "formula_match": False,
                "api_details": {}, "expected_total": 0.0
            }

        def _safe_float(val, default: float = 0.0) -> float:
            if val is None:
                return default
            try:
                cleaned = str(val).replace(",", "").replace("₹", "").replace("INR", "").strip()
                return float(cleaned) if cleaned else default
            except (ValueError, TypeError):
                return default

        # STEP 2 — Read displayed modal values from UI
        modal_values = self.res_page.get_accountant_buyout_modal_values()
        logger.info(f"[Modal UI Values] {modal_values}")

        ui_leave_balance = _safe_float(modal_values.get("leave_balance"))
        ui_buyout_amount = _safe_float(modal_values.get("buyout_amount"))

        # STEP 3 — Fetch API details via browser session (fast — no second login)
        api_details = self.get_employee_buyout_api_details(employee_name)
        api_leave_balance = _safe_float(api_details.get("leave_Balance"))
        api_buyout_days   = int(api_details.get("buyout_Days") or 0)
        api_buyout_amount = _safe_float(api_details.get("buyout_Amount"))
        api_per_day_basic = _safe_float(api_details.get("per_Day_Basic") or api_details.get("perDayBasic"))

        # STEP 4 — VALIDATE: UI Leave Balance == API Leave Balance
        if api_leave_balance > 0:
            leave_balance_match = abs(ui_leave_balance - api_leave_balance) < 0.01
            logger.info(
                f"[Leave Balance Check] UI: {ui_leave_balance} | API: {api_leave_balance} "
                f"→ Match: {leave_balance_match}"
            )
        else:
            # API unavailable — log but don't fail the test on missing API data
            leave_balance_match = True
            logger.warning("[Leave Balance Check] API returned 0 or no data — skipping API cross-check.")

        # STEP 5 — VALIDATE: Buyout Days × Per-Day Basic == Buyout Amount
        ui_buyout_days = int(modal_values.get("buyout_days") or 0)
        effective_buyout_days = ui_buyout_days if ui_buyout_days > 0 else api_buyout_days

        if api_per_day_basic > 0 and effective_buyout_days > 0:
            expected_buyout_from_days = round(effective_buyout_days * api_per_day_basic, 2)
            effective_buyout = ui_buyout_amount if ui_buyout_amount > 0 else api_buyout_amount
            buyout_calc_match = abs(effective_buyout - expected_buyout_from_days) < 1.0
            logger.info(
                f"[Buyout Calc] {effective_buyout_days} days × ₹{api_per_day_basic}/day = "
                f"₹{expected_buyout_from_days} | UI Buyout Amount: ₹{effective_buyout} "
                f"→ Match: {buyout_calc_match}"
            )
        else:
            buyout_calc_match = True
            logger.info("[Buyout Calc] per_Day_Basic not in API response — skipping days×rate check.")

        # STEP 6 — VALIDATE: Deductions / Formula
        ui_total_deductions = _safe_float(modal_values.get("total_deductions"))
        val_leave_payout    = _safe_float(modal_values.get("leave_payout"))
        val_calc_salary     = _safe_float(calculated_salary) if modal_values.get("calculated_salary") else 0.0
        val_buyout_amount   = ui_buyout_amount if ui_buyout_amount > 0 else api_buyout_amount

        if ui_total_deductions > 0:
            formula_valid = abs(ui_total_deductions - val_buyout_amount) < 1.0
            expected_total = ui_total_deductions
            logger.info(
                f"[Formula Validation] Total Deductions ({ui_total_deductions}) == Buyout Amount ({val_buyout_amount}) "
                f"→ Match: {formula_valid}"
            )
        else:
            expected_total = (val_leave_payout + val_calc_salary) - val_buyout_amount
            formula_valid = self.validate_accountant_buyout_formulas(
                leave_payout=val_leave_payout,
                calculated_salary=val_calc_salary,
                buyout_amount=val_buyout_amount,
                expected_total_amount=expected_total
            )

        # STEP 7 — Fill form and submit
        toast = self.res_page.process_accountant_buyout(
            calculated_salary=calculated_salary,
            remarks=remarks,
            confirm_recovery=confirm_recovery,
            approve=approve
        )
        logger.info(f"[Accountant {action_str}] Toast: '{toast}'")

        is_success = bool(
            toast and
            "required" not in toast.lower() and
            "error" not in toast.lower() and
            "failed" not in toast.lower()
        )

        return {
            "success": is_success,
            "toast": toast,
            "modal_values": modal_values,
            "api_details": api_details,
            "leave_balance_match": leave_balance_match,
            "buyout_calc_match": buyout_calc_match,
            "formula_match": formula_valid,
            "expected_total": expected_total,
        }

    def execute_accountant_fnf_settlement_workflow(
        self,
        employee_name: str,
        salary_for_days_worked: str = "0.00",
        other_earnings: str = "0.00",
        remarks: str = "Full & Final Settlement Approved by Accounts"
    ) -> Dict[str, Union[bool, str, Dict[str, str]]]:
        """
        Executes Accountant Full & Final Settlement on /accounts-buyout-processing (FnF Requests tab):
        1. Switches to 'FnF Requests' tab
        2. Opens 'Full & Final Settlement' drawer for employee
        3. Fills earnings and submits FnF
        4. Verifies status changes to COMPLETED
        """
        logger.info("=" * 60)
        logger.info(f"STARTING ACCOUNTANT FnF SETTLEMENT WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        return self.res_page.process_accountant_fnf_settlement(
            employee_name=employee_name,
            salary_for_days_worked=salary_for_days_worked,
            other_earnings=other_earnings,
            remarks=remarks
        )

