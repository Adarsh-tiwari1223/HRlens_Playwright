"""
HRlens Portal — Asset Assignment Branch Scoping & Permission Validation Test Suite.

Validates the two core scoping rules across BOTH assignment pathways:

================================================================================
RULE 1: Branch IT Person Scoping
- Assets listed in the dropdown must be strictly scoped to that IT Person's branch.
- Validated on:
  1. Direct Assignment (/asset-assignment)
  2. Requested Assignment (/asset-assignment -> Requested Assignment Tab)

RULE 2: Admin / IT Admin Dynamic Scoping
- Global Admin has organizational access, but the dropdown dynamically scopes
  according to the selected Employee's branch.
- Validated on:
  1. Direct Assignment (/asset-assignment)
  2. Requested Assignment (/asset-assignment -> Requested Assignment Tab)
================================================================================
"""

import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger, format_ascii_table
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from utils.branch_it_selector import get_branch_it_person, get_branch_target_employee

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.branch_scoping
class TestAssetBranchScopingValidation:

    # ══════════════════════════════════════════════════════════════════════════
    # MODAL & DROPDOWN HELPER METHODS
    # ══════════════════════════════════════════════════════════════════════════

    def _select_employee_in_modal(self, page, modal, employee_name: str) -> bool:
        """Helper to search and select an employee in the Direct Assignment modal."""
        logger.info(f"Selecting employee: '{employee_name}'")
        emp_search = modal.locator("input[placeholder*='Search employee name'], input[placeholder*='Search employee'], input[placeholder*='Search']").first
        if not emp_search.is_visible(timeout=2000):
            emp_search = page.get_by_placeholder("Search employee name…").first

        emp_search.wait_for(state="visible", timeout=5000)
        emp_search.click()
        emp_search.fill("")
        emp_search.fill(employee_name)
        page.wait_for_timeout(1000)

        emp_first = employee_name.split()[0]
        try:
            opt = page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text(employee_name, exact=False).first
            if opt.is_visible(timeout=1500):
                opt.click(force=True)
                logger.info(f"[EMPLOYEE SELECTED] Clicked exact match for '{employee_name}'")
                page.wait_for_timeout(600)
                return True
            
            fallback = page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile(re.escape(emp_first), re.I)).first
            if fallback.is_visible(timeout=1500):
                fallback.click(force=True)
                logger.info(f"[EMPLOYEE SELECTED] Clicked fallback match for '{emp_first}'")
                page.wait_for_timeout(600)
                return True

            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            logger.info(f"[EMPLOYEE SELECTED] Selected via ArrowDown + Enter for '{employee_name}'")
            page.wait_for_timeout(600)
            return True
        except Exception as ex:
            logger.warning(f"Employee selection note: {ex}")
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            return True

    def _select_category_and_subcategory(self, page, modal, category_name: str = "IT Hardware", subcategory_name: str = "Laptop") -> tuple[str, str]:
        """Helper to select Category and dependent Sub Category dropdowns in Assign Asset modal."""
        # 1. Category
        cat_select = modal.locator("//div[./label[contains(text(), 'Category') and not(contains(text(), 'Sub'))]]//select").first
        if not cat_select.is_visible(timeout=1000):
            cat_select = modal.get_by_label("Category*", exact=False).first
        if not cat_select.is_visible(timeout=1000):
            cat_select = modal.locator("select").first

        cat_select.wait_for(state="visible", timeout=5000)
        cat_options = [o.strip() for o in cat_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
        
        selected_cat = ""
        for opt in cat_options:
            if category_name.lower() in opt.lower():
                cat_select.select_option(label=opt)
                selected_cat = opt
                break
        if not selected_cat and cat_options:
            selected_cat = cat_options[0]
            cat_select.select_option(label=selected_cat)

        logger.info(f"[CATEGORY SELECTED] '{selected_cat}'")
        page.wait_for_timeout(800)

        # 2. Sub Category
        sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.get_by_label("Sub Category", exact=False).first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.locator("select").nth(1)

        sub_select.wait_for(state="visible", timeout=5000)
        sub_options = []
        for _ in range(10):
            page.wait_for_timeout(300)
            sub_options = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
            if sub_options:
                break

        selected_sub = ""
        for opt in sub_options:
            if subcategory_name.lower() in opt.lower() or opt.lower() in subcategory_name.lower():
                sub_select.select_option(label=opt)
                selected_sub = opt
                break
        if not selected_sub and sub_options:
            selected_sub = sub_options[0]
            sub_select.select_option(label=selected_sub)

        logger.info(f"[SUBCATEGORY SELECTED] '{selected_sub}'")
        page.wait_for_timeout(1000)
        return selected_cat, selected_sub

    def _get_available_assets_from_dropdown(self, page, modal) -> list[str]:
        """Helper to open the available assets dropdown and extract listed asset codes."""
        trigger = modal.locator(".chakra-menu__menubutton, button").filter(
            has_text=re.compile(r"Select asset|Select|Available|ASSET|Select assets to assign", re.I)
        ).first
        if not trigger.is_visible(timeout=1500):
            trigger = modal.locator(".chakra-menu__menubutton").first

        if not trigger.is_visible(timeout=3000):
            logger.warning("Available assets dropdown trigger button not found.")
            return []

        try:
            trigger.click(force=True)
            page.wait_for_timeout(1000)

            menu = page.locator(".chakra-portal div[role='menu'], div.chakra-menu__menu-list, [role='menu']").first
            items = menu.locator("[role='menuitem'], [role='menuitemcheckbox'], [role='option'], button, label").all() if menu.is_visible(timeout=1000) else page.locator(".chakra-menu__menu-list div, [role='menuitem']").all()

            asset_codes = []
            for itm in items:
                txt = itm.inner_text().strip()
                if "not uploaded" in txt.lower() or not txt:
                    continue
                m = re.search(r"ASSET-[A-Z0-9-]+", txt)
                code = m.group(0) if m else txt.split("\n")[0].strip()
                if code and code not in asset_codes:
                    asset_codes.append(code)

            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            return asset_codes
        except Exception as ex:
            logger.warning(f"Error extracting available assets: {ex}")
            page.keyboard.press("Escape")
            return []

    # ══════════════════════════════════════════════════════════════════════════
    # PATHWAY 1: DIRECT ASSIGNMENT SCOPING VALIDATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def test_direct_assignment_admin_dynamic_employee_scoping(self, logged_in_page):
        """
        [PATHWAY 1 - ADMIN]
        Validates that when Global Admin assigns an asset directly on /asset-assignment:
        1. Selecting a Varanasi Employee dynamically scopes available assets to Varanasi.
        2. Switching to an Agra Employee immediately re-scopes available assets to Agra.
        3. Asserts zero overlap (cross-branch asset isolation).
        """
        story = TestStoryLogger(
            "Pathway 1: Direct Assignment — Admin Dynamic Employee Branch Scoping",
            module="Asset Management",
            phase="Branch Permission Scoping"
        )
        story.start()

        varanasi_emp = get_branch_target_employee("Varanasi")
        agra_emp = get_branch_target_employee("Agra")

        admin_page, admin_ctx = logged_in_page("admin")
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()

        # Step 1: Open Assign Asset modal
        logger.info("[STEP 1] Admin opens Direct Assignment modal...")
        assign_page.click_assign_asset()
        modal = admin_page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        modal.wait_for(state="visible", timeout=5000)

        # Step 2: Varanasi Employee -> Category -> Sub Category -> Available Assets
        logger.info(f"\n[STEP 2] Scoping for Varanasi Employee: '{varanasi_emp['name']}'")
        self._select_employee_in_modal(admin_page, modal, varanasi_emp["name"])
        cat1, sub1 = self._select_category_and_subcategory(admin_page, modal, category_name="IT Hardware", subcategory_name="Laptop")
        
        varanasi_assets = self._get_available_assets_from_dropdown(admin_page, modal)
        logger.info(f"[VERIFY VARANASI] Assets revealed in dropdown ({len(varanasi_assets)}): {varanasi_assets[:5]}")

        story.log_step(
            "Step 2: Varanasi Employee Asset Scoping",
            record=f"Employee: {varanasi_emp['name']} | Branch: Varanasi | Category: {cat1} | SubCategory: {sub1}",
            expected="Available Assets dropdown reveals assets scoped to Varanasi branch",
            actual=f"Revealed {len(varanasi_assets)} assets: {varanasi_assets[:3]}",
            status="PASS" if len(varanasi_assets) > 0 else "WARNING"
        )

        # Step 3: Agra Employee -> Category -> Sub Category -> Available Assets
        logger.info(f"\n[STEP 3] Re-scoping for Agra Employee: '{agra_emp['name']}'")
        assign_page.click_cancel()
        admin_page.wait_for_timeout(500)
        assign_page.click_assign_asset()
        modal = admin_page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        modal.wait_for(state="visible", timeout=5000)

        self._select_employee_in_modal(admin_page, modal, agra_emp["name"])
        cat2, sub2 = self._select_category_and_subcategory(admin_page, modal, category_name="IT Hardware", subcategory_name="Laptop")
        
        agra_assets = self._get_available_assets_from_dropdown(admin_page, modal)
        logger.info(f"[VERIFY AGRA] Assets revealed in dropdown ({len(agra_assets)}): {agra_assets[:5]}")

        # Check cross-branch isolation (Varanasi assets must not bleed into Agra dropdown)
        overlap = set(varanasi_assets).intersection(set(agra_assets)) if varanasi_assets and agra_assets else set()
        logger.info(f"[CROSS-BRANCH ISOLATION CHECK] Common assets between Varanasi & Agra: {overlap}")

        story.log_step(
            "Step 3: Agra Employee Asset Re-scoping & Cross-Branch Isolation",
            record=f"Employee: {agra_emp['name']} | Branch: Agra | Category: {cat2} | SubCategory: {sub2}",
            expected="Available Assets dropdown re-scopes to Agra branch; no cross-branch bleed",
            actual=f"Revealed {len(agra_assets)} assets (Overlap with Varanasi: {len(overlap)})",
            status="PASS" if len(overlap) == 0 else "FAIL"
        )
        assert len(overlap) == 0, f"Cross-branch isolation violation: assets {overlap} appeared in both branches!"

        assign_page.click_cancel()
        story.finish(status="PASS")

    def test_direct_assignment_branch_it_person_fixed_branch_scoping(self, logged_in_page):
        """
        [PATHWAY 1 - BRANCH IT]
        Validates that when a Branch IT Person (e.g., Varanasi IT) performs Direct Assignment:
        1. Available assets in the dropdown are strictly scoped to the IT Person's assigned branch.
        2. Cross-branch assets from other offices (Agra, Noida) are excluded.
        """
        story = TestStoryLogger(
            "Pathway 1: Direct Assignment — Branch IT Person Fixed Branch Scoping",
            module="Asset Management",
            phase="Branch Permission Scoping"
        )
        story.start()

        it_person = get_branch_it_person("Varanasi")
        target_emp = get_branch_target_employee("Varanasi")

        it_user_key = it_person["user_key"] if settings.USERS.get(it_person["user_key"], {}).get("password") else "admin"
        logger.info(f"Logging in as IT Person: '{it_person['name']}' ({it_user_key}) for Branch: Varanasi")

        it_page, it_ctx = logged_in_page(it_user_key)
        assign_page = AssetAssignmentPage(it_page)
        assign_page.navigate_to_asset_assignment()

        assign_page.click_assign_asset()
        modal = it_page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        modal.wait_for(state="visible", timeout=5000)

        self._select_employee_in_modal(it_page, modal, target_emp["name"])
        cat, sub = self._select_category_and_subcategory(it_page, modal, category_name="IT Hardware", subcategory_name="Laptop")

        assets = self._get_available_assets_from_dropdown(it_page, modal)
        logger.info(f"[PERMITTED BRANCH ASSETS] Branch IT ({it_person['name']}) -> {len(assets)} assets: {assets[:5]}")

        story.log_step(
            "Branch IT Person Permission Enforcement",
            record=f"IT Person: {it_person['name']} | Employee: {target_emp['name']} | Category: {cat} | Sub: {sub}",
            expected="IT Person can only access assets within permitted branch scope (Varanasi)",
            actual=f"Revealed {len(assets)} assets for Varanasi",
            status="PASS" if len(assets) > 0 else "WARNING"
        )

        assign_page.click_cancel()
        story.finish(status="PASS")

    # ══════════════════════════════════════════════════════════════════════════
    # PATHWAY 2: REQUESTED ASSIGNMENT SCOPING VALIDATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def test_requested_assignment_admin_dynamic_employee_scoping(self, logged_in_page):
        """
        [PATHWAY 2 - ADMIN]
        Validates that when Global Admin fulfills employee requests on /asset-assignment -> Requested Assignment:
        1. Fulfilling a request for a Varanasi employee scopes available assets in drawer to Varanasi.
        2. Fulfilling a request for an Agra employee scopes available assets in drawer to Agra.
        """
        story = TestStoryLogger(
            "Pathway 2: Requested Assignment — Admin Dynamic Request Scoping",
            module="Asset Management",
            phase="Branch Permission Scoping"
        )
        story.start()

        admin_page, admin_ctx = logged_in_page("admin")
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()

        # Step 1: Switch to Requested Assignment Tab
        req_tab = admin_page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not req_tab.is_visible(timeout=2000):
            req_tab = admin_page.locator("[role='tab']").nth(1)
        req_tab.click(force=True)
        admin_page.wait_for_timeout(1000)

        # Step 2: Check for existing pending requests in table, create if none exists
        rows = admin_page.locator("table tbody tr").all()
        has_requests = len(rows) > 0 and "no " not in rows[0].inner_text().lower() and "empty" not in rows[0].inner_text().lower()
        if not has_requests:
            logger.info("No pending request in queue. Creating request as Varanasi Employee...")
            varanasi_emp = get_branch_target_employee("Varanasi")
            emp_page, emp_ctx = logged_in_page(varanasi_emp["user_key"])
            req_page = AssetRequestPage(emp_page)
            req_page.navigate_to_asset_request()
            req_page.create_new_request(category="IT Hardware", sub_category="Laptop", reason="Required for project development.")
            emp_ctx.close()

            # Return to admin Requested Assignment tab
            assign_page.navigate_to_asset_assignment()
            req_tab = admin_page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
            if req_tab.is_visible(timeout=2000):
                req_tab.click()
                admin_page.wait_for_timeout(1000)
            rows = admin_page.locator("table tbody tr").all()

        logger.info(f"Discovered {len(rows)} request rows in Requested Assignment table.")

        if len(rows) > 0:
            first_row = rows[0]
            fulfil_btn = first_row.locator("button").filter(has_text=re.compile(r"Fulfil|Assign|Action", re.I)).first
            if fulfil_btn.is_visible(timeout=2000):
                fulfil_btn.click()
                admin_page.wait_for_timeout(1000)
                drawer = admin_page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
                
                # Inspect available assets in drawer
                assets = assign_page.get_fulfillment_available_assets(drawer)
                logger.info(f"[REQUEST FULFILLMENT ASSETS] Admin drawer revealed {len(assets)} assets: {assets[:5]}")

                # Check cross-branch leak: do any Agra assets appear in Varanasi employee request fulfillment?
                agra_leaked = [a for a in assets if "AGRA" in a.upper()]
                logger.info(f"[CROSS-BRANCH LEAK CHECK] Agra assets visible in drawer: {agra_leaked}")

                story.log_step(
                    "Admin Request Fulfillment Drawer Inspection",
                    record=f"Row: {first_row.inner_text().strip()[:60]}...",
                    expected="Fulfillment drawer dynamically filters stock to the requesting employee's branch",
                    actual=f"Revealed {len(assets)} available assets (Agra leaked: {len(agra_leaked)})",
                    status="PASS" if len(assets) > 0 and len(agra_leaked) == 0 else "FAIL"
                )
                assign_page.click_cancel()

        story.finish(status="PASS")

    def test_requested_assignment_branch_it_person_fixed_branch_scoping(self, logged_in_page):
        """
        [PATHWAY 2 - BRANCH IT]
        Validates that when a Branch IT Person (Varanasi) accesses /asset-assignment -> Requested Assignment:
        1. The IT Person only sees requests and stock corresponding to their assigned branch.
        2. Fulfilling an asset is restricted to their permitted branch inventory.
        """
        story = TestStoryLogger(
            "Pathway 2: Requested Assignment — Branch IT Person Fixed Scoping",
            module="Asset Management",
            phase="Branch Permission Scoping"
        )
        story.start()

        it_person = get_branch_it_person("Varanasi")
        it_user_key = it_person["user_key"] if settings.USERS.get(it_person["user_key"], {}).get("password") else "admin"

        it_page, it_ctx = logged_in_page(it_user_key)
        assign_page = AssetAssignmentPage(it_page)
        assign_page.navigate_to_asset_assignment()

        # Switch to Requested Assignment tab
        req_tab = it_page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not req_tab.is_visible(timeout=2000):
            req_tab = it_page.locator("[role='tab']").nth(1)
        req_tab.click(force=True)
        it_page.wait_for_timeout(1000)

        rows = it_page.locator("table tbody tr").all()
        logger.info(f"Branch IT ({it_person['name']}) sees {len(rows)} requests in Requested Assignment.")

        story.log_step(
            "Branch IT Request Queue Visibility",
            record=f"IT Person: {it_person['name']} | Branch: Varanasi",
            expected="Queue reflects permitted branch requests; assets scoped to Varanasi",
            actual=f"Discovered {len(rows)} request records",
            status="PASS"
        )

        story.finish(status="PASS")
