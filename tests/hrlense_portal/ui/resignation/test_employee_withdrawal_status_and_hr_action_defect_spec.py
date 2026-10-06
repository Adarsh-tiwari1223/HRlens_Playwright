"""
Defect Specification Suite: Employee Resignation Withdrawal Status & HR Action Gating
Mapped to FRD Point 3:
- Defect 1A (TC-RSG-DEF-001): Status Nomenclature Ambiguity ('REVOKE REQUESTED' vs 'WITHDRAWAL REQUESTED')
- Defect 1B (TC-RSG-DEF-002): Missing HR 'Approve Withdrawal' and 'Reject Withdrawal' Actions
"""

import logging
import pytest
from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
from utils.branch_persona_resolver import get_branch_persona_bundle

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
@pytest.mark.defect
class TestEmployeeWithdrawalStatusAndHrActionDefectSpec:

    def test_tc_rsg_def_001_withdrawal_status_nomenclature_ambiguity(self, logged_in_page):
        """
        [DEFECT 1A - TC-RSG-DEF-001]
        FRD Point 3 Requirement:
            When an employee submits a 'Withdrawal of Resignation' request, the status
            must be explicitly and unambiguously displayed (e.g. 'WITHDRAWAL REQUESTED'
            or 'RESIGNATION WITHDRAWAL PENDING').

        Actual Defect:
            System displays 'REVOKE REQUESTED', conflating an Employee-initiated withdrawal
            with an Employer/HR-initiated retention revoke.

        Verification:
            Asserts that the status badge is semantically specific ('WITHDRAWAL REQUESTED')
            and strictly fails when ambiguous 'REVOKE REQUESTED' is rendered.
        """
        story = TestStoryLogger(
            "TC-RSG-DEF-001: Withdrawal Status Nomenclature Audit",
            module="Resignation & Offboarding",
            phase="Withdrawal Status Verification"
        )
        story.start()

        bundle = get_branch_persona_bundle("Varanasi")
        hr_user = bundle["hr_person"]
        page, _ = logged_in_page(hr_user)
        page.bring_to_front()

        logger.info(f"[STEP 1] Logged in as Branch HR ({hr_user}). Navigating to /resignation-approval...")
        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Look for any row with 'Revoke' or 'Withdraw'
        target_row = page.locator("tr:has-text('REVOKE REQUESTED'), tr:has-text('Revoke Requested'), tr:has-text('WITHDRAWAL'), tr:has-text('Withdraw')").first
        
        if not target_row.is_visible(timeout=5000):
            # Check all visible status badges on page
            badges = [b.inner_text().strip() for b in page.locator(".chakra-badge, span[class*='badge']").all()]
            logger.info(f"[AUDIT] Visible status badges on /resignation-approval: {badges}")
            # If no withdrawal/revoke row exists, look for first active resignation row
            target_row = page.locator("table tbody tr").first

        assert target_row.is_visible(timeout=5000), "No resignation records found on /resignation-approval"

        row_text = target_row.inner_text().replace("\n", " | ")
        logger.info(f"[AUDIT ROW] {row_text}")

        # Extract status badge
        badge = target_row.locator(".chakra-badge, span[class*='badge']").first
        current_status = badge.inner_text().strip() if badge.is_visible(timeout=2000) else "UNKNOWN"
        logger.info(f"[AUDIT STATUS BADGE] Detected Status: '{current_status}'")

        story.log_step(
            "Inspect Status Nomenclature",
            record=f"Status: '{current_status}' | Row: {row_text}",
            expected="Status must be specific: 'WITHDRAWAL REQUESTED' (or 'RESIGNATION WITHDRAWAL PENDING')",
            actual=current_status,
            status="PASS" if "withdraw" in current_status.lower() else "FAIL"
        )

        # DEFECT ASSERTION: Fail if status is ambiguous 'REVOKE REQUESTED'
        assert "revoke requested" not in current_status.lower(), (
            f"DEFECT CONFIRMED [TC-RSG-DEF-001]: Status is ambiguously displayed as '{current_status}'. "
            f"FRD Point 3 requires an employee-initiated retraction to be specifically labeled "
            f"'WITHDRAWAL REQUESTED' (or 'RESIGNATION WITHDRAWAL PENDING') to prevent confusion with HR-initiated Revoke."
        )

        # Assert status explicitly contains 'WITHDRAW'
        assert "withdraw" in current_status.lower(), (
            f"DEFECT CONFIRMED [TC-RSG-DEF-001]: Expected status to contain 'WITHDRAWAL', but found '{current_status}'."
        )

    def test_tc_rsg_def_002_hr_missing_approve_reject_withdrawal_actions(self, logged_in_page):
        """
        [DEFECT 1B - TC-RSG-DEF-002]
        FRD Point 3 Requirement:
            The withdrawal request should go to the authorized HR user for approval.
            HR should be able to:
            - Approve the withdrawal
            - Reject the withdrawal

        Actual Defect:
            HR has no visible action to Approve or Reject the withdrawal request.
            The Actions column only shows the menu icon with NO available workflow to process it.

        Verification:
            Opens the row's Actions menu and asserts 'Approve Withdrawal' and 'Reject Withdrawal'
            options exist. Fails when these actions are missing.
        """
        story = TestStoryLogger(
            "TC-RSG-DEF-002: HR Approve/Reject Withdrawal Actions Audit",
            module="Resignation & Offboarding",
            phase="Withdrawal Action Menu Verification"
        )
        story.start()

        bundle = get_branch_persona_bundle("Varanasi")
        hr_user = bundle["hr_person"]
        page, _ = logged_in_page(hr_user)
        page.bring_to_front()

        logger.info(f"[STEP 1] Navigating HR to /resignation-approval...")
        page.goto(f"{settings.BASE_URL}/resignation-approval", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Locate row with REVOKE REQUESTED or Withdrawal
        target_row = page.locator("tr:has-text('REVOKE REQUESTED'), tr:has-text('Revoke Requested'), tr:has-text('WITHDRAWAL'), tr:has-text('Withdraw')").first
        if not target_row.is_visible(timeout=5000):
            target_row = page.locator("table tbody tr").first

        assert target_row.is_visible(timeout=5000), "No resignation records found on /resignation-approval"

        row_employee = target_row.locator("td").nth(1).inner_text().strip() if target_row.locator("td").count() > 1 else "Unknown"
        logger.info(f"[STEP 2] Inspecting Actions menu for row: '{row_employee}'")

        # Click Actions hamburger menu button
        action_btn = target_row.locator("td").last.locator("button.chakra-menu__menu-button, button").first
        assert action_btn.is_visible(timeout=3000), "Action hamburger button not visible in table row"
        action_btn.click()
        page.wait_for_timeout(1000)

        # Read all visible menu items
        menu_items = page.locator("[role='menuitem'], button.chakra-menu__menuitem, .chakra-menu__menu-list button").all_inner_texts()
        menu_items_clean = [m.strip() for m in menu_items if m.strip()]
        logger.info(f"[AUDIT MENU ITEMS] Available Actions in dropdown: {menu_items_clean}")

        # Check for Approve Withdrawal / Reject Withdrawal
        has_approve_withdrawal = any("approve" in m.lower() and ("withdraw" in m.lower() or "revoke" in m.lower()) for m in menu_items_clean)
        has_reject_withdrawal = any("reject" in m.lower() and ("withdraw" in m.lower() or "revoke" in m.lower()) for m in menu_items_clean)

        story.log_step(
            "Inspect HR Withdrawal Actions",
            record=f"Available Menu Items: {menu_items_clean}",
            expected="Actions menu must contain 'Approve Withdrawal' and 'Reject Withdrawal'",
            actual=str(menu_items_clean),
            status="PASS" if (has_approve_withdrawal and has_reject_withdrawal) else "FAIL"
        )

        # DEFECT ASSERTION: Fail if HR has no options to Approve or Reject Withdrawal
        assert has_approve_withdrawal, (
            f"DEFECT CONFIRMED [TC-RSG-DEF-002]: HR has NO option to 'Approve Withdrawal'. "
            f"Available actions found in menu: {menu_items_clean}. "
            f"FRD Point 3 requires HR to be able to approve employee withdrawal requests."
        )

        assert has_reject_withdrawal, (
            f"DEFECT CONFIRMED [TC-RSG-DEF-002]: HR has NO option to 'Reject Withdrawal'. "
            f"Available actions found in menu: {menu_items_clean}. "
            f"FRD Point 3 requires HR to be able to reject employee withdrawal requests."
        )

    def test_tc_rsg_def_003_withdrawal_option_unavailable_during_pending_buyout(self, logged_in_page):
        """
        [DEFECT 1C - TC-RSG-DEF-003]
        FRD Point 3 / Business Policy Requirement:
            The 'Withdraw Resignation' option must remain available to the employee
            while the Buyout Request is 'Pending HR Review' (before HR processes/approves it).

        Actual Defect:
            The 'Withdraw Resignation' option is completely missing / unavailable on the
            employee resignation status page while Buyout status is 'Pending HR Review'.

        Verification:
            Logs in as employee who has submitted Buyout (e.g. 'Uttam Kumar'), navigates to
            /resignation, verifies 'Pending HR Review' state, and asserts 'Withdraw Resignation'
            button visibility. Fails strictly confirming the defect.
        """
        story = TestStoryLogger(
            "TC-RSG-DEF-003: Withdrawal Option Availability During Pending Buyout Review",
            module="Resignation & Offboarding",
            phase="Buyout Review Gating Audit"
        )
        story.start()

        emp_user = "uttam_kumar"
        page, _ = logged_in_page(emp_user)
        page.bring_to_front()

        res_page = ResignationPage(page)
        logger.info(f"[STEP 1] Logged in as Employee ({emp_user}). Navigating to /resignation...")
        res_page.navigate_to_resignation()
        page.wait_for_timeout(2000)

        # Verify Pending HR Review state in Stepper / Buyout Card / Badge
        is_pending_review = page.locator(
            ".chakra-badge:has-text('BUYOUT REQUESTED'), .chakra-badge:has-text('PENDING HR REVIEW'), text='Pending HR Review'"
        ).first.is_visible(timeout=5000)
        assert is_pending_review, "Prerequisite not met: Employee is not in 'Pending HR Review' / 'BUYOUT REQUESTED' state"

        logger.info(f"[AUDIT] Verified employee is in 'Pending HR Review' state.")

        # Inspect for Withdraw action button
        withdraw_btn = page.locator(
            "button:has-text('Withdraw Resignation'), button:has-text('Request Withdrawal'), "
            "button:has-text('Withdraw'), [role='button']:has-text('Withdraw')"
        ).first
        is_withdraw_visible = withdraw_btn.is_visible(timeout=3000)

        all_buttons = [b.inner_text().strip() for b in page.locator("button").all()]
        logger.info(f"[AUDIT] Visible buttons on employee resignation page: {all_buttons}")

        story.log_step(
            "Audit Withdrawal Option During Pending Buyout",
            record=f"Pending Review: {is_pending_review} | Visible Buttons: {all_buttons}",
            expected="Button 'Withdraw Resignation' / 'Request Withdrawal' must be visible and actionable",
            actual=f"Withdraw Button Visible: {is_withdraw_visible}",
            status="PASS" if is_withdraw_visible else "FAIL"
        )

        # DEFECT ASSERTION: Fail strictly confirming the reported bug
        assert is_withdraw_visible, (
            "DEFECT CONFIRMED [TC-RSG-DEF-003]: 'Withdraw Resignation' option is NOT available "
            "while Buyout is 'Pending HR Review'! "
            "Based on the confirmed business rule, withdrawal remains allowed while Buyout is pending HR review."
        )
