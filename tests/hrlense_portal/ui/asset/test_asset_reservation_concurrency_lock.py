import re
import random
import logging
import pytest
import requests
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from core.config import settings

from utils.api.asset.asset_api import get_stock_by_branch_assets, get_auth_headers

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
class TestAssetReservationConcurrencyLock:
    """
    Test suite verifying inventory concurrency and double-assignment protection:
    When Asset X is assigned to Employee A (Status: RESERVED / PENDING ACCEPTANCE),
    validate whether Asset X is hidden or visible in the available dropdown for Employee B.
    """

    def test_verify_reserved_asset_visibility_for_second_employee(self, admin_page):
        story = TestStoryLogger(
            "Asset Reservation & Double-Assignment Concurrency Lock",
            module="Asset Management",
            phase="Concurrency & Inventory Integrity"
        )
        story.start()

        # =========================================================================
        # STEP 1: Check / Provision Controlled Asset (Varanasi Branch)
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("[STEP 1] Checking Available Assets in Varanasi Branch via API")
        logger.info("=" * 70)

        existing_assets = get_stock_by_branch_assets(branch_id=1, category_id=4, status="Available")
        if existing_assets:
            asset_code = existing_assets[0].get("asset_Code")
            serial_no = existing_assets[0].get("serial_No")
            logger.info(f"[API CHECK PASS] Found {len(existing_assets)} available assets in Varanasi. Reusing: '{asset_code}' (Serial: '{serial_no}')")
            story.log_step(
                "Step 1: Verify Available Asset (API Check)",
                record=f"Asset Code: {asset_code} | Serial: {serial_no}",
                expected="Reuse existing available asset in Varanasi to save execution time",
                actual=f"Found {len(existing_assets)} available assets via API; Reusing '{asset_code}'",
                status="PASS"
            )
        else:
            logger.info("[API CHECK] No available asset found in Varanasi. Provisioning a fresh asset via UI...")
            entry_page = AssetEntryPage(admin_page)
            entry_page.navigate_to_asset_entry()

            suffix = random.randint(100000, 999999)
            serial_no = f"DL-7440-{suffix}"
            asset_name = "Dell Latitude 7440"

            entry_page.click_add_asset()
            entry_page.fill_asset_details(
                name=asset_name,
                brand="Dell",
                model="Latitude 7440",
                category="IT Hardware",
                sub_category="Laptop",
                branch="Varanasi",
                payroll_company="Tekinspirations",
                serial_no=serial_no,
                warranty="Warranty",
                expiry_date="2027-12-31",
                insured="No",
                notes="Company issued standard laptop workstation."
            )
            toast = entry_page.click_save()

            match = re.search(r"ASSET-[A-Z0-9-]+", toast or "")
            asset_code = match.group(0) if match else f"ASSET-LAP-TEST-{suffix}"
            logger.info(f"[PROVISIONED] Asset Code: '{asset_code}', Serial: '{serial_no}'")

            story.log_step(
                "Step 1: Provision Controlled Asset (Fallback)",
                record=f"Asset Code: {asset_code} | Serial: {serial_no}",
                expected="Asset created with initial status = Available",
                actual=f"Toast: '{toast}'",
                status="PASS"
            )

        # =========================================================================
        # STEP 2: Assign Asset X to Employee A (Sanidhy Tiwari) -> Status: RESERVED
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 2] Assigning Asset '{asset_code}' to Employee A (Sanidhy Tiwari)")
        logger.info("=" * 70)

        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        actual_assigned_code = assign_page.fill_assignment_details(
            employee_name="Sanidhy Tiwari",
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=asset_code,
            remarks="Primary assignment for concurrency lock verification."
        )
        assign_page.click_submit_assignment()
        admin_page.wait_for_timeout(2000)

        logger.info(f"[ASSIGNED TO EMPLOYEE A] Asset '{actual_assigned_code}' is now RESERVED for Sanidhy Tiwari.")

        story.log_step(
            "Step 2: Direct Assign to Employee A (Sanidhy Tiwari)",
            record=f"Asset: {actual_assigned_code} -> Sanidhy Tiwari",
            expected=f"Asset {actual_assigned_code} assigned to Sanidhy Tiwari and enters RESERVED state",
            actual="Assignment submitted successfully",
            status="PASS"
        )

        # =========================================================================
        # STEP 3: Open Direct Assignment for Employee B (Adarsh Tiwari)
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 3] Checking Available Dropdown for Employee B (Adarsh Tiwari)")
        logger.info("=" * 70)

        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        # Fill Employee B: Adarsh Tiwari
        emp_search = admin_page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = admin_page.locator("input[placeholder*='Search employee']").first
        emp_search.fill("Adarsh Tiwari")
        admin_page.wait_for_timeout(1000)

        try:
            opt = admin_page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text("Adarsh Tiwari", exact=False).first
            if not opt.is_visible(timeout=2500):
                opt = admin_page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile("Adarsh", re.I)).first
            opt.click(force=True)
        except Exception:
            admin_page.keyboard.press("ArrowDown")
            admin_page.keyboard.press("Enter")

        # Select Category: IT Hardware
        cat_select = admin_page.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = admin_page.locator("select").first
        cat_select.select_option(label="IT Hardware")
        admin_page.wait_for_timeout(500)

        # Select Sub Category: Laptop
        sub_select = admin_page.get_by_label("Sub Category*", exact=True)
        if not sub_select.is_visible(timeout=1000):
            sub_select = admin_page.locator("select").nth(1)
        sub_select.select_option(label="Laptop")
        admin_page.wait_for_timeout(800)

        # =========================================================================
        # STEP 4: Concurrency Check & Assertion (Targeted Search Filter)
        # =========================================================================
        clean_code_b = (actual_assigned_code or "").strip()
        logger.info(f"Targeting asset '{clean_code_b}' in Employee B's available stock...")
        is_asset_visible_for_b = assign_page.is_asset_in_available_dropdown(clean_code_b)

        if is_asset_visible_for_b:
            logger.warning(f"⚠️ [CONCURRENCY ISSUE DETECTED] Asset '{actual_assigned_code}' (Reserved for Employee A) IS STILL VISIBLE in dropdown for Employee B!")
            
            # Attempt to assign it to Employee B to see if backend blocks it
            target_item = admin_page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").filter(has_text=actual_assigned_code).first
            target_item.click(force=True)
            admin_page.wait_for_timeout(500)

            assign_page.click_submit_assignment()
            toast_result = assign_page.wait_for_toast_message()
            logger.warning(f"[DOUBLE-ASSIGNMENT ATTEMPT TOAST]: '{toast_result}'")

            story.log_step(
                "Step 4: Concurrency & Double-Booking Check",
                record=f"Asset: {actual_assigned_code} | Employee A: Sanidhy Tiwari | Employee B: Adarsh Tiwari",
                expected="Asset X should be hidden from dropdown OR blocked on submit",
                actual=f"Asset VISIBLE in dropdown. Attempt Toast: '{toast_result}'",
                status="FAIL" if "assigned" in (toast_result or "").lower() and "already" not in (toast_result or "").lower() else "WARNING"
            )
        else:
            logger.info(f"✅ [INTEGRITY PASS] Asset '{actual_assigned_code}' is correctly HIDDEN from Employee B's available stock dropdown.")
            assign_page.click_cancel()

            story.log_step(
                "Step 4: Concurrency & Double-Booking Check",
                record=f"Asset: {actual_assigned_code} | Employee A: Sanidhy Tiwari | Employee B: Adarsh Tiwari",
                expected=f"Asset {actual_assigned_code} must NOT appear in Employee B dropdown",
                actual="Asset is successfully filtered out of dropdown (Integrity Maintained)",
                status="PASS"
            )

        logger.info("\n" + "=" * 70)
        logger.info(f"[TEST COMPLETED] Reserved Asset Visible in Dropdown for Employee B = {is_asset_visible_for_b}")
        logger.info("=" * 70)

    def test_employee_reject_reserved_asset_reappears_in_dropdown(self, logged_in_page):
        """
        Validates Rejection Lifecycle & Re-visibility:
        1. Identifies the reserved asset assigned to Employee A (Sanidhy Tiwari).
        2. Employee A logs in, navigates to /asset-request, and rejects the assigned asset.
        3. Admin opens Direct Assignment modal for Employee B (Adarsh Tiwari - same branch: Varanasi).
        4. Verifies that the rejected asset is now RE-VISIBLE in the Available stock dropdown.
        """
        story = TestStoryLogger(
            "Asset Rejection & Available Stock Re-visibility",
            module="Asset Management",
            phase="Rejection Lifecycle & Dropdown Release"
        )
        story.start()

        # Step 1: Resolve reserved asset for Sanidhy Tiwari
        logger.info("\n" + "=" * 70)
        logger.info("[STEP 1] Finding Reserved Asset for Sanidhy Tiwari")
        logger.info("=" * 70)

        reserved_asset_code = None
        try:
            headers = get_auth_headers("admin")
            res = requests.get(f"{settings.API_BASE_URL}/Asset/assets?first=0&rows=100", headers=headers, timeout=10)
            if res.status_code == 200:
                for a in res.json().get("data", []):
                    if a.get("status") == "Reserved" and a.get("branch_Name") == "Varanasi":
                        reserved_asset_code = (a.get("asset_Code") or "").strip()
                        break
        except Exception as e:
            logger.warning(f"Note resolving reserved asset via API: {e}")

        # If no asset is currently in Reserved status, assign an available laptop to Sanidhy first
        if not reserved_asset_code:
            logger.info("[STEP 1 Setup] No asset currently Reserved in Varanasi. Assigning available laptop to Sanidhy Tiwari...")
            admin_setup_page, admin_setup_ctx = logged_in_page("admin")
            assign_setup = AssetAssignmentPage(admin_setup_page)
            assign_setup.navigate_to_asset_assignment()
            assign_setup.click_assign_asset()
            assigned_code = assign_setup.fill_assignment_details(
                employee_name="Sanidhy Tiwari",
                category="IT Hardware",
                sub_category="Laptop",
                remarks="Auto-setup for rejection lifecycle test."
            )
            assign_setup.click_submit_assignment()
            admin_setup_page.wait_for_timeout(2000)
            try:
                admin_setup_ctx.close()
            except Exception:
                pass
            reserved_asset_code = (assigned_code or "").strip()

        logger.info(f"Target Reserved Asset to Reject: '{reserved_asset_code}'")

        # Step 2: Employee A (Sanidhy Tiwari) logs in and rejects the asset
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 2] Employee A (Sanidhy Tiwari) Rejecting Asset '{reserved_asset_code}'")
        logger.info("=" * 70)

        emp_page, emp_ctx = logged_in_page("sanidhy")
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()

        rejected = req_page.reject_asset(
            asset_code_or_name=reserved_asset_code,
            reason="Hardware specs do not match project requirement. Releasing to stock."
        )
        emp_page.wait_for_timeout(2000)
        logger.info(f"Rejection outcome for '{reserved_asset_code}': {rejected}")

        story.log_step(
            "Step 2: Employee Rejection",
            record=f"Asset: {reserved_asset_code} | Employee: Sanidhy Tiwari",
            expected="Employee rejects asset on /asset-request",
            actual=f"Rejected = {rejected}",
            status="PASS" if rejected else "FAIL"
        )
        assert rejected, f"Failed to reject asset '{reserved_asset_code}' on Employee /asset-request page!"

        # Step 3: Admin opens Direct Assignment for Employee B (Adarsh Tiwari)
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 3] Admin Auditing Re-visibility of '{reserved_asset_code}' for Employee B (Adarsh Tiwari)")
        logger.info("=" * 70)

        admin_page, admin_ctx = logged_in_page("admin")
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        # Fill Employee B: Adarsh Tiwari
        emp_search = admin_page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = admin_page.locator("input[placeholder*='Search employee']").first
        emp_search.fill("Adarsh Tiwari")
        admin_page.wait_for_timeout(1000)

        try:
            opt = admin_page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text("Adarsh Tiwari", exact=False).first
            if not opt.is_visible(timeout=2500):
                opt = admin_page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile("Adarsh", re.I)).first
            opt.click(force=True)
        except Exception:
            admin_page.keyboard.press("ArrowDown")
            admin_page.keyboard.press("Enter")

        # Select Category: IT Hardware
        cat_select = admin_page.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = admin_page.locator("select").first
        cat_select.select_option(label="IT Hardware")
        admin_page.wait_for_timeout(500)

        # Select Sub Category: Laptop
        sub_select = admin_page.get_by_label("Sub Category*", exact=True)
        if not sub_select.is_visible(timeout=1000):
            sub_select = admin_page.locator("select").nth(1)
        sub_select.select_option(label="Laptop")
        admin_page.wait_for_timeout(800)

        # Step 4: Verify asset is now RE-VISIBLE in dropdown
        clean_reserved_code = (reserved_asset_code or "").strip()
        is_asset_re_visible = assign_page.is_asset_in_available_dropdown(clean_reserved_code)
        logger.info(f"[RE-VISIBILITY CHECK] Asset '{clean_reserved_code}' is re-visible in dropdown: {is_asset_re_visible}")

        story.log_step(
            "Step 4: Check Asset Re-visibility in Available Dropdown",
            record=f"Asset: {reserved_asset_code} | Employee B: Adarsh Tiwari",
            expected="Rejected asset returns to Available status and is re-visible in dropdown",
            actual=f"Re-visible = {is_asset_re_visible}",
            status="PASS" if is_asset_re_visible else "FAIL"
        )
        assert is_asset_re_visible, f"Asset '{reserved_asset_code}' was rejected by Employee A, but did NOT reappear in available dropdown for Employee B!"

        assign_page.click_cancel()
        logger.info("\n" + "=" * 70)
        logger.info(f"[TEST PASSED] Rejected Asset '{reserved_asset_code}' Successfully Reappeared in Dropdown!")
        logger.info("=" * 70)

    def test_employee_accept_reserved_asset_moves_to_assigned_fleet(self, logged_in_page):
        """
        Validates Acceptance Lifecycle & Fleet Active State (TC-AM-001):
        1. Identifies / provisions an available asset assigned to Employee A (Sanidhy Tiwari).
        2. Employee A logs in, navigates to /asset-request, and ACCEPTS the assigned asset.
        3. Verifies asset transitions to 'Assigned' / 'Active' status.
        4. Admin opens Direct Assignment modal for Employee B (Adarsh Tiwari - same branch: Varanasi).
        5. Verifies that the accepted asset remains strictly HIDDEN from the Available stock dropdown.
        6. Clean teardown: Admin returns the asset with condition 'Good' to restore it back to Available.
        """
        story = TestStoryLogger(
            "Asset Acceptance & Active Fleet Isolation",
            module="Asset Management",
            phase="Acceptance Lifecycle & Dropdown Exclusion"
        )
        story.start()

        # Step 1: Resolve or assign an available asset to Sanidhy Tiwari
        logger.info("\n" + "=" * 70)
        logger.info("[STEP 1] Finding or Assigning Asset for Sanidhy Tiwari")
        logger.info("=" * 70)

        reserved_asset_code = None
        try:
            headers = get_auth_headers("admin")
            res = requests.get(f"{settings.API_BASE_URL}/Asset/assets?first=0&rows=100", headers=headers, timeout=10)
            if res.status_code == 200:
                for a in res.json().get("data", []):
                    if a.get("status") == "Reserved" and a.get("branch_Name") == "Varanasi":
                        reserved_asset_code = (a.get("asset_Code") or "").strip()
                        break
        except Exception as e:
            logger.warning(f"Note resolving reserved asset via API: {e}")

        if not reserved_asset_code:
            logger.info("[STEP 1 Setup] No asset currently Reserved in Varanasi. Assigning available laptop to Sanidhy Tiwari...")
            admin_setup_page, admin_setup_ctx = logged_in_page("admin")
            assign_setup = AssetAssignmentPage(admin_setup_page)
            assign_setup.navigate_to_asset_assignment()
            assign_setup.click_assign_asset()
            assigned_code = assign_setup.fill_assignment_details(
                employee_name="Sanidhy Tiwari",
                category="IT Hardware",
                sub_category="Laptop",
                remarks="Auto-setup for acceptance lifecycle test."
            )
            assign_setup.click_submit_assignment()
            admin_setup_page.wait_for_timeout(2000)
            try:
                admin_setup_ctx.close()
            except Exception:
                pass
            reserved_asset_code = (assigned_code or "").strip()

        logger.info(f"Target Reserved Asset to Accept: '{reserved_asset_code}'")

        # Step 2: Employee A (Sanidhy Tiwari) logs in and ACCEPTS the asset
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 2] Employee A (Sanidhy Tiwari) Accepting Asset '{reserved_asset_code}'")
        logger.info("=" * 70)

        emp_page, emp_ctx = logged_in_page("sanidhy")
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()

        accepted = req_page.accept_asset(reserved_asset_code)
        emp_page.wait_for_timeout(2000)
        logger.info(f"Acceptance outcome for '{reserved_asset_code}': {accepted}")

        story.log_step(
            "Step 2: Employee Acceptance",
            record=f"Asset: {reserved_asset_code} | Employee: Sanidhy Tiwari",
            expected="Employee accepts asset on /asset-request",
            actual=f"Accepted = {accepted}",
            status="PASS" if accepted else "FAIL"
        )
        assert accepted, f"Failed to accept asset '{reserved_asset_code}' on Employee /asset-request page!"

        # Step 3: Admin opens Direct Assignment for Employee B (Adarsh Tiwari)
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 3] Admin Verifying '{reserved_asset_code}' is NOT in dropdown for Employee B (Adarsh Tiwari)")
        logger.info("=" * 70)

        admin_page, admin_ctx = logged_in_page("admin")
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        # Fill Employee B: Adarsh Tiwari
        emp_search = admin_page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = admin_page.locator("input[placeholder*='Search employee']").first
        emp_search.fill("Adarsh Tiwari")
        admin_page.wait_for_timeout(1000)

        try:
            opt = admin_page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text("Adarsh Tiwari", exact=False).first
            if not opt.is_visible(timeout=2500):
                opt = admin_page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile("Adarsh", re.I)).first
            opt.click(force=True)
        except Exception:
            admin_page.keyboard.press("ArrowDown")
            admin_page.keyboard.press("Enter")

        # Select Category: IT Hardware
        cat_select = admin_page.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = admin_page.locator("select").first
        cat_select.select_option(label="IT Hardware")
        admin_page.wait_for_timeout(500)

        # Select Sub Category: Laptop
        sub_select = admin_page.get_by_label("Sub Category*", exact=True)
        if not sub_select.is_visible(timeout=1000):
            sub_select = admin_page.locator("select").nth(1)
        sub_select.select_option(label="Laptop")
        admin_page.wait_for_timeout(800)

        # Step 4: Verify accepted asset is HIDDEN from dropdown (since it is actively in use)
        clean_accepted_code = (reserved_asset_code or "").strip()
        is_asset_in_dropdown = assign_page.is_asset_in_available_dropdown(clean_accepted_code)
        logger.info(f"[ACCEPTANCE FLEET CHECK] Asset '{clean_accepted_code}' in available dropdown: {is_asset_in_dropdown}")

        story.log_step(
            "Step 4: Check Asset Hidden from Available Dropdown",
            record=f"Asset: {clean_accepted_code} | Employee B: Adarsh Tiwari",
            expected="Accepted asset is marked Assigned/Active and NOT visible in available dropdown",
            actual=f"Visible in Dropdown = {is_asset_in_dropdown}",
            status="PASS" if not is_asset_in_dropdown else "FAIL"
        )
        assert not is_asset_in_dropdown, f"Accepted asset '{clean_accepted_code}' is STILL VISIBLE in available dropdown for Employee B!"

        assign_page.click_cancel()

        # Step 5: Clean Teardown (Return Asset back to Available stock)
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 5 Teardown] Returning Asset '{clean_accepted_code}' to Available stock")
        logger.info("=" * 70)
        try:
            return_page = AssetReturnPage(admin_page)
            return_page.navigate_to_asset_return()
            return_page.return_asset(
                asset_code_or_name=clean_accepted_code,
                condition="Good",
                tab_name="Assigned Assets",
                remarks="Auto-teardown: Returned in Good condition after acceptance test."
            )
            logger.info(f"Teardown: Asset '{clean_accepted_code}' returned to available stock.")
        except Exception as e:
            logger.warning(f"Teardown return note: {e}")

        logger.info("\n" + "=" * 70)
        logger.info(f"[TEST PASSED] Asset Acceptance & Active Fleet Isolation Confirmed for '{clean_accepted_code}'!")
        logger.info("=" * 70)
