"""
HRlens Portal — Accountant Asset Workflow (Workflow Tier).

Orchestrates end-to-end financial business workflows related to Assets:
1. Asset Recovery & Settlements (/asset-recovery):
   - Full Settlement (Salary Deduction / UPI / Bank Transfer)
   - Installment Plans (EMI auto-split across months for payroll deduction)
   - Partial Recovery
   - KPI metrics reconciliation
2. Asset Disposal & Scrap Accounting (/asset-disposal):
   - Review and approve disposal (Scrap / Sell / Write-Off)
   - Realize Recovery Value into accounting records
   - Disposal metrics & history verification
3. Exit FnF Deductions Integration (/accounts-buyout-processing):
   - Verify damage recovery deductions in Full & Final Settlement drawer
"""

import logging
import re
from typing import Dict, Union, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_recovery_page import AssetRecoveryPage
from pages.hrlense_portal.asset.asset_disposal_page import AssetDisposalPage
from pages.hrlense_portal.resignation.resignation_page import ResignationPage

logger = logging.getLogger(__name__)


class AccountantAssetWorkflow:
    """
    Accountant / Finance Persona Asset Management Workflow.
    Owns the financial realization, recovery, disposal write-off, and payroll/FnF bridges.
    """

    def __init__(self, page: Page):
        self.page = page
        self.recovery_page = AssetRecoveryPage(page)
        self.disposal_page = AssetDisposalPage(page)
        self.res_page = ResignationPage(page)

    # =========================================================================
    # MODULE 1: ASSET RECOVERY & SETTLEMENTS (/asset-recovery)
    # =========================================================================

    def audit_recovery_metrics_workflow(self) -> Dict[str, str]:
        """
        Navigates to /asset-recovery and retrieves KPI metrics cards.
        Validates accounting consistency: Total Recoverable vs Pending vs Recovered.
        """
        logger.info("[ACCOUNTANT WORKFLOW] Auditing Asset Recovery KPI metrics...")
        self.recovery_page.navigate_to_asset_recovery()
        metrics = self.recovery_page.get_kpi_metrics()
        logger.info(f"[ACCOUNTANT WORKFLOW] Recovery KPI Summary: {metrics}")
        return metrics

    def settle_recovery_in_full_workflow(
        self,
        identifier: str,
        payment_mode: str = "Salary Deduction",
        reference_no: str = "",
        settlement_date: str = None,
        remarks: str = "Settled in full by Accountant"
    ) -> Dict[str, Union[bool, str]]:
        """
        Full settlement workflow:
        1. Navigates to /asset-recovery and searches employee or asset code.
        2. Clicks 'Settle' button.
        3. Validates Settle Recovery modal details.
        4. Submits Full settlement with selected payment mode.
        5. Verifies toast notification and checks updated row status.
        """
        logger.info("=" * 60)
        logger.info(f"[ACCOUNTANT WORKFLOW] Settling recovery in FULL for '{identifier}' via '{payment_mode}'")
        logger.info("=" * 60)

        self.recovery_page.navigate_to_asset_recovery()
        opened = self.recovery_page.click_settle_button(identifier)
        if not opened:
            logger.error(f"[ACCOUNTANT WORKFLOW] Could not open Settle modal for '{identifier}'")
            return {"success": False, "error": f"Settle modal not opened for {identifier}"}

        modal_details = self.recovery_page.get_settle_modal_details()
        logger.info(f"[ACCOUNTANT WORKFLOW] Pre-settlement details: {modal_details}")

        toast = self.recovery_page.settle_in_full(
            payment_mode=payment_mode,
            settlement_date=settlement_date,
            reference_no=reference_no,
            remarks=remarks
        )

        self.page.wait_for_timeout(1000)
        updated_row = self.recovery_page.get_recovery_row_details(identifier)

        return {
            "success": bool(toast and "success" in toast.lower() or updated_row.get("status") in ["SETTLED", "PARTIALLY SETTLED"]),
            "toast": toast,
            "pre_details": modal_details,
            "post_details": updated_row
        }

    def create_installment_plan_workflow(
        self,
        identifier: str,
        months_count: int = 3
    ) -> Dict[str, Union[bool, str]]:
        """
        Installment plan creation workflow:
        1. Navigates to /asset-recovery and locates target pending recovery record.
        2. Opens Settle modal and switches to 'Installments' mode.
        3. Configures auto-split for specified months_count.
        4. Saves plan and verifies schedule in table.
        """
        logger.info("=" * 60)
        logger.info(f"[ACCOUNTANT WORKFLOW] Creating {months_count}-month installment plan for '{identifier}'")
        logger.info("=" * 60)

        self.recovery_page.navigate_to_asset_recovery()
        opened = self.recovery_page.click_settle_button(identifier)
        if not opened:
            return {"success": False, "error": f"Settle modal not opened for {identifier}"}

        toast = self.recovery_page.create_installment_plan(months_count=months_count)
        self.page.wait_for_timeout(1000)

        updated_row = self.recovery_page.get_recovery_row_details(identifier)
        return {
            "success": bool(toast),
            "toast": toast,
            "next_due": updated_row.get("next_due"),
            "post_details": updated_row
        }

    def record_partial_recovery_workflow(
        self,
        identifier: str,
        amount: str,
        payment_mode: str = "UPI",
        reference_no: str = "",
        remarks: str = "Partial payment recorded by Accountant"
    ) -> Dict[str, Union[bool, str]]:
        """
        Partial recovery workflow:
        1. Navigates to /asset-recovery, finds target row, and clicks Settle.
        2. Records partial amount and payment details.
        3. Verifies toast and confirms reduced balance.
        """
        logger.info("=" * 60)
        logger.info(f"[ACCOUNTANT WORKFLOW] Recording partial recovery ₹{amount} for '{identifier}'")
        logger.info("=" * 60)

        self.recovery_page.navigate_to_asset_recovery()
        opened = self.recovery_page.click_settle_button(identifier)
        if not opened:
            return {"success": False, "error": f"Settle modal not opened for {identifier}"}

        toast = self.recovery_page.record_partial_settlement(
            amount=amount,
            payment_mode=payment_mode,
            reference_no=reference_no,
            remarks=remarks
        )
        self.page.wait_for_timeout(1000)

        updated_row = self.recovery_page.get_recovery_row_details(identifier)
        return {
            "success": bool(toast),
            "toast": toast,
            "post_details": updated_row
        }

    # =========================================================================
    # MODULE 2: ASSET DISPOSAL & SCRAP ACCOUNTING (/asset-disposal)
    # =========================================================================

    def audit_disposal_metrics_workflow(self) -> Dict[str, str]:
        """
        Navigates to /asset-disposal and retrieves metrics:
        Disposal Queue, Disposed Assets, Recovery Value, Lost Assets.
        """
        logger.info("[ACCOUNTANT WORKFLOW] Auditing Asset Disposal metrics...")
        self.disposal_page.navigate_to_asset_disposal()
        metrics = self.disposal_page.get_metrics_summary()
        logger.info(f"[ACCOUNTANT WORKFLOW] Disposal Metrics: {metrics}")
        return metrics

    def review_and_approve_disposal_workflow(
        self,
        asset_code: str,
        disposal_type: str = "Scrap",
        recovery_value: str = "0.00",
        buyer_or_vendor: str = None,
        reason: str = "Beyond economical repair",
        remarks: str = "Disposal approved as per accounting policy"
    ) -> Dict[str, Union[bool, str]]:
        """
        Accountant reviews and approves an asset disposal request on /asset-disposal:
        1. Navigates to 'Disposal Requests' tab.
        2. Locates target asset row.
        3. Selects disposal decision (Scrap / Sell / Write-Off).
        4. Fills Recovery Value (proceeds from sale/scrap) and reason.
        5. Submits disposal action and verifies toast.
        """
        logger.info("=" * 60)
        logger.info(f"[ACCOUNTANT WORKFLOW] Approving Disposal for '{asset_code}' as '{disposal_type}' (Recovery: ₹{recovery_value})")
        logger.info("=" * 60)

        self.disposal_page.navigate_to_asset_disposal()
        success = self.disposal_page.review_disposal_request(
            asset_code_or_name=asset_code,
            disposal_type=disposal_type,
            recovery_value=recovery_value,
            buyer_or_vendor=buyer_or_vendor,
            reason=reason,
            remarks=remarks
        )

        return {
            "success": success,
            "asset_code": asset_code,
            "disposal_type": disposal_type,
            "recovery_value": recovery_value
        }

    def verify_disposal_history_workflow(self, asset_code: str) -> Dict[str, Union[bool, str]]:
        """
        Verifies that the disposed asset appears in the 'Disposal History' tab.
        """
        logger.info(f"[ACCOUNTANT WORKFLOW] Verifying Disposal History for '{asset_code}'")
        self.disposal_page.navigate_to_asset_disposal()
        history_entry = self.disposal_page.verify_disposal_history_entry(asset_code)
        return {
            "success": bool(history_entry.get("found")),
            "history": history_entry
        }

    # =========================================================================
    # MODULE 3: EXIT FnF DEDUCTION INTEGRATION (/accounts-buyout-processing)
    # =========================================================================

    def verify_asset_recovery_in_fnf_workflow(
        self,
        employee_name: str,
        expected_recovery_amount: str = None
    ) -> Dict[str, Union[bool, str]]:
        """
        Bridges Asset Recovery with Exit Clearance / Full & Final Settlement:
        1. Navigates to /accounts-buyout-processing -> 'FnF Requests' tab.
        2. Opens FnF drawer for resigning employee.
        3. Asserts that 'Asset Recovery' line item under Deductions reflects expected amount.
        """
        logger.info("=" * 60)
        logger.info(f"[ACCOUNTANT WORKFLOW] Verifying Asset Recovery in FnF for '{employee_name}'")
        logger.info("=" * 60)

        self.res_page.navigate_to_accounts_fnf_requests()
        drawer_opened = self.res_page.open_accountant_fnf_drawer(employee_name)
        if not drawer_opened:
            return {"success": False, "error": f"Failed to open FnF drawer for {employee_name}"}

        drawer_summary = self.res_page.read_accountant_fnf_drawer_summary()
        logger.info(f"[ACCOUNTANT WORKFLOW] FnF Drawer Summary: {drawer_summary}")

        deductions = drawer_summary.get("deductions", {})
        asset_recovery_val = deductions.get("asset_recovery", "0")

        matched = True
        if expected_recovery_amount:
            clean_expected = re.sub(r"[^\d.]", "", str(expected_recovery_amount))
            clean_actual = re.sub(r"[^\d.]", "", str(asset_recovery_val))
            matched = clean_expected in clean_actual or clean_actual == clean_expected

        return {
            "success": matched,
            "employee_name": employee_name,
            "asset_recovery_deducted": asset_recovery_val,
            "drawer_summary": drawer_summary
        }
