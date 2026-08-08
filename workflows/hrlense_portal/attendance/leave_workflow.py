"""
Leave Management Workflow Layer for HR Lens Portal.

Encapsulates all end-to-end business workflows for leave application, approval,
dynamic status tab verification (Approved, Rejected, Pending), and structured step logging.
"""

import random
import logging
import re
import pytest
from datetime import date, timedelta
from playwright.sync_api import Page, expect
from pages.hrlense_portal.attendance.leave_page import LeavePage

logger = logging.getLogger("WORKFLOW")


class LeaveWorkflow:
    """
    High-level business workflow encapsulating Leave Management operations with structured visual hierarchy logging.
    """

    def __init__(self, page: Page):
        self.page = page
        self.leave_page = LeavePage(page)

    def apply_leave_and_verify_status_tab_workflow(
        self,
        leave_type: str,
        from_offset: int = None,
        to_offset: int = None,
        subject: str = None
    ) -> dict:
        """
        Executes end-to-end Leave Application business workflow:
        [STEP 1] Navigate to Leave Apply : MyLeaves → • Leave Apply
        [STEP 2] Select Dates      : Selects random date range from offset 1 to 5 days
        [STEP 3] Select Approver   : <Approver Name>
        [STEP 4] Select Leave Type : <Leave Type>
        [STEP 5] Fill Mail Body    : <Subject / Body>
        [STEP 6] Submit Leave      : Click Apply & Confirm
        [VERIFY] Toast             : <Captured Raw Toast Message>
        [SUCCESS] Leave visible in <Target Status> tab
        """
        if from_offset is None:
            from_offset = random.randint(10, 15)
        if to_offset is None:
            to_offset = random.randint(0, 2)

        logger.info("=" * 60)
        logger.info(f"STARTING LEAVE APPLICATION WORKFLOW: '{leave_type}'")
        logger.info("=" * 60)
        
        # [STEP 1] Navigation
        logger.info("[STEP 1] Navigate to Leave Apply : MyLeaves → • Leave Apply")
        self.leave_page.click_my_leave()
        self.leave_page.click_leave_apply()

        # [STEP 2] Select Dates (Random offset 1 to 5 days)
        from_date = date.today() + timedelta(days=from_offset)
        to_date = from_date + timedelta(days=to_offset)
        date_range_str = f"{from_date.strftime('%d %b %Y')} → {to_date.strftime('%d %b %Y')}"
        logger.info(f"[STEP 2] Select Dates      : {date_range_str} (Random offset: +{from_offset} to +{from_offset + to_offset} days)")
        self.leave_page._select_date_from_calendar(self.leave_page.FROM_DATE_TRIGGER, from_date)
        self.leave_page._select_date_from_calendar(self.leave_page.TO_DATE_TRIGGER, to_date)

        # [STEP 3] Select Approver
        approver_name = self.leave_page.get_approver_name()
        logger.info(f"[STEP 3] Select Approver   : {approver_name or 'Default Manager'}")

        # [STEP 4] Select Leave Type
        logger.info(f"[STEP 4] Select Leave Type : {leave_type}")
        self.leave_page.select_leave_type(leave_type)

        # [STEP 5] Fill Mail Body & Subject
        subj_text = subject or f"Leave for {leave_type}"
        logger.info(f"[STEP 5] Fill Mail Body    : Subject = '{subj_text}'")
        self.leave_page.enter_subject(subj_text)

        mail_body = (
            f"Dear Sir/Ma'am,\n\n"
            f"I would like to request leave from {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')} "
            f"for {leave_type}.\n\nKindly approve my leave request.\n\nThank you."
        )
        self.leave_page.fill_mail_body(mail_body)

        # [STEP 6] Submit Leave
        logger.info("[STEP 6] Submit Leave      : Clicking Apply & Confirm buttons")
        self.leave_page.click_submit()
        self.leave_page.click_confirm()

        # [VERIFY] Toast
        raw_toast = self.leave_page.wait_for_apply_spinner_and_toast()
        logger.info(f"[VERIFY] Toast             : {raw_toast}")

        raw_toast_lower = raw_toast.lower()
        if "required" in raw_toast_lower or "error" in raw_toast_lower or "invalid" in raw_toast_lower:
            pytest.fail(f"Leave application failed with validation error toast: '{raw_toast}'")

        # [VERIFY & SUCCESS] Dynamic Tab Verification
        is_located = self.leave_page.verify_toast_leave_status_in_tab(
            toast_msg=raw_toast,
            leave_type=leave_type
        )

        target_tab = "Approved" if "approved" in raw_toast.lower() else ("Rejected" if "rejected" in raw_toast.lower() else "Pending")
        if not is_located:
            logger.warning(f"[VERIFY FAILED] Leave not visually highlighted in {target_tab} tab")

        logger.info("=" * 60)

        return {
            "from_date": from_date,
            "to_date": to_date,
            "toast": raw_toast,
            "leave_type": leave_type,
            "is_located": is_located,
            "target_tab": target_tab,
            "approver_name": approver_name
        }

    def approve_leave_request_workflow(
        self,
        employee_name: str,
        from_date: date = None,
        to_date: date = None,
        mode: str = "auto",
        action: str = "Approve"
    ) -> tuple[bool, str]:
        """
        Executes end-to-end Leave Approval business workflow supporting:
        - Table Row Select Dropdown mode
        - Emp Code Hyperlink Drawer mode (Drawer -> Approve/Reject button -> Confirm)
        """
        logger.info("=" * 60)
        logger.info(f"STARTING LEAVE APPROVAL WORKFLOW: Employee='{employee_name}', Action='{action}', Mode='{mode}'")
        logger.info("=" * 60)

        # [STEP 1] Navigate Attendance -> Leaves Request
        logger.info("[STEP 1] Navigate to Attendance → • Leaves Request")
        self.leave_page.click_attendance()
        self.leave_page.click_leave_request(employee_name=employee_name)

        # [STEP 2] Search Leave Request
        logger.info(f"[STEP 2] Search Leave Request for : {employee_name}")

        # [ACTION] Approve / Reject via selected mode (Randomized among 3 methods if mode is auto/random)
        if mode in ("random", "auto"):
            chosen_mode = random.choice(["dropdown", "emp_code_drawer", "view_link_drawer"])
            logger.info(f"[RANDOM SELECTION] Randomly selected approval method: '{chosen_mode}'")
        else:
            chosen_mode = mode

        logger.info(f"[ACTION] Select '{action}' & Confirm (Mode: '{chosen_mode}')")
        approved, toast = self.leave_page.approve_leave(
            employee_name=employee_name,
            from_date=from_date,
            to_date=to_date,
            mode=chosen_mode,
            action=action
        )

        # [VERIFY] Toast
        logger.info(f"[VERIFY] Toast             : {toast}")

        if approved:
            logger.info(f"[SUCCESS] Leave {action}d Successfully for '{employee_name}'")
        else:
            logger.warning(f"[FAIL] Could not process leave {action} for '{employee_name}'")

        logger.info("=" * 60)

        return approved, toast

    def execute_full_leave_apply_and_approval_flow(
        self,
        logged_in_page_func,
        leave_type: str,
        from_offset: int = None,
        to_offset: int = None
    ) -> dict:
        """
        Executes unified E2E flow without duplicate submissions:
        1. Apply leave -> Get raw toast -> Verify UI in dynamic status tab.
        2. If raw toast status is NOT 'approved':
           - Log in as Approver Manager.
           - Locate leave request & approve.
           - Capture approval toast notification.
        """
        # 1. Apply Leave & Verify Status Tab
        apply_res = self.apply_leave_and_verify_status_tab_workflow(
            leave_type=leave_type,
            from_offset=from_offset,
            to_offset=to_offset
        )

        raw_toast = apply_res["toast"]
        if "approved" in raw_toast.lower():
            logger.info(f"[BUSINESS RULE] Leave request already approved for dates {apply_res['from_date']} → {apply_res['to_date']}. Skipping approval step.")
            return apply_res

        # 2. Login via Approver & Approve
        emp_name = self.leave_page.get_logged_in_employee_name()
        approver_name = apply_res.get("approver_name") or "Vivek Singh"
        
        from core.config import settings
        approver_key = settings.APPROVERS.get(approver_name, "vivek_singh")
        
        logger.info(f"[WORKFLOW] Logging in as Approver Manager '{approver_name}' ({approver_key}) to approve leave for '{emp_name}'...")
        approver_page, _ = logged_in_page_func(approver_key)
        
        approver_workflow = LeaveWorkflow(approver_page)
        approved, approval_toast = approver_workflow.approve_leave_request_workflow(
            employee_name=emp_name,
            from_date=apply_res["from_date"],
            to_date=apply_res["to_date"]
        )

        apply_res["approved"] = approved
        apply_res["approval_toast"] = approval_toast
        return apply_res
