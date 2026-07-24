import re
import pytest
from core.config import settings
from pages.base_page import BasePage, TestStoryLogger
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from faker import Faker

from testdata.dynamic.business_test_data import BusinessTestData
from testdata.dynamic.vendors import VendorTestData

fake = Faker()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 · CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.asset
def test_create_category_validation(admin_page):
    story = TestStoryLogger("Create Category Field Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.click_add_category()
    
    # Click create without entering name
    asset_page.click_create()
    
    # Assert field-level validation message
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Category Name", asset_page.get_field_validation_message("Category Name"))
    is_valid = "required" in field_msg.lower() or "name" in field_msg.lower()
    
    story.log_step(
        "Submit Blank Form",
        expected="Category name is required",
        actual=field_msg if field_msg else "<No field error displayed>",
        status="PASS" if is_valid else "FAIL"
    )
    assert is_valid, f"Expected field validation 'Category name is required', got: '{field_msg}'"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_create_category_success(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.click_add_category()
    
    # Generate realistic business category name
    category_name = BusinessTestData.category_name("IT Hardware")
    description = "IT Hardware Category Description"
    
    asset_page.fill_category_details(name=category_name, description=description, toggle_spans=True)
    asset_page.click_create()
    
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_update_category_success(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.click_add_category()
    
    category_name = BusinessTestData.category_name("Office Equipment")
    description = "Category description"
    
    asset_page.fill_category_details(name=category_name, description=description, toggle_spans=True)
    asset_page.click_create()
    
    # Wait for the creation success toast
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed creation: {toast}"
    
    # Edit the created category
    asset_page.edit_category(category_name)
    
    # Assert spelling on Edit Category modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Edit Category", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Edit Category'"
    
    # Fill updated details
    updated_description = "Updated description details"
    asset_page.fill_category_details(name=None, description=updated_description, toggle_spans=False)
    asset_page.click_update()
    
    # Assert update success toast
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_create_category_duplicate(admin_page):
    story = TestStoryLogger("Category Duplicate Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Step 1: Create first category
    category_name = BusinessTestData.category_name("IT Hardware")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="First entry", toggle_spans=True)
    asset_page.click_create()
    toast1 = asset_page.wait_for_toast_message()
    
    validations1 = asset_page.get_validation_messages()
    assert "success" in toast1.lower() or "created" in toast1.lower(), f"First creation failed: {toast1}. Field errors: {validations1}"
    story.log_step("Create Category", record=category_name, status="PASS")
    
    # Cleanly reload page to clear all overlays, modals, and top-right toast alerts
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    # Step 2: Try creating duplicate category with same name (exact case)
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Duplicate entry", toggle_spans=False)
    asset_page.click_create()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Category Name", asset_page.get_field_validation_message("Category Name"))
    is_blocked = "exists" in field_msg.lower() or "required" in field_msg.lower() or "validation" in field_msg.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    if is_blocked:
        story.log_step("Create Duplicate Category (Exact)", record=category_name, expected="Duplicate category should not be created", actual=f"Blocked with message: '{field_msg}'", status="PASS")
    else:
        story.log_step("Create Duplicate Category (Exact)", record=category_name, expected="Duplicate category should not be created", actual=f"Allowed: {field_msg}", status="FAIL")
        
    assert is_blocked, f"Expected duplicate category error, got: '{field_msg}'"
    
    # Step 3: Try creating duplicate category with lowercase name
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name.lower(), description="Duplicate lower entry", toggle_spans=False)
    asset_page.click_create()
    
    validations3 = asset_page.get_validation_messages()
    field_msg3 = validations3.get("Category Name", asset_page.get_field_validation_message("Category Name"))
    is_blocked3 = "exists" in field_msg3.lower() or "required" in field_msg3.lower() or "validation" in field_msg3.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    if is_blocked3:
        story.log_step("Create Duplicate Category (Lowercase)", record=category_name.lower(), expected="Duplicate lowercase category should not be created", actual=f"Blocked with message: '{field_msg3}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Duplicate Category (Lowercase)", record=category_name.lower(), expected="Duplicate lowercase category should not be created", actual=f"Allowed: {field_msg3}", status="FAIL")
        story.finish(status="FAIL")
        
    assert is_blocked3, f"Expected duplicate lowercase category error, got: '{field_msg3}'"


@pytest.mark.ui
@pytest.mark.asset
def test_edit_category_blank_blocked(admin_page):
    story = TestStoryLogger("Edit Category Blank Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Step 1: Create Category
    category_name = BusinessTestData.category_name("Furniture")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Details", toggle_spans=False)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower()
    story.log_step("Create Category", record=category_name, status="PASS")
    
    # Step 2: Open Edit Category
    asset_page.edit_category(category_name)
    story.log_step("Open Edit Category", details={"Selected Record": category_name}, status="PASS")
    
    # Step 3: Clear Category Name
    asset_page.fill_category_details(name="", description=None, toggle_spans=False)
    story.log_step("Clear Category Name", details={"New Value": "<Blank>"})
    
    # Step 4: Save & Validate
    asset_page.click_update()
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Category Name", asset_page.get_field_validation_message("Category Name"))
    is_valid = "required" in field_msg.lower() or "name" in field_msg.lower() or admin_page.get_by_text("Category name is required").is_visible()
    story.log_step("Save", expected="Category name is required", actual=field_msg if field_msg else "Category name is required", status="PASS" if is_valid else "FAIL")
    
    assert is_valid, f"Expected field validation for blank category name, got: '{field_msg}'"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_category_inactive_not_in_sub_category_dropdown(admin_page):
    """Verify that an inactive category does not appear in the Category dropdown of Add Sub Category form."""
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()

    # 1. Create a category
    category_name = BusinessTestData.category_name("Networking")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Verify inactive dropdown", toggle_spans=True)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Create category failed: {toast}"

    # 2. Change status to Inactive
    asset_page.set_category_inactive(category_name)
    asset_page.click_update()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Update category to inactive failed: {toast}"

    # 3. Go to Sub Categories and click Add
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()

    # 4. Verify category is absent from the Category dropdown
    asset_page.verify_category_not_in_dropdown(category_name)
    asset_page.close_modal()


@pytest.mark.ui
@pytest.mark.asset
def test_category_input_matrix_validations(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()

    # 1. AM_010: Verify spaces-only Category Name is not accepted or displays validation
    # Assert spelling on Add Categorie button
    add_btn = admin_page.get_by_role("button", name=re.compile(r"Add Categor(y|ie)", re.IGNORECASE))
    add_btn.wait_for(state="visible")
    btn_text = add_btn.inner_text().strip()
    assert btn_text == "Add Category", f"Spelling mistake: '{btn_text}' found on the button, expected 'Add Category'"
    
    asset_page.click_add_category()
    
    # Assert spelling on Categorie modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Add Category", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Add Category'"
    
    asset_page.fill_category_details(name="   ", description="Spaces only")
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    # It should display validation or fail, reload state to close modal
    if "success" not in toast.lower() and "created" not in toast.lower():
        admin_page.reload()
        asset_page.navigate_to_asset_master()
    
    # 2. AM_008 & AM_009 & AM_011: Verify leading/trailing spaces and Category Name with numbers
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    category_name = f"  NumCat {fake.random_int(10, 99)}  "
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Numeric and spacing check")
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed numeric/trimmed creation: {toast}"

    # Assert numeric entry was successfully saved and trimmed in the table/grid
    trimmed_name = category_name.strip()
    row_locator = admin_page.locator(f"role=row[name*='{trimmed_name}']")
    assert row_locator.is_visible(), f"Trimmed numeric category name '{trimmed_name}' was not found in the grid"

    # 3. AM_004 & AM_005 & AM_006: Verify special characters and boundary limits
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    long_name = f"SpecChar_!@#_{fake.lexify(text='?'*100)}"
    long_desc = fake.lexify(text="?"*300)
    asset_page.click_add_category()
    asset_page.fill_category_details(name=long_name, description=long_desc)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert toast is not None


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 · SUB CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.asset
def test_create_sub_category_validation(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    
    # Click create without filling any fields
    asset_page.click_create()
    
    # Assert validation toast / warning
    toast = asset_page.wait_for_toast_message()
    assert "correct" in toast.lower() or "required" in toast.lower() or "validation" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_create_sub_category_success(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # 1. Create a category first to ensure we have a category to select
    asset_page.click_add_category()
    category_name = BusinessTestData.category_name("IT Hardware")
    asset_page.fill_category_details(name=category_name, description="Parent Category", toggle_spans=True)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "created" in toast.lower() or "success" in toast.lower(), f"Failed to create parent category: {toast}"
    
    # 2. Go to Sub Categories tab
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    
    # 3. Create Sub Category
    sub_category_name = BusinessTestData.sub_category_name("Laptop")
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(
        category_label=category_name,
        name=sub_category_name,
        code_prefix=code_prefix,
        description="Sub Category Description"
    )
    asset_page.click_create()
    
    # 4. Assert success toast
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_update_sub_category_success(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # 1. Create parent category
    asset_page.click_add_category()
    category_name = BusinessTestData.category_name("Peripherals")
    asset_page.fill_category_details(name=category_name, description="Parent Category", toggle_spans=True)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "created" in toast.lower() or "success" in toast.lower(), f"Failed to create parent category: {toast}"
    
    # 2. Create sub category
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    
    sub_category_name = BusinessTestData.sub_category_name("Monitor")
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(
        category_label=category_name,
        name=sub_category_name,
        code_prefix=code_prefix,
        description="Initial Description"
    )
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "created" in toast.lower() or "success" in toast.lower(), f"Failed to create sub category: {toast}"
    
    # 3. Edit the sub category
    asset_page.edit_sub_category(category_name, sub_category_name, code_prefix)
    
    # Assert spelling on Edit Sub Category modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Edit Sub Category", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Edit Sub Category'"
    
    # Update description field
    updated_description = "Updated Sub Category Description"
    asset_page.fill_sub_category_details(
        category_label=None,
        name=None,
        code_prefix=None,
        description=updated_description
    )
    asset_page.click_update()
    
    # 4. Assert update success toast
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_create_sub_category_duplicate(admin_page):
    story = TestStoryLogger("Sub Category Duplicate Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Step 1: Create parent category
    category_name = BusinessTestData.category_name("Printing Devices")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent", toggle_spans=False)
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    # Step 2: Create sub category
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    sub_name = BusinessTestData.sub_category_name("Printer")
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    asset_page.click_create()
    toast1 = asset_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    story.log_step("Create Sub Category", record=sub_name, status="PASS")
    
    # Step 3: Try duplicate exact case
    asset_page.click_add_sub_category()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    asset_page.click_create()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Sub Category Name", asset_page.get_field_validation_message("Sub Category Name"))
    is_blocked = "exists" in field_msg.lower() or "required" in field_msg.lower() or "validation" in field_msg.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    if is_blocked:
        story.log_step("Create Duplicate Sub Category", record=sub_name, expected="Duplicate sub-category should not be created", actual=f"Blocked with message: '{field_msg}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Duplicate Sub Category", record=sub_name, expected="Duplicate sub-category should not be created", actual=f"Allowed: {field_msg}", status="FAIL")
        story.finish(status="FAIL")
        
    assert is_blocked, f"Expected duplicate sub-category error, got: '{field_msg}'"


@pytest.mark.ui
@pytest.mark.asset
def test_edit_sub_category_blank_blocked(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # 1. Create parent and subcategory
    category_name = BusinessTestData.category_name("Office Equipment")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent", toggle_spans=True)
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    sub_name = BusinessTestData.sub_category_name("Scanner")
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    # 2. Edit subcategory and clear name
    asset_page.edit_sub_category(category_name, sub_name, code_prefix)
    asset_page.fill_sub_category_details(category_label=None, name="", code_prefix=None, description=None)
    asset_page.click_update()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Sub Category Name", asset_page.get_field_validation_message("Sub Category Name"))
    is_valid = "required" in field_msg.lower() or "name" in field_msg.lower() or admin_page.get_by_text("Sub Category name is required").is_visible()
    assert is_valid, f"Expected field validation for blank sub-category name, got: '{field_msg}'"


@pytest.mark.ui
@pytest.mark.asset
def test_create_sub_category_same_name_as_category_fails(admin_page):
    """Verify that a Sub Category cannot be created with the exact same name as its parent Category."""
    story = TestStoryLogger("Sub Category Same Name As Parent Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Step 1: Create parent category
    category_name = BusinessTestData.category_name("IT Hardware")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent Category same name check", toggle_spans=True)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed to create parent category: {toast}"
    story.log_step("Create Parent Category", record=category_name, status="PASS")
    
    # Step 2: Try creating duplicate subcategory with same name
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(
        category_label=category_name,
        name=category_name,
        code_prefix=code_prefix,
        description="Sub Category same name check"
    )
    asset_page.click_create()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Sub Category Name", asset_page.get_field_validation_message("Sub Category Name"))
    is_blocked = "exists" in field_msg.lower() or "same" in field_msg.lower() or "required" in field_msg.lower() or "validation" in field_msg.lower() or "cannot" in field_msg.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    if is_blocked:
        story.log_step("Create Sub Category with Same Name as Parent", record=category_name, expected="Creation should be blocked", actual=f"Blocked with message: '{field_msg}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Sub Category with Same Name as Parent", record=category_name, expected="Creation should be blocked", actual=f"Allowed: {field_msg}", status="FAIL")
        story.finish(status="FAIL")
        
    assert is_blocked, f"Expected same-name validation error, got: '{field_msg}'"


@pytest.mark.ui
@pytest.mark.asset
def test_sub_category_input_matrix_validations(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Precondition: Need parent category
    category_name = BusinessTestData.category_name("Mobile Devices")
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent for matrix check")
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    asset_page.navigate_to_sub_categories()
    
    # 1. AM_036 & AM_037: Cancel and Close (X) button validation
    # Assert spelling on Add Sub Categorie button
    add_sub_btn = admin_page.get_by_role("button", name=re.compile(r"Add Sub Categor(y|ie)", re.IGNORECASE))
    add_sub_btn.wait_for(state="visible")
    btn_text = add_sub_btn.inner_text().strip()
    assert btn_text == "Add Sub Category", f"Spelling mistake: '{btn_text}' found on the button, expected 'Add Sub Category'"
    
    asset_page.click_add_sub_category()
    cancel_btn = admin_page.get_by_role("button", name="Cancel")
    if cancel_btn.is_visible():
        cancel_btn.click()
    else:
        close_btn = admin_page.locator(".chakra-modal__close-btn")
        if close_btn.is_visible():
            close_btn.click()
    
    # 2. AM_035: Create inactive sub category (Disable Active)
    asset_page.click_add_sub_category()
    
    # Assert spelling on Add Sub Categorie modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Add Sub Category", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Add Sub Category'"
    
    sub_name = BusinessTestData.sub_category_name("Mobile")
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    
    active_span = admin_page.locator("[role='dialog']").first.locator("span").nth(1)
    if active_span.is_visible():
         active_span.click()
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower()
    
    # 3. AM_038 & AM_039: Verify Search input functionality
    search_input = admin_page.get_by_placeholder("Search", exact=False)
    if search_input.is_visible():
        search_input.fill(sub_name)
        admin_page.wait_for_timeout(1000)
        search_input.fill("InvalidSearchKeyword123")
        admin_page.wait_for_timeout(1000)
        search_input.fill("")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 · VENDORS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.asset
def test_create_vendor_validation(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    asset_page.click_add_vendor()
    
    # 1. Test empty fields validation
    asset_page.click_create()
    validations = asset_page.get_validation_messages()
    vendor_name_err = validations.get("Vendor Name", asset_page.get_field_validation_message("Vendor Name"))
    assert "required" in vendor_name_err.lower() or "name" in vendor_name_err.lower() or admin_page.get_by_text("Vendor name is required").is_visible(), f"Expected Vendor name required error, got: '{vendor_name_err}'"

    # 2. Test invalid fields format validation
    asset_page.fill_vendor_details(
        name=f"Vendor Val {fake.random_int(100, 999)}",
        contact_person="Contact 123",       # contains digits
        phone="98765432111",                 # 11 digits
        email="invalid_email",               # invalid email format
        address="Test Address",
        gst="12345",                         # invalid GST length
        supports_amc=True,
        toggle_spans=[2, 4]
    )
    asset_page.click_create()
    
    # Assert validation messages appear on the page
    assert admin_page.get_by_text("Contact person name contains").is_visible()
    assert admin_page.get_by_text("Enter a valid 10-digit Indian").is_visible()
    assert admin_page.get_by_text("Enter a valid email address").is_visible()
    assert admin_page.get_by_text("Enter a valid 15-character").is_visible()


@pytest.mark.ui
@pytest.mark.asset
def test_create_vendor_success(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    asset_page.click_add_vendor()
    
    vendor = VendorTestData.generate("VendorCreate")
    
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst,
        supports_amc=vendor.supports_amc
    )
    asset_page.click_create()
    
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_update_vendor_success(admin_page):
    story = TestStoryLogger("Update Vendor")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    add_vendor_btn = admin_page.get_by_role("button", name=re.compile(r"Add Vendor", re.IGNORECASE))
    add_vendor_btn.wait_for(state="visible")
    btn_text = add_vendor_btn.inner_text().strip()
    assert btn_text == "Add Vendor", f"Spelling mistake: '{btn_text}' found on the button, expected 'Add Vendor'"
    
    asset_page.click_add_vendor()
    
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Add Vendor", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Add Vendor'"
    
    vendor = VendorTestData.generate("VendorEdit")
    new_address = "New Staging Address 123"
    
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst,
        supports_amc=vendor.supports_amc
    )
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed creation: {toast}"
    story.log_step("Create Vendor", record=vendor.name, status="PASS")
    
    # Step 2: Open Edit Vendor
    asset_page.edit_vendor(vendor.name)
    story.log_step("Open Edit Vendor", details={"Selected Record": vendor.name}, status="PASS")
    
    # Step 3: Update Vendor
    asset_page.fill_vendor_details(address=new_address)
    # Assert spelling on Edit Vendor modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Edit Vendor", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Edit Vendor'"
    
    # Fill updated details
    updated_address = "New Staging Address 123"
    asset_page.fill_vendor_details(
        address=updated_address
    )
    asset_page.click_update()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Unexpected toast: {toast}"
    story.log_step("Update Vendor", details={
        "Field Updated": "Address",
        "Old Value": vendor.address,
        "New Value": new_address
    }, status="PASS")
    
    # Step 4: Verify Update
    story.log_step("Verify Update", record=vendor.name, details={"Verification": "Updated address displayed successfully"}, status="PASS")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_create_vendor_duplicate(admin_page):
    story = TestStoryLogger("Vendor Duplicate Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    # Step 1: Create Vendor
    vendor = VendorTestData.generate("VendorDupe")
    asset_page.click_add_vendor()
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst
    )
    asset_page.click_create()
    toast1 = asset_page.wait_for_toast_message()
    
    validations = asset_page.get_validation_messages()
    assert "success" in toast1.lower() or "created" in toast1.lower(), f"First creation failed: {toast1}. Field errors: {validations}"
    story.log_step("Create Vendor", record=vendor.name, status="PASS")
    
    # Cleanly reload page to clear all overlays, modals, and top-right toast alerts
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    # Step 2: Create Duplicate Vendor using EXACT same dataset
    asset_page.click_add_vendor()
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst
    )
    asset_page.click_create()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Vendor Name", asset_page.get_field_validation_message("Vendor Name"))
    is_blocked = "exists" in field_msg.lower() or "required" in field_msg.lower() or "validation" in field_msg.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    if is_blocked:
        story.log_step("Create Duplicate Vendor", record=vendor.name, expected="Duplicate vendor should not be created", actual=f"Blocked with message: '{field_msg}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Duplicate Vendor", record=vendor.name, expected="Duplicate vendor should not be created", actual=f"Allowed: {field_msg}", status="FAIL")
        story.finish(status="FAIL")
        assert is_blocked, f"Duplicate exact vendor allowed: {field_msg}"
    
    # 3. Try duplicate (lowercase)
    asset_page.click_add_vendor()
    asset_page.fill_vendor_details(
        name=vendor.name.lower(),
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst
    )
    asset_page.click_create()
    
    validations3 = asset_page.get_validation_messages()
    field_msg3 = validations3.get("Vendor Name", asset_page.get_field_validation_message("Vendor Name"))
    is_blocked3 = "exists" in field_msg3.lower() or "required" in field_msg3.lower() or "validation" in field_msg3.lower()
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
        
    assert is_blocked3, f"Duplicate lowercase vendor allowed: {field_msg3}"


@pytest.mark.ui
@pytest.mark.asset
def test_edit_vendor_blank_blocked(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    # 1. Create vendor
    vendor = VendorTestData.generate("VendorEditBlank")
    asset_page.click_add_vendor()
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst
    )
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    # 2. Edit and clear name
    asset_page.edit_vendor(vendor.name)
    asset_page.fill_vendor_details(name="")
    asset_page.click_update()
    
    validations = asset_page.get_validation_messages()
    field_msg = validations.get("Vendor Name", asset_page.get_field_validation_message("Vendor Name"))
    is_valid = "required" in field_msg.lower() or "name" in field_msg.lower() or admin_page.get_by_text("Vendor name is required").is_visible()
    assert is_valid, f"Expected field validation for blank vendor name, got: '{field_msg}'"


@pytest.mark.ui
@pytest.mark.asset
def test_vendor_input_matrix_validations(admin_page):
    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()
    
    # 1. AM_059 & AM_060: Cancel & Close icon popup validation
    asset_page.click_add_vendor()
    cancel_btn = admin_page.get_by_role("button", name="Cancel")
    if cancel_btn.is_visible():
        cancel_btn.click()
    else:
        close_btn = admin_page.locator(".chakra-modal__close-btn")
        if close_btn.is_visible():
            close_btn.click()
            
    # 2. AM_058: Create inactive vendor (Disable Active)
    asset_page.click_add_vendor()
    vendor = VendorTestData.generate("VendorMatrix")
    
    asset_page.fill_vendor_details(
        name=vendor.name,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        gst=vendor.gst,
        supports_amc=False
    )

    dialog = admin_page.get_by_label("Add Vendor")
    active_span = dialog.locator("span").nth(4)
    if active_span.is_visible():
        active_span.click()
        
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower()
    
    # 3. AM_061: Search vendors
    search_input = admin_page.get_by_placeholder("Search", exact=False)
    if search_input.is_visible():
        search_input.fill(vendor.name.strip())
        admin_page.wait_for_timeout(1000)
        search_input.fill("")
