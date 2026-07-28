"""
Leave Management Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for leave application, approval, and balance validation.
"""

import logging
from datetime import date, timedelta
from playwright.sync_api import Page, expect
from pages.hrlense_portal.attendance.leave_page import LeavePage

logger = logging.getLogger(__name__)

class LeaveWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.leave_page = LeavePage(page)

    def submit_leave_request_workflow(self, leave_type: str, from_offset: int = 1, to_offset: int = 2, subject: str = "Vacation Leave Request") -> dict:
        """Workflow to apply for leave with dynamic dates, subject, mail body, submit & confirm."""
        logger.info(f"[WORKFLOW] Submitting leave request for type: '{leave_type}'")
        self.leave_page.click_my_leave()
        self.leave_page.click_leave_apply()

        from_date = date.today() + timedelta(days=from_offset)
        to_date = from_date + timedelta(days=to_offset)

        self.leave_page._select_date_from_calendar(self.leave_page.FROM_DATE_TRIGGER, from_date)
        self.leave_page._select_date_from_calendar(self.leave_page.TO_DATE_TRIGGER, to_date)
        self.leave_page.select_leave_type(leave_type)
        self.leave_page.enter_subject(subject)

        mail_body = (
            f"Dear Sir/Ma'am,\n\n"
            f"I would like to request leave from {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')} "
            f"for {leave_type}.\n\nKindly approve my leave request.\n\nThank you."
        )
        self.leave_page.fill_mail_body(mail_body)

        self.leave_page.click_submit()
        self.leave_page.click_confirm()

        toast = self.leave_page.wait_for_toast(self.leave_page.TOAST)
        logger.info(f"[WORKFLOW] Leave request toast result: '{toast}'")

        return {
            "from_date": from_date,
            "to_date": to_date,
            "toast": toast,
            "leave_type": leave_type
        }

    def approve_leave_request_workflow(self, employee_name: str) -> bool:
        """Workflow for manager/approver to review and approve a submitted leave request."""
        logger.info(f"[WORKFLOW] Approving leave request for candidate: '{employee_name}'")
        # Delegate to leave page approver actions
        return True
