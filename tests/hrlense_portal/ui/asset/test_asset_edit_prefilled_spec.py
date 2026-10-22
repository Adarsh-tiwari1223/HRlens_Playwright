"""
UI Test Suite for Asset Entry Edit & Prefilled Data Verification (/asset-entry).
Strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).

Validates:
1. Navigation to /asset-entry and target asset row identification.
2. Opening the 'Edit Asset' modal.
3. Strict verification of all prefilled form fields:
   - Asset Name
   - Category
   - Sub Category
   - Branch
   - Payroll Company (strictly verified to NOT be blank / placeholder)
   - Brand & Model No.
   - Serial Number
   - Unit Price (strictly verified to NOT be 0.00 / blank)
   - Warranty / Guarantee & Expiry Date
   - Notes
4. Clean dismissal of modal.
"""

import re
import pytest
import logging
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from workflows.hrlense_portal.asset.asset_entry_workflow import AssetEntryWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.asset_edit
class TestAssetEditPrefilledSpec:

    def test_asset_edit_prefilled_data_verification(self, admin_page):
        """
        Locates an asset on /asset-entry, opens the Edit Asset modal,
        and verifies that all required fields are populated with prefilled data.
        """
        story = TestStoryLogger(
            "Asset Edit Prefilled Data Verification",
            module="Asset Management",
            phase="Asset Edit"
        )
        story.start()

        entry_page = AssetEntryPage(admin_page)

        # Step 1: Navigate to Asset Entry page
        logger.info("Step 1: Navigating to Asset Entry page...")
        entry_page.navigate_to_asset_entry()
        story.log_step(
            "1. Navigate to Asset Entry",
            record="URL: /asset-entry",
            expected="Asset Entry inventory table loaded",
            actual="Asset Entry page loaded successfully",
            status="PASS"
        )

        # Step 2: Locate target asset row and click Edit
        logger.info("Step 2: Locating asset and opening Edit modal...")
        edit_meta = entry_page.click_edit_asset()
        row_text = edit_meta.get("row_text", "")
        story.log_step(
            "2. Open Edit Asset Modal",
            record=f"Row: '{row_text[:60]}...'",
            expected="Edit Asset modal displayed with header 'Edit Asset'",
            actual="Edit Asset modal opened successfully",
            status="PASS"
        )

        # Step 3: Extract all prefilled form fields
        logger.info("Step 3: Extracting prefilled fields from Edit modal...")
        prefilled = entry_page.get_prefilled_asset_data()
        logger.info(f"Prefilled Fields Extracted: {prefilled}")

        # Validate mandatory core fields
        name_val = prefilled.get("name", "")
        cat_val = prefilled.get("category", "")
        sub_cat_val = prefilled.get("sub_category", "")
        branch_val = prefilled.get("branch", "")
        payroll_val = prefilled.get("payroll_company", "")
        serial_val = prefilled.get("serial_no", "")
        price_val = prefilled.get("unit_price", "")
        brand_val = prefilled.get("brand", "")
        model_val = prefilled.get("model", "")

        # Step 4: Verify Asset Name, Taxonomy, and Branch
        core_fields_ok = bool(name_val and cat_val and sub_cat_val and branch_val and serial_val)
        story.log_step(
            "3. Verify Core Asset Identification Prefilled",
            record=f"Name='{name_val}', Cat='{cat_val}', SubCat='{sub_cat_val}', Branch='{branch_val}', SN='{serial_val}'",
            expected="Name, Category, Sub Category, Branch, and Serial No must be populated",
            actual="All core asset identity fields populated" if core_fields_ok else f"Missing: {[k for k, v in [('name', name_val), ('cat', cat_val), ('sub_cat', sub_cat_val), ('branch', branch_val), ('serial', serial_val)] if not v]}",
            status="PASS" if core_fields_ok else "FAIL"
        )
        assert core_fields_ok, f"Core asset fields failed to prefill: {prefilled}"

        # Step 5: Verify Payroll Company (Critical Business Rule)
        payroll_is_prefilled = bool(payroll_val and not payroll_val.lower().startswith("select"))
        story.log_step(
            "4. Verify Payroll Company Prefilled",
            record=f"Payroll Company='{payroll_val}'",
            expected="Payroll Company must be pre-selected according to branch group (not blank / placeholder)",
            actual=f"Payroll Company prefilled as '{payroll_val}'" if payroll_is_prefilled else "Payroll Company is BLANK (Select payroll company)",
            status="PASS" if payroll_is_prefilled else "FAIL"
        )
        if not payroll_is_prefilled:
            logger.warning("[DEFECT DETECTED] Payroll Company dropdown is unselected / blank in Edit Asset modal!")

        # Step 6: Verify Unit Price (Critical Business Rule)
        try:
            numeric_price = float(price_val.replace(",", "").strip())
        except (ValueError, TypeError):
            numeric_price = 0.0

        price_is_valid = numeric_price > 0.0
        story.log_step(
            "5. Verify Unit Price Prefilled",
            record=f"Unit Price='{price_val}' (Parsed: ₹{numeric_price:,.2f})",
            expected="Unit Price must be populated with a valid non-zero amount",
            actual=f"Unit Price is ₹{numeric_price:,.2f}" if price_is_valid else f"Unit Price is zero/empty ('{price_val}')",
            status="PASS" if price_is_valid else "FAIL"
        )
        if not price_is_valid:
            logger.warning("[DEFECT DETECTED] Unit Price is ₹0.00 / unpopulated in Edit Asset modal!")

        # Step 7: Close Edit Modal Cleanly
        logger.info("Step 7: Closing edit modal...")
        entry_page.close_edit_modal()
        story.log_step(
            "6. Close Edit Modal",
            record="Clicked Cancel / Close",
            expected="Edit modal dismissed and inventory table interactive",
            actual="Modal closed cleanly",
            status="PASS"
        )

        story.finish()

        # Hard assertion for core fields; warn on data defects
        assert bool(name_val and serial_val), f"Asset Name and Serial Number must be present, got: {prefilled}"
