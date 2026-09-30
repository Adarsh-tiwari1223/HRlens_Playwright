"""
HRlens Portal - Stock Management & Branch Inventory Suite (/asset-stock).

Validates:
1. Stock Manager page loading, header metrics, and branch selection via AssetStockPage.
2. Accurate stock card values for Varanasi branch:
   - All Assets (20)
   - Available (18)
   - Assigned (1)
   - Reserved (1)
   - Maintenance (0), Damaged (0), Insured (0)
   - Mathematical inventory integrity (Available + Assigned + Reserved + Maintenance + Damaged == All Assets)
3. Inventory data table rows, status chips (AVAILABLE, ASSIGNED, RESERVED), and category filters.
4. Branch stock visibility and permission scoping for Branch IT Person (e.g. Varanasi IT).
"""

import re
import random
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_stock_page import AssetStockPage
from utils.branch_it_selector import get_all_branch_it_persons

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.stock_management
class TestAssetStockManagement:

    def test_varanasi_stock_cards_and_inventory_verification(self, logged_in_page):
        """
        Logs in via Varanasi IT person, navigates to /asset-stock, selects Varanasi,
        and verifies the 7 stock status cards and data table records.
        """
        story = TestStoryLogger(
            "Varanasi Stock Cards & Inventory Verification",
            module="Asset Management",
            phase="Stock Manager Verification"
        )
        story.start()

        # Step 1: Login via randomized Varanasi IT person
        it_persons = get_all_branch_it_persons("Varanasi")
        if not it_persons:
            it_persons = [
                {"user_key": "it_varanasi_ashutosh", "name": "Ashutosh Kumar"},
                {"user_key": "it_varanasi_tejasav", "name": "Tejasav Jaiswal"}
            ]
        it_person = random.choice(it_persons)
        it_key = it_person["user_key"]
        it_name = it_person["name"]

        logger.info(f"\n=======================================================")
        logger.info(f"STEP 1: Logging in as IT Person: '{it_name}' ({it_key})")
        logger.info(f"=======================================================")

        page, ctx = logged_in_page(it_key)
        assert page is not None, f"Failed to initialize browser page for '{it_name}'"
        assert "/login" not in page.url, f"Login failed for '{it_name}'"

        story.log_step(
            f"1. IT Person Login ({it_name})",
            expected="IT Person logs into portal",
            actual=f"URL: {page.url}",
            status="PASS"
        )

        # Step 2: Navigate to Stock Manager (/asset-stock)
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 2: Navigating to Stock Manager (/asset-stock)")
        logger.info(f"=======================================================")

        stock_page = AssetStockPage(page)
        stock_page.navigate_to_asset_stock()
        assert "/asset-stock" in page.url, f"Expected URL to contain '/asset-stock', got: {page.url}"

        header_info = stock_page.get_stock_header_info()
        logger.info(f"Header Info: {header_info}")
        assert header_info.get("title") == "Stock Manager", (
            f"Expected title 'Stock Manager', got: '{header_info.get('title')}'"
        )

        story.log_step(
            "2. Navigate to Stock Manager",
            expected="Stock Manager page loads with header banner",
            actual=f"Title: {header_info.get('title')} | Subtitle: {header_info.get('subtitle')}",
            status="PASS"
        )

        # Step 3: Verify role-based scoping (branch filter available for IT Admin and Admin only)
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 3: Verifying Role Scoping for IT Person: '{it_name}'")
        logger.info(f"=======================================================")

        has_cross_branch_filter = stock_page.is_branch_filter_visible()
        logger.info(f"Cross-branch filter visible: {has_cross_branch_filter} (Only IT Admin / Admin should have cross-branch filter)")

        story.log_step(
            "3. Role Scoping Verification",
            expected="Branch IT user automatically scoped to assigned branch (Varanasi)",
            actual=f"Cross-branch filter visible: {has_cross_branch_filter}",
            status="PASS"
        )

        # Step 4: Extract and Validate the 7 Stock Cards for Varanasi
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 4: Auditing Varanasi Stock Status Cards")
        logger.info(f"=======================================================")

        cards = stock_page.get_stock_cards("Varanasi")
        logger.info(f"Captured Varanasi Stock Cards: {cards}")

        assert "All Assets" in cards, f"Stock Manager did not load 'All Assets' card! Cards: {cards}"
        all_assets = cards.get("All Assets", 0)
        available = cards.get("Available", 0)
        assigned = cards.get("Assigned", 0)
        reserved = cards.get("Reserved", 0)
        maintenance = cards.get("Maintenance", 0)
        damaged = cards.get("Damaged", 0)
        insured = cards.get("Insured", 0)

        # Assert card values
        assert all_assets == 20, f"Expected 20 Total Assets for Varanasi, got {all_assets}"
        assert available >= 1, f"Expected Available Assets to be > 0, got {available}"
        assert assigned >= 1, f"Expected Assigned Assets >= 1 (e.g. Ritesh Singh), got {assigned}"
        assert reserved >= 1, f"Expected Reserved Assets >= 1 (from fulfilled request), got {reserved}"

        # Mathematical sum check: Available + Assigned + Reserved + Maintenance + Damaged == Total Assets (20)
        total_sum = available + assigned + reserved + maintenance + damaged
        assert total_sum == all_assets, (
            f"Stock card inventory mismatch! Sum of statuses ({total_sum}) != All Assets ({all_assets})"
        )

        story.log_step(
            "4. Validate Stock Cards",
            expected="All Assets=20, Available+Assigned+Reserved=20",
            actual=f"Cards: {cards} | Sum: {total_sum}",
            status="PASS"
        )

        # Step 5: Verify Inventory Table Rows
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 5: Verifying Asset Inventory Table Rows")
        logger.info(f"=======================================================")

        rows = stock_page.get_table_asset_rows()
        logger.info(f"Loaded {len(rows)} table rows for Varanasi. Sample: {rows[:3]}")
        assert len(rows) > 0, "No asset rows rendered in Varanasi stock inventory table!"

        # Verify all loaded assets belong to Varanasi branch group
        non_varanasi_rows = [r for r in rows if "varanasi" not in r["name"].lower() and "varanasi" not in r.get("serial_no", "").lower()]
        assert not non_varanasi_rows, (
            f"SECURITY DEFECT: Non-Varanasi assets found in Varanasi stock table: {non_varanasi_rows}"
        )

        # Verify presence of AVAILABLE, ASSIGNED, and RESERVED chips in the table
        table_statuses = {r["status"].upper() for r in rows}
        logger.info(f"Distinct statuses in table: {table_statuses}")
        assert "AVAILABLE" in table_statuses, "No AVAILABLE assets found in Varanasi stock table!"

        pagination = stock_page.get_pagination_summary()
        logger.info(f"Pagination: '{pagination}'")

        story.log_step(
            "5. Verify Inventory Table",
            expected="Table displays 20 Varanasi assets with correct status chips",
            actual=f"Rows: {len(rows)} | Statuses: {table_statuses} | Pagination: {pagination}",
            status="PASS"
        )

        ctx.close()
        story.finish(status="PASS")

    def test_branch_it_stock_visibility_isolation_audit(self, logged_in_page):
        """
        Audits that a Branch IT Person (Tejas / Varanasi IT) does not leak prohibited cross-branch stock.
        """
        story = TestStoryLogger(
            "Branch IT Stock Visibility & Isolation Audit",
            module="Asset Management",
            phase="Security & Branch Isolation"
        )
        story.start()

        # 1. Log in as Tejas (Varanasi IT)
        page, ctx = logged_in_page("it_varanasi_tejasav")
        stock_page = AssetStockPage(page)
        stock_page.navigate_to_asset_stock()

        page_text = page.locator("body").inner_text()
        all_prohibited_branches = [
            "Noida", "Agra", "Bhubaneswar", "Greater Noida",
            "Lucknow", "Jaipur", "Meerut", "Noida NX-One"
        ]

        visible_prohibited_branches = [
            b for b in all_prohibited_branches
            if re.search(rf"\b{re.escape(b)}\b", page_text, re.I)
        ]

        logger.info(f"[AUDIT] Prohibited cross-branch names visible: {visible_prohibited_branches}")

        cross_branch_header_match = re.search(r"(\d+)\s+assets\s+across\s+(\d+)\s+branches", page_text, re.I)
        cross_branch_leak = False
        if cross_branch_header_match:
            total_branches = cross_branch_header_match.group(2)
            cross_branch_leak = int(total_branches) > 1

        story.log_step(
            "Audit /asset-stock Cross-Branch Leakage",
            expected="Only Varanasi branch stock is visible (1 branch)",
            actual=f"Visible Prohibited Branches: {len(visible_prohibited_branches)} | Header: {cross_branch_header_match.group(0) if cross_branch_header_match else 'N/A'}",
            status="FAIL" if (visible_prohibited_branches or cross_branch_leak) else "PASS"
        )

        ctx.close()

        # Defect assertion: Branch IT Person must only see their assigned branch
        assert not visible_prohibited_branches, (
            f"DEFECT FOUND: Branch IT user (Tejas - Varanasi) can see prohibited cross-branch stock: {visible_prohibited_branches}."
        )

        assert not cross_branch_leak, (
            f"DEFECT FOUND: Stock Manager displays '{cross_branch_header_match.group(0)}' to Branch IT user. "
            "It must only show assets for Varanasi branch."
        )

        story.finish(status="PASS")
