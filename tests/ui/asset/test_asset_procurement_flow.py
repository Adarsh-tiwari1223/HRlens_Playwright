import pytest
import re
from core.config import settings
from pages.master.company_page import CompanyPage
from pages.asset.asset_master_page import AssetMasterPage
from pages.asset.asset_procurement_page import AssetProcurementPage
from faker import Faker

fake = Faker()

def get_unique_gst() -> str:
    return f"22{fake.lexify(text='?????').upper()}0000A1Z5"

@pytest.mark.ui
@pytest.mark.asset
def test_asset_e2e_procurement_flow(admin_page):
    # Ensure login has fully completed and redirected to dashboard
    admin_page.wait_for_url("**/dashboard", timeout=20000)
    admin_page.wait_for_load_state("networkidle")

    # 1. Create a unique Company
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    company_page.click_add_new_company()
    
    company_name = f"Procurement Company {fake.word().capitalize()} {fake.random_int(100, 999)}"
    company_code = f"CMP{fake.random_int(100, 999)}"
    company_page.fill_company_details(
        name=company_name,
        address="Varanasi, UP, India",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=company_code,
        director="Admin",
        auditor="Recruiter",
        pf_consultant="Sales"
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create company: {toast}"
    
    # 2. Create a unique Category
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.click_add_category()
    
    category_name = f"Procurement Cat {fake.word().capitalize()} {fake.random_int(100, 999)}"
    asset_page.fill_category_details(name=category_name, description="Procurement Parent Category", toggle_spans=True)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create category: {toast}"
    
    # 3. Create a unique Sub Category under the created Category
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    sub_category_name = f"Procurement Sub {fake.word().capitalize()} {fake.random_int(100, 999)}"
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(
        category_label=category_name,
        name=sub_category_name,
        code_prefix=code_prefix,
        description="Procurement Sub Category"
    )
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create subcategory: {toast}"
    
    # 4. Create a unique Vendor
    asset_page.navigate_to_vendors()
    asset_page.click_add_vendor()
    vendor_name = f"Procurement Vendor {fake.word().capitalize()} {fake.random_int(100, 999)}"
    phone = f"9{fake.random_number(digits=9, fix_len=True)}"
    email = f"proc_vendor_{fake.random_int(100000, 999999)}@example.com"
    gst = get_unique_gst()
    asset_page.fill_vendor_details(
        name=vendor_name,
        contact_person="Test Contact Person",
        phone=phone,
        email=email,
        address="Test vendor address",
        gst=gst,
        supports_amc=True
    )
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create vendor: {toast}"
    
    # 5. Create Asset Procurement
    procurement_page = AssetProcurementPage(admin_page)
    procurement_page.navigate_to_asset_procurement()
    procurement_page.click_new_procurement()
    
    invoice_no = f"INV-{fake.random_int(1000, 9999)}"
    # Fill step 1 details using created vendor, Varanasi branch, and created company
    procurement_page.fill_step1_details(
        vendor_label=vendor_name,
        branch_label="Varanasi",
        company_label=company_name,
        invoice_no=invoice_no,
        purchase_date="2026-07-14",
        amount_before_gst="1000",
        gst_amount="180"
    )
    procurement_page.click_next()
    
    # Fill step 2 details using created category and subcategory
    procurement_page.fill_step2_item(
        index=0,
        category_label=category_name,
        sub_category_label=sub_category_name,
        brand="Logitech",
        model="MX Master 3S",
        quantity="5",
        price="200",
        gst="36"
    )
    procurement_page.click_create()
    
    # Assert successful procurement toast
    toast = procurement_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower() or "procured" in toast.lower(), f"Procurement failed: {toast}"
    
    # Verify procurement code row is visible in the list grid
    admin_page.wait_for_timeout(2000)
    row_locator = admin_page.locator(f"role=row[name*='{vendor_name}'][name*='{invoice_no}']")
    assert row_locator.is_visible(), f"Procurement entry with Vendor '{vendor_name}' and Invoice '{invoice_no}' was not found in the grid"
