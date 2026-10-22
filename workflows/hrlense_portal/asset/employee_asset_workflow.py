"""
HRlens Portal — Employee Asset Workflow (Workflow Tier).
Encapsulates business workflow orchestration for all Employee-side Asset actions:
  [STEP 0] Check whether an asset is already assigned to the employee
  [STEP 1] Request a new company asset (Hardware/Software) with justification
  [STEP 2] Accept or Reject assigned asset custody after IT fulfillment
  [STEP 3] Request asset return (with reasons & mandatory media evidence)
"""

import re
import logging
from typing import Dict, Union, Optional
from playwright.sync_api import Page

from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage

logger = logging.getLogger(__name__)


class EmployeeAssetWorkflow:
    """
    Workflow orchestrator for Employee Asset Management actions.
    Separates Employee Self-Service journeys from Admin/Procurement/Vendor setups.
    """

    def __init__(self, page: Page):
        self.page = page
        self.req_page = AssetRequestPage(page)

    # ══════════════════════════════════════════════════════════════════════
    # STEP 0: CHECK KARNA ASSET ASSIGNED HAI YA NAHI (STATE-AWARE GATE)
    # ══════════════════════════════════════════════════════════════════════

    def check_assigned_assets_workflow(self, asset_code_or_name: Optional[str] = None) -> Dict[str, Union[bool, str]]:
        """
        [STEP 0] Inspects Employee portal (/asset-request) to determine current asset holdings.
        
        Returns:
            dict containing:
              - 'has_assigned' (bool): True if at least one active asset is currently held
              - 'asset_code' (str): Detected asset code (e.g. 'ASSET-LAP-2026-001')
              - 'status' (str): Asset lifecycle status (e.g. 'ACTIVE', 'ASSIGNED', 'PENDING')
              - 'raw_row' (str): Table row text preview
        """
        logger.info("=" * 60)
        logger.info("[STEP 0] CHECKING EMPLOYEE ASSIGNED ASSET STATUS")
        logger.info("=" * 60)

        self.req_page.navigate_to_asset_request()
        has_assets = self.req_page.has_assigned_assets()
        logger.info(f"[STEP 0] Employee currently has assigned assets: {has_assets}")

        detected_code = ""
        status = "EMPTY"
        raw_text = ""

        if has_assets:
            if asset_code_or_name:
                search_res = self.req_page.search_assigned_asset(asset_code_or_name)
                status = search_res.get("status", "ACTIVE")
                raw_text = search_res.get("row_text", "")
                m = re.search(r"ASSET-[A-Z0-9-]+", raw_text)
                detected_code = m.group(0) if m else asset_code_or_name
            else:
                # Read first row
                try:
                    first_row = self.page.locator("table tbody tr, .chakra-card, .css-prwjms").first
                    if first_row.is_visible(timeout=3000):
                        raw_text = first_row.inner_text().strip()
                        m = re.search(r"ASSET-[A-Z0-9-]+", raw_text)
                        detected_code = m.group(0) if m else ""
                        status = "ACTIVE"
                except Exception as ex:
                    logger.warning(f"[STEP 0] Asset row read note: {ex}")

        logger.info(f"[STEP 0 RESULT] Has Asset: {has_assets} | Code: '{detected_code}' | Status: '{status}'")
        return {
            "has_assigned": has_assets,
            "asset_code": detected_code,
            "status": status,
            "raw_row": raw_text[:120],
        }

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: REQUEST NEW ASSET
    # ══════════════════════════════════════════════════════════════════════

    def request_new_asset_workflow(
        self,
        category: str = "Hardware",
        sub_category: str = "Laptop",
        reason: str = "Required for project development activities.",
        remarks: Optional[str] = None
    ) -> Dict[str, Union[bool, str]]:
        """
        [STEP 1] Submits a new asset procurement request from Employee Portal:
        1. Navigates to /asset-request
        2. Clicks '+ New Request'
        3. Selects Category & Sub-Category
        4. Fills Reason & Remarks
        5. Submits form and captures confirmation toast
        """
        logger.info("=" * 60)
        logger.info(f"[STEP 1] SUBMITTING NEW ASSET REQUEST ({category} -> {sub_category})")
        logger.info("=" * 60)

        self.req_page.navigate_to_asset_request()
        res = self.req_page.create_new_request(
            category=category,
            sub_category=sub_category,
            reason=reason,
            remarks=remarks
        )
        toast = res.get("toast", "")
        logger.info(f"[STEP 1 RESULT] Asset Request Submitted. Toast: '{toast}'")

        is_success = bool(toast and "error" not in toast.lower() and "fail" not in toast.lower())
        return {
            "success": is_success,
            "toast": toast,
            "category": category,
            "sub_category": sub_category,
            "reason": reason
        }

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: ACCEPT / REJECT ASSET AFTER FULFILLMENT
    # ══════════════════════════════════════════════════════════════════════

    def accept_assigned_asset_workflow(self, asset_code: Optional[str] = None) -> bool:
        """
        [STEP 2A] Employee accepts custody of a fulfilled/assigned asset:
        1. Navigates to /asset-request
        2. Locates assigned asset card/row
        3. Clicks 'Accept Asset' and confirms dialog
        4. Waits for spinner and verifies accepted status
        """
        logger.info("=" * 60)
        logger.info(f"[STEP 2A] EMPLOYEE ACCEPTING ASSET CUSTODY: '{asset_code or 'Latest'}'")
        logger.info("=" * 60)

        self.req_page.navigate_to_asset_request()
        accepted = self.req_page.accept_asset(asset_code_or_name=asset_code)
        logger.info(f"[STEP 2A RESULT] Custody Accepted: {accepted}")
        return accepted

    def reject_assigned_asset_workflow(
        self,
        asset_code: Optional[str] = None,
        reason: str = "Hardware does not meet project requirements or is defective."
    ) -> bool:
        """
        [STEP 2B] Employee rejects custody of an assigned asset:
        1. Navigates to /asset-request
        2. Clicks 'Reject' button on target asset
        3. Enters rejection reason in modal
        4. Submits rejection and waits for processing
        """
        logger.info("=" * 60)
        logger.info(f"[STEP 2B] EMPLOYEE REJECTING ASSET CUSTODY: '{asset_code or 'Latest'}'")
        logger.info("=" * 60)

        self.req_page.navigate_to_asset_request()
        rejected = self.req_page.reject_asset(asset_code_or_name=asset_code, reason=reason)
        logger.info(f"[STEP 2B RESULT] Custody Rejected: {rejected}")
        return rejected

    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: REQUEST ASSET RETURN (OFFBOARDING / DAMAGED HANDOVER)
    # ══════════════════════════════════════════════════════════════════════

    def request_asset_return_workflow(
        self,
        asset_code_or_name: str,
        reason: str = "Hardware damaged during usage. Requesting return and assessment.",
        upload_media: bool = True
    ) -> Dict[str, Union[bool, str]]:
        """
        [STEP 3] Submits an asset return request with reason and mandatory media attachments:
        1. Navigates to /asset-request
        2. Locates target asset and clicks 'Return Asset'
        3. Fills return justification in modal
        4. Attaches media images/evidence (if upload_media=True)
        5. Submits return request to IT queue and captures confirmation toast
        """
        logger.info("=" * 60)
        logger.info(f"[STEP 3] SUBMITTING ASSET RETURN REQUEST FOR '{asset_code_or_name}'")
        logger.info("=" * 60)

        self.req_page.navigate_to_asset_request()
        res = self.req_page.request_asset_return(
            asset_code_or_name=asset_code_or_name,
            reason=reason,
            upload_media=upload_media
        )
        toast = res.get("toast", "")
        logger.info(f"[STEP 3 RESULT] Asset Return Request submitted. Toast: '{toast}'")

        is_success = bool(toast and "error" not in toast.lower() and "fail" not in toast.lower())
        return {
            "success": is_success,
            "toast": toast,
            "asset_code": asset_code_or_name,
            "reason": reason,
        }
