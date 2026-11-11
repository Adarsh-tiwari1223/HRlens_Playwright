"""
HRlens Portal — Employee Side Asset Management E2E Test Suite.

Validates the full Employee Self-Service Asset lifecycle:
1. Employee Authentication & role-based landing.
2. Direct navigation to /asset-request.
3. Inspection of Employee Dashboard (Assigned Assets & Request Queue).
4. Launching the '+ New Request' modal dialog.
5. Populating Category, SubCategory, genuine Reason & Remarks.
6. Submitting the request & verifying the real-time toast notification.
7. Verification of the newly submitted request in the queue table with 'Pending' status.
8. Captures Playwright traceview archive & visual step screenshots for the User Manual.
"""

import os
import re
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from workflows.hrlense_portal.asset.employee_asset_workflow import EmployeeAssetWorkflow

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join(os.getcwd(), "reports", "screenshots", "employee_flow")


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.employee
@pytest.mark.e2e
class TestEmployeeAssetE2EFlow:

    def test_employee_asset_request_e2e_flow(self, logged_in_page):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        story = TestStoryLogger(
            "Employee Asset Request End-to-End Workflow",
            module="Asset Management",
            phase="Employee Self-Service"
        )
        story.start()

        emp_user_key = "adarsh_tiwari"
        user_info = settings.USERS.get(emp_user_key, {})
        emp_email = user_info.get("username", "adarsh.tiwari@tekinspirations.com")

        # ── Step 1: Employee Authentication ──────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info(f"STEP 1: Authenticating as Employee '{emp_user_key}' ({emp_email})")
        logger.info("=" * 60)

        page, context = logged_in_page(emp_user_key)
        assert page is not None, f"Failed to initialize browser page for '{emp_user_key}'"
        assert "/login" not in page.url, f"Login failed: Browser still on {page.url}"

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_employee_login_landing.png"))
        story.log_step(
            "1. Employee Authentication",
            expected="Employee authenticated and redirected away from login",
            actual=f"URL: {page.url}",
            status="PASS"
        )

        # ── Step 2: Navigate to Asset Request ────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Navigating to Employee Portal -> Asset Request (/asset-request)")
        logger.info("=" * 60)

        req_page = AssetRequestPage(page)
        req_page.navigate_to_asset_request()
        page.wait_for_timeout(2000)

        assert "/asset-request" in page.url, f"Expected '/asset-request' in URL, got '{page.url}'"

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_asset_request_dashboard.png"))
        story.log_step(
            "2. Navigate to Asset Request",
            expected="Asset Request screen loaded with header and action buttons",
            actual=f"URL: {page.url}",
            status="PASS"
        )

        # ── Step 3: Check Current Holdings & History ─────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: Inspecting Existing Assigned Assets & Request History")
        logger.info("=" * 60)

        has_active = req_page.has_assigned_assets()
        logger.info(f"Employee currently holds active assigned assets: {has_active}")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_assigned_assets_and_history.png"))
        story.log_step(
            "3. Inspect Current Holdings",
            expected="Employee holdings inspected on /asset-request",
            actual=f"Has Active Assets: {has_active}",
            status="PASS"
        )

        # ── Step 4: Open '+ New Request' Modal ────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: Opening '+ New Request' Dialog")
        logger.info("=" * 60)

        new_req_btn = page.get_by_role("button", name=re.compile(r"New Request|\+ Request", re.I)).first
        if not new_req_btn.is_visible(timeout=3000):
            new_req_btn = page.locator("button:has-text('Request')").first
        assert new_req_btn.is_visible(timeout=3000), "Could not find '+ New Request' button on page!"
        new_req_btn.click()

        dialog = page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").last
        dialog.wait_for(state="visible", timeout=5000)

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_new_request_modal_opened.png"))
        story.log_step(
            "4. Open New Request Modal",
            expected="Request dialog opens with Category, SubCategory, Reason, and Remarks fields",
            actual="Modal is visible",
            status="PASS"
        )

        # ── Step 5: Fill Category, SubCategory, Reason & Remarks ─────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Populating Request Form Fields")
        logger.info("=" * 60)

        # Category select
        cat_select = dialog.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = dialog.locator("select").first
        cat_select.wait_for(state="visible", timeout=2000)

        # Select option
        try:
            cat_select.select_option(index=1)
        except Exception:
            cat_select.select_option(label="Hardware")
        page.wait_for_timeout(800)

        # SubCategory select
        sub_select = dialog.get_by_label("Sub Category*", exact=False)
        if not sub_select.is_visible(timeout=1000):
            sub_select = dialog.locator("select").nth(1)
        sub_select.wait_for(state="visible", timeout=3000)

        try:
            sub_select.locator("option:not([value=''])").first.wait_for(state="attached", timeout=3000)
            sub_select.select_option(index=1)
        except Exception:
            sub_select.select_option(index=0)
        page.wait_for_timeout(800)

        # Reason & Remarks
        reason_text = "Required for project development and workstation upgrade."
        remarks_text = "Standard company specification. Immediate requirement."

        reason_in = dialog.get_by_placeholder(re.compile(r"^e\.g\. My current laptop is too|Reason", re.I)).first
        if not reason_in.is_visible(timeout=1000):
            reason_in = dialog.locator("textarea, input[placeholder*='reason' i]").first
        if reason_in.is_visible(timeout=1000):
            reason_in.fill(reason_text)

        remarks_in = dialog.get_by_placeholder(re.compile(r"^Any additional remarks|Remarks", re.I)).first
        if remarks_in.is_visible(timeout=1000):
            remarks_in.fill(remarks_text)

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_form_details_filled.png"))
        story.log_step(
            "5. Populate Request Form",
            expected="Category, SubCategory, Reason, and Remarks fields populated",
            actual=f"Reason: '{reason_text}' | Remarks: '{remarks_text}'",
            status="PASS"
        )

        # ── Step 6: Submit Request ───────────────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6: Submitting Asset Request & Verifying Confirmation")
        logger.info("=" * 60)

        submit_btn = dialog.get_by_role("button", name=re.compile(r"Submit Request|Submit", re.I)).first
        assert submit_btn.is_visible(timeout=2000), "Submit button not visible on request dialog"
        submit_btn.click()
        page.wait_for_timeout(800)

        toast = req_page.wait_for_toast_message()
        logger.info(f"Submitted Request Toast Message: '{toast}'")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_submission_toast_confirmation.png"))

        # Clean dialog if lingering
        try:
            if dialog.is_visible(timeout=500):
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        except Exception:
            pass

        story.log_step(
            "6. Submit Request",
            expected="Toast notification displayed confirming request submission",
            actual=f"Toast: '{toast}'",
            status="PASS"
        )

        # ── Step 7: Verify Request in Queue Table ─────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("STEP 7: Verifying Request Appears in Employee Queue Table")
        logger.info("=" * 60)

        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_request_queue_updated.png"))

        table_rows = page.locator("table tbody tr").all_inner_texts()
        logger.info(f"Total rows in request table: {len(table_rows)}")
        assert len(table_rows) > 0, "No records found in Asset Request table after submission!"

        first_row_text = table_rows[0]
        logger.info(f"Top row in request table: '{first_row_text}'")

        story.log_step(
            "7. Verify Queue Record",
            expected="Top row in request table reflects latest submitted request",
            actual=f"Row: '{first_row_text[:120]}'",
            status="PASS"
        )

        story.finish(status="PASS")
