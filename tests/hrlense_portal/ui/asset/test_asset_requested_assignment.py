"""
HRlens Portal - IT Person Login & Requested Asset Assignment Fulfillment Suite.

Validates:
1. IT Person login authentication and role-based portal access.
2. Navigation to Asset Assignment -> Requested Assignment tab.
3. Discovery of pending employee asset requests in queue.
4. Opening the fulfillment drawer.
5. Strict branch-scoping audit on available assets dropdown (Varanasi assets only, 0 cross-branch leaks).
6. Submission of assignment fulfillment and verification of success.
"""

import re
import random
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_stock_page import AssetStockPage
from utils.branch_it_selector import get_all_branch_it_persons

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.requested_assignment
class TestAssetRequestedAssignment:

    def test_it_person_login_and_fulfill_requested_assignment(self, logged_in_page):
        story = TestStoryLogger(
            "IT Person Login & Requested Asset Assignment Fulfillment",
            module="Asset Management",
            phase="IT Fulfillment"
        )
        story.start()

        # Step 1: Resolve all IT Persons for the branch and randomly pick one
        it_persons = get_all_branch_it_persons("Varanasi")
        if not it_persons:
            it_persons = [
                {"user_key": "it_varanasi_ashutosh", "name": "Ashutosh Kumar"},
                {"user_key": "it_varanasi_tejasav", "name": "Tejasav Jaiswal"}
            ]

        # Randomly choose among the N IT persons for this branch
        it_person = random.choice(it_persons)
        it_key = it_person["user_key"]
        it_name = it_person["name"]

        logger.info(f"\n=======================================================")
        logger.info(f"STEP 1: Validating Login via Random IT Person: '{it_name}' ({it_key})")
        logger.info(f"Candidate IT pool for Varanasi ({len(it_persons)}): {[p['name'] for p in it_persons]}")
        logger.info(f"=======================================================")

        it_page, it_ctx = logged_in_page(it_key)
        assert it_page is not None, f"Failed to initialize browser page for IT Person '{it_name}'"
        assert "/login" not in it_page.url, (
            f"Login validation FAILED: IT Person '{it_name}' is still on login page ({it_page.url})!"
        )

        story.log_step(
            f"1. IT Person Login ({it_name})",
            expected="IT Person successfully logs into the HRlens portal",
            actual=f"Authenticated URL: {it_page.url}",
            status="PASS"
        )

        # Step 2: Navigate to Asset Assignment -> Requested Assignment tab
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 2: Navigating to Asset Assignment -> Requested Assignment")
        logger.info(f"=======================================================")

        assign_page = AssetAssignmentPage(it_page)
        assign_page.navigate_to_asset_assignment()
        it_page.wait_for_timeout(2000)

        assert "/asset-assignment" in it_page.url, (
            f"Navigation FAILED: Expected URL to contain '/asset-assignment', got '{it_page.url}'"
        )

        # Step 3: Open fulfillment drawer for pending request
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 3: Opening Fulfillment Drawer for Pending Request")
        logger.info(f"=======================================================")

        drawer = assign_page.open_fulfillment_drawer()
        assert drawer is not None and drawer.is_visible(), (
            f"DEFECT: Fulfillment drawer did not open! No pending requests with 'Fulfil' button found in IT Person '{it_name}' queue."
        )

        story.log_step(
            "2. Open Fulfillment Drawer",
            expected="Fulfillment drawer opens for pending requested assignment",
            actual="Drawer is open and visible",
            status="PASS"
        )

        # Step 4: Audit Available Assets scoping in drawer dropdown
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 4: Auditing Available Assets Scoping in Drawer Dropdown")
        logger.info(f"=======================================================")

        available_assets = assign_page.get_fulfillment_available_assets(drawer)
        logger.info(f"Available assets in fulfillment dropdown ({len(available_assets)} items): {available_assets[:5]}")

        assert len(available_assets) > 0, (
            f"DEFECT / BLOCKER: Available Assets dropdown in fulfillment drawer is EMPTY (0 assets). "
            f"Backend GET /api/Asset/available-assets-for-request returned empty list. "
            f"Employee branch is not correctly resolving to available branch stock."
        )

        # Strict cross-branch leakage audit
        cross_branch_names = ["Agra_", "Lucknow_", "Noida_", "Meerut_", "Ranchi_", "Jaipur_", "Gorakhpur_", "Delhi_", "Dehradun_"]
        cross_leaks = [a for a in available_assets if any(cb in a for cb in cross_branch_names)]
        assert not cross_leaks, (
            f"SECURITY DEFECT: Assets from other branch groups leaked into IT Person fulfillment dropdown: {cross_leaks}"
        )

        story.log_step(
            "3. Audit Available Assets Scoping",
            expected="Available assets strictly scoped to branch group (0 cross-branch leaks)",
            actual=f"Count: {len(available_assets)} | Sample: {available_assets[:3]} | Leaks: {cross_leaks}",
            status="PASS"
        )

        # Step 5: Fulfill Requested Assignment
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 5: Submitting Requested Assignment Fulfillment")
        logger.info(f"=======================================================")

        res = assign_page.submit_open_fulfillment_drawer(
            drawer=drawer,
            asset_code=available_assets[0],
            assignment_type="Permanent",
            expected_return_date=None,
            remarks=None
        )
        logger.info(f"Fulfillment submission result: {res}")

        assert res.get("success"), (
            f"DEFECT: Fulfillment submission failed for IT Person '{it_name}'! Result: {res}"
        )

        story.log_step(
            "4. Submit Fulfillment",
            expected="Requested assignment fulfilled successfully",
            actual=f"Result: {res}",
            status="PASS"
        )

        # Step 6: Validate Stock Manager Cards for Varanasi on /asset-stock
        logger.info(f"\n=======================================================")
        logger.info(f"STEP 6: Checking Stock Manager Cards on /asset-stock for Varanasi")
        logger.info(f"=======================================================")

        stock_page = AssetStockPage(it_page)
        cards = stock_page.get_stock_cards(branch_name="Varanasi")
        logger.info(f"Varanasi Stock Manager Cards: {cards}")

        # Assert stock cards are present and mathematically consistent
        assert "All Assets" in cards, f"Stock Manager did not load 'All Assets' card! Cards: {cards}"
        assert cards.get("All Assets") == 20, f"Expected 20 Total Assets for Varanasi, got {cards.get('All Assets')}"
        assert cards.get("Reserved", 0) >= 1, f"Expected >= 1 Reserved Asset from fulfillment, got {cards.get('Reserved')}"
        assert cards.get("Assigned", 0) >= 1, f"Expected >= 1 Assigned Asset, got {cards.get('Assigned')}"
        assert cards.get("Available", 0) >= 1, f"Expected Available Assets to be > 0, got {cards.get('Available')}"

        # Mathematical sum check: Available + Assigned + Reserved + Maintenance + Damaged == Total Assets (20)
        total_sum = cards.get("Available", 0) + cards.get("Assigned", 0) + cards.get("Reserved", 0) + cards.get("Maintenance", 0) + cards.get("Damaged", 0)
        assert total_sum == cards.get("All Assets"), (
            f"Stock card inventory mismatch! Sum of statuses ({total_sum}) != All Assets ({cards.get('All Assets')})"
        )

        story.log_step(
            "5. Verify Varanasi Stock Cards",
            expected="Varanasi stock reflects: All Assets=20, Available+Assigned+Reserved=20",
            actual=f"Cards: {cards} | Sum: {total_sum}",
            status="PASS"
        )

        it_ctx.close()
        story.finish(status="PASS")
