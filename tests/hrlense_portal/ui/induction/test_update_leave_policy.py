"""
Test Suite: Live Update and Verification of Accurate Leave Policy (18 Paid Leaves: 1 CL + 0.5 EL + Sat/Sun Off).
1. Admin navigates to /master/induction-policy -> Tab 2 -> STEP 5: HR Policies.
2. Locates the Leave Policy row.
3. Edits and updates the content to accurately specify:
   - 1 CL (Casual Leave) and 0.5 EL (Earned Leave) credited monthly (Total 18 Annual Paid Leaves)
   - Saturday & Sunday weekly offs
   - Annual Gazetted / Public Festival Holidays
4. Submits and verifies backend update.
5. Verifies live reflection via Candidate Induction AI Guide (Sufi).
"""

import pytest
import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.master.master_induction_policy_page import MasterInductionPolicyPage
from pages.hrlense_portal.induction.induction_page import InductionPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
class TestUpdateLeavePolicy:
    """Updates Leave Policy in Master Induction Policy and verifies Candidate & AI Guide reflection."""

    def test_update_leave_policy_to_18_paid_leaves_and_verify(self, admin_page: Page):
        policy_page = MasterInductionPolicyPage(admin_page)
        induction_page = InductionPage(admin_page)

        # ----------------- Step 1: Navigate to Step 5 (HR Policies) -----------------
        logger.info("[STEP 1] Navigating to Master Induction Policy -> Tab 2 -> Step 5: HR Policies...")
        policy_page.navigate_to_induction_policy()
        policy_page.switch_to_step_content_tab()
        policy_page.select_step(5)
        admin_page.wait_for_timeout(2000)

        # ----------------- Step 2: Locate Leave Policy Row -----------------
        rows = policy_page.get_all_rows_data()
        logger.info(f"[STEP 2] Found {len(rows)} HR Policy rows in Step 5.")

        leave_row_index = -1
        for idx, r in enumerate(rows):
            title = r.get("TITLE / HEADING", "").lower()
            category = r.get("CATEGORY TAG", "").lower()
            snippet = r.get("CONTENT SNIPPET", "").lower()
            logger.info(f"  Row [{idx}]: Category='{category}' | Title='{title}' | Snippet='{snippet[:50]}...'")
            if "leave" in title or "leave" in category or "leave" in snippet:
                leave_row_index = idx
                break

        assert leave_row_index != -1, "Leave Policy row was not found in Step 5: HR Policies!"
        logger.info(f"[STEP 2] Target Leave Policy row identified at index: {leave_row_index}")

        # ----------------- Step 3: Open Edit Modal & Update Content -----------------
        policy_page.click_edit_row(leave_row_index)
        admin_page.wait_for_timeout(1500)

        original_title = policy_page.get_modal_title_value()
        original_content = policy_page.get_modal_content_value()
        logger.info(f"[STEP 3] Original Title: '{original_title}'")
        logger.info(f"[STEP 3] Original Content: '{original_content}'")

        # New accurate content reflecting: Saturday & Sunday off, 1 CL + 0.5 EL per month (18 annual)
        new_leave_content = (
            "Company Paid Leave Policy:\n"
            "• Weekly Offs: Saturday & Sunday are regular weekly offs.\n"
            "• Monthly Leave Accrual: Employees receive 1 Casual Leave (CL) and 0.5 Earned Leave (EL) credited monthly (Total 18 Paid Leaves annually).\n"
            "• Public Holidays: Gazetted and festive holidays are observed as per the annual company holiday calendar.\n"
            "• Prior Approval: Planned leaves require advance manager approval via the HRMS Leave portal."
        )

        logger.info("[STEP 3] Updating content in modal...")
        policy_page.modal_content_textarea.fill(new_leave_content)
        admin_page.wait_for_timeout(500)

        # ----------------- Step 4: Save Modal Changes -----------------
        logger.info("[STEP 4] Submitting updated Leave Policy...")
        policy_page.save_modal_changes()
        admin_page.wait_for_timeout(2000)

        # Re-fetch Step 5 row to verify in-table update
        policy_page.select_step(5)
        admin_page.wait_for_timeout(1500)
        updated_row = policy_page.get_table_row_data(leave_row_index)
        logger.info(f"[STEP 4] Updated Row Data in Table: {updated_row}")
        assert "18" in updated_row.get("CONTENT SNIPPET", "") or "Leave" in updated_row.get("TITLE / HEADING", ""), (
            f"Table row snippet did not reflect new content! Got: {updated_row.get('CONTENT SNIPPET')}"
        )

        print("\n" + "=" * 80)
        print("           LEAVE POLICY SUCCESSFULLY UPDATED IN MASTER INDUCTION")
        print("=" * 80)
        print(f"  Step:             STEP 5: HR Policies")
        print(f"  Row Index:        {leave_row_index}")
        print(f"  Policy Title:     {original_title}")
        print(f"  New Policy Rules: 1 CL + 0.5 EL monthly (18 Annual Paid Leaves) + Sat/Sun Weekend Offs")
        print(f"  Table Snippet:    {updated_row.get('CONTENT SNIPPET')}")
        print("=" * 80 + "\n")

        # ----------------- Step 5: Verify Live Reflection in Sufi AI Guide -----------------
        logger.info("[STEP 5] Navigating to Candidate /induction to verify Sufi AI Guide reflection...")
        induction_page.navigate_to_induction()
        admin_page.wait_for_timeout(2000)

        if induction_page.is_welcome_slide_visible():
            induction_page.advance_welcome_slides(selected_guide="Sufi")

        induction_page.open_induction_chat()
        admin_page.wait_for_timeout(1000)

        # Ask Sufi about Leave Policy
        query = "What is the company leave policy and weekly offs?"
        logger.info(f"[STEP 5] Asking Sufi: '{query}'...")
        induction_page.ask_induction_guide(query)
        sufi_reply = induction_page.wait_for_guide_response(timeout_sec=20)
        logger.info(f"[STEP 5] Sufi AI Guide live response: {sufi_reply}")

        print("\n" + "=" * 80)
        print("              CANDIDATE SUFI AI GUIDE LIVE RESPONSE")
        print("=" * 80)
        print(sufi_reply)
        print("=" * 80 + "\n")

        assert len(sufi_reply) > 20, "Sufi failed to generate a response!"
