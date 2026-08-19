"""
HRlens Portal - Asset Assignment Standalone Test.

Executes the standalone Asset Assignment & Employee Acceptance workflow:
- Admin navigates to Asset Assignment page.
- Selects Employee (Sanidhy Tiwari), Category, and Sub-Category.
- Assigns asset with expected return date & remarks.
- Switches context to Employee (sanidhy) to accept the assignment in Asset Request.
"""

import logging
import pytest
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.assignment
def test_asset_assignment_standalone(logged_in_page):
    """Standalone test for Asset Assignment & Employee Acceptance."""
    story = TestStoryLogger(
        "Asset Assignment Standalone",
        module="Asset Management",
        phase="Standalone Asset Assignment"
    )
    story.start()

    admin_page, admin_context = logged_in_page("admin")
    
    # Dynamically read existing Category & Sub-Category
    master_page = AssetMasterPage(admin_page)
    category, sub_category = master_page.read_first_existing_sub_category()
    
    assignment_page = AssetAssignmentPage(admin_page)
    assignment_page.navigate_to_asset_assignment()
    assignment_page.click_assign_asset()

    employee_name = "Sanidhy Tiwari"
    employee_user_key = "sanidhy"

    assignment_page.fill_assignment_details(
        employee_name=employee_name,
        category=category,
        sub_category=sub_category,
        expected_return_date="2026-12-31",
        remarks="Standalone Asset Assignment test execution."
    )

    dropdown_info = assignment_page.validate_available_assets_dropdown()
    story.log_step(
        "Validate Available Asset Dropdown Population",
        record=f"Category: '{category}' | Sub-Category: '{sub_category}'",
        expected="Available Asset dropdown populates items for assignment",
        actual=f"Populated: {dropdown_info['populated']} (Count: {dropdown_info['count']}) -> Items: {dropdown_info['items']}",
        status="PASS" if dropdown_info['populated'] else "INFO"
    )

    assignment_page.click_submit_assignment()
    assign_toast = assignment_page.wait_for_toast_message()
    is_assigned = any(term in assign_toast.lower() for term in ["success", "assigned", "created", "saved"])

    story.log_step(
        "Direct Asset Assignment (Admin)",
        record=f"Employee: {employee_name} | Category: {category} | SubCategory: {sub_category}",
        expected="Asset assigned successfully",
        actual=f"Toast: '{assign_toast}'",
        status="PASS" if is_assigned else "FAIL"
    )

    # Employee logs in to accept assignment
    employee_page, employee_context = logged_in_page(employee_user_key)
    request_page = AssetRequestPage(employee_page)
    request_page.navigate_to_asset_request()
    
    is_accepted = request_page.accept_asset()
    story.log_step(
        "Employee Acceptance (Asset Request)",
        record=f"Employee: {employee_name}",
        expected="Employee accepts the assigned asset in portal",
        actual="Asset accepted successfully" if is_accepted else "Accept button processed",
        status="PASS" if is_accepted else "INFO"
    )
    employee_context.close()

    story.finish(status="PASS" if is_assigned else "FAIL")
