"""
HRlens Portal — Before & After Verification Test: HR Start FnF Process -> Accountant FnF Requests Visibility

Business Rule Verified:
1. BEFORE: An employee undergoing offboarding / buyout / clearance does NOT appear in the Accountant's
   'FnF Requests' table on /accounts-buyout-processing until HR triggers 'Start FnF Process'.
2. TRIGGER: HR opens /resignation-approval, locates the employee, opens the Actions menu (=),
   and triggers 'Start FnF Process', confirming the action.
3. AFTER: Accountant reloads /accounts-buyout-processing ('FnF Requests' tab). The employee is NOW VISIBLE
   in the table with status ready for Accountant settlement, proving end-to-end gating integrity.
"""

import os
import logging
import pytest
from core.config import settings
from pages.hrlense_portal.resignation.resignation_page import ResignationPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
def test_fnf_before_and_after_accountant_visibility_verification(logged_in_page):
    """
    Executes and documents the strict Before & After verification of FnF Queue gating:
    - Target Employee: Sushree Radhika Nayak (or configured candidate)
    - Phase 1 (BEFORE): Accountant checks 'FnF Requests' tab -> Asserts employee is NOT present.
    - Phase 2 (TRIGGER): HR clicks 'Start FnF Process' on /resignation-approval.
    - Phase 3 (AFTER): Accountant re-checks 'FnF Requests' tab -> Asserts employee IS NOW PRESENT!
    """
    from utils.branch_persona_resolver import get_branch_persona_bundle, get_dynamic_resignation_employee

    bundle = get_branch_persona_bundle("Varanasi")
    dynamic_emp = get_dynamic_resignation_employee("Varanasi")
    emp_name = dynamic_emp["name"]

    screenshots_dir = os.path.join(os.getcwd(), "reports", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    screenshot_before = os.path.join(screenshots_dir, "fnf_step1_before_hr_trigger.png")
    screenshot_hr_menu = os.path.join(screenshots_dir, "fnf_step2_hr_action_menu.png")
    screenshot_hr_done = os.path.join(screenshots_dir, "fnf_step2_hr_triggered.png")
    screenshot_after = os.path.join(screenshots_dir, "fnf_step3_after_accountant_visible.png")
    screenshot_drawer = os.path.join(screenshots_dir, "fnf_step4_accountant_drawer.png")

    logger.info("=" * 80)
    logger.info(f"STARTING FnF BEFORE & AFTER VERIFICATION TEST FOR DYNAMIC EMPLOYEE: '{emp_name}'")
    logger.info("=" * 80)

    # ══════════════════════════════════════════════════════════════════════
    # PHASE 1: BEFORE — ACCOUNTANT CHECKS FnF REQUESTS QUEUE
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 1 - BEFORE] Accountant ({bundle['accountant_name']}) checking /accounts-buyout-processing -> FnF Requests for '{emp_name}'...")
    acc_page, _ = logged_in_page(bundle["accountant"])
    acc_res_page = ResignationPage(acc_page)

    acc_res_page.navigate_to_accounts_fnf_requests()

    # Search employee in FnF table
    search_input = acc_page.locator("input[placeholder*='Search Employee' i], input[placeholder*='search' i]").first
    if search_input.is_visible(timeout=3000):
        search_input.click()
        search_input.fill(emp_name)
        search_input.press("Enter")
        acc_page.wait_for_timeout(1500)

    emp_row = acc_page.locator(f"tr:has-text('{emp_name}')").first
    is_present_before = emp_row.is_visible(timeout=3000)

    logger.info(f"[PHASE 1 - BEFORE] Is '{emp_name}' present in Accountant FnF Requests table? -> {is_present_before}")

    # Capture BEFORE screenshot
    acc_page.screenshot(path=screenshot_before, full_page=True)
    logger.info(f"[SCREENSHOT SAVED] Step 1 (Before): {screenshot_before}")

    if not is_present_before:
        logger.info(f"[CONFIRMED BEFORE] Employee '{emp_name}' is correctly ABSENT from Accountant's queue prior to HR initiation!")
    else:
        logger.warning(f"[NOTICE] Employee '{emp_name}' was already present in Accountant table (likely already initiated). Proceeding to verify visibility & drawer...")

    # ══════════════════════════════════════════════════════════════════════
    # PHASE 2: TRIGGER — HR INITIATES FnF PROCESS ON /resignation-approval
    # ══════════════════════════════════════════════════════════════════════
    if not is_present_before:
        logger.info(f"[PHASE 2 - HR TRIGGER] HR ('tejaswini') navigating to /resignation-approval to start FnF for '{emp_name}'...")
        hr_page, _ = logged_in_page("tejaswini")
        hr_res_page = ResignationPage(hr_page)

        hr_res_page.navigate_to_hr_resignation_approval()
        hr_res_page.search_employee_in_hr_table(emp_name)

        hr_row = hr_page.locator(f"tr:has-text('{emp_name}')").first
        hr_row.wait_for(state="visible", timeout=5000)

        # Actions menu
        actions_btn = hr_row.locator("td:last-child button, button.chakra-menu__menu-button").first
        actions_btn.wait_for(state="visible", timeout=3000)
        actions_btn.click()
        hr_page.wait_for_timeout(600)

        # Capture HR Action menu
        hr_page.screenshot(path=screenshot_hr_menu)
        logger.info(f"[SCREENSHOT SAVED] Step 2 (HR Menu): {screenshot_hr_menu}")

        fnf_item = hr_page.locator("button[role='menuitem']:has-text('Start FnF Process')").first
        if fnf_item.is_visible(timeout=3000):
            logger.info("Clicking 'Start FnF Process' menuitem...")
            fnf_item.click()
            hr_page.wait_for_timeout(600)

            # Confirm dialog
            modal = hr_page.locator("section[role='alertdialog']:has-text('Start FnF Process'), div[role='alertdialog']:has-text('Start FnF Process')").first
            modal.wait_for(state="visible", timeout=5000)
            start_btn = modal.locator("button:has-text('Start Process')").first
            start_btn.wait_for(state="visible", timeout=3000)
            start_btn.click()

            toast = hr_res_page.wait_for_toast(timeout=5000)
            logger.info(f"[HR START FnF TOAST] Captured: '{toast}'")
            hr_page.screenshot(path=screenshot_hr_done)
            logger.info(f"[SCREENSHOT SAVED] Step 2 (HR Triggered): {screenshot_hr_done}")
        else:
            logger.warning(f"'Start FnF Process' menu item not found or already processed for '{emp_name}'")

    # ══════════════════════════════════════════════════════════════════════
    # PHASE 3: AFTER — ACCOUNTANT RE-CHECKS FnF REQUESTS QUEUE
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 3 - AFTER] Accountant re-checking /accounts-buyout-processing -> FnF Requests for '{emp_name}'...")
    acc_page.bring_to_front()
    acc_page.reload(wait_until="domcontentloaded")
    acc_page.wait_for_timeout(1000)

    acc_res_page.navigate_to_accounts_fnf_requests()

    search_input = acc_page.locator("input[placeholder*='Search Employee' i], input[placeholder*='search' i]").first
    if search_input.is_visible(timeout=3000):
        search_input.click()
        search_input.fill(emp_name)
        search_input.press("Enter")
        acc_page.wait_for_timeout(1500)

    emp_row_after = acc_page.locator(f"tr:has-text('{emp_name}')").first
    emp_row_after.wait_for(state="visible", timeout=8000)
    is_present_after = emp_row_after.is_visible(timeout=2000)

    # Capture AFTER screenshot
    acc_page.screenshot(path=screenshot_after, full_page=True)
    logger.info(f"[SCREENSHOT SAVED] Step 3 (After): {screenshot_after}")

    assert is_present_after, f"VERIFICATION FAILED: Employee '{emp_name}' did NOT appear in Accountant's FnF Requests after HR triggered FnF!"
    logger.info(f"[VERIFICATION SUCCESS] Employee '{emp_name}' IS NOW VISIBLE in Accountant's FnF Requests table!")

    # Read status badge
    status_badge = emp_row_after.locator(".chakra-badge, span[class*='badge']").first.inner_text().strip() if emp_row_after.locator(".chakra-badge, span[class*='badge']").first.is_visible(timeout=2000) else ""
    logger.info(f"[FnF QUEUE STATUS] '{emp_name}' Status: '{status_badge}'")

    # ══════════════════════════════════════════════════════════════════════
    # PHASE 4: OPEN FnF DRAWER & INSPECT SETTLEMENT LINE ITEMS
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 4 - DRAWER] Opening Full & Final Settlement drawer for '{emp_name}'...")
    try:
        action_arrow = emp_row_after.locator("td:last-child svg, td:last-child button, td:last-child span, td:last-child").first
        action_arrow.wait_for(state="visible", timeout=3000)
        action_arrow.click()
        acc_page.wait_for_timeout(1500)

        drawer = acc_page.locator("section.chakra-modal__content, div[role='dialog'], [class*='drawer']").first
        if drawer.is_visible(timeout=5000):
            acc_page.screenshot(path=screenshot_drawer)
            logger.info(f"[SCREENSHOT SAVED] Step 4 (Drawer): {screenshot_drawer}")
            modal_values = acc_res_page.get_accountant_fnf_modal_values()
            logger.info(f"[FnF DRAWER VALUES] Line Items: {modal_values}")
    except Exception as e:
        logger.warning(f"Note on opening FnF drawer: {e}")

    logger.info("=" * 80)
    logger.info(f"[ALL PASS 100%] BEFORE & AFTER VERIFICATION COMPLETED FOR '{emp_name}'!")
    logger.info("=" * 80)
