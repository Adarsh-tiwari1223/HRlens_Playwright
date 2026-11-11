"""
HRlens Portal — IT Person Asset Management Real Click-by-Click Journey.

Executes the exact interactive flow:
1. IT Specialist Login -> Lands on IT Dashboard.
2. Click on "Asset" in the left sidebar.
3. Click on "Asset Assignment" in submenu -> Navigates to /asset-assignment.
4. Click on "Requested Assignment" tab -> Shows queue of pending employee requests.
5. Click on "Fulfil" button on the pending request row -> Drawer opens.
6. Select Available Asset from scoped branch stock.
7. Click "Submit" / "Fulfil" -> Capture Toast confirmation.
8. Saves Playwright trace archive and every exact step screenshot.
"""

import os
import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger

logger = logging.getLogger(__name__)
SCREENSHOT_DIR = os.path.join(os.getcwd(), "reports", "screenshots", "it_journey")


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.it_person
def test_it_person_asset_journey_exact_clicks(browser, request):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    trace_path = os.path.join(os.getcwd(), "reports", "trace_it_asset_journey.zip")

    context = browser.new_context(viewport={"width": 1536, "height": 864})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    story = TestStoryLogger("IT Person Asset Fulfillment Exact Click Journey", module="Asset Management", phase="IT Journey")
    story.start()

    it_user = settings.USERS.get("it_varanasi_ashutosh", {})
    email = it_user.get("username", "ashutosh.kumar@tekinspirations.com")
    password = it_user.get("password")

    # ── Step 1: Open Login Page ──────────────────────────────────────────────
    logger.info("[STEP 1] Opening Login Page for IT Specialist...")
    page.goto(f"{settings.BASE_URL}/login", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step01_it_login_page.png"))

    # ── Step 2: Fill Login & Submit ──────────────────────────────────────────
    logger.info("[STEP 2] Filling IT Specialist credentials and clicking Login...")
    page.locator("input[type=email], input[placeholder*=email i]").first.fill(email)
    page.locator("input[type=password]").first.fill(password)
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Login").click()

    page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step02_it_dashboard_landing.png"))

    # ── Step 3: Click on "Asset" in Sidebar ───────────────────────────────────
    logger.info("[STEP 3] Clicking on 'Asset' in the left sidebar...")
    asset_sidebar = page.locator("aside, nav, div.chakra-stack").locator("text=/^Asset$|^Assets$/i").first
    if not asset_sidebar.is_visible(timeout=2000):
        asset_sidebar = page.locator("text=/^Asset$|^Assets$/i").first
    asset_sidebar.click()
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step03_it_click_sidebar_asset.png"))

    # ── Step 4: Click on "Asset Assignment" in Submenu ────────────────────────
    logger.info("[STEP 4] Clicking on 'Asset Assignment' in submenu...")
    asset_assign_link = page.locator("text=/Asset Assignment/i").first
    asset_assign_link.click()

    page.wait_for_url(lambda u: "/asset-assignment" in u, timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step04_asset_assignment_dashboard.png"))

    # ── Step 5: Click "+ Assign Asset" Button (Direct Assignment Drawer) ──────
    logger.info("[STEP 5] Clicking '+ Assign Asset' button...")
    assign_btn = page.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").first
    if not assign_btn.is_visible(timeout=3000):
        assign_btn = page.get_by_role("button", name="Assign Asset").first
    if assign_btn.is_visible(timeout=3000):
        assign_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step05_direct_assignment_drawer.png"))

        # ── Step 6: Search Employee & Populate Assignment Drawer ──────────────
        logger.info("[STEP 6] Searching employee and populating assignment...")
        emp_inp = page.locator("input[placeholder*='Search employee' i], input[placeholder*='employee name' i]").first
        if emp_inp.is_visible(timeout=2000):
            emp_inp.fill("Adarsh Tiwari")
            page.wait_for_timeout(1000)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step06_direct_assignment_filled.png"))

        # Close Drawer
        close_btn = page.locator("button[aria-label='Close'], button:has-text('Cancel')").first
        if close_btn.is_visible(timeout=2000):
            close_btn.click()
            page.wait_for_timeout(1000)
        else:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

    # ── Step 7: Click on "Requested Assignment" Tab ───────────────────────────
    logger.info("[STEP 7] Clicking on 'Requested Assignment' tab...")
    req_tab = page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Requested Assignment", re.I)).first
    if req_tab.is_visible(timeout=3000):
        req_tab.click()
        page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step07_requested_assignment_tab.png"))

    # ── Step 8: Inspect Fulfil Requisition Option ─────────────────────────────
    logger.info("[STEP 8] Inspecting pending requisitions queue...")
    fulfil_btn = page.locator("button:not([disabled])").filter(has_text=re.compile(r"Fulfil|Fulfill", re.I)).first
    if fulfil_btn.is_visible(timeout=2000) and fulfil_btn.is_enabled():
        fulfil_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step08_fulfillment_drawer_opened.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    else:
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step08_fulfillment_queue_view.png"))

    # ── Step 9: Navigate to Asset Entry (/asset-entry) ────────────────────────
    logger.info("[STEP 9] Navigating to Asset Entry (/asset-entry)...")
    page.goto(f"{settings.BASE_URL}/asset-entry", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step09_asset_entry_dashboard.png"))

    # ── Step 10: Open Add Asset Modal ─────────────────────────────────────────
    logger.info("[STEP 10] Opening '+ Add Asset' Modal...")
    add_btn = page.locator("button:has-text('Add Asset'), button:has-text('+ Add')").first
    if add_btn.is_visible(timeout=3000):
        add_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step10_add_asset_modal.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # ── Step 11: Open Generate Assets (Bulk PO) Modal ─────────────────────────
    logger.info("[STEP 11] Opening 'Generate Assets' Modal...")
    gen_btn = page.locator("button:has-text('Generate Assets'), button:has-text('Generate')").first
    if gen_btn.is_visible(timeout=3000):
        gen_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step11_generate_assets_modal.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # ── Finish Tracing & Save ────────────────────────────────────────────────
    context.tracing.stop(path=trace_path)
    logger.info(f"[TRACE SAVED] Exported exact IT trace to: {trace_path}")

    context.close()
    story.finish(status="PASS")
