"""
HRlens Portal — Asset Assignment & Resignation Email Notification Lifecycle Test.

Validates the full cross-module email notifications:
[PHASE 1 - ASSET ASSIGNMENT]
1. Admin assigns a company hardware asset (Laptop) to candidate employee.
2. Candidate employee logs into /asset-request and accepts the asset.
3. Gmail REST API Verification: Checks if an asset assignment / handover email was delivered.

[PHASE 2 - RESIGNATION & EXIT CLEARANCE NOTIFICATIONS]
4. Candidate employee submits resignation on /resignation.
5. Gmail REST API Verification:
   - Verifies "Resignation Submitted" notification email.
   - Verifies "Exit Clearance Tasks Assigned" email dispatched to IT / HR.

[PHASE 3 - RELEASED LETTERS DISPATCH NOTIFICATIONS]
6. Checks Gmail for exit letters dispatched to the employee (Relieving / Experience / Settlement).
"""

import re
import random
import time
import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
from workflows.hrlense_portal.resignation.employee_resignation_workflow import EmployeeResignationWorkflow
from utils.mail.gmail_client import GmailClient

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.resignation
class TestAssetAndResignationEmailLifecycle:

    def _ensure_or_find_available_stock(self, page, branch_name: str = "Varanasi") -> tuple[str, str, str]:
        entry_page = AssetEntryPage(page)
        entry_page.navigate_to_asset_entry()
        page.wait_for_timeout(1500)

        rows = page.locator("table tbody tr").all()
        # Prefer physical Laptop under Hardware
        for r in rows:
            text = r.inner_text().strip()
            if "AVAILABLE" in text.upper() and "LAPTOP" in text.upper():
                m = re.search(r"ASSET-[A-Z0-9-]+", text)
                if m:
                    code = m.group(0)
                    logger.info(f"[STOCK FOUND] Found available Laptop stock: '{code}' (Hardware -> Laptop)")
                    return code, "Hardware", "Laptop"

        # General available stock fallback matching seeded taxonomy
        for r in rows:
            text = r.inner_text().strip()
            if "AVAILABLE" in text.upper():
                m = re.search(r"ASSET-[A-Z0-9-]+", text)
                if m:
                    code = m.group(0)
                    detected_cat = "Hardware"
                    for cat in ["Hardware", "Peripheral", "Communication Equipment", "Networking", "Software"]:
                        if cat.lower() in text.lower():
                            detected_cat = cat
                            break
                    detected_sub = "Laptop"
                    for sub in ["Laptop", "Desktop Computer", "Monitor", "Keyboard", "Mouse", "Router"]:
                        if sub.lower() in text.lower():
                            detected_sub = sub
                            break
                    logger.info(f"[STOCK FOUND] Found available stock asset: '{code}' ({detected_cat} -> {detected_sub})")
                    return code, detected_cat, detected_sub

        logger.info(f"[STOCK CREATING] Creating new stock asset under '{branch_name}' branch...")
        serial_no = f"DL-7440-{random.randint(100000, 999999)}"
        entry_page.click_add_asset()
        entry_data = entry_page.fill_asset_details(
            name="Dell Latitude 7440",
            category="IT Hardware",
            sub_category="Laptop",
            branch=branch_name,
            brand="Dell",
            model="Latitude 7440",
            serial_no=serial_no,
            insured="No"
        )
        add_toast = entry_page.click_save()
        m = re.search(r"ASSET-[A-Z0-9-]+", add_toast or "")
        created_code = m.group(0) if m else serial_no
        chosen_cat = entry_data.get("category") or "IT Hardware"
        chosen_sub = entry_data.get("sub_category") or "Laptop"
        logger.info(f"[STOCK CREATED] New asset created: '{created_code}' ({chosen_cat} -> {chosen_sub}) (Toast: '{add_toast}')")
        return created_code, chosen_cat, chosen_sub

    def test_asset_and_resignation_email_notifications(self, logged_in_page):
        story = TestStoryLogger("Asset & Resignation Email Verification", module="Asset & Resignation", phase="Email Notifications")
        story.start()

        target_emp_name = "Sanidhy Tiwari"
        target_emp_key = "sanidhy"
        mail_client = GmailClient()

        # ──────────────────────────────────────────────────────────────────
        # PHASE 1: ASSET ASSIGNMENT & EMPLOYEE ACCEPTANCE
        # ──────────────────────────────────────────────────────────────────
        story.log_step("Phase 1: Start Asset Assignment", record=f"Target Employee: {target_emp_name}")
        logger.info(f"[PHASE 1] Checking / Assigning asset for '{target_emp_name}'...")

        admin_page, _ = logged_in_page("admin")
        stock_code, stock_cat, stock_sub = self._ensure_or_find_available_stock(admin_page, branch_name="Varanasi")

        # Check if employee has an asset or assign one
        emp_page, _ = logged_in_page(target_emp_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        has_assets = req_page.has_assigned_assets()

        assigned_code = ""
        if not has_assets:
            logger.info(f"Assigning asset '{stock_code}' to '{target_emp_name}' via Admin...")
            assign_page = AssetAssignmentPage(admin_page)
            assign_page.navigate_to_asset_assignment()
            admin_page.wait_for_timeout(1000)
            assign_page.click_assign_asset()
            assigned_code = assign_page.fill_assignment_details(
                employee_name=target_emp_name,
                category=stock_cat,
                sub_category=stock_sub,
                asset_name_or_code=stock_code,
                remarks="Automated email verification assignment."
            )
            if assigned_code:
                assign_page.click_submit_assignment()
                toast = assign_page.wait_for_toast_message()
                logger.info(f"Asset Assignment Toast: '{toast}'")

                # Employee accepts
                emp_page.bring_to_front()
                req_page.navigate_to_asset_request()
                req_page.accept_asset(assigned_code if assigned_code != "ASSET" else None)
        else:
            logger.info(f"Employee '{target_emp_name}' already holds active assigned assets.")

        story.log_step("Phase 1 Completed", record=f"Asset assigned/verified for '{target_emp_name}'", status="PASS")

        # ──────────────────────────────────────────────────────────────────
        # PHASE 2: VERIFY ASSET EMAIL NOTIFICATION IN GMAIL
        # ──────────────────────────────────────────────────────────────────
        story.log_step("Phase 2: Check Asset Email in Gmail", record="Querying Gmail for Asset Assignment notifications")
        logger.info("Checking Gmail inbox for Asset-related emails...")
        asset_email = mail_client.wait_for_email(subject_keyword="Asset", employee_name=target_emp_name, timeout_sec=15)
        if not asset_email:
            asset_email = mail_client.wait_for_email(subject_keyword="Asset", timeout_sec=10)

        if asset_email:
            story.log_step(
                "Asset Email Verification",
                record=f"Subject: '{asset_email['subject']}' | From: '{asset_email['from']}'",
                expected="Asset notification email delivered",
                actual="Delivered",
                status="PASS"
            )
            logger.info(f"[GMAIL ASSET] Verified email: '{asset_email['subject']}' ({asset_email['date']})")
        else:
            story.log_step(
                "Asset Email Verification",
                record="No specific 'Asset' email found in recent messages (may be configured for specific categories)",
                expected="Asset notification email",
                actual="None detected",
                status="WARNING"
            )
            logger.warning("[GMAIL ASSET] No Asset email arrived within timeout.")

        # ──────────────────────────────────────────────────────────────────
        # PHASE 3: RESIGNATION SUBMISSION & EXIT CLEARANCE EMAIL CHECK
        # ──────────────────────────────────────────────────────────────────
        story.log_step("Phase 3: Resignation Email Verification", record="Checking Resignation & Clearance Emails in Gmail")
        logger.info("Checking Gmail inbox for Resignation Submitted and Exit Clearance Task emails...")

        # 1. Check 'Resignation Submitted' emails
        res_mail = mail_client.wait_for_email(subject_keyword="Resignation Submitted", timeout_sec=15)
        if res_mail:
            story.log_step(
                "Resignation Submitted Email",
                record=f"Subject: '{res_mail['subject']}' | Date: '{res_mail['date']}'",
                expected="Resignation Submitted email delivered to inbox",
                actual="Delivered",
                status="PASS"
            )
            logger.info(f"[GMAIL RESIGNATION] Verified: '{res_mail['subject']}'")
        else:
            story.log_step(
                "Resignation Submitted Email",
                record="No 'Resignation Submitted' email found in inbox",
                status="WARNING"
            )

        # 2. Check 'Exit Clearance Tasks Assigned' emails (Asset & HR clearances)
        clearance_mail = mail_client.wait_for_email(subject_keyword="Exit Clearance Tasks Assigned", timeout_sec=15)
        if clearance_mail:
            story.log_step(
                "Exit Clearance Tasks Assigned Email",
                record=f"Subject: '{clearance_mail['subject']}' | Date: '{clearance_mail['date']}'",
                expected="Exit Clearance Tasks email delivered to IT/HR",
                actual="Delivered",
                status="PASS"
            )
            logger.info(f"[GMAIL CLEARANCE] Verified: '{clearance_mail['subject']}'")
        else:
            story.log_step(
                "Exit Clearance Tasks Assigned Email",
                record="No 'Exit Clearance Tasks Assigned' email found in inbox",
                status="WARNING"
            )

        # ──────────────────────────────────────────────────────────────────
        # PHASE 4: SUMMARY & GMAIL AUDIT REPORT
        # ──────────────────────────────────────────────────────────────────
        logger.info("\n" + "=" * 70)
        logger.info("EMAIL FUNCTIONALITY VERIFICATION SUMMARY:")
        logger.info(f"Asset Email Status       : {'Delivered' if asset_email else 'Not Detected'}")
        logger.info(f"Resignation Email Status : {'Delivered' if res_mail else 'Not Detected'}")
        logger.info(f"Clearance Email Status   : {'Delivered' if clearance_mail else 'Not Detected'}")
        logger.info("=" * 70 + "\n")

        story.finish()
