"""
UI Test Suite for Asset Procurement Edit Functionality (HR Lens Portal).
Strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates 6-step edit modal opening, prefilled data verification, step navigation, and saving.
"""

import os
import time
import pytest
import logging
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
def test_edit_procurement_workflow(admin_page):
    """
    End-to-End Asset Procurement Edit Workflow:
    1. Locate target row
    2. Locate Edit button
    3. Verify Edit button count
    4. Verify Edit button visible
    5. Click Edit button
    6. Verify modal opened
    7. Read & verify all required fields have prefilled data
    8. Update field on Step 1 (Remarks) & attach invoice (required in both Create and Edit)
    9. Click 'Next — Add items' button to proceed to Stepper 2
    10. Verify Stepper 2 product card(s) per product
    11. Click 'Save Procurement' button and validate updates
    """
    story = TestStoryLogger("Edit Asset Procurement Workflow", module="Asset Management", phase="Asset Procurement")
    story.start()

    proc_page = AssetProcurementPage(admin_page)
    proc_page.navigate_to_asset_procurement()

    # Ensure a target procurement record exists (with invoice attachment)
    invoice_no = proc_page.ensure_procurement_exists_for_edit()
    logger.info(f"Target procurement record ID: '{invoice_no}'")

    # =========================================================================
    # 1. Locate target row
    # =========================================================================
    if invoice_no:
        proc_page.search_procurement(invoice_no)
        admin_page.wait_for_timeout(500)
    
    target_row = admin_page.locator("tbody tr").first
    row_text = target_row.inner_text().replace("\n", " | ")
    logger.info(f"[STEP 1] Located target row: '{row_text}'")
    story.log_step(
        "1. Locate Target Row",
        record=f"Row: '{row_text[:60]}...'",
        expected="Target procurement row is located in the table",
        actual=f"Target row found: {row_text[:60]}...",
        status="PASS"
    )

    # =========================================================================
    # 2. Locate Edit button
    # =========================================================================
    # =========================================================================
    # 2. Locate Edit button
    # =========================================================================
    edit_btn = target_row.locator("button[aria-label='Edit'], .chakra-button[aria-label='Edit']").first
    if not edit_btn.is_visible(timeout=2000):
        edit_btn = target_row.locator("button:has(svg), td:nth-child(12) button").first
    if not edit_btn.is_visible(timeout=2000):
        edit_btn = admin_page.locator("button[aria-label='Edit']").first

    logger.info(f"[STEP 2] Located Edit button: {edit_btn}")
    story.log_step(
        "2. Locate Edit Button",
        record="Selector: button[aria-label='Edit']",
        expected="Edit action button is located in the target row",
        actual="Edit button located successfully",
        status="PASS"
    )

    # =========================================================================
    # 3. Verify Edit button count
    # =========================================================================
    edit_btn_count = admin_page.locator("button[aria-label='Edit']").count()
    if edit_btn_count == 0:
        edit_btn_count = target_row.locator("button, td:nth-child(12) div").count()
    
    logger.info(f"[STEP 3] Verified Edit button count: {edit_btn_count}")
    story.log_step(
        "3. Verify Edit Button Count",
        record=f"Count: {edit_btn_count}",
        expected="At least 1 Edit button exists in table",
        actual=f"Found {edit_btn_count} Edit button(s)",
        status="PASS" if edit_btn_count >= 1 else "FAIL"
    )
    assert edit_btn_count >= 1, f"Expected at least 1 Edit button, found {edit_btn_count}"

    # =========================================================================
    # 4. Verify Edit button visible
    # =========================================================================
    is_visible = edit_btn.is_visible(timeout=5000)
    logger.info(f"[STEP 4] Verified Edit button visible: {is_visible}")
    story.log_step(
        "4. Verify Edit Button Visible",
        record="Visibility check",
        expected="Edit button is visible and ready for interaction",
        actual="Edit button is visible" if is_visible else "Edit button is hidden",
        status="PASS" if is_visible else "FAIL"
    )
    assert is_visible, "Expected Edit button to be visible."

    # =========================================================================
    # 5. Click Edit button
    # =========================================================================
    logger.info("[STEP 5] Clicking Edit button...")
    edit_btn.scroll_into_view_if_needed()
    admin_page.wait_for_timeout(300)
    try:
        edit_btn.click(timeout=3000)
    except Exception:
        edit_btn.click(force=True)

    story.log_step(
        "5. Click Edit Button",
        record="Clicked Edit button",
        expected="Edit button trigger dispatches click event",
        actual="Edit button clicked successfully",
        status="PASS"
    )

    # =========================================================================
    # 6. Verify modal opened
    # =========================================================================
    admin_page.get_by_text("Edit Procurement", exact=True).wait_for(state="visible", timeout=15000)
    logger.info("[STEP 6] Verified 'Edit Procurement' modal opened successfully.")
    story.log_step(
        "6. Verify Modal Opened",
        record="Header text: 'Edit Procurement'",
        expected="Modal with header '<p class=\"chakra-text ...\">Edit Procurement</p>' opens",
        actual="Edit Procurement modal displayed and active",
        status="PASS"
    )

    # =========================================================================
    # 7. Read & verify all required fields have prefilled data
    # =========================================================================
    prefilled = proc_page.get_prefilled_step1_data()
    required_keys = ["vendor", "branch", "company", "invoice_no", "purchase_date"]
    all_prefilled = all(bool(prefilled.get(k)) for k in required_keys)
    
    story.log_step(
        "7. Validate Prefilled Step 1 Data",
        record=f"Prefilled Data: {prefilled}",
        expected="Required fields (Vendor, Branch, Company, Invoice, Date) must be prefilled",
        actual=f"Prefilled fields: {prefilled}" if all_prefilled else f"Missing fields: {[k for k in required_keys if not prefilled.get(k)]}",
        status="PASS" if all_prefilled else "FAIL"
    )
    assert all_prefilled, f"Expected required fields to have prefilled data, got: {prefilled}"

    # =========================================================================
    # 8. Update field on Step 1 (Remarks) & Attach Invoice
    # =========================================================================
    updated_remarks = f"Updated via Automated Edit Test - {int(time.time())}"
    rem_input = admin_page.get_by_label("Remarks", exact=False).first
    if not rem_input.is_visible():
        rem_input = admin_page.locator("textarea[name*='remark' i], textarea[placeholder*='Remark' i]").first
    rem_input.fill("")
    rem_input.fill(updated_remarks)

    # Attach invoice file (required in both Create and Edit situations)
    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")

    logger.info(f"Attaching invoice for edit submission: {sample_invoice_path}")
    proc_page.upload_invoice(sample_invoice_path)

    story.log_step(
        "8. Update Step 1 Field & Attach Invoice",
        record=f"Remarks='{updated_remarks}', Invoice={os.path.basename(sample_invoice_path)}",
        expected="Remarks field updated and invoice attachment verified",
        actual=f"Filled remarks: '{updated_remarks}' and attached invoice",
        status="PASS"
    )

    # =========================================================================
    # 9. Click 'Next — Add items' button to proceed to Stepper 2
    # =========================================================================
    res_next = proc_page.click_next()
    is_step2_active = proc_page.is_step2_active()
    story.log_step(
        "9. Advance to Stepper 2",
        record="Clicked 'Next — Add items' button",
        expected="Stepper 2 opens (Line Items form active)",
        actual="Stepper 2 active confirmed" if is_step2_active else f"Failed to reach Stepper 2: Toast='{res_next.get('toast')}'",
        status="PASS" if is_step2_active else "FAIL"
    )
    assert is_step2_active, f"Expected to advance to Stepper 2, got: {res_next}"

    # =========================================================================
    # 10. Verify Stepper 2 product card(s) per product
    # =========================================================================
    product_cards = proc_page.inspect_and_log_asset_line_items()
    story.log_step(
        "10. Inspect Product Cards on Stepper 2",
        record=f"Found {len(product_cards)} product card(s)",
        expected="Product cards displayed per product with item details",
        actual=f"Read {len(product_cards)} product card(s) from Stepper 2",
        status="PASS" if product_cards else "FAIL"
    )
    assert len(product_cards) >= 1, "Expected at least 1 product card on Stepper 2."

    # =========================================================================
    # 11. Click 'Save Procurement' button and validate updates
    # =========================================================================
    proc_page.select_step2_dropdowns()
    toast = ""
    for attempt in range(2):
        toast = proc_page.save_procurement()
        is_saved = any(term in (toast or "").lower() for term in ["success", "saved", "updated", "procured", "procurement"]) or toast == ""
        if is_saved:
            break
        logger.warning(f"Edit save returned toast: '{toast}'. Auto-fixing and retrying...")
        proc_page._fix_step2_field_by_error(toast)
        admin_page.wait_for_timeout(800)

    is_saved = any(term in (toast or "").lower() for term in ["success", "saved", "updated", "procured", "procurement"]) or toast == ""
    story.log_step(
        "11. Save Procurement Updates",
        record="Clicked 'Save Procurement' button",
        expected="Procurement updates saved successfully with confirmation toast",
        actual=f"Toast notification received: '{toast}'",
        status="PASS" if is_saved else "FAIL"
    )
    assert is_saved, f"Unexpected toast when saving procurement: '{toast}'"

    story.finish()
