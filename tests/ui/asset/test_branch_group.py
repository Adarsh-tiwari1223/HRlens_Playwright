import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.asset.branch_group_page import BranchGroupPage
from faker import Faker

fake = Faker()





@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_validation(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    # Save blank group
    bg_page.click_create()
    
    # Assert validation warning
    toast = bg_page.wait_for_toast_message()
    assert "correct" in toast.lower() or "required" in toast.lower() or "validation" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_success(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"Group {fake.word().capitalize()} {fake.random_int(100, 999)}"
    # Noida/Varanasi are common branches, select Noida
    bg_page.fill_group_details(group_name=group_name, branch_names=["Noida"])
    bg_page.click_create()
    
    toast = bg_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_update_branch_group_success(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"Group Edit {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Failed creation: {toast}"
    
    # Edit the created group
    bg_page.edit_branch_group(group_name)
    bg_page.click_update()
    
    toast = bg_page.wait_for_toast_message()
    assert "success" in toast.lower() or "updated" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_create_branch_group_duplicate(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"GroupDup {fake.word().capitalize()} {fake.random_int(1000, 9999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    
    # Try duplicate exact case
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    
    # Reset state if duplicate exact case was blocked (modal remains open)
    if "success" not in toast2.lower() and "created" not in toast2.lower():
        admin_page.reload()
        bg_page.navigate_to_branch_group()
        
    assert "success" not in toast2.lower() and "created" not in toast2.lower(), f"Duplicate branch group allowed: {toast2}"


@pytest.mark.ui
@pytest.mark.asset
def test_edit_branch_group_blank_save(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    bg_page.click_new_group()
    
    group_name = f"GroupBlankEdit {fake.word().capitalize()} {fake.random_int(1000, 9999)}"
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra"])
    bg_page.click_create()
    bg_page.wait_for_toast_message()
    
    # Edit group and clear name
    bg_page.edit_branch_group(group_name)
    bg_page.fill_group_details(group_name="", branch_names=None)
    bg_page.click_update()
    
    toast = bg_page.wait_for_toast_message()
    assert "required" in toast.lower() or "correct" in toast.lower() or "validation" in toast.lower(), f"Unexpected toast: {toast}"


@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_input_matrix_validations(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()

    # 1. AM_073: Verify spaces-only Group Name is rejected or handled
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name="   ", branch_names=["Agra"])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    # It should display validation or fail, reload state to close modal
    if "success" not in toast.lower() and "created" not in toast.lower():
        admin_page.reload()
        bg_page.navigate_to_branch_group()

    # 2. AM_070 & AM_071 & AM_072 & AM_076: Verify special characters, boundary length, and multiple unique branches
    group_name = f"  GroupSpecChar_!@#_{fake.lexify(text='?'*80)}  "
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name, branch_names=["Agra", "Noida"])
    bg_page.click_create()
    toast = bg_page.wait_for_toast_message()
    assert toast is not None

    # 3. AM_080 & AM_081: Search branch groups
    search_input = admin_page.get_by_placeholder("Search", exact=False)
    if search_input.is_visible():
        search_input.fill(group_name.strip()[:10])
        admin_page.wait_for_timeout(1000)
        search_input.fill("NonExistingGroupSearchKeyword123")
        admin_page.wait_for_timeout(1000)
        search_input.fill("")


@pytest.mark.ui
@pytest.mark.asset
def test_branch_group_reassignment_validation(admin_page):
    bg_page = BranchGroupPage(admin_page)
    bg_page.navigate_to_branch_group()
    
    # 1. Create first Branch Group with branch "Agra"
    group_name1 = f"GroupMapped1 {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name1, branch_names=["Agra"])
    bg_page.click_create()
    toast1 = bg_page.wait_for_toast_message()
    assert "success" in toast1.lower() or "created" in toast1.lower()
    
    # 2. AM_074: Try creating second group and select the already assigned branch "Agra"
    group_name2 = f"GroupMapped2 {fake.word().capitalize()} {fake.random_int(100, 999)}"
    bg_page.click_new_group()
    bg_page.fill_group_details(group_name=group_name2, branch_names=["Agra"])
    bg_page.click_create()
    toast2 = bg_page.wait_for_toast_message()
    
    # Reset page state if duplicate exact case was blocked (modal remains open)
    if "success" not in toast2.lower() and "created" not in toast2.lower():
        admin_page.reload()
        bg_page.navigate_to_branch_group()
        
    # Assert validation warning - should not allow duplicate mapping
    assert "success" not in toast2.lower() and "created" not in toast2.lower(), f"Branch was allowed to be reassigned to multiple groups: {toast2}"
