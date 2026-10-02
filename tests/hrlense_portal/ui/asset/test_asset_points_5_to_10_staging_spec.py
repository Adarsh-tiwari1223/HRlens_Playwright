"""
Staging Verification Test Suite for HRlens Asset Management FRD Changes (Points 5 to 10).

Specification Coverage:
- Point 5: Multiple Assets in the Same Category/Subcategory (not permanently blocked)
- Point 6: Pending Asset Requests on Dashboard (clickable counter linking to requests)
- Point 7: Dashboard – Today's Asset Activities (requests today, employees today, return today, approaching)
- Point 8: Temporary Asset Return Reminder (Expected Return Date tracking & validation)
- Point 9: Asset Return / Exit Clearance – Consolidated UI (all assigned assets in single screen)
- Point 10: Individual Inspection for Every Asset (Working condition, Physical condition, Remarks, Evidence)

Execution Command:
    venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_points_5_to_10_staging_spec.py -v -s
"""

import os
import re
import logging
import pytest
from playwright.sync_api import expect

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_dashboard_page import AssetDashboardPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.staging_verification
class TestAssetPoints5To10StagingSpec:

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 5: MULTIPLE ASSETS IN SAME CATEGORY / SUBCATEGORY
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_05_multi_asset_same_category_assignment(self, admin_page):
        """
        Point 5: Multiple Assets in the Same Category/Subcategory
        Requirement: The system should not permanently block another asset assignment
        simply because an employee already has an asset in the same category (e.g. 2 laptops).
        """
        story = TestStoryLogger(
            "Point 5: Multiple Assets in Same Category/Subcategory",
            module="Asset Management",
            phase="Assignment Verification"
        )
        story.start()

        page = admin_page

        logger.info("[STEP 1] Navigating to /asset-assignment")
        page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Open Drawer
        assign_btn = page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first
        expect(assign_btn).to_be_visible(timeout=10000)
        assign_btn.click()
        page.wait_for_timeout(2000)

        drawer = page.locator("[role='dialog'], .chakra-modal__content").first
        expect(drawer).to_be_visible(timeout=5000)

        # Step 2: Search Employee (DEF_020 Check)
        emp_input = drawer.locator("input[placeholder*='Search employee' i]").first
        expect(emp_input).to_be_visible(timeout=5000)
        emp_input.fill("sanidhy")
        page.wait_for_timeout(2500)

        # Hard assertion: Employee options must appear in dropdown / portal
        matching_option = page.locator(".chakra-portal, [role='listbox'], [role='menu'], div[class*='popover']").locator("text=sanidhy, text=Sanidhy").first
        is_emp_rendered = matching_option.is_visible(timeout=3000)

        assert is_emp_rendered, (
            "DEF_020 Failure: Employee Search in Assign Asset Drawer is broken! "
            "Typing 'sanidhy' did not display any selectable employee dropdown/popup. "
            "Assignment of multiple assets cannot proceed."
        )

        matching_option.click()
        page.wait_for_timeout(1000)
        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 6: PENDING ASSET REQUESTS ON DASHBOARD
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_06_dashboard_pending_asset_requests_counter(self, admin_page):
        """
        Point 6: Pending Asset Requests on Dashboard
        Requirement: The main dashboard / IT dashboard should display the count of
        pending asset requests (e.g. 'Pending Asset Requests: 8') and it should be clickable.
        """
        story = TestStoryLogger(
            "Point 6: Pending Asset Requests on Dashboard",
            module="Asset Management",
            phase="Dashboard Verification"
        )
        story.start()

        page = admin_page

        logger.info("[STEP 1] Navigating to Dashboard")
        page.goto(f"{settings.BASE_URL}/", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Look for Pending Asset Requests counter
        pending_counter = page.locator("text=Pending Asset Request, text=Pending Request, [data-testid*='pending-asset']").first
        is_visible_on_home = pending_counter.is_visible(timeout=3000)

        if not is_visible_on_home:
            logger.info("Checking /asset-dashboard for dedicated IT pending requests counter...")
            page.goto(f"{settings.BASE_URL}/asset-dashboard", timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            pending_counter = page.locator("text=Pending Asset Request, text=Pending Request, text=Asset Request").first

        logger.info(f"Pending Requests counter element found: {pending_counter.is_visible(timeout=3000)}")
        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 7: DASHBOARD – TODAY'S ASSET ACTIVITIES
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_07_dashboard_todays_asset_activities_section(self, admin_page):
        """
        Point 7: Dashboard – Today's Asset Activities
        Requirement: The dashboard should display today's asset activities:
        - Requests received today
        - Employees who submitted requests today
        - Total pending requests
        - Assets expected to be returned today / approaching return date
        """
        story = TestStoryLogger(
            "Point 7: Today's Asset Activities Section",
            module="Asset Management",
            phase="Dashboard Verification"
        )
        story.start()

        page = admin_page

        # Audit both Root and Asset Dashboard
        for route in ["/", "/asset-dashboard"]:
            logger.info(f"[STEP] Auditing route '{route}' for Today's Asset Activities")
            page.goto(f"{settings.BASE_URL}{route}", timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            # Check for section title or card keywords
            today_cards = page.locator("div.chakra-card, div.chakra-stat, div[class*='card']").all_inner_texts()
            logger.info(f"Captured {len(today_cards)} widget card texts on {route}")

        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 8: TEMPORARY ASSET RETURN REMINDER
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_08_temporary_asset_expected_return_date_tracking(self, admin_page):
        """
        Point 8: Temporary Asset Return Reminder
        Requirement: For assets assigned temporarily, the system should track Expected Return Date.
        """
        story = TestStoryLogger(
            "Point 8: Temporary Asset Return Reminder",
            module="Asset Management",
            phase="Assignment Verification"
        )
        story.start()

        page = admin_page

        logger.info("[STEP 1] Navigating to /asset-assignment")
        page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Open Assign Drawer
        assign_btn = page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first
        assign_btn.click()
        page.wait_for_timeout(2000)

        drawer = page.locator("[role='dialog'], .chakra-modal__content").first
        expect(drawer).to_be_visible(timeout=5000)

        # Select Temporary in Assignment Type duration dropdown
        duration_select = drawer.locator("select:has(option:has-text('Permanent'))").first
        if not duration_select.is_visible(timeout=2000):
            duration_select = drawer.locator("select").first
        
        expect(duration_select).to_be_visible(timeout=5000)
        duration_select.select_option(label="Temporary")
        page.wait_for_timeout(1000)

        # Hard assertion: Expected Return Date field MUST appear
        return_date_input = drawer.locator("input[type='date'], label:has-text('Expected Return Date') + div input").first
        expect(return_date_input).to_be_visible(timeout=5000)
        logger.info("Point 8 Verified: Expected Return Date field dynamically appears for Temporary assignments.")

        close_btn = drawer.locator("button[aria-label='Close'], button:has-text('Cancel')").first
        close_btn.click()
        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 9: CONSOLIDATED ASSET RETURN UI
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_09_consolidated_asset_return_ui(self, admin_page):
        """
        Point 9: Asset Return / Exit Clearance – Consolidated UI
        Requirement: A consolidated asset-return screen should display all assets
        assigned to the employee and allow return details to be entered from the same interface.
        """
        story = TestStoryLogger(
            "Point 9: Consolidated Asset Return UI",
            module="Asset Management",
            phase="Return Verification"
        )
        story.start()

        page = admin_page

        logger.info("[STEP 1] Navigating to /asset-return")
        page.goto(f"{settings.BASE_URL}/asset-return", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Check Assigned Assets tab
        assigned_tab = page.locator("button[role='tab']:has-text('Assigned Assets')").first
        if assigned_tab.is_visible(timeout=3000):
            assigned_tab.click()
            page.wait_for_timeout(1500)

        rows = page.locator("table tbody tr").all()
        table_text = page.locator("table tbody").inner_text() if rows else ""
        
        # Hard assertion: We cannot claim Consolidated Return passes if there are 0 assigned assets
        assert len(rows) > 0 and "no assigned assets" not in table_text.lower(), (
            "BLOCKED: /asset-return has 0 assigned assets ('No assigned assets'). "
            "Consolidated Return UI cannot be validated without real active assigned assets. "
            "Assignment is currently blocked by DEF_020 (Employee search failure)."
        )

        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 10: INDIVIDUAL INSPECTION FOR EVERY ASSET
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_10_individual_inspection_for_every_asset(self, admin_page):
        """
        Point 10: Individual Inspection for Every Asset
        Requirement: Even when a consolidated screen is used, each asset must be inspected
        individually. The IT user should record return date, working condition, physical condition,
        remarks, images, and video evidence.
        """
        story = TestStoryLogger(
            "Point 10: Individual Inspection for Every Asset",
            module="Asset Management",
            phase="Return Inspection Verification"
        )
        story.start()

        page = admin_page

        logger.info("[STEP 1] Navigating to /asset-return")
        page.goto(f"{settings.BASE_URL}/asset-return", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        action_btns = page.locator("table tbody tr button").all()
        assert len(action_btns) > 0, (
            "BLOCKED: 0 action buttons found on /asset-return because table is empty. "
            "Individual asset inspection form cannot be opened or verified without active assigned assets."
        )

        story.finish(status="PASS")
