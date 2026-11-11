"""
HRlens Portal — Group Email Master Workflow Layer.
Encapsulates business operations and multi-step orchestration for Group Email Settings.
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.master.group_email_page import GroupEmailPage

logger = logging.getLogger(__name__)


class GroupEmailWorkflow:
    """Workflow orchestrator for Group Email Master (/master/group-email)."""

    def __init__(self, page: Page):
        self.page = page
        self.group_email_page = GroupEmailPage(page)

    def load_group_email_overview(self) -> Dict[str, Any]:
        """
        Navigates to Group Email Master and inspects initial overview state:
        - Available tabs
        - Active tab
        - Column headers
        - Table row count
        """
        logger.info("[WORKFLOW] Loading Group Email Master overview...")
        self.group_email_page.navigate_to_group_email()

        available_tabs = self.group_email_page.get_available_tabs()
        active_tab = self.group_email_page.get_active_tab_name()
        headers = self.group_email_page.get_column_header_titles()
        row_count = self.group_email_page.get_row_count()

        return {
            "available_tabs": available_tabs,
            "active_tab": active_tab,
            "headers": headers,
            "row_count": row_count,
        }

    def inspect_tab_structure(self, tab_name: str) -> Dict[str, Any]:
        """
        Switches to the specified tab and extracts its column headers and row count.
        """
        logger.info(f"[WORKFLOW] Inspecting tab structure for: '{tab_name}'")
        self.group_email_page.select_tab(tab_name)
        headers = self.group_email_page.get_column_header_titles()
        row_count = self.group_email_page.get_row_count()
        return {
            "tab_name": tab_name,
            "headers": headers,
            "row_count": row_count,
        }

    def inspect_global_tab_details(self, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Switches to 'Global' tab, validates headers and extracts structured rows.
        Optionally captures evidence screenshot.
        """
        logger.info("[WORKFLOW] Performing deep inspection of 'Global' tab...")
        self.group_email_page.select_tab("Global")

        headers = self.group_email_page.get_column_header_titles()
        row_count = self.group_email_page.get_row_count()
        rows_data = self.group_email_page.get_global_table_data()

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Captured Global tab screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        return {
            "tab_name": "Global",
            "headers": headers,
            "row_count": row_count,
            "rows_data": rows_data,
        }

    def validate_invalid_email_format(
        self, tab_name: str = "Company", row_index: int = 0, invalid_email: str = "notanemail", screenshot_path: Optional[str] = None
    ) -> str:
        """
        Attempts to set an invalid email format for a row, validates toast notification,
        and safely restores the original email value.
        """
        logger.info(f"[WORKFLOW] Validating invalid email handling on tab '{tab_name}', row {row_index}...")
        self.group_email_page.select_tab(tab_name)

        original_val = self.group_email_page.get_email_value(row_index)
        logger.info(f"Original email value: '{original_val}'")

        # Fill invalid email and press Enter
        toast = self.group_email_page.fill_email(row_index, invalid_email, press_enter=True)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Captured screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        # Restore original email
        logger.info(f"Restoring original email: '{original_val}'")
        self.group_email_page.fill_email(row_index, original_val, press_enter=False)

        return toast

    def update_and_revert_email(
        self, tab_name: str = "Company", row_index: int = 0, new_email: str = "automation_test@example.com", screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates an email entry, verifies the success response, and reverts back to original value.
        """
        logger.info(f"[WORKFLOW] Testing update and revert flow on tab '{tab_name}', row {row_index}...")
        self.group_email_page.select_tab(tab_name)

        original_val = self.group_email_page.get_email_value(row_index)

        # Update to new email
        update_toast = self.group_email_page.fill_email(row_index, new_email, press_enter=True)
        persisted_val = self.group_email_page.get_email_value(row_index)

        if screenshot_path:
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Captured screenshot at: '{screenshot_path}'")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        # Revert back
        revert_toast = self.group_email_page.fill_email(row_index, original_val, press_enter=True)
        restored_val = self.group_email_page.get_email_value(row_index)

        return {
            "original_email": original_val,
            "update_toast": update_toast,
            "persisted_email": persisted_val,
            "revert_toast": revert_toast,
            "restored_email": restored_val,
        }
