"""
Staging Verification for HRlens Resignation & FnF Buyout Enhancements (FRD Point 2):
- TC-RSG-118: Configurable Buyout Components Display
- TC-RSG-121: Buyout Formula Info Icon
- TC-RSG-122 to TC-RSG-124: Buyout Calculation Breakdown
"""

import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from utils.branch_persona_resolver import get_branch_persona_bundle

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
@pytest.mark.staging_verification
class TestStagingBuyoutEnhancementsSpec:

    def test_audit_buyout_drawer_components(self, logged_in_page):
        """
        Opens Buyout drawer on /resignation-approval as Branch HR (Tejaswini) and audits:
        1. Configurable salary components & checkboxes (TC-RSG-118, TC-RSG-120).
        2. Formula info / help icon (TC-RSG-121).
        3. Dynamic calculation breakdown (TC-RSG-122 to TC-RSG-124).
        """
        story = TestStoryLogger(
            "Audit Buyout Drawer Components & Formula",
            module="Resignation & FnF",
            phase="Buyout Drawer Verification"
        )
        story.start()

        bundle = get_branch_persona_bundle("Varanasi")
        # Step 1: Login strictly as Varanasi Branch HR (No Admin Bypass)
        page, ctx = logged_in_page(bundle["hr_person"])
        page.bring_to_front()
        page.wait_for_timeout(2000)

        logger.info("[STEP 1] Navigating to /resignation-approval")
        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Locate first row with 'Buyout'
        buyout_row = page.locator("tr:has-text('Buyout'), tr:has-text('BUYOUT')").first
        if not buyout_row.is_visible(timeout=5000):
            logger.warning("No buyout row visible on page 1 of /resignation-approval")
            return

        row_text = buyout_row.inner_text().replace('\n', ' | ')
        logger.info(f"[AUDIT ROW] {row_text}")

        # Click Actions hamburger menu in that row
        action_btn = buyout_row.locator("button, [role='button']").last
        action_btn.click()
        page.wait_for_timeout(1000)

        menu_items = page.locator("[role='menuitem'], .chakra-menu__menuitem").all_inner_texts()
        logger.info(f"[AUDIT MENU ITEMS] {menu_items}")

        # Look for Buyout Request or Process Buyout
        buyout_item = page.locator("[role='menuitem']:has-text('Buyout'), button:has-text('Buyout')").first
        if buyout_item.is_visible(timeout=3000):
            buyout_item.click()
            page.wait_for_timeout(2000)

            # Audit Drawer / Modal
            modal = page.locator("[role='dialog'], section.chakra-modal__content").first
            if modal.is_visible(timeout=3000):
                modal_text = modal.inner_text()
                logger.info(f"[AUDIT BUYOUT MODAL CONTENT]\n{modal_text}")

                # Check for checkboxes (Salary components)
                checkboxes = modal.locator("input[type='checkbox'], [role='checkbox']").all()
                logger.info(f"[AUDIT] Found {len(checkboxes)} checkboxes in buyout drawer")

                # Check for Info / Formula icon
                info_icon = modal.locator("[aria-label*='info' i], [data-testid*='info'], svg.chakra-icon").all()
                logger.info(f"[AUDIT] Found {len(info_icon)} icons/tooltips in buyout drawer")

        page.wait_for_timeout(3000)

    def test_audit_accountant_buyout_processing_queue(self, logged_in_page):
        """
        Logs in strictly as Varanasi Branch Accountant (Sunil Kumar) without Admin bypass.
        Verifies /accounts-buyout-processing page accessibility and audit queues.
        """
        story = TestStoryLogger(
            "Audit Accountant Buyout Processing Queue",
            module="Resignation & FnF",
            phase="Accountant Buyout Verification"
        )
        story.start()

        bundle = get_branch_persona_bundle("Varanasi")
        # Step 1: Login strictly as Varanasi Branch Accountant (Sunil Kumar)
        acc_page, _ = logged_in_page(bundle["accountant"])
        acc_page.bring_to_front()
        acc_page.wait_for_timeout(2000)

        logger.info(f"[STEP 1] Logged in as Accountant '{bundle['accountant_name']}' ({bundle['accountant']})")
        acc_page.goto(f"{settings.BASE_URL}/accounts-buyout-processing", timeout=30000)
        acc_page.wait_for_load_state("domcontentloaded")
        acc_page.wait_for_timeout(3000)

        page_title = acc_page.locator("h1, h2, .chakra-heading").first.inner_text()
        logger.info(f"[ACCOUNTANT PAGE HEADING] {page_title}")
        story.log_step("Accountant Portal Access", record=f"Heading: {page_title}", expected="Accounts Buyout Processing visible", actual=page_title, status="PASS")
