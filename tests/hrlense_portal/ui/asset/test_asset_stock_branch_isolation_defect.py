"""
HRlens Portal - Asset Stock Branch Isolation Defect Test.

Defect / Security Leak:
- User: Tejasav Jaiswal (it_varanasi_tejasav) - Assigned Branch: Varanasi.
- Target URL: https://stg-hrlense.jobvritta.com/asset-stock (Stock Manager).
- Expected Behavior:
    A Branch IT Person must ONLY see the stock of their assigned branch (Varanasi).
    Cross-branch inventory (Noida, Agra, Lucknow, etc.) must not be visible.
- Actual Behavior:
    GET /api/Asset/stock-by-branch returns all 9 branches (441 assets).
    The UI renders all 9 branches and defaults to loading Noida stock (branchId=8).
"""

import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.security
@pytest.mark.branch_isolation
class TestAssetStockBranchIsolation:

    def test_branch_it_stock_visibility_isolation_on_asset_stock(self, logged_in_page):
        story = TestStoryLogger(
            "Asset Stock Branch Isolation Audit (Tejas / Varanasi IT)",
            module="Asset Management",
            phase="Stock Branch Permission Isolation"
        )
        story.start()

        # 1. Log in as Tejas (Varanasi IT)
        it_page, it_ctx = logged_in_page("it_varanasi_tejasav")
        
        # Intercept stock APIs
        stock_api_branches = []

        def on_response(resp):
            if "api/asset/stock-by-branch" in resp.url.lower():
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        stock_api_branches.extend(data)
                    elif isinstance(data, dict) and "data" in data:
                        stock_api_branches.extend(data["data"])
                except Exception:
                    pass

        it_page.on("response", on_response)

        # 2. Navigate to /asset-stock
        logger.info("Navigating Tejas (Varanasi IT) to /asset-stock...")
        it_page.goto(f"{settings.BASE_URL}/asset-stock")
        it_page.wait_for_timeout(3000)

        # 3. Read rendered branch cards on the page
        page_text = it_page.locator("body").inner_text()
        
        all_prohibited_branches = [
            "Noida", "Agra", "Bhubaneswar", "Greater Noida",
            "Lucknow", "Jaipur", "Meerut", "Noida NX-One"
        ]

        visible_prohibited_branches = [
            b for b in all_prohibited_branches
            if re.search(rf"\b{re.escape(b)}\b", page_text, re.I)
        ]

        logger.info(f"[AUDIT] Prohibited cross-branch names visible to Tejas: {visible_prohibited_branches}")

        # 4. Check Stock Manager Header (e.g. '441 assets across 9 branches')
        cross_branch_header_match = re.search(r"(\d+)\s+assets\s+across\s+(\d+)\s+branches", page_text, re.I)
        cross_branch_leak = False
        if cross_branch_header_match:
            total_assets = cross_branch_header_match.group(1)
            total_branches = cross_branch_header_match.group(2)
            logger.warning(f"[SECURITY LEAK] Exposed to Tejas: {total_assets} assets across {total_branches} branches!")
            cross_branch_leak = int(total_branches) > 1

        story.log_step(
            "Audit /asset-stock Cross-Branch Leakage",
            record="User: Tejasav Jaiswal (Varanasi IT)",
            expected="Only Varanasi branch stock is visible (1 branch)",
            actual=f"Visible Branches: {len(visible_prohibited_branches) + 1} | Header: {cross_branch_header_match.group(0) if cross_branch_header_match else 'N/A'}",
            status="FAIL" if (visible_prohibited_branches or cross_branch_leak) else "PASS"
        )

        it_ctx.close()

        # Defect assertion: Branch IT Person must only see their assigned branch
        assert not visible_prohibited_branches, (
            f"DEFECT FOUND: Branch IT user (Tejas - Varanasi) can see prohibited cross-branch stock: {visible_prohibited_branches}. "
            "Backend GET /api/Asset/stock-by-branch is leaking all organization branches instead of scoping to the user's assigned branch."
        )

        assert not cross_branch_leak, (
            f"DEFECT FOUND: Stock Manager displays '{cross_branch_header_match.group(0)}' to Branch IT user. "
            "It must only show assets for Varanasi branch."
        )

        story.finish(status="PASS")
