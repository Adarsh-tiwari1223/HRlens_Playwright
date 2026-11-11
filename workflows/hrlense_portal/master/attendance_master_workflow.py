"""
Attendance Master Workflow Layer for HR Lens Portal Master Module.
Encapsulates business operations and multi-step interactions for Attendance Settings.
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator
from pages.hrlense_portal.master.attendance_master_page import AttendanceMasterPage

logger = logging.getLogger(__name__)


class AttendanceMasterWorkflow:
    """Workflow orchestrator for Attendance Setting Master."""

    def __init__(self, page: Page):
        self.page = page
        self.attendance_page = AttendanceMasterPage(page)

    def load_attendance_settings_overview(self) -> Dict[str, Any]:
        """
        Navigates to the Attendance Setting Master and inspects overview state:
        - Checks page title visibility
        - Reads table column headers
        - Determines whether data records exist or empty state is active
        """
        logger.info("[WORKFLOW] Loading Attendance Setting Master overview...")
        self.attendance_page.navigate_to_attendance_master()
        
        headers = self.attendance_page.get_column_header_titles()
        is_empty = self.attendance_page.empty_state_message.is_visible(timeout=2000)
        row_count = 0 if is_empty else self.attendance_page.table_rows.count()

        return {
            "title_visible": self.attendance_page.heading.is_visible(timeout=5000),
            "headers": headers,
            "is_empty": is_empty,
            "row_count": row_count,
            "add_button_enabled": self.attendance_page.add_attendance_setting_button.is_enabled()
        }

    def open_and_verify_add_modal(self) -> Locator:
        """
        Opens the 'Add Attendance Setting' modal and verifies modal container.
        """
        logger.info("[WORKFLOW] Triggering 'Add Attendance Setting' modal flow...")
        self.attendance_page.navigate_to_attendance_master()
        modal = self.attendance_page.click_add_attendance_setting()
        return modal

    def inspect_add_modal_fields_workflow(self) -> Dict[str, bool]:
        """
        Opens the Add Attendance Setting modal and verifies the presence of all form fields:
        - Company selector
        - Branch selector
        - Department selector
        - Late grace input
        - Grace hour input
        - Total working hour input
        - Half day time input
        - Short leave range inputs (from/to)
        - Short leave count input
        - Save & Cancel buttons
        """
        logger.info("[WORKFLOW] Inspecting Add Attendance Setting modal fields...")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.click_add_attendance_setting()

        fields_state = {
            "company_dropdown_visible": self.attendance_page.company_dropdown_button.is_visible(timeout=3000),
            "branch_dropdown_visible": self.attendance_page.branch_dropdown_button.is_visible(timeout=3000),
            "department_dropdown_visible": self.attendance_page.department_dropdown_button.is_visible(timeout=3000),
            "late_minute_input_visible": self.attendance_page.late_minute_input.is_visible(timeout=3000),
            "grace_hour_input_visible": self.attendance_page.grace_hour_input.is_visible(timeout=3000),
            "total_working_hour_input_visible": self.attendance_page.total_working_hour_input.is_visible(timeout=3000),
            "half_day_time_input_visible": self.attendance_page.half_day_time_input.is_visible(timeout=3000),
            "short_leave_from_input_visible": self.attendance_page.short_leave_from_input.is_visible(timeout=3000),
            "short_leave_to_input_visible": self.attendance_page.short_leave_to_input.is_visible(timeout=3000),
            "short_leave_count_input_visible": self.attendance_page.short_leave_count_for_half_day_input.is_visible(timeout=3000),
            "save_button_visible": self.attendance_page.modal_save_button.is_visible(timeout=3000),
            "cancel_button_visible": self.attendance_page.modal_cancel_button.is_visible(timeout=3000),
        }

        # Dismiss modal safely
        self.attendance_page.close_add_modal()
        return fields_state

    def create_attendance_setting_workflow(self, setting_data: Dict[str, Any]) -> Optional[str]:
        """
        Executes end-to-end Attendance Setting creation workflow:
        1. Navigates to page
        2. Opens modal
        3. Fills all fields
        4. Submits and returns toast message
        """
        logger.info(f"[WORKFLOW] Creating Attendance Setting: {setting_data.get('company') or setting_data.get('companies')}")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.click_add_attendance_setting()
        self.attendance_page.fill_attendance_setting_form(setting_data)
        toast = self.attendance_page.submit_attendance_setting_form()
        return toast

    def close_add_modal(self, modal: Locator = None):
        """
        Safely dismisses the Add Attendance Setting modal.
        """
        logger.info("[WORKFLOW] Closing 'Add Attendance Setting' modal...")
        self.attendance_page.close_add_modal()

    def search_settings(self, query: str) -> Dict[str, Any]:
        """
        Executes a search filter on Attendance Settings and retrieves outcome.
        """
        logger.info(f"[WORKFLOW] Executing search filter: '{query}'")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.search(query)

        is_empty = self.attendance_page.empty_state_message.is_visible(timeout=3000)
        return {
            "query": query,
            "is_empty": is_empty,
            "row_count": 0 if is_empty else self.attendance_page.table_rows.count()
        }

    def verify_empty_search_workflow(self, query: str) -> Dict[str, Any]:
        """Executes search with expected non-matching query and returns result state."""
        return self.search_settings(query)

    def create_attendance_setting_via_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes backend creation/setup of Attendance Master setting:
        POST /AttandanceMaster
        """
        from utils.api.attendance.attendance_api import create_attendance_master_api
        logger.info(f"[WORKFLOW] Calling POST /AttandanceMaster via Playwright API context: {payload}")
        return create_attendance_master_api(payload=payload)

    def get_backend_attendance_settings(self, first: int = 0, rows: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches attendance settings directly from backend API:
        GET /AttandanceMaster?first={first}&rows={rows}
        """
        from utils.api.attendance.attendance_api import get_attendance_master_list_api
        logger.info(f"[WORKFLOW] Querying GET /AttandanceMaster?first={first}&rows={rows} for backend verification...")
        return get_attendance_master_list_api(first=first, rows=rows)

    def verify_setting_persisted_via_api(
        self,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        expected_rules: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Validates that a setting added via UI exists in the backend API response
        GET /AttandanceMaster?first=0&rows=20 and matches expected rule values.
        """
        records = self.get_backend_attendance_settings()
        for rec in records:
            match = True
            if company_id is not None and rec.get("companyId") != company_id:
                match = False
            if branch_id is not None and rec.get("branchId") != branch_id:
                match = False
            if department_id is not None and rec.get("departmentId") != department_id:
                match = False
            if match and expected_rules:
                for k, v in expected_rules.items():
                    if rec.get(k) is not None and rec.get(k) != v:
                        match = False
                        break
            if match:
                logger.info(f"[WORKFLOW] Verified Attendance Setting in backend API: ID={rec.get('id')}")
                return rec
        return None

    def open_edit_setting_workflow(self, row_index: int = 0) -> Dict[str, Any]:
        """
        Navigates to Attendance Master, opens Edit modal for a row, and inspects form values.
        """
        logger.info(f"[WORKFLOW] Opening Edit Attendance Setting modal for row {row_index}...")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.click_edit_setting_by_index(row_index=row_index)
        values = self.attendance_page.get_form_values()
        header_text = self.attendance_page.modal_header.inner_text().strip()
        self.attendance_page.close_add_modal()
        return {
            "header": header_text,
            "values": values
        }

    def get_add_form_label_sequence_workflow(self) -> List[str]:
        """Navigates to Attendance Master, opens Add modal, and returns label sequence."""
        logger.info("[WORKFLOW] Inspecting Add modal form label sequence...")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.click_add_attendance_setting()
        seq = self.attendance_page.get_form_field_label_sequence()
        self.attendance_page.close_add_modal()
        return seq

    def get_edit_form_label_sequence_workflow(self, row_index: int = 0) -> List[str]:
        """Navigates to Attendance Master, opens Edit modal, and returns label sequence."""
        logger.info(f"[WORKFLOW] Inspecting Edit modal form label sequence for row {row_index}...")
        self.attendance_page.navigate_to_attendance_master()
        self.attendance_page.click_edit_setting_by_index(row_index=row_index)
        seq = self.attendance_page.get_form_field_label_sequence()
        self.attendance_page.close_add_modal()
        return seq




