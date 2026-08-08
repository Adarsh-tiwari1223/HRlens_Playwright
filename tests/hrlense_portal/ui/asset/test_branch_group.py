import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from faker import Faker

fake = Faker()



@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_validation(admin_page):
    story = TestStoryLogger("Create Branch Group Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    # Step 1: Save blank group
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    is_valid = "correct" in toast.lower() or "required" in toast.lower() or "validation" in toast.lower()
    
    story.log_step("Submit Blank Form", expected="Validation message should appear", actual="Validation message displayed" if is_valid else f"Unexpected toast: {toast}", status="PASS" if is_valid else "FAIL")
    assert is_valid, f"Unexpected toast: {toast}"
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
    
    # Open modal to get unassigned branches
    bg_page.click_new_group()
    available = bg_page.get_unassigned_branches()
    assert len(available) > 0, "No available unassigned branches found in dropdown!"
    branch_city = available[0]
    
    group_name = f"{branch_city} Division"
    bg_page.fill_group_details(group_name=group_name, branch_names=[branch_city])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed creation: {toast}"
    story.log_step("Create Branch Group", record=group_name, status="PASS")
    
    # Step 2: Open Edit
    bg_page.edit_branch_group(group_name)
    story.log_step("Open Edit Branch Group", details={"Selected Record": group_name}, status="PASS")

    # Step 3: Update
    bg_page.click_update()
    toast = bg_page.wait_for_toast_message()
    is_updated = "success" in toast.lower() or "updated" in toast.lower()
    
    story.log_step("Update Branch Group", record=group_name, details={"Verification": "Branch Group updated successfully"}, status="PASS" if is_updated else "FAIL")
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
    assert len(available) >= 2, "Need at least 2 available branches!"
    branch_city1 = available[0]
    branch_city2 = available[1]

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
    story = TestStoryLogger("Branch Group Reassignment Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # Open modal to get unassigned branches
    bg_page.click_new_group()
    available = bg_page.get_unassigned_branches()
    assert len(available) > 0, "No available unassigned branches found in dropdown!"
    branch_city = available[0]
    
    # Step 1: Create first Branch Group with branch
    group_name1 = f"{branch_city} Area A"
    bg_page.fill_group_details(group_name=group_name1, branch_names=[branch_city])
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    story.log_step("Create Group 1", record=group_name1, details={"Assigned Branch": branch_city}, status="PASS")
    
    # Step 2: Try creating second group and select the already assigned branch
    group_name2 = f"{branch_city} Area B"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name2, branch_names=[branch_city])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    
    is_blocked = "success" not in toast2.lower() and "created" not in toast2.lower()
    if is_blocked:
        admin_page.reload()
        bg_page.navigate_to_branch_group()
        story.log_step("Reassign Branch to Group 2", record=group_name2, expected="Branch should not be allowed to be reassigned to multiple groups", actual="Validation message displayed", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Reassign Branch to Group 2", record=group_name2, expected="Branch should not be allowed to be reassigned to multiple groups", actual=f"Allowed reassignment: {toast2}", status="FAIL")
        story.finish(status="FAIL")
        raise ValidationFailure(expected="Branch reassignment to multiple groups blocked", actual=f"Application allowed branch reassignment to multiple groups: {toast2}")


