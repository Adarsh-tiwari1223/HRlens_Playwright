import pytest
import re
import random
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage
from faker import Faker

fake = Faker()

@pytest.mark.ui
@pytest.mark.asset
def test_asset_e2e_procurement_flow(logged_in_page):
    story = TestStoryLogger("Asset Procurement Form Submission Test")
    story.start()

    # Step 1: Admin login
    admin_page, admin_context = logged_in_page("admin")

    # Step 2: Navigate to Asset Procurement
    procurement_page = AssetProcurementPage(admin_page)
    procurement_page.navigate_to_asset_procurement()
    procurement_page.click_new_procurement()

    invoice_no = f"INV-{random.randint(10000, 99999)}"
    # Fill step 1 details using pre-existing dropdown values (index 1)
    procurement_page.fill_step1_details(
        vendor_label=None,
        branch_label=None,
        company_label=None,
        invoice_no=invoice_no,
        purchase_date="2026-07-23",
        amount_before_gst="1000",
        gst_amount="180"
    )
    procurement_page.click_next()

    # Fill step 2 details using first options (index 1) for category/subcategory
    procurement_page.fill_step2_item(
        index=0,
        category_label=None,
        sub_category_label=None,
        brand="Logitech",
        model="MX Master 3S",
        quantity="5",
        price="200"
    )
    procurement_page.click_create()

    # Assert successful procurement toast
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
    
    story.finish(status="PASS")
