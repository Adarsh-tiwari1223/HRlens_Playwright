import pytest
import logging
from pages.admin_control.cross_company_hierarchy_page import CrossCompanyHierarchyPage
from pages.admin_control.management_interaction_page import ManagementInteractionPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.admin_control
@pytest.mark.dependency(name="test_e2e_hierarchy_reassignment")
def test_exclude_team_lead_hierarchy_reassignment_e2e(admin_page):
    """
    E2E: Branch Access Removal & Team Management Validation

    Flow:
      1. Management Interaction -> find first employee with visible team members
      2. Collect team members -> derive target_branch from first member
      3. Cross Company Hierarchy -> open editor
         - ensure target_branch is selected (restore if missing)
         - ensure at least 2 branches selected (add extra if only 1)
         - save if any changes made
      4. Open editor -> deselect target_branch -> Update
      5. Validate reassignment modal -> pick replacement -> Confirm & Save
      6. Verify success toast
      7. Management Interaction -> verify affected members removed from old TL
      8. Management Interaction -> verify affected members appear under new TL
    """
    logger.info("Start: Branch access removal & team management validation")

    hierarchy_page = CrossCompanyHierarchyPage(admin_page)
    mgmt_page      = ManagementInteractionPage(admin_page)

    # Step 1: Find target_employee
    mgmt_page.navigate_to_management()
    target_employee = mgmt_page.get_first_employee_with_team()
    assert target_employee, "No employee with visible team members found"
    logger.info(f"Target employee: '{target_employee}'")

    # Step 2: Collect baseline
    initial_data    = mgmt_page.get_employee_management_data(target_employee)
    initial_members = mgmt_page.view_team(target_employee)
    assert initial_members, f"No team members found for '{target_employee}'"

    logger.info(f"[{target_employee}] Role: {initial_data['role']} | Team Size: {initial_data['team_size']}")
    for m in initial_members:
        logger.info(f"  -> {m['name']} | {m['company']} | {m['branch']}")

    first_member  = initial_members[0]
    branch_part   = first_member["branch"]
    company_part  = first_member["company"]
    target_branch = f"{branch_part} ({company_part})"
    logger.info(f"target_branch: '{target_branch}'")

    affected_names = [
        m["name"] for m in initial_members
        if m["company"].lower() == company_part.lower()
        and m["branch"].lower() == branch_part.lower()
    ]
    logger.info(f"Affected members: {affected_names}")

    # Step 3: Open editor once - restore target_branch + ensure 2 branches, save once
    hierarchy_page.navigate_to_hierarchy()
    hierarchy_page.edit_employee_hierarchy(target_employee)

    # Detect if target_branch is the default branch
    default_company, default_branch = hierarchy_page.get_default_company_branch()
    is_target_default = (
        branch_part.lower() == default_branch.lower() and
        company_part.lower() == default_company.lower()
    )
    logger.info(f"target_branch is default: {is_target_default}")

    needs_save = False

    # 3a: Ensure target_branch is active
    # Default branch is always active (switch OFF = included) — no restore needed
    if not is_target_default:
        if hierarchy_page.select_branch(target_branch, checked=True):
            logger.info(f"Restored '{target_branch}'")
            needs_save = True

    # 3b: Count active branches
    # Default branch counts as +1 when switch is OFF (included)
    dialog = admin_page.locator("role=dialog")
    all_cbs = dialog.locator("input.chakra-checkbox__input").all()
    checked_count = sum(1 for cb in all_cbs if cb.is_checked())
    switch_input = admin_page.locator("input.chakra-switch__input:visible")
    try:
        if not switch_input.is_checked():
            checked_count += 1
    except Exception:
        pass
    logger.info(f"Active branches (incl. default): {checked_count}")

    if checked_count < 2:
        all_ps = dialog.locator(
            "xpath=.//p[../../label[contains(@class,'chakra-checkbox')]]"
        ).all()
        for p_elem in all_ps:
            branch_text = p_elem.inner_text().strip()
            if not branch_text or "(" not in branch_text or branch_text == target_branch:
                continue
            cb = dialog.locator(
                f"xpath=.//p[normalize-space(.)='{branch_text}']"
                f"/../../label//input[@type='checkbox']"
            ).first
            try:
                if not cb.is_checked():
                    hierarchy_page.select_branch(branch_text, checked=True)
                    logger.info(f"Added extra branch: '{branch_text}'")
                    needs_save = True
                    break
            except Exception:
                continue

    if needs_save:
        hierarchy_page.click_update()
        hierarchy_page.wait_for_toast_success()
        logger.info("Saved branch changes")
        hierarchy_page.navigate_to_hierarchy()

        mgmt_page.navigate_to_management()
        initial_members = mgmt_page.view_team(target_employee)
        affected_names = [
            m["name"] for m in initial_members
            if m["company"].lower() == company_part.lower()
            and m["branch"].lower() == branch_part.lower()
        ]
        logger.info(f"Affected members after restore: {affected_names}")
        hierarchy_page.navigate_to_hierarchy()
    else:
        logger.info("No changes needed - closing drawer")
        admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(500)

    # Step 4: Deselect target_branch
    hierarchy_page.edit_employee_hierarchy(target_employee)
    if is_target_default:
        logger.info(f"Deselecting default branch '{target_branch}' via exclude switch")
        admin_page.locator(".chakra-switch__track").click()
        admin_page.wait_for_timeout(500)
    else:
        hierarchy_page.select_branch(target_branch, checked=False)
    hierarchy_page.click_update()
    hierarchy_page.wait_for_reassignment_dialog()
    logger.info(f"Removed branch: '{target_branch}'")
    modal = hierarchy_page.get_modal_reassignment_details()
    logger.info(f"Modal: {modal}")

    assert target_employee in modal.get("employee_name", ""), \
        f"Modal employee name mismatch: got '{modal.get('employee_name')}'"
    assert f"{company_part} - {branch_part}" in modal.get("raw_text", ""), \
        f"Modal text missing '{company_part} - {branch_part}'"

    selected_tl = hierarchy_page.reassign_team_lead()
    hierarchy_page.click_confirm_and_save()
    logger.info(f"Reassigned to: '{selected_tl}'")

    # Step 6: Verify success toast
    toast_msg = hierarchy_page.wait_for_toast_success()
    assert "updated" in toast_msg.lower() or "success" in toast_msg.lower(), \
        f"Unexpected toast: '{toast_msg}'"
    logger.info(f"Toast: {toast_msg}")

    # Step 7: Verify affected members removed from old TL
    mgmt_page.navigate_to_management()
    final_members = mgmt_page.view_team(target_employee)
    final_names   = [m["name"] for m in final_members]
    logger.info(f"[{target_employee}] Final team: {final_names}")
    for name in affected_names:
        assert name not in final_names, \
            f"'{name}' still under {target_employee} after reassignment"
    logger.info(f"[{target_employee}] Verified - affected members removed")

    # Step 8: Verify affected members appear under new TL
    new_tl_search = " ".join(selected_tl.split()[:2])
    new_tl_data   = mgmt_page.get_employee_management_data(new_tl_search)
    if new_tl_data["team_size"] > 0:
        new_tl_members = mgmt_page.view_team(new_tl_search)
        new_tl_names   = [m["name"] for m in new_tl_members]
        logger.info(f"[{new_tl_search}] Team: {new_tl_names}")
        for name in affected_names:
            assert name in new_tl_names, \
                f"'{name}' not found under new TL '{new_tl_search}'"
        logger.info(f"[{new_tl_search}] All reassigned members verified")
    else:
        logger.info(f"[{new_tl_search}] Not listed as TL - skipping Step 8 assertion")


@pytest.mark.ui
@pytest.mark.admin_control
@pytest.mark.dependency(depends=["test_e2e_hierarchy_reassignment"])
def test_update_cross_company_hierarchy(admin_page):
    logger.info("Verify Cross Company Hierarchy: table read, branch update, pagination")

    hierarchy_page = CrossCompanyHierarchyPage(admin_page)
    hierarchy_page.navigate_to_hierarchy()

    table_rows = hierarchy_page.get_table_data()
    assert len(table_rows) > 0, "No records found in Cross Company Hierarchy table"
    for row in table_rows:
        logger.info(
            f"Row -> Employee: {row['employee']} | "
            f"Default Co: {row['default_company']} | "
            f"Default Access: {row['default_access']} | "
            f"Branches: {row['assigned_branches']}"
        )

    target_employee = table_rows[0]["employee"]
    target_branch   = (table_rows[0].get("assigned_branches") or [None])[0]

    if not target_branch:
        pytest.skip(f"No assigned branches for '{target_employee}' - skipping")

    hierarchy_page.edit_employee_hierarchy(target_employee)
    hierarchy_page.select_branch(target_branch)
    hierarchy_page.click_update()
    toast_msg = hierarchy_page.wait_for_toast_success()
    assert "updated" in toast_msg.lower() or "success" in toast_msg.lower(), \
        f"Update failed: '{toast_msg}'"
    logger.info(f"Toast: {toast_msg}")

    hierarchy_page.navigate_to_hierarchy()
    hierarchy_page.navigate_page(2)
    table_rows_p2 = hierarchy_page.get_table_data()
    assert len(table_rows_p2) > 0, "No records found on Page 2"
