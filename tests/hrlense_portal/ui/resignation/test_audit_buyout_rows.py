"""
Audit rows on /accounts-buyout-processing and /resignation-approval
"""

import logging
import pytest
from core.config import settings

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
class TestAuditAccountsBuyoutRows:

    def test_read_accounts_buyout_table(self, logged_in_page):
        page, ctx = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        # 1. Accounts buyout processing
        page.goto(f"{settings.BASE_URL}/accounts-buyout-processing", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Switch to FnF Requests tab
        fnf_tab = page.locator("button[role='tab']:has-text('FnF'), [role='tab']:has-text('FnF'), button:has-text('FnF')").first
        if fnf_tab.is_visible(timeout=5000):
            logger.info("Clicking 'FnF Requests' tab...")
            fnf_tab.click()
            page.wait_for_timeout(2000)

        fnf_rows = page.locator("table tbody tr").all()
        logger.info(f"[ACCOUNTS FnF REQUESTS TAB] Found {len(fnf_rows)} rows in table:")
        for idx, r in enumerate(fnf_rows):
            logger.info(f"   FnF Row [{idx}]: {r.inner_text().replace(chr(10), ' | ')}")

        kailash_row = page.locator("tr:has-text('Kailash Singh')").first
        if kailash_row.is_visible(timeout=5000):
            logger.info("Found Kailash Singh on FnF Requests tab! Inspecting row cells...")
            cells = kailash_row.locator("td").all()
            for c_idx, c in enumerate(cells):
                logger.info(f"   Cell [{c_idx}]: text='{c.inner_text().strip()}', html='{c.inner_html()}'")

            # Click action button / arrow in last cell or row
            action_el = kailash_row.locator("td").last.locator("button, img, svg, a").first
            if not action_el.is_visible(timeout=2000):
                action_el = kailash_row.locator("td").last
            logger.info("Clicking action element to open FnF settlement drawer...")
            action_el.click()
            page.wait_for_timeout(3000)

            # Check if drawer opened
            drawer = page.locator("div[role='dialog'], section.chakra-modal__content").first
            if drawer.is_visible(timeout=5000):
                logger.info(f"Drawer Content: {drawer.inner_text()[:300].replace(chr(10), ' | ')}")
                # Fill salary / earnings if needed
                sal_in = drawer.locator("tr:has-text('Salary for Days Worked') input, input[name*='salary' i]").first
                if sal_in.is_visible(timeout=2000):
                    sal_in.fill("1000")
                rem_area = drawer.locator("textarea").first
                if rem_area.is_visible(timeout=2000):
                    rem_area.fill("Full & Final settlement cleared by Accountant.")
                
                # Submit FnF
                sub_btn = drawer.locator("button:has-text('Submit FnF'), button:has-text('Submit'), button:has-text('Save')").first
                if sub_btn.is_visible(timeout=3000):
                    logger.info("Clicking 'Submit FnF'...")
                    sub_btn.click()
                    page.wait_for_timeout(2000)
                    confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('Yes')").first
                    if confirm_btn.is_visible(timeout=2000):
                        confirm_btn.click()
                    page.wait_for_timeout(3000)
                    toast = page.locator(".chakra-toast, [role='status'], [role='alert']").first
                    logger.info(f"Submit FnF Toast: '{toast.inner_text() if toast.is_visible(timeout=3000) else ''}'")

        # 2. Resignation approval status list
        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        resig_rows = page.locator("table tbody tr").all()
        logger.info(f"[RESIGNATION APPROVAL] Found {len(resig_rows)} rows in table:")
        for idx, r in enumerate(resig_rows):
            logger.info(f"   Row [{idx}]: {r.inner_text().replace(chr(10), ' | ')}")

