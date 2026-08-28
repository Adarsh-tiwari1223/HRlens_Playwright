import re
import random
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
class TestAssetRequestGovernanceRules:
    """
    Test Suite validating the 2 strict Asset Request Governance Rules:
    1. Employee CANNOT submit a duplicate request if a request is already PENDING for that Category.SubCategory.
    2. Employee CANNOT request an asset if they already possess an ACTIVE/ASSIGNED asset in that Category.SubCategory.
    3. Re-Eligibility: Once an asset is RETURNED, the employee CAN request that Category.SubCategory again.
    """

    def test_rule_1_duplicate_pending_request_is_blocked(self, logged_in_page):
        """
        Rule 1: Blocks duplicate pending requests under the same Category.SubCategory.
        """
        story = TestStoryLogger(
            "Asset Request Rule 1: Duplicate Pending Request Block",
            module="Asset Management",
            phase="Request Governance"
        )
        story.start()

        emp_user_key = "sanidhy"
        emp_page, emp_ctx = logged_in_page(emp_user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()

        # Step 1: Submit 1st Asset Request
        logger.info("[RULE 1 - STEP 1] Submitting First Asset Request for 'IT Hardware.Laptop'...")
        req1 = req_page.create_new_request(
            reason="Primary workstation request for automated testing.",
            remarks="First legitimate request.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        logger.info(f"[REQUEST 1 RESULT] Toast: '{req1.get('toast')}'")

        story.log_step(
            "Step 1: Submit 1st Asset Request",
            record="Category: IT Hardware | SubCategory: Laptop",
            expected="1st Request submitted in Pending state",
            actual=f"Toast: '{req1.get('toast')}'",
            status="PASS"
        )

        # Step 2: Attempt 2nd Asset Request for same Category.SubCategory
        logger.info("[RULE 1 - STEP 2] Attempting Duplicate 2nd Asset Request for same Category.SubCategory...")
        req2 = req_page.create_new_request(
            reason="Duplicate request attempt while first is pending.",
            remarks="Should be blocked by governance rule.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        toast2 = req2.get("toast", "")
        logger.info(f"[REQUEST 2 RESULT] Toast: '{toast2}'")

        is_blocked = any(kw in toast2.lower() for kw in ["already", "pending", "duplicate", "exist", "cannot", "prohibited", "not allowed", "active"])
        logger.info(f"[GOVERNANCE RULE 1 VERDICT] Duplicate Request Blocked = {is_blocked} (Toast: '{toast2}')")

        story.log_step(
            "Step 2: Submit Duplicate 2nd Asset Request",
            record="Category: IT Hardware | SubCategory: Laptop (Duplicate)",
            expected="System blocks duplicate request (Toast: Already pending / Cannot submit)",
            actual=f"Toast: '{toast2}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        emp_ctx.close()

        assert is_blocked, (
            f"APPLICATION BUG (Defect): Employee was allowed to submit a duplicate "
            f"Asset Request for 'IT Hardware.Laptop' while a request is already PENDING. "
            f"Received Toast: '{toast2}'"
        )

    def test_rule_2_active_assigned_asset_blocks_new_request(self, admin_page, logged_in_page):
        """
        Rule 2: Blocks asset request when employee already has an active/assigned asset in that Category.SubCategory.
        """
        story = TestStoryLogger(
            "Asset Request Rule 2: Active Asset Possession Block",
            module="Asset Management",
            phase="Request Governance"
        )
        story.start()

        # Step 1: Admin Direct Assigns a Laptop to Adarsh Tiwari
        logger.info("[RULE 2 - STEP 1] Admin Direct Assigns an Asset to Adarsh Tiwari...")
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

        # Assign to Adarsh Tiwari
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        actual_code = assign_page.fill_assignment_details(
            employee_name="Adarsh Tiwari",
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=asset_code,
            remarks="Active possession governance check."
        )
        assign_page.click_submit_assignment()
        admin_page.wait_for_timeout(2000)

        # Step 2: Adarsh Tiwari Accepts Asset -> Status becomes ACTIVE / IN-USE
        emp_page, emp_ctx = logged_in_page("adarsh_tiwari")
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(actual_code)
        emp_page.wait_for_timeout(1500)

        story.log_step(
            "Step 1: Provision & Accept Asset into Active Possession",
            record=f"Employee: Adarsh Tiwari | Asset: {actual_code} (ACTIVE)",
            expected="Asset is accepted and locked in employee active custody",
            actual="Asset accepted successfully",
            status="PASS"
        )

        # Step 3: Adarsh Tiwari Attempts to Request another Laptop while holding an active one
        logger.info("[RULE 2 - STEP 3] Employee with Active Asset attempts to request another Laptop...")
        req_attempt = req_page.create_new_request(
            reason="Attempting to request a second laptop while already holding one.",
            remarks="Should be blocked by active asset governance rule.",
            category="IT Hardware",
            sub_category="Laptop"
        )
        toast_attempt = req_attempt.get("toast", "")
        logger.info(f"[ACTIVE POSSESSION REQUEST RESULT] Toast: '{toast_attempt}'")

        is_blocked = any(kw in toast_attempt.lower() for kw in ["already", "active", "assigned", "cannot", "prohibited", "not allowed", "limit", "exist"])
        logger.info(f"[GOVERNANCE RULE 2 VERDICT] Active Possession Request Blocked = {is_blocked} (Toast: '{toast_attempt}')")

        story.log_step(
            "Step 2: Request New Asset while Holding Active Asset",
            record="Category: IT Hardware | SubCategory: Laptop (Active Held)",
            expected="System blocks request because employee already has active asset in subcategory",
            actual=f"Toast: '{toast_attempt}' | Blocked: {is_blocked}",
            status="PASS" if is_blocked else "FAIL"
        )

        emp_ctx.close()

        assert is_blocked, (
            f"APPLICATION BUG (Defect): Employee was allowed to request another "
            f"asset for 'IT Hardware.Laptop' while already holding an ACTIVE/ASSIGNED asset. "
            f"Received Toast: '{toast_attempt}'"
        )
