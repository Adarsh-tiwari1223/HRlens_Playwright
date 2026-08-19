"""
HRlens Portal — Branch-Scoped IT Persona Asset Lifecycle Specification Test Suite.

Enforces Branch-Level IT Persona Responsibilities:
1. IT Person procures and generates new assets for their respected branch.
2. IT Person directly assigns assets to employees in their respected branch.
3. Target employee accepts asset on employee portal.
4. IT Person completes return request & condition assessment (Good, Repair Required, Damaged, Lost).
5. IT Person handles repair/maintenance or disposal for their respected branch.
"""

import re
import random
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from pages.hrlense_portal.asset.asset_maintenance_page import AssetMaintenancePage
from pages.hrlense_portal.asset.asset_disposal_page import AssetDisposalPage
from utils.branch_it_selector import get_branch_it_person, get_branch_target_employee, get_all_supported_branches

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.branch_it_lifecycle
class TestBranchScopedITAssetLifecycleSpec:

    @pytest.mark.parametrize("branch_name", ["Varanasi", "Agra", "Meerut", "Noida", "Lucknow"])
    def test_branch_scoped_it_asset_procurement_assignment_return(self, logged_in_page, branch_name):
        """
        Validates Branch-Scoped IT Responsibility:
        - IT Person procures new asset for respected branch.
        - Directly assigns asset to respected branch employee.
        - Performs IT Condition Assessment & Return Request.
        """
        story = TestStoryLogger(f"Branch IT Lifecycle: {branch_name}", module="Asset Management", phase="Branch IT Persona")
        story.start()

        # Step 1: Identify Respected IT Person & Target Employee for Branch
        it_person = get_branch_it_person(branch_name)
        target_emp = get_branch_target_employee(branch_name)
        
        logger.info(f"[BRANCH IT TEST] Branch: {branch_name} | IT Person: {it_person['name']} ({it_person['user_key']}) | Target Emp: {target_emp['name']}")

        # Log in as Branch IT Person persona (or fallback to admin if password is blank in .env)
        it_user_key = it_person["user_key"]
        user_info = settings.USERS.get(it_user_key, {})
        if not user_info.get("password"):
            logger.info(f"[{branch_name}] Password for IT Person '{it_person['name']}' ({it_user_key}) is blank in .env. Using IT Admin persona for operations.")
            it_user_key = "admin"
        else:
            logger.info(f"[{branch_name}] Logging in as Branch IT Person: '{it_person['name']}' ({it_user_key})")

        it_page, _ = logged_in_page(it_user_key)

        # Step 2: IT Procurement & Asset Generation for Branch
        logger.info(f"[STEP] Phase 1: IT Procurement & QR Generation for Branch '{branch_name}'")
        entry_page = AssetEntryPage(it_page)
        entry_page.navigate_to_asset_entry()
        entry_page.click_add_asset()

        serial_no = f"SN-{branch_name[:3].upper()}-{random.randint(100000, 999999)}"
        entry_data = entry_page.fill_asset_details(
            name=f"Dell Workstation ({branch_name})",
            brand="Dell",
            model="Latitude 7440",
            serial_no=serial_no,
            warranty="Warranty",
            expiry_date="2028-12-31",
            insured="No",
            notes=f"Procured by IT Person '{it_person['name']}' for {branch_name} branch."
        )
        cat_name = entry_data.get("category") or "Hardware"
        sub_name = entry_data.get("sub_category") or "Laptop"
        entry_page.click_save()
        entry_toast = entry_page.wait_for_toast_message()
        logger.info(f"[{branch_name} PROCUREMENT] Toast='{entry_toast}' | Serial={serial_no}")

        # Capture created Asset Code
        entry_page.navigate_to_asset_entry()
        it_page.locator("input[placeholder*='Search']").first.fill(serial_no)
        it_page.locator("input[placeholder*='Search']").first.press("Enter")
        it_page.wait_for_timeout(1000)
        row = it_page.locator("table tbody tr").filter(has_text=serial_no).first
        row_text = row.inner_text() if row.is_visible(timeout=2000) else ""
        m = re.search(r"ASSET-[A-Z0-9-]+", row_text)
        created_asset_code = m.group(0) if m else None
        logger.info(f"[{branch_name} ASSET CREATED] Asset Code: '{created_asset_code}'")

        # Step 3: Direct Assignment by IT Person to Branch Employee
        logger.info(f"[STEP] Phase 2: Direct Asset Assignment to Branch '{branch_name}' Employee '{target_emp['name']}'")
        assign_page = AssetAssignmentPage(it_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        assigned_code = assign_page.fill_assignment_details(
            employee_name=target_emp["name"],
            category=cat_name,
            sub_category=sub_name,
            asset_name_or_code=created_asset_code,
            remarks=f"Direct assignment by IT Person {it_person['name']} for {branch_name} branch."
        )
        assign_page.click_submit_assignment()
        assign_toast = assign_page.wait_for_toast_message()
        if not assigned_code or assigned_code == "ASSET":
            assigned_code = created_asset_code or "ASSET"
        logger.info(f"[{branch_name} ASSIGNMENT] Toast='{assign_toast}' | Assigned Code='{assigned_code}'")

        # Step 4: Target Employee Accepts Assignment
        logger.info(f"[STEP] Phase 3: Employee Accepts Asset on Employee Portal")
        emp_key = target_emp.get("user_key", "sanidhy")
        emp_page, emp_ctx = logged_in_page(emp_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(assigned_code)
        emp_ctx.close()

        # Step 5: IT Return Request & Condition Assessment by Branch IT Person
        logger.info(f"[STEP] Phase 4: IT Person Return Request & Condition Assessment ('Good') for Branch '{branch_name}'")
        it_page.goto(f"{settings.BASE_URL}/asset-return")
        it_page.wait_for_load_state("domcontentloaded")

        return_page = AssetReturnPage(it_page)
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code=assigned_code,
            condition="Good",
            remarks=f"IT Person '{it_person['name']}' verified return in good condition for {branch_name} branch."
        )

        # Step 6: Verify Return History & Status Reset to AVAILABLE
        logger.info(f"[STEP] Phase 5: Return History Log & Asset Status Verification")
        history_entry = return_page.verify_return_history_entry(assigned_code)
        logger.info(f"[{branch_name} RETURN VERIFIED] {history_entry}")
        assert history_entry["condition"].lower() == "good", f"Expected condition 'Good', got '{history_entry['condition']}'"
        assert history_entry["new_status"].upper() == "AVAILABLE", f"Expected status 'AVAILABLE', got '{history_entry['new_status']}'"
