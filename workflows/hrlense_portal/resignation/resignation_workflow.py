"""
HRlens Portal — Resignation Business Workflow Layer.

Encapsulates end-to-end business logic for Employee Resignation:
- Form filling, optional checkboxes, and suggestions
- Modal confirmation orchestration
- Status tab verification & Stepper inspection
- Early relieving request workflow
"""

import logging
from typing import Dict, Optional, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage

logger = logging.getLogger("WORKFLOW")


class ResignationWorkflow:
    """Business Workflow class encapsulating high-level operations for Employee Resignation."""

    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def submit_resignation_workflow(
        self,
        reason: str = "1",
        stay_connected: bool = False,
        share_suggestions: bool = False,
        suggestion_text: Optional[str] = None,
        confirm: bool = True,
    ) -> Dict[str, Union[dict, str]]:
        """
        Executes end-to-end Employee Resignation Application Business Workflow:
        [STEP 1] Navigate to Resignation -> Apply Resignation tab
        [STEP 2] Verify auto-filled fields (Personal Email, Contact Number)
        [STEP 3] Select Separation Reason
        [STEP 4] Toggle optional checkboxes (Stay Connected / Share Suggestions)
        [STEP 5] Enter mandatory suggestions text (if Share Suggestions is True)
        [STEP 6] Click Submit Resignation -> Verify Confirmation Modal -> Click 'Yes, Submit'
        [STEP 7] Capture success toast message
        """
        logger.info("=" * 60)
        logger.info("STARTING EMPLOYEE RESIGNATION APPLICATION WORKFLOW")
        logger.info("=" * 60)

        # [STEP 1] Navigation
        logger.info("[STEP 1] Navigate to Resignation -> Apply Resignation tab")
        self.res_page.navigate_to_resignation()
        self.res_page.click_apply_resignation_tab()



        # [STEP 2] Verify Auto-filled Fields
        logger.info("[STEP 2] Verifying auto-filled Personal Email & Contact Number")
        autofill_status = self.res_page.verify_autofilled_fields()

        # [STEP 3] Select Separation Reason
        logger.info(f"[STEP 3] Selecting Separation Reason: '{reason}'")
        selected_reason = self.res_page.select_reason_of_separation(reason)

        # [STEP 4] Toggle Optional Checkboxes
        if stay_connected:
            logger.info("[STEP 4a] Toggling 'Stay Connected' checkbox")
            self.res_page.toggle_stay_connected()

        if share_suggestions:
            logger.info("[STEP 4b] Toggling 'Share Suggestions' checkbox")
            self.res_page.toggle_share_suggestions()
            if suggestion_text:
                logger.info(f"[STEP 5] Entering suggestions text: '{suggestion_text}'")
                self.res_page.enter_suggestions(suggestion_text)

        # [STEP 6] Submit & Confirm Modal
        logger.info("[STEP 6] Triggering Submit Resignation & Modal Confirmation")
        self.res_page.click_submit_resignation_button()

        modal_visible = self.res_page.is_confirmation_modal_visible()
        if not modal_visible:
            logger.warning("Confirmation modal 'Submit Resignation Request' was not visible!")

        self.res_page.click_confirm_modal_button(confirm=confirm)

        # [STEP 7] Capture Toast
        toast_msg = self.res_page.wait_for_toast(timeout=10000) if confirm else ""
        logger.info(f"[STEP 7] Captured Toast Message: '{toast_msg}'")

        return {
            "autofill_status": autofill_status,
            "selected_reason": selected_reason,
            "modal_visible": modal_visible,
            "toast": toast_msg,
        }

    def verify_resignation_status_workflow(self) -> Dict[str, bool]:
        """
        Executes Business Workflow to inspect post-submission Status tab:
        [STEP 1] Open / Verify Status tab
        [STEP 2] Check Applied On header, Stepper stages (Applied -> Notice Period -> Relieved), and Summary details
        """
        logger.info("=" * 60)
        logger.info("STARTING RESIGNATION STATUS TAB VERIFICATION WORKFLOW")
        logger.info("=" * 60)

        self.res_page.click_status_tab()
        status_details = self.res_page.get_status_view_details()
        logger.info(f"Status Tab View Verification Results: {status_details}")
        return status_details

    def request_early_relieving_workflow(self, early_relieving_date: str) -> str:
        """
        Executes Business Workflow to request early relieving:
        [STEP 1] Navigate to Resignation -> Status tab
        [STEP 2] Enter Early Relieving Date
        [STEP 3] Submit Early Relieving request and capture toast
        """
        logger.info("=" * 60)
        logger.info(f"STARTING EARLY RELIEVING WORKFLOW (Target Date: {early_relieving_date})")
        logger.info("=" * 60)

        self.res_page.navigate_to_resignation()
        self.res_page.click_status_tab()

        self.res_page.fill_early_relieving_date(early_relieving_date)
        self.res_page.click_early_relieving_submit_button()

        toast_msg = self.res_page.wait_for_toast(timeout=10000)
        logger.info(f"Early Relieving Request Toast Message: '{toast_msg}'")
        return toast_msg

    def validate_blank_form_submission_workflow(self) -> Dict[str, str]:
        """
        Executes Business Workflow to test blank form validation:
        [STEP 1] Navigate to Resignation -> Apply Resignation tab
        [STEP 2] Toggle 'Share Suggestions' checkbox without entering text
        [STEP 3] Click Submit Resignation button
        [STEP 4] Discover and return Chakra UI field-level error messages
        """
        logger.info("=" * 60)
        logger.info("STARTING BLANK FORM VALIDATION WORKFLOW")
        logger.info("=" * 60)

        self.res_page.navigate_to_resignation()
        if not self.res_page.click_apply_resignation_tab():
            logger.warning("Apply Resignation tab not accessible for blank form validation test")

        # Toggle suggestions checkbox to open required suggestion textarea
        self.res_page.toggle_share_suggestions()

        # Click Submit Resignation without filling required fields
        self.res_page.click_submit_resignation_button()

        # Capture Chakra UI field errors
        errors = self.res_page.get_form_validation_errors()
        logger.info(f"Captured Chakra UI Form Validation Errors: {errors}")
        return errors

    def validate_early_relieving_max_date_workflow(self, exceed_date_str: str = "2026-12-15") -> Dict[str, Union[str, bool]]:
        """
        Executes Business Workflow to test Early Relieving Date > Last Working Day boundary:
        [STEP 1] Navigate to Resignation -> Status tab
        [STEP 2] Read 'max' date constraint attribute from date picker input
        [STEP 3] Attempt filling date exceeding Last Working Day (exceed_date_str)
        [STEP 4] Submit and capture validation / boundary enforcement result
        """
        logger.info("=" * 60)
        logger.info(f"STARTING EARLY RELIEVING MAX DATE VALIDATION WORKFLOW (Exceed Date: {exceed_date_str})")
        logger.info("=" * 60)

        self.res_page.navigate_to_resignation()
        self.res_page.click_status_tab()

        max_date_attr = self.res_page.get_early_relieving_max_date()
        logger.info(f"Read input max date attribute constraint: '{max_date_attr}'")

        self.res_page.fill_early_relieving_date(exceed_date_str)
        self.res_page.click_early_relieving_submit_button()

        toast_msg = self.res_page.wait_for_toast(timeout=5000)

    def validate_buyout_date_boundaries_workflow(self) -> Dict[str, str]:
        """
        Executes Business Workflow to inspect and validate Buyout / Early Relieving Date calendar boundaries:
        1. Reads 'min' date attribute (Present Date)
        2. Reads 'max' date attribute (Last Working Day, e.g. '2026-11-30')
        3. Returns min and max date attributes for boundary verification
        """
        logger.info("=" * 60)
        logger.info("STARTING BUYOUT / EARLY RELIEVING DATE CALENDAR BOUNDARY WORKFLOW")
        logger.info("=" * 60)

        self.res_page.navigate_to_resignation()
        self.res_page.click_status_tab()

        min_date = self.res_page.get_early_relieving_min_date()
        max_date = self.res_page.get_early_relieving_max_date()

        logger.info(f"Calendar Boundary Range: MIN='{min_date}', MAX='{max_date}'")

        return {
            "min_date_present": min_date,
            "max_date_lwd": max_date,
        }

    def validate_multiple_duplicate_attempts_workflow(self, attempts: int = 3) -> Dict[str, Union[int, list]]:
        """
        Executes Business Workflow for N repeated duplicate resignation attempts:
        Attempts submission N times and verifies system prevents creation of N duplicate requests.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING REPEATED DUPLICATE RESIGNATION ATTEMPTS WORKFLOW ({attempts} Attempts)")
        logger.info("=" * 60)

        toasts_captured = []
        for i in range(1, attempts + 1):
            logger.info(f"Attempt #{i} to submit duplicate resignation...")
            result = self.submit_resignation_workflow(reason="1", confirm=True)
            toast_text = result.get("toast", "")
            toasts_captured.append(toast_text)
            logger.info(f"Attempt #{i} Toast captured: '{toast_text}'")

        return {
            "attempts": attempts,
            "toasts": toasts_captured,
        }

    def validate_revoke_without_buyout_workflow(self, hr_page_instance: Page, employee_name: str) -> bool:
        """
        Executes Business Workflow for Revoke without Buyout rule:
        'When Employee has NOT submitted a Buyout request, HR SHOULD be able to see and initiate Revoke Request'
        """
        logger.info("=" * 60)
        logger.info(f"STARTING REVOKE WITHOUT BUYOUT WORKFLOW FOR EMPLOYEE: '{employee_name}'")
        logger.info("=" * 60)

        hr_res_page = ResignationPage(hr_page_instance)
        hr_res_page.navigate_to_resignation()

        is_revoke_visible = hr_res_page.hr_revoke_request_flow(employee_name=employee_name)
        logger.info(f"HR Revoke Request Flow result for employee '{employee_name}': {is_revoke_visible}")

        return is_revoke_visible

    def execute_e2e_revoke_workflow(self, hr_page_instance: Page, employee_name: str) -> Dict[str, Union[bool, str]]:
        """
        Executes complete E2E Revoke Lifecycle Workflow covering RR_001 through RR_006:
        Cycle 1:
        [1] Employee A submits Resignation #1 (No Buyout) -> RR_002
        [2] HR executes hr_revoke_request_flow (searches Employee A, checks status, opens modal, confirms Revoke) -> RR_005
        [3] Employee A ACCEPTS Revoke Request -> Resignation #1 ENDS/CLOSED -> RR_003

        Cycle 2:
        [4] Employee A submits FRESH Resignation #2 -> RR_006
        [5] HR sends Revoke Request again -> Employee A REJECTS -> Resignation #2 CONTINUES -> RR_004
        [6] Employee A requests BUYOUT -> HR opens modal -> Revoke button is BLOCKED/HIDDEN -> RR_001
        """
        logger.info("=" * 60)
        logger.info(f"STARTING FULL E2E REVOKE LIFECYCLE WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        # CYCLE 1: Resignation #1 -> Revoke -> Accept -> Closed
        logger.info("--- [CYCLE 1] Resignation #1 -> Revoke -> ACCEPT ---")
        hr_res_page = ResignationPage(hr_page_instance)

        res1 = self.submit_resignation_workflow(reason="1", confirm=True)
        hr_sent_revoke_1 = hr_res_page.hr_revoke_request_flow(employee_name)

        # Employee A accepts Revoke #1
        self.res_page.navigate_to_resignation()
        self.res_page.respond_to_revoke_request(accept=True)



        # CYCLE 2: Fresh Resignation #2 -> Revoke -> Reject -> Buyout -> HR Revoke Blocked
        logger.info("--- [CYCLE 2] Fresh Resignation #2 -> Revoke -> REJECT -> Buyout ---")
        res2 = self.submit_resignation_workflow(reason="2", confirm=True)

        hr_res_page.navigate_to_resignation()
        hr_sent_revoke_2 = hr_res_page.hr_revoke_request_flow(employee_name)

        # Employee A rejects Revoke #2
        self.res_page.navigate_to_resignation()
        self.res_page.respond_to_revoke_request(accept=False)

        # Employee A requests Buyout
        self.res_page.click_status_tab()
        self.res_page.click_buyout_request_button()

        # HR verifies Revoke is blocked due to Buyout
        hr_res_page.navigate_to_resignation()
        hr_res_page.search_employee_in_hr_table(employee_name)
        status_badge = hr_res_page.get_hr_table_employee_status(employee_name)

        modal_opened = hr_res_page.open_hr_resignation_details_modal(employee_name)
        is_revoke_blocked_by_buyout = not hr_res_page.is_modal_revoke_button_visible() if modal_opened else True

    def employee_accept_revoke_and_apply_new_resignation_workflow(self, hr_page_instance: Page, employee_name: str) -> Dict[str, Union[bool, str]]:
        """
        Executes Employee Side Accept Revoke Flow:
        1. Employee A submits Resignation #1
        2. HR executes hr_revoke_request_flow to send Revoke Request
        3. Employee A clicks 'Accept' -> Resignation #1 Ends / Closed
        4. Employee A submits a NEW Resignation Request #2 -> Success toast captured!
        """
        logger.info("=" * 60)
        logger.info(f"STARTING EMPLOYEE ACCEPT REVOKE FLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        # Step 1: Employee submits initial resignation
        res1 = self.submit_resignation_workflow(reason="1", confirm=True)

        # Step 2: HR sends Revoke Request
        hr_res_page = ResignationPage(hr_page_instance)
        hr_res_page.navigate_to_resignation()
        hr_sent_revoke = hr_res_page.hr_revoke_request_flow(employee_name)

        # Step 3: Employee Accepts Revoke Request
        self.res_page.navigate_to_resignation()
        decision_visible = self.res_page.is_employee_revoke_decision_visible()
        self.res_page.respond_to_revoke_request(accept=True)
        accept_toast = self.res_page.wait_for_toast(timeout=5000)

        # Step 4: Employee submits NEW Resignation Request #2
        res2 = self.submit_resignation_workflow(reason="2", confirm=True)

        return {
            "hr_sent_revoke": hr_sent_revoke,
            "decision_buttons_visible": decision_visible.get("accept_visible", False),
            "accept_toast": accept_toast,
            "new_resignation_submitted": not res2.get("has_active_resignation"),
            "new_resignation_toast": res2.get("toast", ""),
        }

    def employee_reject_revoke_and_verify_continuation_workflow(self, hr_page_instance: Page, employee_name: str) -> Dict[str, Union[bool, str]]:
        """
        Executes Employee Side Reject Revoke Flow:
        1. Employee A submits Resignation
        2. HR executes hr_revoke_request_flow to send Revoke Request
        3. Employee A clicks 'Reject' -> Resignation Continues Active Lifecycle
        4. Verifies resignation remains active and duplicate applications remain blocked
        """
        logger.info("=" * 60)
        logger.info(f"STARTING EMPLOYEE REJECT REVOKE FLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        # Step 1: Employee submits resignation
        res1 = self.submit_resignation_workflow(reason="1", confirm=True)

        # Step 2: HR sends Revoke Request
        hr_res_page = ResignationPage(hr_page_instance)
        hr_res_page.navigate_to_resignation()
        hr_sent_revoke = hr_res_page.hr_revoke_request_flow(employee_name)

        # Step 3: Employee Rejects Revoke Request
        self.res_page.navigate_to_resignation()
        decision_visible = self.res_page.is_employee_revoke_decision_visible()
        self.res_page.respond_to_revoke_request(accept=False)
        reject_toast = self.res_page.wait_for_toast(timeout=5000)

        # Step 4: Employee A requests Early Relieving Date post-rejection to prove active flow continuation
        logger.info("[STEP 4] Employee A requesting Early Relieving Date post-rejection to prove workflow continuation...")
        self.res_page.click_status_tab()
        early_relieving_toast = self.res_page.request_early_relieving("2026-10-31")

        # Step 5: Verify Resignation continues active workflow
        status_details = self.verify_resignation_status_workflow()

        return {
            "hr_sent_revoke": hr_sent_revoke,
            "decision_buttons_visible": decision_visible.get("reject_visible", False),
            "reject_toast": reject_toast,
            "early_relieving_submitted": early_relieving_toast != "",
            "early_relieving_toast": early_relieving_toast,
            "resignation_continues_active": status_details.get("stepper_applied_visible", False),
        }







