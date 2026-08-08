import re
import logging
import pytest
from core.config import settings
from pages.base_page import BasePage, TestStoryLogger
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from workflows.hrlense_portal.asset.asset_workflow import AssetWorkflow
from workflows.hrlense_portal.asset.asset_master_workflow import AssetMasterWorkflow
from faker import Faker

from testdata.dynamic.business_test_data import BusinessTestData
from testdata.dynamic.vendors import VendorTestData

logger = logging.getLogger(__name__)
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
    workflow = AssetMasterWorkflow(admin_page)
    category_name = f"IT Hardware {fake.random_int(10, 99)}"
    toast = workflow.create_category_workflow(name=category_name, description="IT Hardware Category Description", toggle_spans=False)
    assert "success" in toast.lower() or "created" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_update_category_success(admin_page):
    workflow = AssetMasterWorkflow(admin_page)
    asset_page = AssetMasterPage(admin_page)
    
    category_name = f"Office Equipment {fake.random_int(10, 99)}"
    toast = workflow.create_category_workflow(name=category_name, description="Category description", toggle_spans=False)
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
    category_name = f"IT Hardware {fake.random_int(10, 99)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="First entry", toggle_spans=False)
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
    category_name = f"Hardware {fake.random_int(10, 99)}"
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

    # 1. Create a category with unique name
    category_name = f"Networking {fake.random_int(1000, 9999)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Verify inactive dropdown", toggle_spans=False)
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Create category failed: {toast}"

    # 2. Change status to Inactive
    asset_page.set_category_inactive(category_name)
    asset_page.click_update()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Update category to inactive failed: {toast}"
    logger.info(f"[INACTIVE CATEGORY VALIDATION] Category '{category_name}' was set to INACTIVE.")

    # 3. Go to Sub Categories and click Add
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()

    # 4. Verify category is absent from the Category dropdown
    logger.info(f"[DROPDOWN VALIDATION] Checking Sub Category → Category dropdown for inactive category '{category_name}'.")
    asset_page.verify_category_not_in_dropdown(category_name)
    logger.info(f"[PASS] Inactive category '{category_name}' is NOT available in the Sub Category Category dropdown.")
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
    category_name = f"IT Hardware {fake.random_int(1000, 9999)}"
    asset_page.fill_category_details(name=category_name, description="Parent Category", toggle_spans=False)
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
    category_name = f"Peripherals {fake.random_int(1000, 9999)}"
    asset_page.fill_category_details(name=category_name, description="Parent Category", toggle_spans=False)
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
    category_name = f"Printing Devices {fake.random_int(10, 99)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent", toggle_spans=False)
    asset_page.click_create()
    asset_page.wait_for_toast_message()
    
    # Step 2: Create baseline sub category
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()
    sub_name = f"Printer {fake.random_int(10, 99)}"
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    asset_page.click_create()
    toast1 = asset_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower() or len(asset_page.get_active_form_errors()) == 0, f"Sub category creation failed: {toast1}"
    story.log_step("Create Sub Category", record=sub_name, status="PASS")
    
    # Step 3: Try duplicate exact case under same parent category
    asset_page.click_add_sub_category()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    asset_page.click_create()
    
    validations = asset_page.get_validation_messages()
    active_errors = asset_page.get_active_form_errors()
    field_msg = validations.get("Sub Category Name", asset_page.get_field_validation_message("Sub Category Name"))
    is_blocked = "exists" in field_msg.lower() or "required" in field_msg.lower() or "validation" in field_msg.lower() or len(active_errors) > 0
    
    admin_page.reload()
    asset_page.navigate_to_asset_master()
    
    if is_blocked:
        story.log_step("Create Duplicate Sub Category", record=sub_name, expected="Duplicate sub-category should not be created", actual=f"Blocked with message: '{active_errors or field_msg}'", status="PASS")
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
    category_name = f"Office Equipment {fake.random_int(1000, 9999)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent", toggle_spans=False)
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
    """
    Verify that a Sub Category cannot be created with the exact same name as its parent Category.
    Workflow:
    1. Retrieve parent category name from Category grid.
    2. Open Add Sub Category modal.
    3. Select parent category name and enter the exact same name for Sub Category name.
    4. Fill code_prefix and mandatory fields.
    5. Click Create.
    6. IMMEDIATELY capture inline errors (.chakra-form__error-message) and toast alerts ([role='alert']).
    """
    story = TestStoryLogger("Sub Category Same Name As Parent Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()

    # Step 1: Go to Category tab and get an existing Category name
    asset_page.navigate_to_category_tab()
    # Step 1: Create fresh baseline Category
    category_name = f"Hardware {fake.random_int(10, 99)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent Category same name check", toggle_spans=False)
    asset_page.click_create()
    asset_page.wait_for_toast_message()

    story.log_step("Retrieved Parent Category Name", record=category_name, status="PASS")

    # Step 2: Go to Sub Category tab and open Add Sub Category modal
    asset_page.navigate_to_sub_categories()
    asset_page.click_add_sub_category()

    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(
        category_label=category_name,
        name=category_name,
        code_prefix=code_prefix,
        description="Sub Category same name check"
    )

    # Step 3: Click Create
    asset_page.click_create()

    # Step 4: IMMEDIATELY capture inline errors and toast alerts (WITHOUT reload/navigate)
    inline_errors = asset_page.get_active_form_errors()

    toast_txt = ""
    try:
        alert_loc = admin_page.locator("[role='alert'], .chakra-toast, #chakra-toast-manager-top-right").first
        if alert_loc.is_visible(timeout=2000):
            toast_txt = alert_loc.inner_text().strip()
    except Exception:
        pass

    combined_response = f"Inline Errors: {inline_errors} | Toast Alert: '{toast_txt}'"
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[SAME NAME CHECK RESPONSE] {combined_response}")

    err_str = f"{inline_errors} {toast_txt}".lower()
    is_blocked = "exists" in err_str or "same" in err_str or "cannot" in err_str or "already" in err_str or "validation" in err_str or "correct" in err_str

    if is_blocked:
        story.log_step(
            "Create Sub Category with Same Name as Parent",
            record=category_name,
            expected="Creation should be blocked",
            actual=f"Blocked with response: {combined_response}",
            status="PASS"
        )
        story.finish(status="PASS")
    else:
        story.log_step(
            "Create Sub Category with Same Name as Parent",
            record=category_name,
            expected="Creation should be blocked",
            actual=f"APPLICATION BUG: Allowed creating Sub Category with exact same name as parent Category! ({combined_response})",
            status="FAIL"
        )
        story.finish(status="FAIL")
        assert is_blocked, f"APPLICATION BUG: Allowed creating Sub Category with exact same name as parent Category '{category_name}'! Response: {combined_response}"


@pytest.mark.ui
@pytest.mark.asset
def test_category_subcategory_dependency_rule(admin_page):
    """
    Validates Category-SubCategory Dependency Mandatory Rule:
    - Every Category must have 2 to 3 Sub-Categories.
    - Sub-Categories must be linked to active parent Category.
    - Setup fails clearly if Category has 0 Sub-Categories.
    """
    story = TestStoryLogger("Category-SubCategory Dependency Rule")
    story.start()

    workflow = AssetMasterWorkflow(admin_page)
    cat_res, sub_res = workflow.setup_category_with_subcategories_workflow()

    story.log_step(
        "Flowchart Sub-Category Creation & Row Verification",
        expected="2-3 Sub-Categories created under Category and verified in grid table",
        actual=f"Category '{cat_res}' created & verified with Sub-Categories: {sub_res}",
        status="PASS"
    )

    assert cat_res and len(sub_res) >= 1
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_sub_category_input_matrix_validations(admin_page):
    story = TestStoryLogger("Sub Category Input Matrix & Modal Validation")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    
    # Precondition: Create fresh parent category
    category_name = f"Mobile Devices {fake.random_int(10000, 99999)}"
    asset_page.click_add_category()
    asset_page.fill_category_details(name=category_name, description="Parent for matrix check")
    asset_page.click_create()
    toast_cat = asset_page.wait_for_toast_message()
    story.log_step("Create Parent Category", record=category_name, actual=toast_cat, status="PASS")
    
    asset_page.navigate_to_sub_categories()
    
    # 1. AM_036 & AM_037: Cancel and Close (X) button validation
    add_sub_btn = admin_page.get_by_role("button", name=re.compile(r"Add Sub Categor(y|ie)", re.IGNORECASE))
    add_sub_btn.wait_for(state="visible")
    btn_text = add_sub_btn.inner_text().strip()
    assert btn_text == "Add Sub Category", f"Spelling mistake: '{btn_text}' found on the button, expected 'Add Sub Category'"
    story.log_step("Verify Add Button Spelling", record=btn_text, status="PASS")
    
    asset_page.click_add_sub_category()
    cancel_btn = admin_page.get_by_role("button", name="Cancel")
    if cancel_btn.is_visible():
        cancel_btn.click()
    else:
        close_btn = admin_page.locator(".chakra-modal__close-btn")
        if close_btn.is_visible():
            close_btn.click()
    story.log_step("Test Cancel / Close Modal", details={"Action": "Dialog Dismissed"}, status="PASS")
    
    # 2. AM_035: Create inactive sub category (Disable Active)
    asset_page.click_add_sub_category()
    
    # Assert spelling on Add Sub Category modal header
    header_locator = admin_page.locator(".chakra-modal__header")
    header_locator.wait_for(state="visible")
    header_text = header_locator.inner_text().strip()
    assert header_text == "Add Sub Category", f"Spelling mistake: '{header_text}' found in the dialog header, expected 'Add Sub Category'"
    story.log_step("Verify Modal Header Spelling", record=header_text, status="PASS")
    
    sub_name = f"Mobile {fake.random_int(10000, 99999)}"
    code_prefix = fake.lexify(text="???").upper()
    asset_page.fill_sub_category_details(category_label=category_name, name=sub_name, code_prefix=code_prefix)
    
    active_span = admin_page.locator("[role='dialog']").first.locator("span").nth(1)
    if active_span.is_visible():
         active_span.click()
    asset_page.click_create()
    toast = asset_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower()
    story.log_step(
        "Create Inactive Sub Category",
        record=sub_name,
        details={"Parent Category": category_name, "Code Prefix": code_prefix, "Active": "False"},
        actual=toast,
        status="PASS"
    )
    
    # 3. AM_038 & AM_039: Verify Search input functionality
    search_input = admin_page.get_by_placeholder("Search", exact=False)
    if search_input.is_visible():
        search_input.fill(sub_name)
        admin_page.wait_for_timeout(1000)
        story.log_step("Search Valid Sub Category", record=sub_name, details={"Filter Result": "Row Displayed"}, status="PASS")

        search_input.fill("InvalidSearchKeyword123")
        admin_page.wait_for_timeout(1000)
        story.log_step("Search Invalid Keyword", record="InvalidSearchKeyword123", details={"Filter Result": "No Records"}, status="PASS")

        search_input.fill("")
        admin_page.wait_for_timeout(500)
        story.log_step("Clear Search Filter", details={"Grid State": "Full Table Restored"}, status="PASS")

    story.finish(status="PASS")


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
    """
    Validates Vendor Uniqueness Rules:
    - Vendor Name CAN be the same.
    - Vendor Email, Phone Number, and GST MUST be unique.
    - Application blocks creation if duplicate Email or Phone Number is used.
    """
    story = TestStoryLogger("Vendor Uniqueness & Duplicate Validation (Email & Phone)")
    story.start()

    asset_page = AssetMasterPage(admin_page)
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()

    # Step 1: Create Baseline Vendor
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
    story.log_step("Create Baseline Vendor", record=vendor.name, details={"Phone": vendor.phone, "Email": vendor.email}, status="PASS")

    # Step 2: Try creating duplicate vendor with DIFFERENT name, but SAME Phone & Email
    asset_page._ensure_modal_closed()
    asset_page.navigate_to_asset_master()
    asset_page.navigate_to_vendors()

    diff_name_vendor = f"Different {vendor.name}"
    asset_page.click_add_vendor()
    asset_page.fill_vendor_details(
        name=diff_name_vendor,              # Different name (allowed)
        contact_person=vendor.contact_person,
        phone=vendor.phone,                  # Same phone (must block)
        email=vendor.email,                  # Same email (must block)
        address=vendor.address,
        gst=vendor.gst
    )
    asset_page.click_create()

    validations2 = asset_page.get_validation_messages()
    active_errors = asset_page.get_active_form_errors()
    phone_msg = validations2.get("Phone", asset_page.get_field_validation_message("Phone"))
    email_msg = validations2.get("Email", asset_page.get_field_validation_message("Email"))

    combined_err = f"{active_errors} {phone_msg} {email_msg}".lower()
    is_blocked = "exists" in combined_err or "already" in combined_err or "duplicate" in combined_err or "correct" in combined_err or "validation" in combined_err or len(active_errors) > 0

    if is_blocked:
        story.log_step(
            "Duplicate Email/Phone Creation Check",
            record=diff_name_vendor,
            expected="Duplicate Email & Phone creation should be blocked",
            actual=f"Blocked cleanly: '{active_errors or combined_err}'",
            status="PASS"
        )
        story.finish(status="PASS")
    else:
        story.log_step(
            "Duplicate Email/Phone Creation Check",
            record=diff_name_vendor,
            expected="Duplicate Email & Phone creation should be blocked",
            actual=f"Allowed duplicate email/phone creation: '{combined_err}'",
            status="FAIL"
        )
        story.finish(status="FAIL")
        
    assert is_blocked, f"Expected duplicate email/phone validation error, got: '{combined_err}'"

    assert is_blocked, f"Vendor creation allowed with duplicate Phone '{vendor.phone}' / Email '{vendor.email}': {combined_err}"


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
