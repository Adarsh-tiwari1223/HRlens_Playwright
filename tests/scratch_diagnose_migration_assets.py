import os
import logging
import pytest
from core.config import settings

logger = logging.getLogger("migration_diag")

@pytest.mark.ui
def test_diagnose_it_and_admin_roles(logged_in_page):
    screenshots_dir = os.path.join(os.getcwd(), "reports", "migration_audit_screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    # 1. Log in as IT Person (Ashutosh Kumar)
    logger.info("Logging in as IT Person: 'it_varanasi_ashutosh'...")
    it_page, _ = logged_in_page("it_varanasi_ashutosh")
    it_page.bring_to_front()
    it_page.wait_for_timeout(2000)

    # Check IT Sidebar items
    sidebar_items = [b.inner_text().strip() for b in it_page.locator("nav a, div[class*='sidebar'] a, div[class*='nav'] a, aside a").all()]
    logger.info(f"IT Person Sidebar Links: {sidebar_items}")
    it_page.screenshot(path=os.path.join(screenshots_dir, "05_it_dashboard.png"), full_page=True)

    # Check /asset-stock as IT
    logger.info("IT visiting /asset-stock...")
    it_page.goto(f"{settings.BASE_URL}/asset-stock", timeout=30000)
    it_page.wait_for_load_state("domcontentloaded")
    it_page.wait_for_timeout(3000)
    it_page.screenshot(path=os.path.join(screenshots_dir, "06_it_asset_stock.png"), full_page=True)
    stock_text = it_page.locator("table").first.inner_text() if it_page.locator("table").first.is_visible(timeout=2000) else "NO TABLE"
    logger.info(f"IT Asset Stock Table Preview:\n{stock_text[:400]}")

    # 2. Log in as Admin to inspect Master menu
    logger.info("Logging in as Admin...")
    admin_page, _ = logged_in_page("admin")
    admin_page.bring_to_front()
    admin_page.wait_for_timeout(2000)

    admin_page.goto(f"{settings.BASE_URL}/dashboard", timeout=30000)
    admin_page.wait_for_timeout(2000)

    # Click Profile Menu -> Master
    profile_btn = admin_page.locator("button.chakra-menu__menu-button:has(.chakra-avatar), button:has(.chakra-avatar)").first
    if profile_btn.is_visible(timeout=3000):
        profile_btn.click()
        admin_page.wait_for_timeout(1000)
        master_item = admin_page.locator("[role='menuitem']:has-text('Master'), a:has-text('Master')").first
        if master_item.is_visible(timeout=2000):
            master_item.click()
            admin_page.wait_for_load_state("domcontentloaded")
            admin_page.wait_for_timeout(3000)
            logger.info(f"Current URL after clicking Master: {admin_page.url}")
            admin_page.screenshot(path=os.path.join(screenshots_dir, "07_admin_master_page.png"), full_page=True)
            
            # Print links or cards visible on Master page
            master_links = [l.inner_text().strip() for l in admin_page.locator("a, button, div.chakra-card").all() if l.inner_text().strip()]
            logger.info(f"Master Page Items Sample: {master_links[:20]}")
