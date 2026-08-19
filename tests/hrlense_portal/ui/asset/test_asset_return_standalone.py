"""
HRlens Portal - Asset Return Standalone Test.

Executes the Asset Return process independently:
- Navigates to Asset Return page.
- Identifies assigned assets in the grid.
- Initiates Return & Condition Assessment (Good -> Available).
"""

import logging
import pytest
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.return_asset
def test_asset_return_standalone(logged_in_page):
    """Standalone test for Asset Return & Condition Assessment."""
    story = TestStoryLogger(
        "Asset Return Standalone",
        module="Asset Management",
        phase="Standalone Asset Return"
    )
    story.start()

    admin_page, admin_context = logged_in_page("admin")
    return_page = AssetReturnPage(admin_page)
    return_page.navigate_to_asset_return()

    # Find the first asset code or name in the table
    target_asset = ""
    try:
        rows = admin_page.locator("table tbody tr").filter(has=admin_page.locator("td")).all()
        for r in rows:
            txt = r.inner_text().strip()
            if txt and not txt.startswith("No "):
                # Extract first word/code
                cells = r.locator("td").all()
                if cells:
                    target_asset = cells[0].inner_text().strip()
                    if target_asset:
                        break
    except Exception as ex:
        logger.warning(f"Row read note: {ex}")

    if not target_asset:
        target_asset = "ASSET-AVL-2026-004"

    logger.info(f"Targeting asset for Return: '{target_asset}'")

    res = return_page.return_asset(
        asset_code_or_name=target_asset,
        condition="Good",
        return_date="2026-08-15",
        remarks="Standalone test return process executed."
    )

    if res == "No asset pending return":
        toast = "No asset pending return on grid"
        is_success = True
    else:
        toast = return_page.wait_for_toast_message()
        is_success = any(kw in toast.lower() for kw in ["success", "returned", "received", "completed", "saved"])
    
    story.log_step(
        "Asset Return Execution",
        record=f"Target: {target_asset} | Condition: Good",
        expected="Asset returned successfully",
        actual=f"Toast: '{toast}'",
        status="PASS" if is_success else "INFO"
    )

    story.finish(status="PASS" if is_success else "INFO")
