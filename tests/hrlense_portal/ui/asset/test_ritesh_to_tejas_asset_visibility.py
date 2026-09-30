"""
Diagnostic Test Suite: Ritesh Singh Asset Request Visibility to Tejasav Jaiswal (Tejas - IT Varanasi).

Validates:
1. Ritesh Singh logs in, navigates to /asset-request, checks existing requests, and submits an asset request.
2. Tejasav Jaiswal (Varanasi Branch IT) logs in, navigates to /asset-assignment -> Requested Assignment tab,
   and checks if Ritesh's request appears in Varanasi branch queue.
3. Global Admin logs in, checks Requested Assignment tab to diagnose branch scoping or approval barriers.
"""

import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.requested_assignment
class TestRiteshToTejasAssetVisibility:

    def test_ritesh_asset_request_visibility_to_tejas_and_admin(self, logged_in_page):
        story = TestStoryLogger(
            "Ritesh Singh Asset Request -> Tejas IT Visibility Diagnostics",
            module="Asset Management",
            phase="Request & Visibility Diagnostics"
        )
        story.start()

        # =========================================================================
        # PHASE 1: RITESH SINGH LOGS IN & CHECKS / CREATES ASSET REQUEST
        # =========================================================================
        logger.info("=== PHASE 1: Ritesh Singh Asset Request Status ===")
        ritesh_page, ritesh_ctx = logged_in_page("ritesh_singh")
        req_page = AssetRequestPage(ritesh_page)
        req_page.navigate_to_asset_request()
        ritesh_page.wait_for_timeout(2000)

        # Inspect existing requests on Ritesh's page
        ritesh_rows = ritesh_page.locator("table tbody tr").all()
        logger.info(f"[RITESH PORTAL] Found {len(ritesh_rows)} existing rows on /asset-request table.")
        for idx, r in enumerate(ritesh_rows[:5]):
            txt = " | ".join([c.strip() for c in r.locator("td").all_text_contents() if c.strip()])
            logger.info(f"  Ritesh Row {idx + 1}: {txt}")

        # Check if there is an active/pending request or raise a new one
        create_btn = ritesh_page.locator("button:has-text('New Request'), button:has-text('Request Asset'), button:has-text('Add Request')").first
        req_toast = "Existing Request Checked"
        req_success = False

        if create_btn.is_visible(timeout=2000):
            logger.info("Creating a fresh asset request for Ritesh Singh...")
            req_success = req_page.create_new_request(
                reason="Asset required for client demo and validation",
                remarks="Urgent demo testing requirement"
            )
            req_toast = req_page.wait_for_toast_message() or "Request submitted"
            logger.info(f"[RITESH REQUEST TOAST] {req_toast}")
        else:
            logger.info("New Request button not visible or limit reached.")

        story.log_step(
            "Phase 1: Ritesh Singh Asset Request Portal",
            record="User: ritesh.singh@tekinspirations.com",
            expected="Asset request submitted or existing pending requests audited",
            actual=f"Toast: '{req_toast}' | Existing Rows: {len(ritesh_rows)}",
            status="PASS"
        )
        ritesh_ctx.close()

        # =========================================================================
        # PHASE 2: TEJAS (IT VARANASI) CHECKS REQUESTED ASSIGNMENT QUEUE
        # =========================================================================
        logger.info("=== PHASE 2: Tejasav Jaiswal (Tejas) Requested Assignment Check ===")
        tejas_page, tejas_ctx = logged_in_page("it_varanasi_tejasav")
        tejas_assign = AssetAssignmentPage(tejas_page)
        tejas_assign.navigate_to_asset_assignment()
        tejas_page.wait_for_timeout(2000)

        # Switch to Requested Assignment tab
        req_tab = tejas_page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not req_tab.is_visible(timeout=2000):
            req_tab = tejas_page.locator("[role='tab']").nth(1)
        req_tab.click(force=True)
        tejas_page.wait_for_timeout(2000)

        tejas_rows = tejas_page.locator("table tbody tr").all()
        logger.info(f"[TEJAS IT PORTAL] Total rows visible under Requested Assignment: {len(tejas_rows)}")
        for idx, r in enumerate(tejas_rows[:10]):
            txt = " | ".join([c.strip() for c in r.locator("td").all_text_contents() if c.strip()])
            logger.info(f"  Tejas Queue Row {idx + 1}: {txt}")

        # Search specifically for Ritesh
        search_in = tejas_page.locator("input[placeholder*='Search' i]").first
        ritesh_visible_to_tejas = False
        if search_in.is_visible(timeout=2000):
            search_in.fill("Ritesh")
            search_in.press("Enter")
            tejas_page.wait_for_timeout(2000)
            search_rows = tejas_page.locator("table tbody tr").all()
            for r in search_rows:
                row_text = r.inner_text()
                if "ritesh" in row_text.lower():
                    ritesh_visible_to_tejas = True
                    logger.info(f"  --> FOUND Ritesh in Tejas queue: {row_text}")

        logger.info(f"[DIAGNOSIS RESULT] Is Ritesh Singh visible to Tejas? {ritesh_visible_to_tejas}")

        assert ritesh_visible_to_tejas, (
            f"DEFECT: Ritesh Singh request was NOT visible in Tejas's (Varanasi IT) Requested Assignment queue! "
            f"Total queue rows visible: {len(tejas_rows)}."
        )

        story.log_step(
            "Phase 2: Tejas IT Requested Assignment Visibility",
            record="IT: tejasav.jaiswal@tekinspirations.com (Varanasi IT)",
            expected="Ritesh Singh request is strictly visible in Tejas queue",
            actual=f"Visible: {ritesh_visible_to_tejas} | Total Queue Rows: {len(tejas_rows)}",
            status="PASS"
        )
        tejas_ctx.close()

        # =========================================================================
        # PHASE 3: GLOBAL ADMIN CHECKS REQUESTED ASSIGNMENT QUEUE
        # =========================================================================
        logger.info("=== PHASE 3: Global Admin Requested Assignment Check ===")
        admin_page, admin_ctx = logged_in_page("admin")
        admin_assign = AssetAssignmentPage(admin_page)
        admin_assign.navigate_to_asset_assignment()
        admin_page.wait_for_timeout(2000)

        admin_req_tab = admin_page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not admin_req_tab.is_visible(timeout=2000):
            admin_req_tab = admin_page.locator("[role='tab']").nth(1)
        admin_req_tab.click(force=True)
        admin_page.wait_for_timeout(2000)

        admin_search = admin_page.locator("input[placeholder*='Search' i]").first
        ritesh_visible_to_admin = False
        if admin_search.is_visible(timeout=2000):
            admin_search.fill("Ritesh")
            admin_search.press("Enter")
            admin_page.wait_for_timeout(2000)
            admin_rows = admin_page.locator("table tbody tr").all()
            logger.info(f"[ADMIN PORTAL] Rows matching 'Ritesh' in Admin queue: {len(admin_rows)}")
            for idx, r in enumerate(admin_rows):
                txt = " | ".join([c.strip() for c in r.locator("td").all_text_contents() if c.strip()])
                logger.info(f"  Admin Ritesh Row {idx + 1}: {txt}")
                if "ritesh" in txt.lower():
                    ritesh_visible_to_admin = True

        story.log_step(
            "Phase 3: Global Admin Visibility & Branch Isolation Verification",
            record="Admin: admin@tek.com",
            expected="Verify if Ritesh request exists globally and determine branch scoping",
            actual=f"Visible to Admin: {ritesh_visible_to_admin}",
            status="PASS"
        )
        admin_ctx.close()

        story.finish(status="PASS")
