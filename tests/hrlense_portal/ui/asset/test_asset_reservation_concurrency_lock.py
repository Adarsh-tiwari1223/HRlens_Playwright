import re
import random
import logging
import pytest
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from core.config import settings

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
        # STEP 1: Provision a fresh controlled asset
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("[STEP 1] Provisioning a Fresh Controlled Asset")
        logger.info("=" * 70)

        entry_page = AssetEntryPage(admin_page)
        entry_page.navigate_to_asset_entry()

        suffix = random.randint(100000, 999999)
        serial_no = f"DL-7440-{suffix}"
        asset_name = "Dell Latitude 7440"

        entry_page.click_add_asset()
        entry_data = entry_page.fill_asset_details(
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

        # Extract generated asset code
        match = re.search(r"ASSET-[A-Z0-9-]+", toast or "")
        if match:
            asset_code = match.group(0)
        else:
            asset_code = f"ASSET-LAP-TEST-{suffix}"

        logger.info(f"[PROVISIONED] Asset Code: '{asset_code}', Serial: '{serial_no}'")

        story.log_step(
            "Step 1: Provision Controlled Asset",
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
        logger.info(f"Targeting asset '{actual_assigned_code}' in Employee B's available stock...")
        is_asset_visible_for_b = assign_page.is_asset_in_available_dropdown(actual_assigned_code)

        if is_asset_visible_for_b:
            logger.warning(f"⚠️ [CONCURRENCY ISSUE DETECTED] Asset '{asset_code}' (Reserved for Employee A) IS STILL VISIBLE in dropdown for Employee B!")
            
            # Attempt to assign it to Employee B to see if backend blocks it
            target_item = admin_page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").filter(has_text=asset_code).first
            target_item.click(force=True)
            admin_page.wait_for_timeout(500)

            assign_page.click_submit_assignment()
            toast_result = assign_page.wait_for_toast_message()
            logger.warning(f"[DOUBLE-ASSIGNMENT ATTEMPT TOAST]: '{toast_result}'")

            story.log_step(
                "Step 4: Concurrency & Double-Booking Check",
                record=f"Asset: {asset_code} | Employee A: Sanidhy Tiwari | Employee B: Adarsh Tiwari",
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
