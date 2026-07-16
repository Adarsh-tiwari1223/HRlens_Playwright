import pytest
import logging
from pages.admin_control.cross_company_hierarchy_page import CrossCompanyHierarchyPage

logger = logging.getLogger(__name__)

@pytest.mark.ui
@pytest.mark.admin_control
def test_update_cross_company_hierarchy(admin_page):
    logger.info("Verify Cross Company Hierarchy module: Reading table, updating assignment, and pagination")
    
    hierarchy_page = CrossCompanyHierarchyPage(admin_page)
    hierarchy_page.navigate_to_hierarchy()
    
    # 1. Read table content and print to verify
    table_rows = hierarchy_page.get_table_data()
    assert len(table_rows) > 0, "No records found in Cross Company Hierarchy table"
    for row in table_rows:
        logger.info(f"Row -> Employee: {row['employee']} | Default Co: {row['default_company']} | Default Access: {row['default_access']} | Branches: {row['assigned_branches']}")
        
    # 2. Select first employee (Sanidhy Tiwari) and edit their hierarchy
    target_employee = "Sanidhy Tiwari"
    hierarchy_page.edit_employee_hierarchy(target_employee)
    
    # 3. Choose a branch to assign/toggle (e.g. Agra (Adventa Tech Inc))
    target_branch = "Agra (Adventa Tech Inc)"
    hierarchy_page.select_branch(target_branch)
    
    # 4. Click update and verify success toast
    hierarchy_page.click_update()
    toast_msg = hierarchy_page.wait_for_toast_success()
    assert "updated" in toast_msg.lower() or "success" in toast_msg.lower(), f"Update failed: {toast_msg}"
    
    # 5. Navigate pagination to verify Page 2
    hierarchy_page.navigate_page(2)
    table_rows_p2 = hierarchy_page.get_table_data()
    assert len(table_rows_p2) > 0, "No records found on Page 2 of hierarchy table"


@pytest.mark.ui
@pytest.mark.admin_control
def test_exclude_team_lead_hierarchy_reassignment(admin_page):
    logger.info("Verify team lead exclusion triggers confirmation popup with reassignment picker")
    
    hierarchy_page = CrossCompanyHierarchyPage(admin_page)
    hierarchy_page.navigate_to_hierarchy()
    
    # 1. Navigate to Page 2 to locate Vikesh Singh
    hierarchy_page.navigate_page(2)
    
    # 2. Edit Vikesh Singh's hierarchy
    hierarchy_page.edit_employee_hierarchy("Vikesh Singh")
    
    # 3. Toggle exclusion switch to True
    hierarchy_page.toggle_exclude_employee(True)
    
    # 4. Click Update
    hierarchy_page.click_update()
    
    # 5. Handle Team Lead Reassignment popup
    hierarchy_page.reassign_team_lead("abha", "Abha Verma 931")
    
    # 6. Confirm and save
    hierarchy_page.click_confirm_and_save()
    
    # 7. Verify success toast
    toast_msg = hierarchy_page.wait_for_toast_success()
    assert "updated" in toast_msg.lower() or "success" in toast_msg.lower(), f"Reassignment failed: {toast_msg}"
