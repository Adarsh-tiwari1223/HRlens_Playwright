"""
HRlens Portal — Employee Asset Request Real Click-by-Click Journey.

Executes the exact interactive flow:
1. Employee Login -> Lands on Dashboard.
2. Click on "Asset" in the left sidebar.
3. Click on "Asset Request" in the submenu -> Navigates to /asset-request.
4. Click on "+ New Request" button -> Modal opens.
5. Fill Category, Sub Category, Reason & Remarks.
6. Click "Submit Request" -> Capture Toast confirmation.
7. Click on "Request History" tab -> Display real-time status (Pending).
8. Saves Playwright trace archive and every exact step screenshot.
"""

import os
import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger

logger = logging.getLogger(__name__)
SCREENSHOT_DIR = os.path.join(os.getcwd(), "reports", "screenshots", "employee_journey")


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.employee
def test_employee_asset_journey_exact_clicks(browser, request):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    trace_path = os.path.join(os.getcwd(), "reports", "trace_employee_asset_journey.zip")

    context = browser.new_context(viewport={"width": 1536, "height": 864})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    story = TestStoryLogger("Employee Asset Request Exact Click Journey", module="Asset Management", phase="Employee Journey")
    story.start()

    emp_user = settings.USERS.get("adarsh_tiwari", {})
    email = emp_user.get("username", "adarsh.tiwari@tekinspirations.com")
    password = emp_user.get("password")

    # ── Step 1: Open Login Page ──────────────────────────────────────────────
    logger.info("[STEP 1] Opening Login Page...")
    page.goto(f"{settings.BASE_URL}/login", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step01_login_page.png"))

    # ── Step 2: Fill Login & Submit ──────────────────────────────────────────
    logger.info("[STEP 2] Filling credentials and clicking Login...")
    page.locator("input[type=email], input[placeholder*=email i]").first.fill(email)
    page.locator("input[type=password]").first.fill(password)
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Login").click()

    page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step02_dashboard_landing.png"))

    # ── Step 3: Click on "Asset" in Sidebar ───────────────────────────────────
    logger.info("[STEP 3] Clicking on 'Asset' in the left sidebar...")
    asset_sidebar = page.locator("aside, nav, div.chakra-stack").locator("text=/^Asset$|^Assets$/i").first
    if not asset_sidebar.is_visible(timeout=2000):
        asset_sidebar = page.locator("text=/^Asset$|^Assets$/i").first
    asset_sidebar.click()
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step03_click_sidebar_asset.png"))

    # ── Step 4: Click on "Asset Request" in Submenu ───────────────────────────
    logger.info("[STEP 4] Clicking on 'Asset Request' in the submenu...")
    asset_req_link = page.locator("text=/Asset Request/i").first
    asset_req_link.click()

    page.wait_for_url(lambda u: "/asset-request" in u, timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step04_asset_request_page.png"))

    # ── Step 5: Click on "+ New Request" Button ──────────────────────────────
    logger.info("[STEP 5] Clicking on '+ New Request' button...")
    new_req_btn = page.locator("button").filter(has_text=re.compile(r"New Request|\+ Request", re.I)).first
    new_req_btn.click()

    dialog = page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").last
    dialog.wait_for(state="visible", timeout=6000)
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step05_modal_opened.png"))

    # ── Step 6: Fill Requisition Form ────────────────────────────────────────
    logger.info("[STEP 6] Selecting Category, Sub Category, Reason & Remarks...")
    cat_select = dialog.get_by_label("Category*", exact=True)
    if not cat_select.is_visible(timeout=1000):
        cat_select = dialog.locator("select").first
    cat_select.wait_for(state="visible", timeout=2000)

    try:
        cat_select.select_option(index=1)
    except Exception:
        cat_select.select_option(label="Hardware")
    page.wait_for_timeout(1000)

    sub_select = dialog.get_by_label("Sub Category*", exact=False)
    if not sub_select.is_visible(timeout=1000):
        sub_select = dialog.locator("select").nth(1)
    sub_select.wait_for(state="visible", timeout=3000)

    try:
        sub_select.locator("option:not([value=''])").first.wait_for(state="attached", timeout=3000)
        sub_select.select_option(index=1)
    except Exception:
        sub_select.select_option(index=0)
    page.wait_for_timeout(1000)

    reason_in = dialog.get_by_placeholder(re.compile(r"^e\.g\. My current laptop is too|Reason", re.I)).first
    if not reason_in.is_visible(timeout=1000):
        reason_in = dialog.locator("textarea, input[placeholder*='reason' i]").first
    reason_in.fill("Primary work system required for project delivery and automation testing.")

    remarks_in = dialog.get_by_placeholder(re.compile(r"^Any additional remarks|Remarks", re.I)).first
    if remarks_in.is_visible(timeout=1000):
        remarks_in.fill("Standard company specifications. Immediate allocation needed.")

    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step06_form_filled.png"))

    # ── Step 7: Click Submit & Capture Toast ──────────────────────────────────
    logger.info("[STEP 7] Clicking 'Submit Request' button...")
    submit_btn = dialog.get_by_role("button", name=re.compile(r"Submit Request|Submit", re.I)).first
    submit_btn.click()
    page.wait_for_timeout(800)

    # Toast screenshot
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step07_toast_confirmation.png"))

    # Clean dialog if lingering
    try:
        if dialog.is_visible(timeout=500):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
    except Exception:
        pass

    # ── Step 8: Click on "Request History" Tab ────────────────────────────────
    logger.info("[STEP 8] Clicking on 'Request History' tab...")
    page.wait_for_timeout(1000)
    history_tab = page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Request History|History", re.I)).first
    if history_tab.is_visible(timeout=3000):
        history_tab.click()
        page.wait_for_timeout(1500)

    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step08_request_history_tab_pending.png"))

    # ── Finish Tracing & Save ────────────────────────────────────────────────
    context.tracing.stop(path=trace_path)
    logger.info(f"[TRACE SAVED] Exported exact trace to: {trace_path}")

    context.close()
    story.finish(status="PASS")
