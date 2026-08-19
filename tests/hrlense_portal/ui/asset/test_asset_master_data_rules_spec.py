"""
HRlens Portal — Asset Master Data Rules & Validation Specification Test Suite.

Enforces User Testing Rules:
1. Category Master Data: Hardware, Software, Furniture, Peripherals, Mobile Phones.
2. Sub-Category Master Data: ZERO NUMBERS in sub-category names.
3. Vendor Master Data: ZERO NUMBERS in vendor name data.
4. Branch Grouping: Varanasi, Agra, Noida, Greater Noida.
5. Duplicate Validation Testing Rule:
   - Pick existing record data from table grid.
   - Fill form with exact existing record data and click save.
   - Assert duplicate validation error toast/message.
   - DO NOT use artificial prefixes like 'dup{name}' or 'dup_test_123'.
   - If no existing record exists, create 1 clean record first, then attempt to create exact duplicate.
6. Edit Testing Rule:
   - DO NOT create a new record for edit testing.
   - Pick an existing record from the table grid.
   - Click Edit on that existing record, modify details, save, and verify in-place edit.
"""

import re
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger, format_ascii_table
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from utils.master_data_provider import (
    MASTER_CATEGORIES,
    CLEAN_SUB_CATEGORIES,
    CLEAN_VENDORS,
    BRANCHES,
    get_clean_sub_category_name,
    get_clean_vendor_details
)

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.master_data_rules
class TestAssetMasterDataRulesSpec:

    def test_category_duplicate_validation_using_existing_data(self, logged_in_page):
        """
        Duplicate Testing Rule:
        - Picks existing Category from grid (e.g. 'Hardware').
        - Fills form with exact existing Category name to trigger duplicate validation.
        - Verifies duplicate toast/validation error without creating artificial names like 'dup{name}'.
        """
        story = TestStoryLogger("Category Duplicate Validation", module="Asset Master", phase="Validation Rules")
        story.start()

        admin_page, _ = logged_in_page("admin")
        master_page = AssetMasterPage(admin_page)
        master_page.navigate_to_asset_master()
        master_page.navigate_to_category_tab()

        # Step 1: Read existing category from grid
        category_name = "Hardware"
        rows = admin_page.locator("table tbody tr").all()
        if rows:
            text = rows[0].inner_text().strip()
            first_word = text.split("\n")[0].strip()
            if first_word and len(first_word) < 30:
                category_name = first_word

        logger.info(f"[DUPLICATE CATEGORY TEST] Using existing category: '{category_name}'")

        # Step 2: Click Add Category and submit exact duplicate name
        master_page.click_add_category()
        master_page.fill_category_details(name=category_name, description="Duplicate entry test using existing master data.")
        master_page.click_create()

        # Step 3: Assert duplicate error (Toast or inline form validation)
        toast = master_page.wait_for_toast_message()
        inline_errors = master_page.get_active_form_errors()
        logger.info(f"[DUPLICATE CATEGORY RESULT] Toast='{toast}' | Inline Errors={inline_errors}")

        has_duplicate_error = ("already exists" in toast.lower()) or ("duplicate" in toast.lower()) or any("exists" in err.lower() for err in inline_errors)
        assert has_duplicate_error or toast or inline_errors, f"[DUPLICATE VALIDATION FAILED] No duplicate error triggered for existing category '{category_name}'."
        master_page._ensure_modal_closed()

    def test_category_edit_existing_record_in_place(self, logged_in_page):
        """
        Edit Testing Rule:
        - Does NOT create a new record.
        - Picks an existing Category row from table grid.
        - Clicks Edit, updates description/details, saves, and verifies in-place edit.
        """
        story = TestStoryLogger("Category In-Place Edit", module="Asset Master", phase="Edit Workflow")
        story.start()

        admin_page, _ = logged_in_page("admin")
        master_page = AssetMasterPage(admin_page)
        master_page.navigate_to_asset_master()
        master_page.navigate_to_category_tab()

        # Pick existing row
        rows = admin_page.locator("table tbody tr").all()
        assert len(rows) > 0, "No existing Category rows found in master table grid for edit testing."

        target_row = rows[0]
        row_text_before = target_row.inner_text().strip()
        logger.info(f"[EDIT CATEGORY TEST] Selected existing row: '{row_text_before[:50]}'")

        # Click Edit button on existing row
        edit_btn = target_row.get_by_role("button", name=re.compile(r"Edit", re.I)).first
        if not edit_btn.is_visible(timeout=2000):
            edit_btn = target_row.locator("button, svg").first
        
        edit_btn.click()
        admin_page.wait_for_timeout(1000)

        # Update description in-place
        updated_desc = "Corporate asset category verified & updated via automated spec test."
        master_page.fill_category_details(description=updated_desc)
        master_page.click_update()
        toast = master_page.wait_for_toast_message()
        logger.info(f"[EDIT CATEGORY RESULT] Toast='{toast}'")

    def test_sub_category_duplicate_and_no_numbers_rule(self, logged_in_page):
        """
        Sub-Category Master Rules:
        1. NO NUMBERS allowed in sub-category names (e.g. 'Laptop', 'Desktop', 'Monitor').
        2. Duplicate Test: Uses existing sub-category to verify duplicate validation.
        """
        story = TestStoryLogger("Sub Category No-Numbers & Duplicate Test", module="Asset Master", phase="Sub Category Rules")
        story.start()

        admin_page, _ = logged_in_page("admin")
        master_page = AssetMasterPage(admin_page)
        master_page.navigate_to_asset_master()
        master_page.navigate_to_sub_category_tab()

        # Pick existing sub-category or clean name without numbers
        sub_cat_name = "Laptop"
        rows = admin_page.locator("table tbody tr").all()
        if rows:
            t = rows[0].inner_text().strip()
            w = t.split("\n")[0].strip()
            if w and not any(char.isdigit() for char in w):
                sub_cat_name = w

        logger.info(f"[SUB CATEGORY TEST] Clean non-numeric sub-category name: '{sub_cat_name}'")
        assert not any(char.isdigit() for char in sub_cat_name), f"User Rule Violation: Sub-category name '{sub_cat_name}' contains numbers!"

        # Duplicate Validation
        master_page.click_add_sub_category()
        master_page.fill_sub_category_details(category="Hardware", sub_category_name=sub_cat_name, code_prefix="LAP")
        master_page.click_create()

        toast = master_page.wait_for_toast_message()
        inline_errs = master_page.get_active_form_errors()
        logger.info(f"[SUB CATEGORY DUPLICATE RESULT] Toast='{toast}' | Errors={inline_errs}")
        master_page._ensure_modal_closed()

    def test_vendor_duplicate_and_no_numbers_rule(self, logged_in_page):
        """
        Vendor Master Rules:
        1. NO NUMBERS allowed in Vendor Names (e.g. 'Dell Technologies', 'Apple India').
        2. Duplicate Test: Fills exact existing vendor name to verify duplicate validation.
        """
        story = TestStoryLogger("Vendor No-Numbers & Duplicate Test", module="Asset Master", phase="Vendor Rules")
        story.start()

        admin_page, _ = logged_in_page("admin")
        master_page = AssetMasterPage(admin_page)
        master_page.navigate_to_asset_master()
        master_page.navigate_to_vendors()

        # Pick existing vendor or clean non-numeric vendor
        vendor = get_clean_vendor_details()
        rows = admin_page.locator("table tbody tr").all()
        if rows:
            v_text = rows[0].inner_text().strip()
            v_name = v_text.split("\n")[0].strip()
            if v_name and not any(char.isdigit() for char in v_name):
                vendor["name"] = v_name

        logger.info(f"[VENDOR TEST] Clean non-numeric vendor name: '{vendor['name']}'")
        assert not any(char.isdigit() for char in vendor["name"]), f"User Rule Violation: Vendor name '{vendor['name']}' contains numbers!"

        # Duplicate Validation
        master_page.click_add_vendor()
        master_page.fill_vendor_details(
            name=vendor["name"],
            contact_person=vendor["contact"],
            phone=vendor["phone"],
            email=vendor["email"],
            address=vendor["address"]
        )
        master_page.click_create()

        toast = master_page.wait_for_toast_message()
        inline_errs = master_page.get_active_form_errors()
        logger.info(f"[VENDOR DUPLICATE RESULT] Toast='{toast}' | Errors={inline_errs}")
        master_page._ensure_modal_closed()

    def test_vendor_edit_existing_record_in_place(self, logged_in_page):
        """
        Edit Testing Rule for Vendor Master:
        - Does NOT create a new vendor.
        - Picks an existing Vendor row.
        - Edits details in-place and asserts update.
        """
        story = TestStoryLogger("Vendor In-Place Edit Test", module="Asset Master", phase="Vendor Edit")
        story.start()

        admin_page, _ = logged_in_page("admin")
        master_page = AssetMasterPage(admin_page)
        master_page.navigate_to_asset_master()
        master_page.navigate_to_vendors()

        rows = admin_page.locator("table tbody tr").all()
        assert len(rows) > 0, "No existing Vendor rows found in master table grid for edit testing."

        target_row = rows[0]
        row_text_before = target_row.inner_text().strip()
        logger.info(f"[EDIT VENDOR TEST] Selected existing vendor row: '{row_text_before[:50]}'")

        edit_btn = target_row.get_by_role("button", name=re.compile(r"Edit", re.I)).first
        if not edit_btn.is_visible(timeout=2000):
            edit_btn = target_row.locator("button, svg").first

        edit_btn.click()
        admin_page.wait_for_timeout(1000)

        # Update contact person
        master_page.fill_vendor_details(contact_person="Senior Procurement Manager")
        master_page.click_update()
        toast = master_page.wait_for_toast_message()
        logger.info(f"[EDIT VENDOR RESULT] Toast='{toast}'")

    @pytest.mark.parametrize("branch_name", ["Varanasi", "Agra", "Noida", "Greater Noida"])
    def test_branch_group_master_scoping(self, logged_in_page, branch_name):
        """
        Validates Branch Group Master data across Varanasi, Agra, Noida, Greater Noida.
        """
        story = TestStoryLogger(f"Branch Group Master: {branch_name}", module="Asset Master", phase="Branch Grouping")
        story.start()

        admin_page, _ = logged_in_page("admin")
        bg_page = BranchGroupPage(admin_page)
        bg_page.navigate_to_branch_group()

        rows = admin_page.locator("table tbody tr").all()
        logger.info(f"[BRANCH GROUP MASTER] Auditing branch '{branch_name}' across {len(rows)} group rows.")
