"""
HRlens Portal — Internal Mail Composer Workflow Layer.
Encapsulates business operations, cascading filter orchestration,
and the three requested mail sending scopes:
1. For All (Unfiltered global employee search)
2. Company Wise (Scoped to Company)
3. Company + Branch Wise (Scoped to Company + Branch)
4. Group / Branch Broadcast
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, expect
from pages.hrlense_portal.internal_mail.internal_mail_composer_page import InternalMailComposerPage

logger = logging.getLogger(__name__)


class InternalMailComposerWorkflow:
    """Workflow orchestrator for Internal Mail Composer (/internal-mail-composer)."""

    def __init__(self, page: Page):
        self.page = page
        self.composer = InternalMailComposerPage(page)

    def open_fresh_composer(self) -> None:
        """Navigates to internal mail composer and opens composer drawer."""
        logger.info("[WORKFLOW] Opening fresh composer drawer...")
        self.composer.navigate_to_composer()
        self.composer.click_compose()

    def verify_empty_recipient_validation(
        self,
        subject: str = "[Validation] Empty Recipient",
        body: str = "This message should not be sent without a recipient."
    ) -> str:
        """
        Attempts to send an email without selecting any recipient.
        Returns the captured validation toast message.
        """
        logger.info("[WORKFLOW] Executing empty recipient validation flow...")
        self.composer.fill_subject(subject)
        self.composer.fill_message_body(body)
        toast = self.composer.click_send_message()
        self.composer.click_discard()
        return toast

    def verify_cascading_dropdown_dependency_states(
        self,
        company_name: str = "TEK Inspirations LLC",
        branch_name: str = "Varanasi"
    ) -> Dict[str, Any]:
        """
        Validates the cascading dependency hierarchy:
        1. Initial state:
           - Company: Enabled ('Select Company')
           - Branch: Disabled ('Select Company First')
           - Department: Disabled ('Select Branch First')
        2. Select Company:
           - Branch: Becomes Enabled ('Select Branch')
        3. Select Branch:
           - Department: Becomes Enabled ('Select Department')
        """
        logger.info("[WORKFLOW] Verifying cascading dropdown dependency states...")
        self.composer.select_recipient_mode("individual")

        # Step 1: Initial State Check
        initial_company_text = self.composer.get_company_filter_button_text()
        initial_branch_text = self.composer.get_branch_filter_button_text()
        initial_branch_enabled = self.composer.is_branch_filter_enabled()
        initial_dept_text = self.composer.get_department_filter_button_text()
        initial_dept_enabled = self.composer.is_department_filter_enabled()

        logger.info(
            f"[INITIAL STATE] Company: '{initial_company_text}' | "
            f"Branch: '{initial_branch_text}' (enabled={initial_branch_enabled}) | "
            f"Dept: '{initial_dept_text}' (enabled={initial_dept_enabled})"
        )

        # Step 2: Select Company
        self.composer.select_company_filter(company_name)
        after_company_branch_text = self.composer.get_branch_filter_button_text()
        after_company_branch_enabled = self.composer.is_branch_filter_enabled()

        logger.info(
            f"[AFTER COMPANY] Branch: '{after_company_branch_text}' (enabled={after_company_branch_enabled})"
        )

        # Step 3: Select Branch
        self.composer.select_branch_filter(branch_name)
        self.page.wait_for_timeout(1500)
        after_branch_dept_text = self.composer.get_department_filter_button_text()
        after_branch_dept_enabled = self.composer.is_department_filter_enabled()

        logger.info(
            f"[AFTER BRANCH] Dept: '{after_branch_dept_text}' (enabled={after_branch_dept_enabled})"
        )

        return {
            "initial": {
                "company_text": initial_company_text,
                "branch_text": initial_branch_text,
                "branch_enabled": initial_branch_enabled,
                "dept_text": initial_dept_text,
                "dept_enabled": initial_dept_enabled,
            },
            "after_company": {
                "branch_text": after_company_branch_text,
                "branch_enabled": after_company_branch_enabled,
            },
            "after_branch": {
                "dept_text": after_branch_dept_text,
                "dept_enabled": after_branch_dept_enabled,
            },
        }

    def send_mail_for_all_unfiltered(
        self,
        employee_name: str,
        subject: str,
        body: str,
        screenshot_path: Optional[str] = None
    ) -> str:
        """
        Scenario 1: 'for all'
        Searches employee across ALL employees (without Company/Branch filters),
        selects recipient, fills message, and sends mail.
        """
        logger.info(f"[WORKFLOW] Sending mail for ALL (unfiltered) to: '{employee_name}'...")
        self.composer.select_recipient_mode("individual")

        selected = self.composer.select_employee_by_name(employee_name)
        assert selected, f"Failed to select employee recipient: '{employee_name}'"

        self.composer.fill_subject(subject)
        self.composer.fill_message_body(body)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Screenshot capture note: {e}")

        toast = self.composer.click_send_message()
        return toast

    def send_mail_company_wise(
        self,
        company_name: str,
        employee_name: str,
        subject: str,
        body: str,
        screenshot_path: Optional[str] = None
    ) -> str:
        """
        Scenario 2: 'company'
        Filters by Company, searches employee under that company,
        selects recipient, fills message, and sends mail.
        """
        logger.info(f"[WORKFLOW] Sending mail Company-wise ({company_name}) to: '{employee_name}'...")
        self.composer.select_recipient_mode("individual")

        comp_selected = self.composer.select_company_filter(company_name)
        assert comp_selected, f"Failed to filter by Company: '{company_name}'"

        emp_selected = self.composer.select_employee_by_name(employee_name)
        assert emp_selected, f"Failed to select employee under Company {company_name}: '{employee_name}'"

        self.composer.fill_subject(subject)
        self.composer.fill_message_body(body)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Screenshot capture note: {e}")

        toast = self.composer.click_send_message()
        return toast

    def send_mail_company_plus_branch_wise(
        self,
        company_name: str,
        branch_name: str,
        employee_name: str,
        subject: str,
        body: str,
        screenshot_path: Optional[str] = None
    ) -> str:
        """
        Scenario 3: 'company + branch'
        Filters by Company and Branch, searches employee under that branch,
        selects recipient, fills message, and sends mail.
        """
        logger.info(f"[WORKFLOW] Sending mail Company + Branch wise ({company_name} -> {branch_name}) to: '{employee_name}'...")
        self.composer.select_recipient_mode("individual")

        comp_selected = self.composer.select_company_filter(company_name)
        assert comp_selected, f"Failed to filter by Company: '{company_name}'"

        branch_selected = self.composer.select_branch_filter(branch_name)
        assert branch_selected, f"Failed to filter by Branch: '{branch_name}'"

        emp_selected = self.composer.select_employee_by_name(employee_name)
        assert emp_selected, f"Failed to select employee under {company_name} -> {branch_name}: '{employee_name}'"

        self.composer.fill_subject(subject)
        self.composer.fill_message_body(body)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Screenshot capture note: {e}")

        toast = self.composer.click_send_message()
        return toast

    def send_mail_group_wise(
        self,
        target_name: str = "Varanasi",
        subject: str = "[Automation] Group Mail",
        body: str = "Group mail body",
        screenshot_path: Optional[str] = None
    ) -> str:
        """
        Scenario 4: Group Broadcast
        Switches to Group mode, selects target, fills message, and sends mail.
        """
        logger.info(f"[WORKFLOW] Sending group internal mail to '{target_name}'...")
        self.composer.select_recipient_mode("group")

        target_selected = self.composer.select_group_target(target_name)
        assert target_selected, f"Failed to select group target: '{target_name}'"

        self.composer.fill_subject(subject)
        self.composer.fill_message_body(body)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Screenshot capture note: {e}")

        toast = self.composer.click_send_message()
        return toast
