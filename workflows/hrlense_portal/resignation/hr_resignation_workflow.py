"""
HRlens Portal — HR Resignation Workflow (Workflow Tier).
Handles business workflow orchestration for HR-side resignation actions.
"""

from typing import Dict, Union
from playwright.sync_api import Page
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
import logging
logger = logging.getLogger(__name__)



class HrResignationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.res_page = ResignationPage(page)

    def execute_hr_revoke_request_workflow(self, employee_name: str) -> bool:
        """
        Executes HR Revoke Request Flow:
        1. Navigates Offboarding -> • Resignation Request (p:has-text('Resignation Requests'))
        2. Types dynamic employee_name in input[placeholder="Search employee by name..."]
        3. Inspects status badge (.chakra-badge) in tr:has-text(employee_name)
        4. If status is 'Resignation Requested' (or 'Applied'), clicks employee name to open modal (header:has-text('Resignation Details'))
        5. Verifies button:has-text('Revoke') is visible -> clicks Revoke -> clicks Confirm / Yes
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR REVOKE REQUEST WORKFLOW FOR EMPLOYEE: '{employee_name}'")
        logger.info("=" * 60)

        is_success = self.res_page.hr_revoke_request_flow(employee_name=employee_name)
        logger.info(f"HR Revoke Request Workflow Result for '{employee_name}': {is_success}")
        return is_success

    def verify_hr_table_status_workflow(self, employee_name: str) -> str:
        """
        Searches employee in HR Resignation table and reads status badge.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR TABLE STATUS VERIFICATION FOR EMPLOYEE: '{employee_name}'")
        logger.info("=" * 60)

        self.res_page.navigate_to_hr_resignation_approval()
        self.res_page.search_employee_in_hr_table(employee_name)
        status = self.res_page.get_hr_table_employee_status(employee_name)
        logger.info(f"HR Table Status for '{employee_name}': '{status}'")
        return status

    def validate_buyout_prevents_hr_revoke_workflow(self, employee_name: str) -> bool:
        """
        Verifies that when an Employee has applied for Buyout Request, HR's Revoke option is BLOCKED.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR BUYOUT REVOKE RESTRICTION WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        self.res_page.navigate_to_hr_resignation_approval()
        self.res_page.search_employee_in_hr_table(employee_name)
        status = self.res_page.get_hr_table_employee_status(employee_name)

        if "buyout" in status.lower():
            logger.info(f"Status is '{status}': Revoke option is BLOCKED as expected!")
            return False

        modal_opened = self.res_page.open_hr_resignation_details_modal(employee_name)
        if modal_opened:
            is_revoke_visible = self.res_page.is_modal_revoke_button_visible()
            return is_revoke_visible
        return False

    def process_buyout_request_workflow(self, employee_name: str, process: bool = True) -> str:
        """
        Executes HR Process Buyout Request Workflow:
        1. Navigates to Offboarding -> Resignation Approval
        2. Searches employee_name in table
        3. Clicks Actions hamburger button -> selects 'Buyout Request' menu item to open drawer
        4. Clicks 'Process Buyout' (or 'Reject Buyout') button and returns toast message!
        """
        action_str = "PROCESS" if process else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING HR {action_str} BUYOUT REQUEST WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        drawer_opened = self.res_page.open_hr_buyout_request_drawer(employee_name)
        if not drawer_opened:
            logger.error(f"Failed to open 'Buyout Request' drawer for '{employee_name}'")
            return ""

        toast = self.res_page.process_or_reject_hr_buyout(process=process)
        logger.info(f"HR {action_str} Buyout Toast Captured: '{toast}'")
        return toast

    def execute_hr_exit_clearance_workflow(
        self,
        employee_name: str,
        remarks: str = "HR Exit formalities and document checklist completed"
    ) -> Dict[str, Union[bool, str]]:
        """
        Executes HR Exit Clearance workflow on /exit-clearance:
        Completes HR-side offboarding checklist task to achieve full 2/2 clearance.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR EXIT CLEARANCE WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        return self.res_page.process_hr_exit_clearance(
            employee_name=employee_name,
            remarks=remarks
        )

    def execute_start_fnf_workflow(self, employee_name: str) -> str:
        """
        Executes HR Start FnF Process workflow on /resignation-approval:
        Opens Actions menu (=) and triggers Start FnF Process to send case to Accounts.
        """
        logger.info("=" * 60)
        logger.info(f"STARTING HR INITIATE FnF PROCESS WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        return self.res_page.trigger_start_fnf_process(employee_name=employee_name)

    def execute_send_released_employee_letters_workflow(
        self,
        employee_name: str,
        letters: list = None,
        custom_content_map: Dict[str, str] = None,
        verify_sync: bool = True,
        signatory_index: int = 1
    ) -> Dict[str, Union[bool, Dict[str, Union[str, bool]]]]:
        """
        Executes dispatch of release letters on /released-employee by HR:
        Letters supported:
        - 'Relieving Letter'
        - 'Full & Final Settlement'
        - 'Experience Letter'
        
        Features:
        1. Opens preview via row actions menu
        2. If custom_content_map provided, edits left-side SunEditor
        3. If verify_sync=True, verifies that the left-side edit dynamically updates right-side Live Preview
        4. Selects signatory (e.g. Vivekanand Singh)
        5. Clicks 'Send to Employee' and captures toast
        6. Clicks Back button to return to table for next document
        """
        if letters is None:
            letters = ["Relieving Letter", "Full & Final Settlement", "Experience Letter"]

        logger.info("=" * 60)
        logger.info(f"STARTING HR DISPATCH OF RELEASED LETTERS FOR: '{employee_name}' | Letters: {letters}")
        logger.info("=" * 60)

        dispatches = {}
        sync_verifications = {}
        all_success = True

        for letter in letters:
            logger.info(f"[HR DISPATCH LETTER] Opening '{letter}' for '{employee_name}'...")
            opened = self.res_page.open_released_employee_letter(employee_name, letter_type=letter)
            if not opened:
                logger.error(f"Failed to open '{letter}' preview for '{employee_name}'")
                dispatches[letter] = "Failed to open preview"
                all_success = False
                continue

            # Check if custom content should be edited for this letter
            custom_text = None
            if custom_content_map and letter in custom_content_map:
                custom_text = custom_content_map[letter]
            elif verify_sync and letter in ["Relieving Letter", "Experience Letter"]:
                # Default validation phrase for Relieving / Experience letters
                custom_text = f"[Verified Live Preview Note for {employee_name}]"

            if custom_text:
                logger.info(f"[HR LETTER SYNC] Editing left-side editor for '{letter}' with: '{custom_text}'")
                self.res_page.edit_letter_content(custom_text, append=True)

                if verify_sync:
                    is_synced = self.res_page.verify_letter_content_sync(custom_text)
                    sync_verifications[letter] = is_synced
                    if not is_synced:
                        logger.warning(f"[HR LETTER SYNC] Live preview did NOT sync text for '{letter}'")
                        all_success = False
                    else:
                        logger.info(f"[HR LETTER SYNC] Live preview successfully synchronized for '{letter}'!")

            toast = self.res_page.send_letter_to_employee(signatory_index=signatory_index)
            dispatches[letter] = toast or "Sent"
            logger.info(f"[HR DISPATCH LETTER] '{letter}' dispatched. Toast: '{toast}'")

            # Return to /released-employee table for next letter
            self.res_page.click_letter_back_button()

        return {
            "success": all_success,
            "dispatches": dispatches,
            "sync_verifications": sync_verifications
        }

    def process_withdrawal_workflow(self, employee_name: str, approve: bool = True) -> Dict[str, Union[bool, str]]:
        """
        Executes HR Process Withdrawal Workflow:
        1. Navigates to Offboarding -> Resignation Approval
        2. Searches employee_name in table
        3. Identifies and executes Withdrawal action (Approve/Reject) via Actions menu or Details modal
        4. Verifies confirmation dialog and returns result dict with toast and final status
        """
        action_str = "APPROVE" if approve else "REJECT"
        logger.info("=" * 60)
        logger.info(f"STARTING HR {action_str} WITHDRAWAL WORKFLOW FOR: '{employee_name}'")
        logger.info("=" * 60)

        result = self.res_page.process_hr_withdrawal_request(employee_name=employee_name, approve=approve)
        logger.info(f"HR {action_str} Withdrawal Result for '{employee_name}': {result}")
        return result

    def get_hr_available_actions_workflow(self, employee_name: str) -> list:
        """
        Reads all available action options in the HR Resignation table row menu for an employee.
        """
        logger.info(f"HR Workflow: Reading available action menu items for '{employee_name}'")
        return self.res_page.get_hr_table_row_actions(employee_name)

