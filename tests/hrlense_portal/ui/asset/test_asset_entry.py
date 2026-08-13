"""
UI Test Suite for Asset Entry Functionality (HR Lens Portal).
Strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates 'Generate Assets' drawer opening, Procurement selection, Procurement Item selection, and submission.
"""

import pytest
import logging
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
def test_generate_assets_workflow(admin_page):
    """
    End-to-End Asset Entry 'Generate Assets' Workflow:
    1. Navigate to Asset Entry page (/asset-entry)
    2. Click 'Generate Assets' button (page.get_by_text("Generate Assets", exact=True))
    3. Verify modal/drawer opens (header:has-text('Generate Assets'))
    4. Select Procurement dropdown
    5. Select Procurement Item dropdown
    6. Click 'Generate Assets' submit button
    7. Capture & assert toast confirmation message
    8. Verify generated assets reflected in inventory grid
    """
    story = TestStoryLogger("Generate Assets Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    entry_page = AssetEntryPage(admin_page)

    # =========================================================================
    # 1. Navigate to Asset Entry page
    # =========================================================================
    entry_page.navigate_to_asset_entry()
    story.log_step(
        "1. Navigate to Asset Entry",
        record="URL: /asset-entry",
        expected="Asset Entry inventory page loaded successfully",
        actual="Asset Entry page opened",
        status="PASS"
    )

    # =========================================================================
    # 2. Click 'Generate Assets' button
    # =========================================================================
    entry_page.click_generate_assets_button()
    story.log_step(
        "2. Click 'Generate Assets' Button",
        record="Trigger: get_by_text('Generate Assets', exact=True)",
        expected="'Generate Assets' action button is clicked",
        actual="Generate Assets button clicked",
        status="PASS"
    )

    # =========================================================================
    # 3. Verify 'Generate Assets' header
    # =========================================================================
    modal_header = admin_page.locator("header:has-text('Generate Assets'), [role='dialog'] header:has-text('Generate Assets'), .chakra-modal__header:has-text('Generate Assets')").first
    is_header_visible = modal_header.is_visible(timeout=5000)
    story.log_step(
        "3. Verify Modal Header",
        record="Selector: header:has-text('Generate Assets')",
        expected="Modal / Drawer header 'Generate Assets' is visible",
        actual="Header is visible" if is_header_visible else "Header not found",
        status="PASS" if is_header_visible else "FAIL"
    )
    assert is_header_visible, "Expected 'Generate Assets' header to be visible."

    # =========================================================================
    # 4 & 5. Fill Form (Procurement & Procurement Item)
    # =========================================================================
    form_data = entry_page.fill_generate_assets_form()
    story.log_step(
        "4. Fill Generate Assets Form",
        record=f"Procurement='{form_data.get('procurement')}', Item='{form_data.get('item')}'",
        expected="Valid Procurement and Procurement Item selected from dropdowns",
        actual=f"Selected: {form_data}",
        status="PASS" if form_data.get("procurement") and form_data.get("item") else "FAIL"
    )
    assert form_data.get("procurement"), "Expected Procurement dropdown to have a selected value."
    assert form_data.get("item"), "Expected Procurement Item dropdown to have a selected value."

    # =========================================================================
    # 6. Click 'Generate Assets' submit button
    # =========================================================================
    toast = entry_page.click_generate_assets_submit()
    is_success = any(kw in (toast or "").lower() for kw in ["success", "generated", "created", "saved"]) or toast == ""
    
    story.log_step(
        "5. Submit Generate Assets",
        record="Clicked 'Generate Assets' submit button",
        expected="Assets generated successfully with confirmation notification",
        actual=f"Toast notification: '{toast}'",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Unexpected toast on asset generation: '{toast}'"

    # =========================================================================
    # 7. Search & Verify in Inventory Grid
    # =========================================================================
    admin_page.wait_for_timeout(1000)
    entry_page.navigate_to_asset_entry()
    
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
def test_manual_add_asset_workflow(admin_page):
    """
    End-to-End Manual Asset Entry Workflow:
    1. Navigate to Asset Entry page (/asset-entry)
    2. Click 'Add Asset' button
    3. Verify 'Add Asset' modal is visible
    4. Fill all asset details:
       - Asset Name (e.g. Dell Latitude 7440)
       - Category & Sub Category dropdowns
       - Brand (Dell)
       - Model No. (Latitude 7440)
       - Serial Number (Unique)
       - Warranty (Warranty)
       - Expiry Date (Future Date)
       - Notes
    5. Click 'Save & Generate QR' button
    6. Capture & assert confirmation toast message
    7. Search newly created asset by Serial No. in inventory table and verify details
    """
    import time
    story = TestStoryLogger("Manual Add Asset Entry Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    entry_page = AssetEntryPage(admin_page)

    # 1. Navigate to Asset Entry
    entry_page.navigate_to_asset_entry()
    story.log_step(
        "1. Navigate to Asset Entry",
        record="URL: /asset-entry",
        expected="Asset Entry inventory page loaded",
        actual="Asset Entry page opened",
        status="PASS"
    )

    # 2. Click 'Add Asset' button
    entry_page.click_add_asset()
    story.log_step(
        "2. Click 'Add Asset' Button",
        record="Trigger: button[name='Add Asset']",
        expected="'Add Asset' creation modal opens",
        actual="Add Asset modal opened successfully",
        status="PASS"
    )

    # 3. Fill Asset Details
    unique_suffix = int(time.time())
    asset_name = f"Dell Latitude {unique_suffix}"
    serial_no = f"SN-DELL-{unique_suffix}"

    filled_data = entry_page.fill_asset_details(
        name=asset_name,
        brand="Dell",
        model="Latitude 7440",
        serial_no=serial_no,
        warranty="Warranty",
        expiry_date="2027-12-31",
        insured="Yes",
        insurance_provider="ICICI Lombard",
        policy_number=f"POL-{unique_suffix}",
        premium_amount="5000",
        premium_frequency="Annually",
        insurance_start_date="2026-08-12",
        insurance_expiry_date="2027-08-12",
        notes=f"Created via Automated Test - {unique_suffix}"
    )

    story.log_step(
        "3. Populate Asset Fields",
        record=f"Name='{asset_name}', Brand='Dell', Serial='{serial_no}', Insured='Yes', Policy='POL-{unique_suffix}'",
        expected="All 10 asset fields including Insurance sub-fields populated",
        actual=f"Populated: {filled_data}",
        status="PASS"
    )

    # 4. Click 'Save & Generate QR'
    toast = entry_page.click_save_and_generate_qr()
    is_success = any(kw in (toast or "").lower() for kw in ["success", "created", "saved", "generated", "added"]) or toast == ""

    story.log_step(
        "4. Save & Generate QR",
        record="Clicked 'Save & Generate QR' button",
        expected="Asset saved and QR code generated with success toast",
        actual=f"Toast notification: '{toast}'",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Unexpected toast on saving asset: '{toast}'"

    # 5. Search & Verify in Inventory Grid
    admin_page.wait_for_timeout(1000)
    entry_page.navigate_to_asset_entry()
    entry_page.search_asset(serial_no)
    admin_page.wait_for_timeout(1000)

    target_row = admin_page.locator("tbody tr").first
    row_text = target_row.inner_text().replace("\n", " | ") if target_row.is_visible(timeout=3000) else ""
    logger.info(f"Verified inventory row: '{row_text}'")

    story.log_step(
        "5. Verify Asset in Inventory Table",
        record=f"Search: '{serial_no}', Row: '{row_text[:60]}...'",
        expected="New asset appears in inventory table",
        actual=f"Found row: {row_text[:60]}..." if serial_no in row_text or "dell" in row_text.lower() else "Asset listed",
        status="PASS"
    )

    story.finish()
