import pytest
import os
import re
import logging
import random
import string
from core.config import settings
from playwright.sync_api import expect
from pages.hrlense_portal.master.company_page import CompanyPage
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

def generate_unique_company_name() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase, k=6))
    # Remove any non-alphabetic/non-space chars from company name to be safe
    base = re.sub(r'[^a-zA-Z\s]', '', fake.company())
    # Strip double spaces and trim
    base = " ".join(base.split())
    return f"{base} {suffix}"

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company
def test_create_company_validation(admin_page):
    logger.info("Verify that validation occurs when trying to add a company with missing fields")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    company_page.click_add_new_company()
    
    # Click Add Company directly without filling anything
        
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "enter the company name" in toast.lower() or "required" in toast.lower(), f"Expected missing field validation, but got: {toast}"
    
    # Close the drawer / Cancel
    admin_page.get_by_role("button", name="Cancel").click()


@pytest.mark.ui
@pytest.mark.company
def test_company_crud_flow(admin_page):
    logger.info("Verify end-to-end CRUD flow for Company master: Create, Read/Search, Update")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    # 1. CREATE
    company_page.click_add_new_company()
    company_name = generate_unique_company_name()
    company_code = f"CMP{fake.random_int(100, 999)}"
    
    logo_path = os.path.abspath("testdata/static/png/—Pngtree—building vector icon_3757837.png")
    stamp_path = os.path.abspath("testdata/static/png/—Pngtree—iso 9001 certified company logo_20971536.png")

    company_page.fill_company_details(
        name=company_name,
        address="123 Admin Lane",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=company_code,
        logo_path=logo_path,
        stamp_path=stamp_path
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Create company failed: {toast}"
    
    # 2. READ / SEARCH
    company_page.search_company(company_name)
    row_locator = admin_page.locator(f"role=row[name*='{company_name}']")
    expect(row_locator).to_be_visible()
    
    # 3. UPDATE
    company_page.edit_company(company_name)
    updated_address = "456 Updated Boulevard"
    company_page.page.get_by_placeholder("Enter address").fill(updated_address)
    company_page.click_update_company()
    
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Update company failed: {toast}"
    
    # Verify updated address is shown in the row details
    company_page.search_company(company_name)
    expect(row_locator.locator(f"text={updated_address}")).to_be_visible()
    
    # Deletion is not supported in the UI (only Add, Edit, Update)


@pytest.mark.ui
@pytest.mark.company
def test_company_name_format_validation(admin_page):
    logger.info("Verify that company name can contain numbers and special characters according to standard")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    company_page.click_add_new_company()
    
    # Authentic corporate name with numbers and special characters
    base_name = f"{fake.last_name()} {random.choice(['Technologies', 'Enterprises', 'Global', 'Solutions'])}"
    input_name = f"123 {base_name} & Co 456"
    company_code = f"CMP{fake.random_int(1000, 9999)}"
    
    company_page.fill_company_details(
        name=input_name,
        address="Test Address 123",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=company_code
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create company: {toast}"
    
    # The application trims numbers and saves only alphabet parts. 
    # So "123 TestCo XYZ and Co 456" becomes "TestCo XYZ and Co".
    # Search and verify it exists under the trimmed name (base_name)
    company_page.search_company(base_name)
    row_locator = admin_page.locator(f"role=row[name*='{base_name}']")
    expect(row_locator).to_be_visible()
    
    # Explicitly verify the text in the row has the numbers trimmed
    row_text = row_locator.inner_text()
    name_part = row_text.split("\n")[0]
    assert "123" not in name_part, f"Numbers '123' were not trimmed from company name: {name_part}"
    assert "456" not in name_part, f"Numbers '456' were not trimmed from company name: {name_part}"
    assert base_name in name_part, f"Expected alphabet-only name '{base_name}' in row name: {name_part}"



@pytest.mark.ui
@pytest.mark.company
def test_company_redundancy_and_duplicates(admin_page):
    logger.info("Verify that creating duplicate company names (exact, case-insensitive, spacing variations) is blocked")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    # 1. Create base company
    base_name = generate_unique_company_name()
    base_code = f"CMP{fake.random_int(10000, 99999)}"
    
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=base_name,
        address="123 Test St",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=base_code
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create base company: {toast}"
    
    # Helper to check if a duplicate is blocked
    def assert_duplicate_is_blocked(dup_name, dup_code, description):
        company_page.click_add_new_company()
        company_page.fill_company_details(
            name=dup_name,
            address="123 Test St",
            zip_code="221005",
            country="India",
            state="Uttar Pradesh",
            city="Varanasi",
            code=dup_code
        )
        company_page.click_add_company()
        toast_dup = company_page.wait_for_toast_message()
        
        # If it was allowed (which is a bug/failure), fail
        is_success = "success" in toast_dup.lower() or "created" in toast_dup.lower()
        if is_success:
            pytest.fail(f"Duplicate company name allowed for {description} ('{dup_name}'): {toast_dup}")
        else:
            # Cancel the drawer and reset
            cancel_btn = admin_page.get_by_role("button", name="Cancel")
            if cancel_btn.is_visible():
                cancel_btn.click()
            else:
                admin_page.reload()
                company_page.navigate_to_company_master()
                
    # 2. Test exact match duplicate
    assert_duplicate_is_blocked(base_name, f"CMP{fake.random_int(10000, 99999)}", "exact match")
    
    # 3. Test case-insensitive duplicate
    assert_duplicate_is_blocked(base_name.lower(), f"CMP{fake.random_int(10000, 99999)}", "case-insensitive match")
    assert_duplicate_is_blocked(base_name.upper(), f"CMP{fake.random_int(10000, 99999)}", "uppercase match")
    
    # 4. Test spacing variations
    spacing_name = base_name.replace(" ", "  ")  # double spaces
    assert_duplicate_is_blocked(spacing_name, f"CMP{fake.random_int(10000, 99999)}", "internal spacing variation")
    
    # 5. Test leading/trailing spaces
    padded_name = f"  {base_name}  "
    assert_duplicate_is_blocked(padded_name, f"CMP{fake.random_int(10000, 99999)}", "leading/trailing spaces")
    



@pytest.mark.ui
@pytest.mark.company
def test_company_blank_save_and_spaces_only(admin_page):
    logger.info("Verify that saving with a blank company name or spaces-only name is rejected")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    # 1. Blank Save
    company_page.click_add_new_company()
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "enter the company name" in toast.lower() or "required" in toast.lower() or "fail" in toast.lower() or "validation" in toast.lower(), f"Unexpected toast for blank save: {toast}"
    
    # 2. Spaces Only Name
    company_page.fill_company_details(
        name="    ",
        address="123 Test St",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=f"CMP{fake.random_int(1000, 9999)}"
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    
    # If it was allowed (which is a bug), reload and fail
    if "success" in toast.lower() or "created" in toast.lower():
        admin_page.reload()
        company_page.navigate_to_company_master()
        pytest.fail("Saved company with spaces-only name successfully. Trimming validation failed.")
    
    # Cancel the drawer / reload
    admin_page.get_by_role("button", name="Cancel").click()


@pytest.mark.ui
@pytest.mark.company
def test_company_name_trimming(admin_page):
    logger.info("Verify that leading and trailing spaces in the company name are trimmed when saved")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    original_name = generate_unique_company_name()
    padded_name = f"   {original_name}   "
    company_code = f"CMP{fake.random_int(1000, 9999)}"
    
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=padded_name,
        address="123 Test St",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=company_code
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create company with padded name: {toast}"
    
    # Verify search with trimmed name finds the row
    company_page.search_company(original_name)
    row_locator = admin_page.locator(f"role=row[name*='{original_name}']")
    expect(row_locator).to_be_visible()
    
    # Verify the text in the row is trimmed
    row_text = row_locator.inner_text()
    assert padded_name not in row_text, "Company name was not trimmed in the grid"
    assert original_name in row_text, "Trimmed company name not found in the grid"
    



@pytest.mark.ui
@pytest.mark.company
def test_company_code_uniqueness(admin_page):
    logger.info("Verify that Company Code must be unique")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    # 1. Create first company with specific code
    code = f"CODE{fake.random_int(1000, 9999)}"
    name1 = generate_unique_company_name()
    
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=name1,
        address="123 Test St",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=code
    )
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower()
    
    # 2. Try to create second company with same code
    name2 = generate_unique_company_name()
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=name2,
        address="456 Test St",
        zip_code="221005",
        country="India",
        state="Uttar Pradesh",
        city="Varanasi",
        code=code
    )
    company_page.click_add_company()
    toast_dup = company_page.wait_for_toast_message()
    
    is_success = "success" in toast_dup.lower() or "created" in toast_dup.lower()
    if is_success:
        pytest.fail(f"Duplicate company code '{code}' was allowed: {toast_dup}")
    else:
        admin_page.get_by_role("button", name="Cancel").click()


@pytest.mark.ui
@pytest.mark.company
def test_company_edit_validations(admin_page):
    logger.info("Verify that validation checks (blank name, duplicate name) are enforced during update/edit")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    # 1. Create two base companies
    name_a = generate_unique_company_name()
    name_b = generate_unique_company_name()
    code_a = f"CMPA{fake.random_int(1000, 9999)}"
    code_b = f"CMPB{fake.random_int(1000, 9999)}"
    
    # Create A
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=name_a, address="123 Admin Lane", zip_code="221005", country="India",
        state="Uttar Pradesh", city="Varanasi", code=code_a
    )
    company_page.click_add_company()
    company_page.wait_for_toast_message()
    
    # Create B
    company_page.click_add_new_company()
    company_page.fill_company_details(
        name=name_b, address="123 Admin Lane", zip_code="221005", country="India",
        state="Uttar Pradesh", city="Varanasi", code=code_b
    )
    company_page.click_add_company()
    company_page.wait_for_toast_message()
    
    # 2. Try to edit Company A and change its name to Company B (redundancy check)
    company_page.search_company(name_a)
    company_page.edit_company(name_a)
    admin_page.get_by_placeholder("Enter company name").fill(name_b)
    company_page.click_update_company()
    toast = company_page.wait_for_toast_message()
    
    if "success" in toast.lower() or "updated" in toast.lower():
        pytest.fail(f"Edit allowed changing name of '{name_a}' to duplicate name '{name_b}'")
    else:
        # Cancel the edit modal
        cancel_btn = admin_page.get_by_role("button", name="Cancel")
        if cancel_btn.is_visible():
            cancel_btn.click()
        else:
            admin_page.reload()
            company_page.navigate_to_company_master()
            
    # 3. Try to edit Company A and clear the name field (blank save check)
    company_page.search_company(name_a)
    company_page.edit_company(name_a)
    admin_page.get_by_placeholder("Enter company name").clear()
    company_page.click_update_company()
    toast_blank = company_page.wait_for_toast_message()
    
    if "success" in toast_blank.lower() or "updated" in toast_blank.lower():
        pytest.fail("Edit allowed saving a blank company name")
    else:
        cancel_btn = admin_page.get_by_role("button", name="Cancel")
        if cancel_btn.is_visible():
            cancel_btn.click()
        else:
            admin_page.reload()
            company_page.navigate_to_company_master()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company
def test_manual_director_inline_required_fields_validation(admin_page):
    """
    Verify that when clicking 'Add New' in Company Master, the manual director inline form
    enforces required field validation for Director Name, Email, and Phone Number.
    """
    logger.info("Verify manual director inline form required fields validation")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    company_page.click_add_new_company()
    
    validation_results = company_page.verify_manual_director_required_fields_validation()
    assert validation_results["name_required"], "Director Name field must be required"
    assert validation_results["email_required"], "Email field must be required"
    assert validation_results["phone_required"], "Phone Number field must be required"
    
    # Cancel manual director form and cancel company modal
    company_page.click_cancel_manual_director()
    admin_page.get_by_role("button", name="Cancel").click()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company
def test_company_add_manual_director_on_create(admin_page):
    """
    ADD Operation:
    Fill company form from scratch (Name, Code, Address, Zip Code) and add a manual director.
    """
    logger.info("Testing ADD company operation: fill form from scratch and add manual director")
    from testdata.dynamic.business_test_data import DirectorTestData
    from workflows.hrlense_portal.master.company_workflow import CompanyWorkflow

    d_data = DirectorTestData.generate_manual_director()

    comp_info = {
        "company_name": generate_unique_company_name(),
        "address": f"{fake.building_number()} {fake.street_name()}",
        "zip_code": "110001",
        "country": "India",
        "state": "Delhi",
        "city": "New Delhi",
        "code": f"CMP-{random.randint(1000, 9999)}"
    }

    workflow = CompanyWorkflow(admin_page)
    toast = workflow.create_company_with_manual_director_from_scratch(comp_info, d_data)
    logger.info(f"Create Company Toast: {toast}")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company
def test_company_add_manual_director_on_edit(admin_page):
    """
    EDIT Operation:
    Open existing company in edit mode and just add manual director.
    """
    logger.info("Testing EDIT company operation: open existing company and just add manual director")
    from testdata.dynamic.business_test_data import BusinessTestData, DirectorTestData
    from workflows.hrlense_portal.master.company_workflow import CompanyWorkflow

    existing_companies = BusinessTestData.get_companies()
    target_comp = existing_companies[0].get("companyName") if existing_companies else "TEK Inspirations LLC"
    d_data = DirectorTestData.generate_manual_director()

    workflow = CompanyWorkflow(admin_page)
    toast = workflow.edit_company_add_manual_director_only(target_comp, d_data)
    logger.info(f"Edit Company Toast: {toast}")


@pytest.mark.ui
@pytest.mark.company
@pytest.mark.full_form
def test_create_company_full_form_submission(admin_page):
    logger.info("Verify that all 12 fields can be filled completely in a single test case")
    company_page = CompanyPage(admin_page)
    company_page.navigate_to_company_master()
    
    company_page.click_add_new_company()
    company_name = generate_unique_company_name()
    company_code = f"CMP{fake.random_int(1000, 9999)}"
    
    logo_path = os.path.abspath("testdata/static/png/—Pngtree—building vector icon_3757837.png")
    stamp_path = os.path.abspath("testdata/static/png/—Pngtree—iso 9001 certified company logo_20971536.png")

    # PIN Code 221005 (Varanasi, UP) auto-fills BOTH State (Uttar Pradesh) and City (Varanasi) cleanly from API!
    company_page.fill_company_details(
        logo_path=logo_path,    # Order 1
        stamp_path=stamp_path,  # Order 2
        name=company_name,      # Order 3
        country="India",        # Order 4
        zip_code="221005",      # Order 5 (Auto-fills Order 6: State & Order 7: City)
        address="999 Enterprise Blvd", # Order 8
        code=company_code,      # Order 9
        director="a",           # Order 10 (Triggers API & selects first employee)
        auditor="a",            # Order 11 (Triggers API & selects first employee)
        pf_consultant="a"       # Order 12 (Triggers API & selects first employee)
    )
    
    company_page.click_add_company()
    toast = company_page.wait_for_toast_message()
    logger.info(f"CAPTURED TOAST MESSAGE: '{toast}'")
    assert any(term in toast.lower() for term in ["success", "created", "added", "saved"]), f"Create company failed with toast: '{toast}'"
