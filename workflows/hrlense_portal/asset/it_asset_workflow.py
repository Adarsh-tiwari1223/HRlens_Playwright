"""
HRlens Portal — IT Asset Workflow (Workflow Tier).

Orchestrates end-to-end IT Persona asset operational workflows:
1. Stock & Ingestion:
   - Direct manual asset entry (/asset-entry)
   - Bulk asset generation from procurement PO (/asset-entry)
   - Asset procurement via vendor invoice (/asset-procurement)
2. Allocation & Assignment (Employee Handover):
   - Method 1: Direct Asset Assignment to Employee (/asset-assignment)
   - Method 2: Fulfill Requested Assets from employee requests queue (/asset-assignment)
3. Maintenance & Hardware Repair:
   - Create Maintenance Request (/asset-maintenance)
   - Review & Complete Maintenance (/asset-maintenance)
4. Exit Clearance & Offboarding:
   - Physical asset handover, condition inspection, damage evidence, and clearance approval (/exit-clearance)
"""

import logging
import re
from typing import Dict, Union, Optional, List
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_maintenance_page import AssetMaintenancePage
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage
from pages.hrlense_portal.resignation.resignation_page import ResignationPage

logger = logging.getLogger(__name__)


class ItAssetWorkflow:
    """
    IT Persona Asset Management Workflow Layer.
    Owns hardware ingestion, employee direct/fulfillment assignment, maintenance repair, and exit offboarding clearance.
    """

    def __init__(self, page: Page):
        self.page = page
        self.entry_page = AssetEntryPage(page)
        self.assignment_page = AssetAssignmentPage(page)
        self.maintenance_page = AssetMaintenancePage(page)
        self.procurement_page = AssetProcurementPage(page)
        self.res_page = ResignationPage(page)

    # =========================================================================
    # PILLAR 1: STOCK & INGESTION (/asset-entry & /asset-procurement)
    # =========================================================================

    def add_manual_asset_workflow(self, asset_data: dict) -> Dict[str, Union[bool, str, dict]]:
        """
        Creates a single asset manually via /asset-entry modal:
        1. Navigates to /asset-entry.
        2. Clicks 'Add Asset' / 'Add Manual'.
        3. Fills details (Category, Sub-category, Serial, Brand, Model, etc.).
        4. Clicks 'Save & Generate QR' and verifies toast.
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Adding manual asset: {asset_data.get('name', 'N/A')}")
        logger.info("=" * 60)

        self.entry_page.navigate_to_asset_entry()
        self.entry_page.click_add_asset()
        filled = self.entry_page.fill_asset_details(**asset_data)
        toast = self.entry_page.click_save_and_generate_qr()

        return {
            "success": bool(toast and "success" in toast.lower()),
            "toast": toast,
            "filled": filled
        }

    def generate_bulk_assets_workflow(self, procurement_code: str = None) -> Dict[str, Union[bool, str, dict]]:
        """
        Generates assets in bulk from an approved Procurement Order:
        1. Navigates to /asset-entry.
        2. Clicks 'Generate Assets'.
        3. Selects procurement PO and item.
        4. Submits bulk generation form.
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Generating bulk assets from Procurement: '{procurement_code or 'AUTO'}'")
        logger.info("=" * 60)

        self.entry_page.navigate_to_asset_entry()
        self.entry_page.click_generate_assets_button()
        filled = self.entry_page.fill_generate_assets_form(procurement_code=procurement_code)
        toast = self.entry_page.submit_generate_assets_form()

        return {
            "success": bool(toast and "success" in toast.lower()),
            "toast": toast,
            "details": filled
        }

    # =========================================================================
    # PILLAR 2: ALLOCATION & ASSIGNMENT (/asset-assignment)
    # =========================================================================

    def assign_asset_direct_workflow(
        self,
        employee_name: str,
        category: str,
        sub_category: str,
        asset_name_or_code: str = None,
        duration_type: str = "Permanent",
        expected_return_date: str = "2026-12-31",
        remarks: str = "Assigned via IT Direct Allocation"
    ) -> Dict[str, Union[bool, str]]:
        """
        Method 1: Direct Assignment:
        1. IT navigates to /asset-assignment.
        2. Clicks 'Assign Asset'.
        3. Selects Employee, Category, Sub-Category, and available Asset.
        4. Optionally configures assignment duration ('Permanent' vs 'Temporary').
        5. Submits assignment form and captures toast.
        Status transitions to 'Pending Acceptance' (waiting for Employee Step 2).
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Direct Asset Assignment to '{employee_name}' (Cat: {category}, Sub: {sub_category})")
        logger.info("=" * 60)

        self.assignment_page.navigate_to_asset_assignment()
        self.assignment_page.click_assign_asset()

        if duration_type and duration_type != "Permanent":
            self.assignment_page.select_assignment_duration(duration_type)

        selected_code = self.assignment_page.fill_assignment_details(
            employee_name=employee_name,
            category=category,
            sub_category=sub_category,
            asset_name_or_code=asset_name_or_code,
            expected_return_date=expected_return_date,
            remarks=remarks
        )

        self.assignment_page.click_submit_assignment()
        toast = self.assignment_page.wait_for_toast_message()

        return {
            "success": bool(toast and "success" in toast.lower() or selected_code),
            "asset_code": selected_code,
            "employee_name": employee_name,
            "toast": toast
        }

    def fulfill_employee_asset_request_workflow(
        self,
        employee_name: str = None,
        asset_code: str = None,
        assignment_type: str = "Permanent",
        expected_return_date: str = "2026-12-31",
        remarks: str = "Fulfilled by IT from pending employee request"
    ) -> Dict[str, Union[bool, str]]:
        """
        Method 2: Fulfill Requested Assets:
        1. IT navigates to /asset-assignment.
        2. Switches to 'Requested Assignment' tab.
        3. Locates pending employee request and clicks 'Fulfil'.
        4. Selects available asset matching requested specifications.
        5. Submits fulfillment drawer and captures toast.
        Request transitions to 'FULFILLED', awaiting Employee custody acceptance.
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Fulfilling pending asset request for '{employee_name or 'ANY PENDING'}'")
        logger.info("=" * 60)

        self.assignment_page.navigate_to_asset_assignment()
        drawer = self.assignment_page.open_fulfillment_drawer(employee_name=employee_name)
        if not drawer:
            logger.error(f"[IT WORKFLOW] No pending fulfillment request found for '{employee_name}'")
            return {"success": False, "error": f"Fulfillment drawer not opened for {employee_name}"}

        result = self.assignment_page.submit_open_fulfillment_drawer(
            drawer=drawer,
            asset_code=asset_code,
            assignment_type=assignment_type,
            expected_return_date=expected_return_date,
            remarks=remarks
        )

        return {
            "success": bool(result.get("success")),
            "asset_code": result.get("asset_code"),
            "employee_name": employee_name,
            "toast": result.get("toast")
        }

    # =========================================================================
    # PILLAR 3: MAINTENANCE & HARDWARE REPAIR (/asset-maintenance)
    # =========================================================================

    def create_maintenance_request_workflow(
        self,
        asset_code_or_name: str,
        issue_type: str,
        description: str = None,
        sent_date: str = None,
        expected_return: str = None,
        estimated_cost: str = None,
        remarks: str = None
    ) -> Dict[str, Union[bool, str]]:
        """
        Creates maintenance/repair case for a faulty/damaged asset:
        1. Navigates to /asset-maintenance.
        2. Clicks 'Create Maintenance'.
        3. Fills details (Asset, Issue Type, Description, Sent Date, Vendor/Cost).
        4. Submits and asset moves to 'UNDER MAINTENANCE' status.
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Creating Maintenance for '{asset_code_or_name}' (Issue: {issue_type})")
        logger.info("=" * 60)

        self.maintenance_page.navigate_to_asset_maintenance()
        self.maintenance_page.click_create_maintenance()
        self.maintenance_page.fill_maintenance_details(
            asset_code_or_name=asset_code_or_name,
            issue_type=issue_type,
            description=description,
            sent_date=sent_date,
            expected_return=expected_return,
            estimated_cost=estimated_cost,
            remarks=remarks
        )

        submit_btn = self.page.locator("button:has-text('Save'), button:has-text('Submit'), button.chakra-button:has-text('Create')").first
        if submit_btn.is_visible(timeout=2000):
            submit_btn.click()
        toast = self.maintenance_page.wait_for_toast_message()

        return {
            "success": bool(toast and "success" in toast.lower()),
            "toast": toast,
            "asset_code": asset_code_or_name
        }

    def complete_maintenance_workflow(
        self,
        asset_code_or_name: str,
        resolution: str = "Repaired",
        cost: str = "1500",
        remarks: str = "Repaired and returned to active stock"
    ) -> Dict[str, Union[bool, str]]:
        """
        Marks maintenance case as resolved/repaired:
        1. Navigates to /asset-maintenance -> 'Maintenance Request' tab.
        2. Locates target asset row and clicks 'Approve'.
        3. Records completion details and cost.
        4. Asset returns to 'AVAILABLE' stock.
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Completing Maintenance for '{asset_code_or_name}' (Resolution: {resolution})")
        logger.info("=" * 60)

        toast = self.maintenance_page.complete_maintenance(
            asset_code_or_name=asset_code_or_name,
            resolution=resolution,
            cost=cost,
            remarks=remarks
        )

        return {
            "success": bool(toast and "success" in toast.lower()),
            "toast": toast,
            "asset_code": asset_code_or_name
        }

    # =========================================================================
    # PILLAR 4: EXIT CLEARANCE & OFFBOARDING (/exit-clearance)
    # =========================================================================

    def process_it_exit_clearance_workflow(
        self,
        employee_name: str,
        asset_condition: str = "Good Condition",
        asset_conditions: list = None,
        remarks: str = "IT Asset clearance verified & completed"
    ) -> Dict[str, Union[bool, str]]:
        """
        Executes complete IT Person Exit Clearance workflow on /exit-clearance:
        1. Navigates to /exit-clearance.
        2. Searches employee and opens 'Release Employee Checklist'.
        3. Handles physical asset inspection (loops through each assigned device):
           - Good Condition -> Returns to AVAILABLE stock
           - Damaged -> Records damage, logs photo evidence, triggers recovery
           - Lost -> Records loss/penalty
        4. Revokes credentials/system access.
        5. Completes IT clearance checklist (Task 1 of 2).
        """
        logger.info("=" * 60)
        logger.info(f"[IT WORKFLOW] Executing IT Exit Clearance for: '{employee_name}'")
        logger.info("=" * 60)

        return self.res_page.process_it_person_asset_clearance(
            employee_name=employee_name,
            asset_condition=asset_condition,
            asset_conditions=asset_conditions,
            remarks=remarks
        )
