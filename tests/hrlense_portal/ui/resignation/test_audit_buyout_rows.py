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

        rows = page.locator("table tbody tr").all()
        logger.info(f"[ACCOUNTS BUYOUT] Found {len(rows)} rows in table:")
        for idx, r in enumerate(rows[:5]):
            logger.info(f"   Row [{idx}]: {r.inner_text().replace(chr(10), ' | ')}")

        # 2. Resignation approval status list
        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        resig_rows = page.locator("table tbody tr").all()
        logger.info(f"[RESIGNATION APPROVAL] Found {len(resig_rows)} rows in table:")
        for idx, r in enumerate(resig_rows[:5]):
            logger.info(f"   Row [{idx}]: {r.inner_text().replace(chr(10), ' | ')}")
