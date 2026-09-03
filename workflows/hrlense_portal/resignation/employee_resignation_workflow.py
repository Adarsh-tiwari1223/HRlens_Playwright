"""
HRlens Portal — Employee Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for Employee-side resignation actions.
"""

from typing import Dict, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
import logging
logger = logging.getLogger(__name__)



class EmployeeResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def submit_resignation_workflow(
        self,
        reason: str = "1",
        stay_connected: bool = False,
        share_suggestions: bool = False,
        suggestion_text: str = "",
        confirm: bool = True
    ) -> Dict[str, Union[bool, str, dict]]:
        """
        Executes Employee Resignation Application Workflow:
        [STEP 1] Navigate to Resignation module -> Apply Resignation tab
        [STEP 2] Verify auto-filled fields (Personal Email & Contact Number)
        [STEP 3] Select Separation Reason from dropdown
        [STEP 4] Toggle optional checkboxes ('Stay Connected', 'Share Suggestions')
        [STEP 5] Fill mandatory suggestions text if Share Suggestions is toggled
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
        logger.info("STARTING EMPLOYEE RESIGNATION STATUS TAB VERIFICATION WORKFLOW")
        logger.info("=" * 60)

        self.res_page.click_status_tab()
        status_details = self.res_page.get_status_view_details()
        logger.info(f"Status Tab View Details: {status_details}")
        return status_details

    def request_early_relieving_workflow(self, early_relieving_date: str) -> str:
        """
        Executes Early Relieving / Buyout Date submission workflow for Employee:
        [STEP 1] Navigate to Status tab
        [STEP 2] Enter Early Relieving Date
        [STEP 3] Click Submit & capture toast
        """
        logger.info("=" * 60)
        logger.info(f"STARTING EARLY RELIEVING DATE REQUEST WORKFLOW ({early_relieving_date})")
        logger.info("=" * 60)

        self.res_page.click_status_tab()
        self.res_page.fill_early_relieving_date(early_relieving_date)
        self.res_page.click_early_relieving_submit_button()
        toast = self.res_page.wait_for_toast(timeout=10000)
        logger.info(f"Early Relieving Submission Toast: '{toast}'")
        return toast

    def respond_to_revoke_request_workflow(self, accept: bool = True) -> str:
        """
        Executes Employee response (Accept or Reject) to an incoming HR Revoke Request.
        """
        action_str = "ACCEPT" if accept else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING EMPLOYEE {action_str} REVOKE REQUEST WORKFLOW")
        logger.info("=" * 60)

        self.res_page.navigate_to_resignation()
        self.res_page.respond_to_revoke_request(accept=accept)
        toast = self.res_page.wait_for_toast(timeout=5000)
        logger.info(f"Employee {action_str} Revoke Toast: '{toast}'")
        return toast
