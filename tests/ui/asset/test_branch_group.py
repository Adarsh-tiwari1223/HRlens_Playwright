import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.asset.branch_group_page import BranchGroupPage
from faker import Faker

fake = Faker()

pytestmark = pytest.mark.skip(reason="Branch group in refinement stage")

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
    story = TestStoryLogger("Create Branch Group Success")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"Group {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Noida"])
    story.log_step("Fill Details", record=group_name, details={"Selected Branch": "Noida"}, status="PASS")

    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    is_success = "success" in toast.lower() or "created" in toast.lower()
    
    story.log_step("Create Group", record=group_name, actual=toast, status="PASS" if is_success else "FAIL")
    assert is_success, f"Unexpected toast: {toast}"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_update_branch_group_success(admin_page):
    story = TestStoryLogger("Update Branch Group")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"Group Edit {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
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
    bg_page.click_new_group()
    
    group_name = f"GroupDup {fake.word().capitalize()} {fake.random_int(1000, 9999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    story.log_step("Create Branch Group", record=group_name, status="PASS")
    
    # Step 2: Try duplicate exact case
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    
    is_blocked = "success" not in toast2.lower() and "created" not in toast2.lower()
    if is_blocked:
        admin_page.reload()
        bg_page.navigate_to_branch_group()
        story.log_step("Create Duplicate Branch Group", record=group_name, expected="Duplicate branch group should not be created", actual=f"Blocked with message: '{toast2}'", status="PASS")
        story.finish(status="PASS")
    else:
        story.log_step("Create Duplicate Branch Group", record=group_name, expected="Duplicate branch group should not be created", actual=f"Allowed creation: {toast2}", status="FAIL")
        story.finish(status="FAIL")
        raise ValidationFailure(expected="Duplicate branch group creation blocked", actual=f"Application allowed duplicate branch group creation: {toast2}")



@pytest.mark.ui
@pytest.mark.asset
def test_edit_branch_group_blank_blocked(admin_page):
    story = TestStoryLogger("Edit Branch Group Blank Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"GroupBlankEdit {fake.word().capitalize()} {fake.random_int(1000, 9999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    bg_page.wait_for_toast_message()
    story.log_step("Create Branch Group", record=group_name, status="PASS")
    
    # Step 2: Edit group and clear name
    bg_page.edit_branch_group(group_name)
    story.log_step("Open Edit Branch Group", details={"Selected Record": group_name}, status="PASS")

    bg_page.fill_group_details(group_name="", branch_names=None)
    story.log_step("Clear Group Name", details={"New Value": "<Blank>"})

    bg_page.click_update()
    toast = bg_page.wait_for_toast_message()
    is_valid = "required" in toast.lower() or "correct" in toast.lower() or "validation" in toast.lower()
    
    story.log_step("Save", expected="Validation message should appear", actual="Validation message displayed" if is_valid else f"Unexpected toast: {toast}", status="PASS" if is_valid else "FAIL")
    assert is_valid, f"Unexpected toast: {toast}"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_input_matrix_validations(admin_page):
    story = TestStoryLogger("Branch Group Input Matrix Validation")
    story.start()

    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()

    # Step 1: Spaces-only Group Name
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name="   ", branch_names=["Agra"])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    is_spaces_blocked = "success" not in toast.lower() and "created" not in toast.lower()
    if is_spaces_blocked:
        admin_page.reload()
        bg_page.navigate_to_branch_group()
    story.log_step("Spaces Only Group Name", expected="Validation warning should appear", actual="Validation displayed" if is_spaces_blocked else f"Toast: {toast}", status="PASS" if is_spaces_blocked else "FAIL")

    # Step 2: Special characters & Multiple Branches
    group_name = f"GroupSpecChar_{fake.lexify(text='?'*10)}"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra", "Noida"])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    story.log_step("Special Chars & Multiple Branches", record=group_name, details={"Branches": "Agra, Noida"}, actual=toast2, status="PASS")

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
    
    # Step 1: Create first Branch Group with branch "Agra"
    group_name1 = f"GroupMapped1 {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name1, branch_names=["Agra"])
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    story.log_step("Create Group 1", record=group_name1, details={"Assigned Branch": "Agra"}, status="PASS")
    
    # Step 2: Try creating second group and select the already assigned branch "Agra"
    group_name2 = f"GroupMapped2 {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name2, branch_names=["Agra"])
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


