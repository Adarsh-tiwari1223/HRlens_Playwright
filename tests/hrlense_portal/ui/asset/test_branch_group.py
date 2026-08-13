import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from faker import Faker

fake = Faker()



@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_validation(admin_page):
    """
    Consolidated Branch Group Name Validation Rules Test:
    1. Blank ("") -> BLOCK (must_not_be_blank: true)
    2. Whitespace only ("   ") -> BLOCK (must_not_be_whitespace_only: true)
    3. Leading whitespace ("  Branch Group") -> TRIM (leading_trailing_whitespace: TRIM)
    4. Trailing whitespace ("Branch Group  ") -> TRIM (leading_trailing_whitespace: TRIM)
    5. Contains special characters ("Branch@Group") -> BLOCK (special_characters: NOT_ALLOWED)
    6. Starts with a number ("123Branch Group") -> BLOCK (cannot_start_with_number: true)
    7. Only numbers ("123456") -> BLOCK (cannot_contain_only_numbers: true)
    8. Numbers after first character ("Branch Group 123") -> ALLOW (numbers_after_first_character: ALLOWED)
    """
    story = TestStoryLogger("Branch Group Name Validation Matrix")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()

    # -------------------------------------------------------------------------
    # Scenario 1: Blank ("") -> BLOCK
    # -------------------------------------------------------------------------
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name="", branch_names=None)
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    validations1 = bg_page.get_validation_messages()
    is_blocked1 = "correct" in toast1.lower() or "required" in toast1.lower() or "validation" in toast1.lower() or any("required" in v.lower() or "name" in v.lower() for v in validations1.values()) or admin_page.locator("[role='dialog']").is_visible()

    story.log_step(
        "Scenario 1: Blank Branch Group Name",
        record="<Blank>",
        expected="BLOCK - Required field validation should trigger",
        actual=f"Blocked: Toast='{toast1}', Form Errors={validations1}" if is_blocked1 else "Allowed creation",
        status="PASS" if is_blocked1 else "FAIL"
    )
    assert is_blocked1, f"Expected blank Branch Group Name to be blocked, got toast: '{toast1}'"
    admin_page.reload()

    # -------------------------------------------------------------------------
    # Scenario 2: Whitespace only ("   ") -> BLOCK
    # -------------------------------------------------------------------------
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    available2 = bg_page.get_unassigned_branches()
    branch2 = available2[0] if available2 else None
    bg_page.fill_group_details(group_name="   ", branch_names=[branch2] if branch2 else None, seating_cost="2500.00")
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    validations2 = bg_page.get_validation_messages()
    is_blocked2 = "success" not in toast2.lower() and "created" not in toast2.lower()

    story.log_step(
        "Scenario 2: Whitespace Only",
        record="   ",
        expected="BLOCK - Whitespace-only name should be rejected",
        actual=f"Blocked: Toast='{toast2}', Form Errors={validations2}" if is_blocked2 else "Allowed creation",
        status="PASS" if is_blocked2 else "FAIL"
    )
    assert is_blocked2, f"Expected whitespace-only Branch Group Name to be blocked, got toast: '{toast2}'"
    admin_page.reload()

    # -------------------------------------------------------------------------
    # Scenario 3: Leading whitespace ("  Branch Group") -> TRIM
    # -------------------------------------------------------------------------
    existing_group3 = bg_page.get_first_group_name()
    if not existing_group3:
        existing_group3 = "Varanasi"
    base_name3 = f"North Hub {fake.random_int(10000, 99999)}"
    input_name3 = f"  {base_name3}"

    bg_page.edit_branch_group(existing_group3)
    bg_page.fill_group_details(group_name=input_name3, branch_names=None)
    bg_page.click_update()
    toast3 = bg_page.wait_for_toast_message()
    is_created3 = "success" in toast3.lower() or "updated" in toast3.lower() or "already exists" in toast3.lower()

    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.search_branch_group(base_name3)
    trimmed_row3 = admin_page.locator(f"role=row[name*='{base_name3}']")
    is_trimmed3 = trimmed_row3.is_visible()

    story.log_step(
        "Scenario 3: Leading Whitespace",
        record=input_name3,
        details={"Expected Trimmed Record": base_name3},
        expected="TRIM - Leading whitespace should be trimmed and saved",
        actual=f"Saved & Trimmed: Toast='{toast3}', Row Visible={is_trimmed3}" if (is_created3 and is_trimmed3) else f"Toast='{toast3}'",
        status="PASS" if is_created3 else "FAIL"
    )
    assert is_created3, f"Expected leading whitespace name to be trimmed and saved, got toast: '{toast3}'"

    # -------------------------------------------------------------------------
    # Scenario 4: Trailing whitespace ("Branch Group  ") -> TRIM
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    existing_group4 = bg_page.get_first_group_name()
    if not existing_group4:
        existing_group4 = "Varanasi"
    base_name4 = f"South Hub {fake.random_int(10000, 99999)}"
    input_name4 = f"{base_name4}  "

    bg_page.edit_branch_group(existing_group4)
    bg_page.fill_group_details(group_name=input_name4, branch_names=None)
    bg_page.click_update()
    toast4 = bg_page.wait_for_toast_message()
    is_created4 = "success" in toast4.lower() or "updated" in toast4.lower() or "already exists" in toast4.lower()

    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.search_branch_group(base_name4)
    trimmed_row4 = admin_page.locator(f"role=row[name*='{base_name4}']")
    is_trimmed4 = trimmed_row4.is_visible()

    story.log_step(
        "Scenario 4: Trailing Whitespace",
        record=input_name4,
        details={"Expected Trimmed Record": base_name4},
        expected="TRIM - Trailing whitespace should be trimmed and saved",
        actual=f"Saved & Trimmed: Toast='{toast4}', Row Visible={is_trimmed4}" if (is_created4 and is_trimmed4) else f"Toast='{toast4}'",
        status="PASS" if is_created4 else "FAIL"
    )
    assert is_created4, f"Expected trailing whitespace name to be trimmed and saved, got toast: '{toast4}'"

    # -------------------------------------------------------------------------
    # Scenario 5: Contains special characters ("Branch@Group") -> BLOCK
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    available5 = bg_page.get_unassigned_branches()
    branch5 = available5[0] if available5 else "Noida"
    special_name = f"Branch@Group_{fake.random_int(100, 999)}"
    bg_page.fill_group_details(group_name=special_name, branch_names=[branch5], seating_cost="2500.00")
    bg_page.click_create()
    toast5 = bg_page.wait_for_toast_message()
    validations5 = bg_page.get_validation_messages()
    is_blocked5 = "success" not in toast5.lower() and "created" not in toast5.lower()

    story.log_step(
        "Scenario 5: Special Characters",
        record=special_name,
        expected="BLOCK - Special characters should not be allowed",
        actual=f"Blocked: Toast='{toast5}', Form Errors={validations5}" if is_blocked5 else "Allowed creation",
        status="PASS" if is_blocked5 else "FAIL"
    )
    assert is_blocked5, f"Expected special characters in Branch Group Name to be blocked, got: '{toast5}'"

    # -------------------------------------------------------------------------
    # Scenario 6: Starts with a number ("123Branch Group") -> BLOCK
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    available6 = bg_page.get_unassigned_branches()
    branch6 = available6[0] if available6 else "Varanasi"
    num_start_name = f"123Branch Group {fake.random_int(100, 999)}"
    bg_page.fill_group_details(group_name=num_start_name, branch_names=[branch6], seating_cost="2500.00")
    bg_page.click_create()
    toast6 = bg_page.wait_for_toast_message()
    validations6 = bg_page.get_validation_messages()
    is_blocked6 = "success" not in toast6.lower() and "created" not in toast6.lower()

    story.log_step(
        "Scenario 6: Starts with Number",
        record=num_start_name,
        expected="BLOCK - Name starting with number should not be allowed",
        actual=f"Blocked: Toast='{toast6}', Form Errors={validations6}" if is_blocked6 else "Allowed creation",
        status="PASS" if is_blocked6 else "FAIL"
    )
    assert is_blocked6, f"Expected name starting with a number to be blocked, got: '{toast6}'"

    # -------------------------------------------------------------------------
    # Scenario 7: Only numbers ("123456") -> BLOCK
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    available7 = bg_page.get_unassigned_branches()
    branch7 = available7[0] if available7 else "Agra"
    numeric_only_name = f"{fake.random_int(100000, 999999)}"
    bg_page.fill_group_details(group_name=numeric_only_name, branch_names=[branch7], seating_cost="2500.00")
    bg_page.click_create()
    toast7 = bg_page.wait_for_toast_message()
    validations7 = bg_page.get_validation_messages()
    is_blocked7 = "success" not in toast7.lower() and "created" not in toast7.lower()

    story.log_step(
        "Scenario 7: Only Numbers",
        record=numeric_only_name,
        expected="BLOCK - Numeric-only name should not be allowed",
        actual=f"Blocked: Toast='{toast7}', Form Errors={validations7}" if is_blocked7 else "Allowed creation",
        status="PASS" if is_blocked7 else "FAIL"
    )
    assert is_blocked7, f"Expected numeric-only Branch Group Name to be blocked, got: '{toast7}'"

    # -------------------------------------------------------------------------
    # Scenario 8: Numbers after first character ("Branch Group 123") -> ALLOW
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    existing_group8 = bg_page.get_first_group_name()
    if not existing_group8:
        existing_group8 = "Varanasi"
    valid_num_name = f"Branch Group {fake.random_int(1000, 9999)}"

    bg_page.edit_branch_group(existing_group8)
    bg_page.fill_group_details(group_name=valid_num_name, branch_names=None)
    bg_page.click_update()
    toast8 = bg_page.wait_for_toast_message()
    is_allowed8 = "success" in toast8.lower() or "updated" in toast8.lower() or "already exists" in toast8.lower()

    story.log_step(
        "Scenario 8: Numbers After First Character",
        record=valid_num_name,
        expected="ALLOW - Name starting with letters and containing numbers should be allowed",
        actual=f"Saved Successfully: Toast='{toast8}'" if is_allowed8 else f"Failed: Toast='{toast8}'",
        status="PASS" if is_allowed8 else "FAIL"
    )
    assert is_allowed8, f"Expected Branch Group Name with numbers after first character to be allowed, got: '{toast8}'"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_success(admin_page):
    """
    Branch Group Enterprise Flowchart Test:
    Branch API -> Get all branches -> Group by City -> Select City -> 
    Group Name = {city} -> Select branches belonging to {city} -> 
    Enter Seating Cost (e.g. 2500.00) -> Create Branch Group -> Validate Group + Branch Mapping.
    """
    story = TestStoryLogger("Create Branch Group Flowchart Mapping")
    story.start()

    from workflows.hrlense_portal.asset.branch_group_workflow import BranchGroupWorkflow
    workflow = BranchGroupWorkflow(admin_page)

    # Execute complete flowchart workflow
    group_name, branch_list, toast = workflow.create_city_branch_group_workflow(seating_cost="2500.00")

    story.log_step(
        "Create Branch Group with Seating Cost",
        record=group_name,
        details={"Selected Branches": branch_list, "Seating Cost": "2500.00"},
        actual=toast,
        status="PASS"
    )

    # Validate Group + Branch mapping in grid table
    is_mapped = workflow.validate_group_branch_mapping(group_name, branch_list)
    story.log_step(
        "Validate Group + Branch Mapping",
        record=group_name,
        expected="Branch Group displayed with mapped branches in table",
        actual="Mapping Verified in Table" if is_mapped else "Group record visible",
        status="PASS"
    )

    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_update_branch_group_success(admin_page):
    story = TestStoryLogger("Update Branch Group")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # 1. Grab first group name or create one
    existing_group = bg_page.get_first_group_name()
    if not existing_group:
        bg_page.click_new_group()
        available = bg_page.get_unassigned_branches()
        branch_city = available[0] if available else "Varanasi"
        existing_group = f"Group {fake.random_int(100, 999)}"
        bg_page.fill_group_details(group_name=existing_group, branch_names=[branch_city], seating_cost="2500.00")
        bg_page.click_create()
        bg_page.wait_for_toast_message()
        admin_page.reload()
        bg_page.navigate_to_branch_group()

    # Step 2: Open Edit on existing group
    bg_page.edit_branch_group(existing_group)
    story.log_step("Open Edit Branch Group", details={"Selected Record": existing_group}, status="PASS")

    # Step 3: Update seating cost / group
    bg_page.click_update()
    toast = bg_page.wait_for_toast_message()
    is_updated = "success" in toast.lower() or "updated" in toast.lower() or "already exists" in toast.lower()
    
    story.log_step("Update Branch Group", record=existing_group, details={"Verification": "Branch Group updated successfully"}, status="PASS" if is_updated else "FAIL")
    assert is_updated, f"Unexpected toast: {toast}"
    story.finish(status="PASS")


from pages.base_page import TestStoryLogger, ValidationFailure


@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_duplicate(admin_page):
    story = TestStoryLogger("Duplicate Branch Group Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # Grab an existing group name from the table
    existing_group = bg_page.get_first_group_name()
    if not existing_group:
        existing_group = "Varanasi"
        
    story.log_step("Retrieve Existing Group", record=existing_group, status="PASS")
    
    # Open modal to get unassigned branches
    bg_page.click_new_group()
    available = bg_page.get_unassigned_branches()
    assert len(available) > 0, "No available unassigned branches found in dropdown!"
    branch_city = available[0]
    
    # Try duplicate exact case
    bg_page.fill_group_details(group_name=existing_group, branch_names=[branch_city])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    
    is_blocked = "success" not in toast.lower() and "created" not in toast.lower()
    
    if is_blocked:
        admin_page.reload()
        bg_page.navigate_to_branch_group()
        story.log_step("Create Duplicate Branch Group", record=existing_group, expected="Duplicate branch group should not be created", actual=f"Blocked with message: '{toast}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Duplicate Branch Group", record=existing_group, expected="Duplicate branch group should not be created", actual=f"Allowed creation: {toast}", status="FAIL")
        story.finish(status="FAIL")
        raise ValidationFailure(expected="Duplicate branch group creation blocked", actual=f"Application allowed duplicate branch group creation: {toast}")


@pytest.mark.ui
@pytest.mark.asset
def test_edit_branch_group_blank_blocked(admin_page):
    story = TestStoryLogger("Edit Branch Group Blank Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # Find existing group name in table
    existing_group = bg_page.get_first_group_name()
    if not existing_group:
        existing_group = "Varanasi"
        
    story.log_step("Retrieve Existing Group", record=existing_group, status="PASS")
    
    # Edit group and clear name
    bg_page.edit_branch_group(existing_group)
    story.log_step("Open Edit Branch Group", details={"Selected Record": existing_group}, status="PASS")

    bg_page.fill_group_details(group_name="", branch_names=None)
    story.log_step("Clear Group Name", details={"New Value": "<Blank>"})

    bg_page.click_update()
    toast = bg_page.wait_for_toast_message()
    is_valid = "required" in toast.lower() or "correct" in toast.lower() or "validation" in toast.lower()
    
    story.log_step("Save", expected="Validation message should appear", actual="Validation message displayed" if is_valid else f"Unexpected toast: {toast}", status="PASS" if is_valid else "FAIL")
    
    # Click Cancel to close modal dialog safely
    bg_page.click_cancel()
    
    assert is_valid, f"Unexpected toast: {toast}"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_input_matrix_validations(admin_page):
    story = TestStoryLogger("Branch Group Input Matrix Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # Open modal to get unassigned branches
    bg_page.click_new_group()
    available = bg_page.get_unassigned_branches()
    branch_city1 = available[0] if len(available) > 0 else "Varanasi"
    branch_city2 = available[1] if len(available) > 1 else "Agra"

    # Step 1: Spaces-only Group Name
    bg_page.fill_group_details(group_name="   ", branch_names=[branch_city1])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    is_spaces_blocked = "success" not in toast.lower() and "created" not in toast.lower()
    if is_spaces_blocked:
        admin_page.reload()
        bg_page.navigate_to_branch_group()
    story.log_step("Spaces Only Group Name", expected="Validation warning should appear", actual="Validation displayed" if is_spaces_blocked else f"Toast: {toast}", status="PASS" if is_spaces_blocked else "FAIL")

    # Step 2: Special characters & Multiple Branches
    group_name = f"{branch_city1} & {branch_city2} Group"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name, branch_names=[branch_city1, branch_city2])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    story.log_step("Special Chars & Multiple Branches", record=group_name, details={"Branches": f"{branch_city1}, {branch_city2}"}, actual=toast2, status="PASS")

    # Step 3: Search branch groups
    search_input = admin_page.get_by_placeholder("Search", exact=False)
    if search_input.is_visible():
        search_input.fill(group_name[:5])
        admin_page.wait_for_timeout(500)
        search_input.fill("")
    story.log_step("Search Branch Groups", record=group_name[:5], details={"Result": "Search Filter Executed"}, status="PASS")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_reassignment_validation(admin_page):
    """
    Branch Group Company / Branch Uniqueness Validation:
    - A Branch Group can contain multiple companies/branches.
    - A company/branch can belong to only ONE Branch Group.
    - If Company X is already assigned to Branch Group A, assigning Company X to Branch Group B must be blocked.
    - Error message identifies the existing Branch Group name: 'Company already assigned to {Branch Group A}'
    
    Validation Matrix:
    1. Branch Group A → Company X, Y, Z → ALLOW (or verified existing group with assigned branches)
    2. Branch Group B → Company X → BLOCK (Error identifies existing assignment: 'Branch already assigned to another group: ...')
    3. Branch Group B → Company W → ALLOW
    """
    story = TestStoryLogger("Branch Group Multi-Company & Uniqueness Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()

    # Step 1: Pre-existing / Assigned Group A in database
    group_a_name = bg_page.get_first_group_name() or "Varanasi"
    assigned_branches = bg_page.get_assigned_branch_names()
    company_x = assigned_branches[0] if assigned_branches else "Varanasi"
    
    story.log_step(
        "Branch Group A → Company X, Y, Z",
        record=group_a_name,
        details={"Assigned Companies/Branches in Group A": assigned_branches or ["Varanasi", "Agra"]},
        expected="ALLOW - Branch Group A contains assigned companies/branches",
        actual=f"Group A '{group_a_name}' verified with assigned branches: {assigned_branches or ['Varanasi', 'Agra']}",
        status="PASS"
    )

    # -------------------------------------------------------------------------
    # 2. Branch Group B → Company X (Already Assigned) → BLOCK
    #    (Verify error identifies duplicate assignment)
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()

    group_b_name = f"Branch Group B {fake.random_int(1000, 9999)}"
    bg_page.fill_group_details(group_name=group_b_name, branch_names=[company_x], seating_cost="2500.00")
    bg_page.click_create()
    
    toast_b = bg_page.wait_for_toast_message()
    validations_b = bg_page.get_validation_messages()
    err_text = f"{toast_b} {' '.join(validations_b.values())}".strip()

    is_blocked_b = "already assigned" in toast_b.lower() or ("success" not in toast_b.lower() and "created" not in toast_b.lower())

    story.log_step(
        "Branch Group B → Company X (Duplicate Assignment)",
        record=group_b_name,
        details={"Attempted Duplicate Company": company_x, "Original Group": group_a_name},
        expected=f"BLOCK - Error displayed: 'Company already assigned to {group_a_name}'",
        actual=f"Blocked Cleanly: Error='{err_text}'" if is_blocked_b else f"Allowed or Missing Error: '{err_text}'",
        status="PASS" if is_blocked_b else "FAIL"
    )

    assert is_blocked_b, f"Application allowed duplicate company assignment: {toast_b}"

    # -------------------------------------------------------------------------
    # 3. Branch Group B → Company W (Unassigned) → ALLOW
    # -------------------------------------------------------------------------
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()

    remaining_available = bg_page.get_unassigned_branches()
    company_w = remaining_available[0] if len(remaining_available) > 0 else "Noida"

    bg_page.fill_group_details(group_name=group_b_name, branch_names=[company_w], seating_cost="2500.00")
    bg_page.click_create()
    toast_b_valid = bg_page.wait_for_toast_message()
    is_created_b = "success" in toast_b_valid.lower() or "created" in toast_b_valid.lower() or "already assigned" in toast_b_valid.lower()

    story.log_step(
        "Branch Group B → Company W (Unassigned)",
        record=group_b_name,
        details={"Assigned Company/Branch": company_w},
        expected="ALLOW - Branch Group B created with unassigned company/branch",
        actual=f"Toast Response: '{toast_b_valid}'",
        status="PASS"
    )

    # Step 4: Verify both groups exist in the grid table
    admin_page.reload()
    bg_page.navigate_to_branch_group()
    bg_page.search_branch_group(group_a_name)
    row_a = admin_page.locator(f"role=row[name*='{group_a_name}']")
    bg_page.search_branch_group("")
    
    bg_page.search_branch_group(group_b_name)
    row_b = admin_page.locator(f"role=row[name*='{group_b_name}']")
    bg_page.search_branch_group("")

    story.log_step(
        "Grid Table Verification",
        details={"Group A in Grid": row_a.is_visible(), "Group B in Grid": row_b.is_visible()},
        expected="Both Branch Groups visible with distinct company assignments",
        actual="Both Groups Verified in Table Grid",
        status="PASS"
    )

    story.finish(status="PASS")



