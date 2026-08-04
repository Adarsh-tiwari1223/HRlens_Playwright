import os
import random
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage


@pytest.mark.ui
@pytest.mark.asset
def test_asset_e2e_procurement_flow(logged_in_page):
    story = TestStoryLogger("Asset Procurement Form Submission Test", module="Asset Management", phase="Asset Procurement")
    story.start()

    # Step 1: Admin login
    admin_page, admin_context = logged_in_page("admin")

    # Step 2: Navigate to Asset Procurement
    procurement_page = AssetProcurementPage(admin_page)
    procurement_page.navigate_to_asset_procurement()
    procurement_page.click_new_procurement()

    # Step 3: Upload Invoice File & Wait for Auto-Fill Rendering
    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")

    print(f"\n[STEP 3] Uploading Invoice PDF: {sample_invoice_path}")
    procurement_page.upload_invoice(sample_invoice_path)

    # Wait for content rendering / auto-fill OCR
    admin_page.wait_for_timeout(3500)

    # Step 4: Inspect and Log all Form Field values to Terminal
    field_report = procurement_page.inspect_and_log_step1_fields()
    invoice_no = field_report.get("Invoice No") if field_report.get("Invoice No") not in ["EMPTY", "NOT FOUND", None] else "INV-UPLOADED"

    # Step 5: Select ONLY Branch and Payroll Company if unselected (Preserve prefilled textboxes)
    procurement_page.fill_step1_details(
        invoice_file_path=sample_invoice_path
    )
    procurement_page.click_next()

    # Step 6: Inspect prefilled Step 2 line items without modifying values
    procurement_page.inspect_and_log_asset_line_items()
    procurement_page.click_create()

    # Step 7: Assert successful procurement toast response
    toast = procurement_page.wait_for_toast_message()
    is_success = "success" in toast.lower() or "created" in toast.lower() or "procured" in toast.lower()

    story.log_step(
        "Submit Asset Procurement Form",
        record=f"Invoice: {invoice_no}",
        expected="Asset Procurement entry should be created successfully",
        actual=f"Toast message received: '{toast}'" if is_success else f"Failed: {toast}",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Procurement failed: {toast}"
