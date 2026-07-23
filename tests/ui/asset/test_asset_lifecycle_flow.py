import pytest
import re
import random
from faker import Faker
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.asset.asset_master_page import AssetMasterPage
from pages.asset.asset_entry_page import AssetEntryPage
from pages.asset.asset_assignment_page import AssetAssignmentPage
from pages.asset.asset_return_page import AssetReturnPage
from pages.asset.asset_maintenance_page import AssetMaintenancePage
from pages.asset.asset_request_page import AssetRequestPage
from pages.asset.asset_procurement_page import AssetProcurementPage
from testdata.dynamic.business_test_data import BusinessTestData

fake = Faker()

@pytest.mark.ui
@pytest.mark.asset
def test_asset_lifecycle_flow(logged_in_page):
    story = TestStoryLogger("Asset Lifecycle Main Stream Flow")
    story.start()

    # Step 1: Admin login
    admin_page, admin_context = logged_in_page("admin")

    # Step 2: Asset Procurement (Procure Asset)
    procurement_page = AssetProcurementPage(admin_page)
    procurement_page.navigate_to_asset_procurement()
    procurement_page.click_new_procurement()

    invoice_no = f"INV-{random.randint(10000, 99999)}"
    # Fill step 1 details using pre-existing dropdown values (index 1)
    procurement_page.fill_step1_details(
        vendor_label=None,
        branch_label=None,
        company_label=None,
        invoice_no=invoice_no,
        purchase_date="2026-07-23",
        amount_before_gst="1500",
        gst_amount="270"
    )
    procurement_page.click_next()

    # Fill step 2 details using first options (index 1) for category/subcategory
    procurement_page.fill_step2_item(
        index=0,
        category_label=None,
        sub_category_label=None,
        brand="Dell",
        model="Latitude 7440",
        quantity="5",
        price="300"
    )
    procurement_page.click_create()
    toast = procurement_page.wait_for_toast_message()
    is_procured = "success" in toast.lower() or "created" in toast.lower() or "procured" in toast.lower()
    story.log_step(
        "Asset Procurement",
        record=f"Invoice: {invoice_no}",
        expected="Asset should be procured successfully",
        actual=f"Toast message received: '{toast}'" if is_procured else f"Failed: {toast}",
        status="PASS" if is_procured else "FAIL"
    )
    assert is_procured, f"Asset Procurement failed: {toast}"

    # Step 3: Asset Entry (Create individual Asset)
    entry_page = AssetEntryPage(admin_page)
    entry_page.navigate_to_asset_entry()
    entry_page.click_add_asset()
    
    asset_name = "Dell Latitude 7440"
    serial_no = f"SN-DELL-{random.randint(100000, 999999)}"
    category_name, sub_category_name = entry_page.fill_asset_details(
        name=asset_name,
        brand="Dell",
        model="Latitude 7440",
        serial_no=serial_no,
        warranty="Warranty",
        expiry_date="2027-12-31",
        notes="Procured under IT Hardware budget."
    )
    entry_page.click_save()
    toast = entry_page.wait_for_toast_message()
    assert "success" in toast.lower() or "created" in toast.lower(), f"Asset Entry creation failed: {toast}"
    
    # Search and verify the asset in the inventory grid to capture its auto-generated Asset Code
    entry_page.navigate_to_asset_entry()
    admin_page.locator("input[placeholder*='Search']").first.fill(serial_no)
    admin_page.wait_for_timeout(2000)
    
    # Read the row to extract code (it usually starts with the prefix like ASSET-LAP-)
    row_text = admin_page.locator("table tbody tr").first.inner_text()
    match = re.search(r"ASSET-[A-Z0-9-]+", row_text)
    asset_code = match.group(0) if match else "ASSET-LAP-"
    
    story.log_step("Create Asset Entry", record=f"Code: {asset_code}, Serial: {serial_no}", status="PASS")

    # Step 4: Asset Assignment (Assign Asset to Employee)
    assignment_page = AssetAssignmentPage(admin_page)
    assignment_page.navigate_to_asset_assignment()
    assignment_page.click_assign_asset()
    
    employee_name = "Sanidhy Tiwari"
    employee_user_key = "sanidhy" # Key matching settings.USERS for login
    assignment_page.fill_assignment_details(
        employee_name=employee_name,
        category=category_name,
        sub_category=sub_category_name,
        asset_name_or_code=asset_code,
        expected_return_date="2026-12-31",
        remarks="Assigned to developer."
    )
    assignment_page.click_submit_assignment()
    toast = assignment_page.wait_for_toast_message()
    
    is_assigned = "success" in toast.lower() or "assigned" in toast.lower()
    story.log_step(
        "Assign Asset to Employee",
        record=f"Asset: {asset_code} → Employee: {employee_name}",
        expected="Asset should be successfully assigned",
        actual=f"Toast message received: '{toast}'" if is_assigned else f"Failed: {toast}",
        status="PASS" if is_assigned else "FAIL"
    )
    assert is_assigned, f"Asset Assignment failed: {toast}"

    # Step 5: Login as the Assigned Employee and accept the asset assignment
    employee_page, employee_context = logged_in_page(employee_user_key)
    
    request_page = AssetRequestPage(employee_page)
    request_page.navigate_to_asset_request()
    
    # A. Accept the assignment
    is_accepted = request_page.accept_asset(asset_code)
    story.log_step(
        "Employee Accepts Asset Assignment",
        record=f"User: {employee_name}, Asset: {asset_code}",
        expected="Employee should see and accept the assigned asset",
        actual="Asset accepted successfully in UI" if is_accepted else "Accept Asset button not found or clicked",
        status="PASS" if is_accepted else "FAIL"
    )
    assert is_accepted, "Employee failed to accept assigned asset."
    
    # Close employee browser context
    employee_context.close()

    # Step 6: Admin Returns the Asset in Asset Return Submenu
    admin_page.reload()
    return_page = AssetReturnPage(admin_page)
    return_page.navigate_to_asset_return()
    return_page.return_asset(asset_code)
    toast = return_page.wait_for_toast_message()
    
    is_returned = "success" in toast.lower() or "returned" in toast.lower() or "received" in toast.lower()
    story.log_step(
        "Admin Returns Assigned Asset",
        record=f"Asset: {asset_code}",
        expected="Admin should successfully return the assigned asset to inventory",
        actual=f"Toast message received: '{toast}'" if is_returned else f"Failed: {toast}",
        status="PASS" if is_returned else "FAIL"
    )
    assert is_returned, f"Asset Return failed: {toast}"

    # Step 7: Send Asset to Maintenance (Logged by Admin)
    maintenance_page = AssetMaintenancePage(admin_page)
    maintenance_page.navigate_to_asset_maintenance()
    maintenance_page.click_create_maintenance()
    
    maintenance_page.fill_maintenance_details(
        asset_code_or_name=asset_code,
        issue_type="Hardware issue",
        description="Keyboard keys are non-functional.",
        expected_return="2026-12-31",
        estimated_cost="1500",
        remarks="Sent to local Dell center."
    )
    maintenance_page.click_submit_case()
    toast = maintenance_page.wait_for_toast_message()
    
    is_maintained = "success" in toast.lower() or "maintenance" in toast.lower() or "created" in toast.lower()
    story.log_step(
        "Send Asset to Maintenance",
        record=f"Asset: {asset_code}",
        expected="Maintenance case should be created successfully",
        actual=f"Toast message received: '{toast}'" if is_maintained else f"Failed: {toast}",
        status="PASS" if is_maintained else "FAIL"
    )
    assert is_maintained, f"Asset Maintenance case creation failed: {toast}"

    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_employee_asset_request(logged_in_page):
    story = TestStoryLogger("Employee Initiates New Asset Request")
    story.start()

    # Step 1: Employee login
    employee_name = "Sanidhy Tiwari"
    employee_user_key = "sanidhy"
    employee_page, employee_context = logged_in_page(employee_user_key)

    # Step 2: Navigate to Asset Request and submit a new request
    request_page = AssetRequestPage(employee_page)
    request_page.navigate_to_asset_request()
    is_submitted = request_page.create_new_request(
        reason="Need a secondary screen or testing device for development.",
        remarks="Requested via automated UI test."
    )
    
    story.log_step(
        "Submit New Asset Request Form",
        record=f"User: {employee_name}",
        expected="New Asset Request form should be submitted successfully",
        actual="Form submitted successfully" if is_submitted else "Submission failed",
        status="PASS" if is_submitted else "FAIL"
    )
    assert is_submitted, "Employee failed to submit new asset request."

    employee_context.close()

    # Step 3: Admin login to fulfill the request in Asset Assignment Requested tab
    admin_page, admin_context = logged_in_page("admin")
    
    assignment_page = AssetAssignmentPage(admin_page)
    assignment_page.navigate_to_asset_assignment()
    assignment_page.assign_requested_asset(employee_name=employee_name)
    toast = assignment_page.wait_for_toast_message()
    
    is_fulfilled = "success" in toast.lower() or "fulfilled" in toast.lower() or "assigned" in toast.lower()
    story.log_step(
        "Admin Fulfills Requested Assignment",
        record=f"Employee: {employee_name}",
        expected="Admin should successfully fulfill and assign the requested asset",
        actual=f"Toast message received: '{toast}'" if is_fulfilled else f"Failed: {toast}",
        status="PASS" if is_fulfilled else "FAIL"
    )
    assert is_fulfilled, f"Fulfillment failed: {toast}"
    
    admin_context.close()
    story.finish(status="PASS")
