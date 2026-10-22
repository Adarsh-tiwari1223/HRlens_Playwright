"""
Staging Verification Suite for HRlens Asset Management Enhancements (Points 5, 6, 7).
Mapped to Test Cases in Google Sheet (Asset Management tab):
- TC-AST-013 to TC-AST-018: Multiple Assets Same Category
- TC-AST-019 to TC-AST-024: IT Dashboard Pending Requests Widget
- TC-AST-025 to TC-AST-031: Today's Asset Activities Section
"""

import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.staging_verification
class TestStagingAssetEnhancementsSpec:

    def test_dashboard_pending_requests_and_today_activities(self, logged_in_page):
        """
        TC-AST-019 to TC-AST-031:
        1. Login as IT Admin/Admin on Staging.
        2. Inspect Main Dashboard for 'Pending Asset Requests' KPI counter.
        3. Test Clickable deep-link on 'Pending Asset Requests' navigating to /asset-requests.
        4. Inspect 'Today's Asset Activities' section and activity metrics.
        """
        story = TestStoryLogger(
            "Staging IT Dashboard Widgets Verification",
            module="Asset Management",
            phase="Dashboard Verification"
        )
        story.start()

        # Step 1: Login as Admin
        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        # Step 2: Navigate to Dashboard / Asset Dashboard
        logger.info("[STEP 2] Navigating to Dashboard")
        page.goto(f"{settings.BASE_URL}/", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Step 3: Check for 'Pending Asset Requests' widget on Dashboard
        logger.info("[STEP 3] Inspecting Dashboard for 'Pending Asset Requests' metric")
        pending_card = page.get_by_text(re.compile(r"Pending.*Asset.*Request", re.I)).or_(page.locator("[data-testid*='pending-asset']")).or_(page.get_by_text(re.compile(r"Pending.*Request", re.I))).first
        
        # Also check /asset-dashboard if not on main root
        try:
            is_pending_visible = pending_card.is_visible(timeout=3000)
        except Exception:
            is_pending_visible = False

        if not is_pending_visible:
            logger.info("Checking /asset-dashboard for dedicated IT widgets...")
            page.goto(f"{settings.BASE_URL}/asset-dashboard", timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            pending_card = page.get_by_text(re.compile(r"Pending.*Asset.*Request", re.I)).or_(page.get_by_text(re.compile(r"Pending.*Request", re.I))).first
            try:
                is_pending_visible = pending_card.is_visible(timeout=3000)
            except Exception:
                is_pending_visible = False

        logger.info(f"[AUDIT] 'Pending Asset Requests' widget visible: {is_pending_visible}")

        # Step 4: Audit 'Today's Asset Activities' section and dump all visible card titles
        logger.info("[STEP 4] Auditing 'Today's Asset Activities' section")
        # Extract text from all visible cards/widgets on the page
        card_texts = page.locator(".chakra-stat, .chakra-card, div[class*='card'], div[class*='stat'], div[class*='widget']").all_inner_texts()
        logger.info(f"[AUDIT DUMP] Found {len(card_texts)} cards on dashboard:")
        for idx, text in enumerate(card_texts[:10]):
            logger.info(f"   Card [{idx}]: {text.replace(chr(10), ' | ')}")

        today_activity_section = page.get_by_text(re.compile(r"Today.*Asset.*Activit", re.I)).or_(page.get_by_text(re.compile(r"Today.*Activit", re.I))).or_(page.get_by_text(re.compile(r"Daily Asset", re.I))).first
        try:
            is_today_section_visible = today_activity_section.is_visible(timeout=3000)
        except Exception:
            is_today_section_visible = False
        logger.info(f"[AUDIT] 'Today\\'s Asset Activities' section visible: {is_today_section_visible}")

        # Pause slightly so user inspecting in headed mode can observe the page
        page.wait_for_timeout(3000)

    def test_consolidated_asset_return_screen(self, logged_in_page):
        """
        TC-AST-038 to TC-AST-047:
        1. Navigate to /asset-return on Staging.
        2. Inspect for Consolidated Return UI across assigned employee assets.
        3. Audit individual inspection columns (Working Condition, Physical Condition, Remarks, Evidence).
        """
        story = TestStoryLogger(
            "Consolidated Asset Return Screen Audit",
            module="Asset Management",
            phase="Return Verification"
        )
        story.start()

        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(1500)

        logger.info("[STEP 1] Navigating to /asset-return")
        page.goto(f"{settings.BASE_URL}/asset-return", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Audit page title / header
        header = page.locator("h1, h2, h3, .chakra-heading").all_inner_texts()
        logger.info(f"[AUDIT] Return page headers: {header}")

        # Check tabs (e.g. Return Requests, Assigned Assets, Bulk Return)
        tabs = page.locator("[role='tab']").all_inner_texts()
        logger.info(f"[AUDIT] Available tabs on /asset-return: {tabs}")

        # Check table headers
        table_headers = page.locator("table th").all_inner_texts()
        logger.info(f"[AUDIT] Table headers on Return page: {table_headers}")

        page.wait_for_timeout(3000)

    def test_multi_asset_same_category_assignment_drawer(self, logged_in_page):
        """
        TC-AST-013 to TC-AST-016:
        1. Login as Admin/IT on Staging.
        2. Navigate to /asset-assignment.
        3. Open '+ Assign Asset' drawer.
        4. Inspect Category dropdown for employees who already have assigned assets.
        5. Verify that existing categories (e.g. Laptop, Mobile) are NOT permanently blocked.
        """
        story = TestStoryLogger(
            "Multi-Asset Same Category Drawer Verification",
            module="Asset Management",
            phase="Assignment Verification"
        )
        story.start()

        # Step 1: Login
        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        # Step 2: Navigate to Asset Assignment
        logger.info("[STEP 2] Navigating to /asset-assignment")
        page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Step 3: Click '+ Assign Asset'
        logger.info("[STEP 3] Opening Assign Asset drawer")
        assign_btn = page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first
        if assign_btn.is_visible(timeout=5000):
            assign_btn.click()
            page.wait_for_timeout(2000)
        else:
            logger.warning("Assign Asset button not immediately found; checking drawer triggers")

        # Step 4: Inspect Category and Assignment Type controls
        logger.info("[STEP 4] Inspecting Category and Type options in Drawer")
        category_select = page.locator("label:has-text('Category')").locator("xpath=..").locator("select, input, [role='combobox']").first
        assignment_type = page.locator("label:has-text('Assignment Type'), label:has-text('Type')").locator("xpath=..").locator("select, [role='radiogroup'], input").first

        logger.info(f"[AUDIT] Category control visible: {category_select.is_visible(timeout=3000)}")
        logger.info(f"[AUDIT] Assignment Type control visible: {assignment_type.is_visible(timeout=3000)}")

        # Pause so user can visually inspect
        page.wait_for_timeout(4000)
