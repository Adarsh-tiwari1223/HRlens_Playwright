import re
import random
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
class TestAssetDualRoleGovernanceMatrix:
    """
    Complete Dual-Role Asset Governance Matrix Test Suite:
    
    --------------------------------------------------------------------------
    PART 1: EMPLOYEE ROLE (/asset-request)
    --------------------------------------------------------------------------
    1. Employee CANNOT submit duplicate asset request for same Category.SubCategory (Pending Block).
    2. Employee CANNOT request an asset if they already hold an ACTIVE assigned asset for that Category.SubCategory.

    --------------------------------------------------------------------------
    PART 2: IT PERSON / ADMIN ROLE (/asset-assignment)
    --------------------------------------------------------------------------
    3. IT Person CANNOT direct-assign asset if employee already has a PENDING request for that Category.SubCategory.
    4. IT Person CANNOT direct-assign asset if employee already holds an ACTIVE assigned asset for that Category.SubCategory.
    """

    # =========================================================================
    # PART 1: EMPLOYEE VALIDATION
    # =========================================================================

    def test_employee_cannot_request_duplicate_pending_record(self, logged_in_page):
        """
        Employee Role: Validates that an employee cannot request a duplicate record
        when a request for that Category.SubCategory is already pending.
        """
        story = TestStoryLogger(
            "Employee Role: Duplicate Pending Request Block",
            module="Asset Governance",
            phase="Employee Validation"
        )
        story.start()

        emp_user_key = "sanidhy"
        emp_page, emp_ctx = logged_in_page(emp_user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()

        logger.info("[EMPLOYEE RULE 1 - STEP 1] Submitting 1st Asset Request for 'IT Hardware.Laptop'...")
        req1_res = req_page.create_new_request(
            reason="Primary workstation request for automated testing.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        toast1 = req1_res.get("toast", "")
        logger.info(f"[EMPLOYEE RULE 1 - REQUEST 1 TOAST]: '{toast1}'")
        emp_page.wait_for_timeout(1000)

        is_already_blocked = any(kw in toast1.lower() for kw in ["already", "pending", "duplicate", "exist", "cannot", "prohibited", "not allowed"])

        if is_already_blocked:
            logger.info(f"[GOVERNANCE RULE 1 VERIFIED ON ATTEMPT 1] Employee already has pending request and new request was properly blocked: '{toast1}'")
            eval_toast = toast1
            is_blocked = True
        else:
            # Step 2: If Request 1 created a pending state, attempt duplicate Request 2
            logger.info("[EMPLOYEE RULE 1 - STEP 2] Attempting Duplicate 2nd Asset Request for same Category.SubCategory...")
            req2_res = req_page.create_new_request(
                reason="Duplicate request attempt while first is pending.",
                category="IT Hardware",
                sub_category="Laptop"
            )
            toast2 = req2_res.get("toast", "")
            logger.info(f"[EMPLOYEE RULE 1 - REQUEST 2 TOAST]: '{toast2}'")
            eval_toast = toast2
            is_blocked = any(kw in toast2.lower() for kw in ["already", "pending", "duplicate", "exist", "cannot", "prohibited", "not allowed"])

        logger.info(f"[EMPLOYEE RULE 1 VERDICT] Duplicate Request Blocked = {is_blocked} (Toast: '{eval_toast}')")

        story.log_step(
            "Employee Role: Duplicate Request Block",
            record="Category: IT Hardware | SubCategory: Laptop (Duplicate Attempt)",
            expected="System blocks duplicate request submission",
            actual=f"Toast: '{eval_toast}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        emp_ctx.close()
        assert is_blocked, f"APPLICATION BUG: Employee was allowed to request duplicate pending record. Toast: '{eval_toast}'"

    def test_employee_cannot_request_when_already_holding_active_asset(self, logged_in_page):
        """
        Employee Role: Validates that an employee cannot request an asset if they
        already hold an active/assigned asset for that Category.SubCategory.
        """
        story = TestStoryLogger(
            "Employee Role: Active Possession Request Block",
            module="Asset Governance",
            phase="Employee Validation"
        )
        story.start()

        emp_name = "Adarsh Tiwari"
        emp_user_key = "adarsh_tiwari"

        # Step 1: Admin provisions and assigns 1st Laptop to Adarsh Tiwari
        logger.info("[EMPLOYEE RULE 2 - STEP 1] Admin ensures employee holds an active Laptop...")
        admin_page, admin_ctx = logged_in_page("admin")
        entry_page = AssetEntryPage(admin_page)
        entry_page.navigate_to_asset_entry()

        suffix = random.randint(100000, 999999)
        serial_no = f"DL-7440-{suffix}"
        entry_page.click_add_asset()
        entry_page.fill_asset_details(
            name="Dell Latitude 7440",
            brand="Dell",
            model="Latitude 7440",
            category="IT Hardware",
            sub_category="Laptop",
            branch="Varanasi",
            payroll_company="Tekinspirations",
            serial_no=serial_no,
            insured="No"
        )
        add_toast = entry_page.click_save()
        match = re.search(r"ASSET-[A-Z0-9-]+", add_toast or "")
        asset_code = match.group(0) if match else f"ASSET-LAP-ACT-{suffix}"

        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        actual_code = assign_page.fill_assignment_details(
            employee_name=emp_name,
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=asset_code,
            remarks="Active possession setup."
        )
        assign_page.click_submit_assignment()
        admin_page.wait_for_timeout(1500)
        admin_ctx.close()

        # Step 2: Employee accepts asset to enter ACTIVE state
        emp_page, emp_ctx = logged_in_page(emp_user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(actual_code)
        emp_page.wait_for_timeout(1500)

        # Step 3: Employee attempts to request another asset of same Category.SubCategory
        logger.info("[EMPLOYEE RULE 2 - STEP 2] Employee attempts to request another Laptop while holding active one...")
        req_res = req_page.create_new_request(
            reason="Attempting second laptop request while holding active asset.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        toast = req_res.get("toast", "")
        logger.info(f"[EMPLOYEE RULE 2 TOAST]: '{toast}'")

        is_blocked = any(kw in toast.lower() for kw in ["already", "active", "assigned", "pending", "cannot", "prohibited", "not allowed", "exist"])
        logger.info(f"[EMPLOYEE RULE 2 VERDICT] Active Possession Request Blocked = {is_blocked}")

        story.log_step(
            "Employee Role: Active Possession Request Block",
            record="Category: IT Hardware | SubCategory: Laptop (Active Held)",
            expected="System blocks request because employee already has active asset in subcategory",
            actual=f"Toast: '{toast}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        emp_ctx.close()
        assert is_blocked, f"APPLICATION BUG: Employee was allowed to request asset while already holding an active device. Toast: '{toast}'"

    # =========================================================================
    # PART 2: IT PERSON / ADMIN VALIDATION
    # =========================================================================

    def test_it_person_cannot_direct_assign_when_pending_request_exists(self, logged_in_page):
        """
        IT Person Role: Validates that IT cannot direct-assign an asset to an employee
        who already has a PENDING request for that Category.SubCategory.
        """
        story = TestStoryLogger(
            "IT Role: Direct Assignment Block on Pending Request",
            module="Asset Governance",
            phase="IT Person Validation"
        )
        story.start()

        emp_name = "Sanidhy Tiwari"
        emp_user_key = "sanidhy"

        # Step 1: Employee submits a pending request
        logger.info(f"[IT RULE 1 - STEP 1] Employee '{emp_name}' submits a pending request...")
        emp_page, emp_ctx = logged_in_page(emp_user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.create_new_request(
            reason="Legitimate pending request for governance test.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        emp_ctx.close()

        # Step 2: IT Person attempts direct assignment for same employee & category
        logger.info(f"[IT RULE 1 - STEP 2] IT attempts direct assignment for '{emp_name}' with pending request...")
        admin_page, admin_ctx = logged_in_page("admin")
        entry_page = AssetEntryPage(admin_page)
        entry_page.navigate_to_asset_entry()

        suffix = random.randint(100000, 999999)
        serial_no = f"DL-7440-{suffix}"
        entry_page.click_add_asset()
        entry_page.fill_asset_details(
            name="Dell Latitude 7440",
            brand="Dell",
            model="Latitude 7440",
            category="IT Hardware",
            sub_category="Laptop",
            branch="Varanasi",
            payroll_company="Tekinspirations",
            serial_no=serial_no,
            insured="No"
        )
        add_toast = entry_page.click_save()
        match = re.search(r"ASSET-[A-Z0-9-]+", add_toast or "")
        asset_code = match.group(0) if match else f"ASSET-LAP-{suffix}"

        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        assign_page.fill_assignment_details(
            employee_name=emp_name,
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=asset_code,
            remarks="Direct assignment attempt on pending request."
        )
        assign_page.click_submit_assignment()
        admin_page.wait_for_timeout(1000)

        assign_toast = assign_page.wait_for_toast_message() or ""
        logger.info(f"[IT RULE 1 DIRECT ASSIGNMENT TOAST]: '{assign_toast}'")

        is_blocked = any(kw in assign_toast.lower() for kw in ["already", "pending", "exist", "cannot", "prohibited", "not allowed", "conflict"])
        logger.info(f"[IT RULE 1 VERDICT] IT Direct Assignment Blocked = {is_blocked}")

        assign_page.click_cancel()
        admin_ctx.close()

        story.log_step(
            "IT Role: Pending Request Assignment Conflict Block",
            record=f"Employee: {emp_name} | Asset: {asset_code} (Pending Request Conflict)",
            expected="IT direct assignment is blocked due to existing pending request",
            actual=f"Toast: '{assign_toast}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        assert is_blocked, f"APPLICATION BUG: IT was allowed to direct-assign asset to employee with pending request. Toast: '{assign_toast}'"

    def test_it_person_cannot_direct_assign_when_active_asset_already_assigned(self, logged_in_page):
        """
        IT Person Role: Validates that IT cannot direct-assign a second asset to an employee
        who already has an ACTIVE assigned asset for that Category.SubCategory.
        """
        story = TestStoryLogger(
            "IT Role: Duplicate Active Assignment Block",
            module="Asset Governance",
            phase="IT Person Validation"
        )
        story.start()

        emp_name = "Adarsh Tiwari"
        emp_user_key = "adarsh_tiwari"

        # Step 1: Ensure Employee holds 1st Active Laptop
        logger.info(f"[IT RULE 2 - STEP 1] Provisioning 1st Laptop for '{emp_name}'...")
        admin_page, admin_ctx = logged_in_page("admin")
        entry_page = AssetEntryPage(admin_page)
        entry_page.navigate_to_asset_entry()

        suffix1 = random.randint(100000, 999999)
        entry_page.click_add_asset()
        entry_page.fill_asset_details(
            name="Dell Latitude 7440",
            brand="Dell",
            model="Latitude 7440",
            category="IT Hardware",
            sub_category="Laptop",
            branch="Varanasi",
            payroll_company="Tekinspirations",
            serial_no=f"DL-7440-{suffix1}",
            insured="No"
        )
        toast1 = entry_page.click_save()
        match1 = re.search(r"ASSET-[A-Z0-9-]+", toast1 or "")
        code1 = match1.group(0) if match1 else f"ASSET-LAP-1-{suffix1}"

        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        assign_page.fill_assignment_details(
            employee_name=emp_name,
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=code1,
            remarks="First legitimate assignment."
        )
        assign_page.click_submit_assignment()
        admin_page.wait_for_timeout(1500)
        admin_ctx.close()

        # Accept 1st asset
        emp_page, emp_ctx = logged_in_page(emp_user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(code1)
        emp_ctx.close()

        # Step 2: Provision 2nd Laptop and attempt duplicate direct-assignment
        logger.info(f"[IT RULE 2 - STEP 2] IT attempts 2nd Direct Assignment to '{emp_name}'...")
        admin_page2, admin_ctx2 = logged_in_page("admin")
        entry_page2 = AssetEntryPage(admin_page2)
        entry_page2.navigate_to_asset_entry()
        suffix2 = random.randint(100000, 999999)
        entry_page2.click_add_asset()
        entry_page2.fill_asset_details(
            name="Dell Latitude 7440",
            brand="Dell",
            model="Latitude 7440",
            category="IT Hardware",
            sub_category="Laptop",
            branch="Varanasi",
            payroll_company="Tekinspirations",
            serial_no=f"DL-7440-{suffix2}",
            insured="No"
        )
        toast2 = entry_page2.click_save()
        match2 = re.search(r"ASSET-[A-Z0-9-]+", toast2 or "")
        code2 = match2.group(0) if match2 else f"ASSET-LAP-2-{suffix2}"

        assign_page2 = AssetAssignmentPage(admin_page2)
        assign_page2.navigate_to_asset_assignment()
        assign_page2.click_assign_asset()
        assign_page2.fill_assignment_details(
            employee_name=emp_name,
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=code2,
            remarks="Second duplicate assignment attempt."
        )
        assign_page2.click_submit_assignment()
        admin_page2.wait_for_timeout(1000)

        assign_toast2 = assign_page2.wait_for_toast_message() or ""
        logger.info(f"[IT RULE 2 DUPLICATE ASSIGNMENT TOAST]: '{assign_toast2}'")

        is_blocked = any(kw in assign_toast2.lower() for kw in ["already", "active", "assigned", "exist", "cannot", "prohibited", "not allowed", "limit"])
        logger.info(f"[IT RULE 2 VERDICT] Duplicate Direct Assignment Blocked = {is_blocked}")

        assign_page2.click_cancel()
        admin_ctx2.close()

        story.log_step(
            "IT Role: Duplicate Active Assignment Block",
            record=f"Employee: {emp_name} | Asset 2: {code2} (Active Laptop Already Assigned)",
            expected="IT direct assignment is blocked because employee already holds an active laptop",
            actual=f"Toast: '{assign_toast2}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        assert is_blocked, f"APPLICATION BUG: IT was allowed to assign multiple active assets of same subcategory to employee. Toast: '{assign_toast2}'"
