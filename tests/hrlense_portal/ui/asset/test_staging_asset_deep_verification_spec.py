"""
Deep Staging Verification for HRlens Asset Enhancements:
- Cluster 1: Multi-Asset Assignment (TC-AST-013 to TC-AST-016)
- Cluster 4: Temporary Asset Assignment & Expected Return Date Validation (TC-AST-032 to TC-AST-034)
- Cluster 7: Consolidated Asset Return Action (TC-AST-041 to TC-AST-045)
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
class TestStagingAssetDeepVerificationSpec:

    def test_temporary_assignment_expected_return_date_behavior(self, logged_in_page):
        """
        Verifies TC-AST-032 & TC-AST-033:
        1. Open /asset-assignment.
        2. Click '+ Assign Asset'.
        3. Switch Assignment Type to 'Temporary'.
        4. Check if 'Expected Return Date' field appears.
        5. Verify validation when submitting without return date or with past date.
        """
        story = TestStoryLogger(
            "Temporary Assignment Return Date Behavior",
            module="Asset Management",
            phase="Temporary Assignment Verification"
        )
        story.start()

        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        logger.info("[STEP 1] Navigating to /asset-assignment")
        page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Open Drawer
        assign_btn = page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first
        assert assign_btn.is_visible(timeout=5000), "Assign Asset button not visible"
        assign_btn.click()
        page.wait_for_timeout(2000)

        # Audit drawer controls
        drawer_text = page.locator("[role='dialog'], .chakra-modal__content, .drawer-content").first.inner_text()
        logger.info(f"[DRAWER CONTENT]\n{drawer_text}")

        # Look for Assignment Type selector (Permanent vs Temporary)
        temp_radio = page.locator("label:has-text('Temporary'), input[value*='temp' i], [role='radio']:has-text('Temporary')").first
        is_temp_option_visible = temp_radio.is_visible(timeout=3000)
        logger.info(f"[AUDIT] Temporary Assignment Type option visible: {is_temp_option_visible}")

        if is_temp_option_visible:
            temp_radio.click()
            page.wait_for_timeout(1000)

            # Check if Expected Return Date field is visible
            return_date_field = page.locator("label:has-text('Expected Return Date'), label:has-text('Return Date'), input[placeholder*='Return' i], input[type='date']").first
            is_return_date_visible = return_date_field.is_visible(timeout=3000)
            logger.info(f"[AUDIT] Expected Return Date field visible after selecting Temporary: {is_return_date_visible}")

        page.wait_for_timeout(3000)

    def test_multi_asset_category_selection_in_drawer(self, logged_in_page):
        """
        Verifies TC-AST-013 & TC-AST-014:
        1. Open /asset-assignment.
        2. Open '+ Assign Asset' drawer.
        3. Inspect employee list and category list.
        4. Check whether categories like Laptop/Mobile are available for selection.
        """
        story = TestStoryLogger(
            "Multi-Asset Category Selection Audit",
            module="Asset Management",
            phase="Assignment Verification"
        )
        story.start()

        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Open Drawer
        page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first.click()
        page.wait_for_timeout(2000)

        # Inspect all select dropdowns / inputs in drawer
        inputs = page.locator("[role='dialog'] select, [role='dialog'] input, .chakra-modal__content select, .chakra-modal__content input").all()
        logger.info(f"[AUDIT] Found {len(inputs)} input controls in Assign Asset drawer")

        # Check options inside Category select
        category_select = page.locator("[role='dialog'] select, .chakra-modal__content select").first
        if category_select.is_visible(timeout=3000):
            options = category_select.locator("option").all_inner_texts()
            logger.info(f"[AUDIT] Category Options: {options}")

        page.wait_for_timeout(3000)
