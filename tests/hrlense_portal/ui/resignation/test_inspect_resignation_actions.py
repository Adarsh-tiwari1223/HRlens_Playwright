"""
Inspect Action menu items dynamically on /resignation-approval (No hardcoded employee, No admin bypass).
"""

import logging
import pytest
from core.config import settings
from utils.branch_persona_resolver import get_branch_persona_bundle

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
class TestInspectResignationActions:

    def test_inspect_actions_menu(self, logged_in_page):
        bundle = get_branch_persona_bundle("Varanasi")
        page, ctx = logged_in_page(bundle["hr_person"])
        page.bring_to_front()
        page.wait_for_timeout(2000)

        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Locate first available row dynamically (No hardcoded employee)
        rows = page.locator("table tbody tr")
        row_count = rows.count()
        logger.info(f"[RESIGNATION TABLE] Found {row_count} rows on /resignation-approval")

        if row_count == 0:
            logger.warning("No resignation rows currently in queue on /resignation-approval")
            return

        row = rows.first
        row_text = row.inner_text().replace("\n", " | ")
        logger.info(f"[DYNAMIC ROW SELECTED]: {row_text}")

        # Click Actions button
        action_btn = row.locator("button.chakra-menu__menu-button, [id^='menu-button'], button:has-text('Actions')").first
        if action_btn.is_visible(timeout=5000):
            action_btn.click()
            page.wait_for_timeout(1000)

            menu_items = page.locator("[role='menuitem'], .chakra-menu__menuitem").all_inner_texts()
            logger.info(f"[DYNAMIC ROW ACTION MENU ITEMS]: {menu_items}")
            assert len(menu_items) > 0, "Expected action menu items to be visible"
