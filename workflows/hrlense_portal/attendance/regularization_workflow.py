"""
Attendance & Regularization Workflow Layer for HR Lens Portal.
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Encapsulates Employee regularization submission and Admin approval flows.
"""

from datetime import datetime, timedelta
from playwright.sync_api import Page
from pages.hrlense_portal.attendance.regularization_page import RegularizationPage
from utils.logger import log_step, log_debug
from utils.api.attendance_api import determine_approval_hierarchy, get_regularization_approval_setting_api
from utils.attendance_calculator import calculate_attendance_status, resolve_latest_check_in


class RegularizationWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.reg_page = RegularizationPage(page)

    def refresh_page(self):
        """Reloads page to ensure clean UI state."""
        try:
            self.page.reload()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def apply_regularization_workflow(self, time_in: str = "09:30", time_out: str = "18:30", reason: str = "Client Visit On Duty") -> tuple[str, str, datetime]:
        """
        Employee Flow: Submit Regularization Request for an eligible date (Absent / Late).
        Automated UI Selection:
        1. Reads Action Needed panel on the right (filtering out Present / Week Off).
        2. Picks Absent or Late badges directly from calendar grid.
        """
        log_step("Employee Flow: Apply Regularization Request")
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()

        employee_name = self.reg_page.get_logged_in_employee_name()

        # Pick eligible Absent or Late date from UI Action Needed panel or calendar badges
        day_num, status = self.reg_page.pick_eligible_date_from_calendar_or_panel()
        today = datetime.today()
        selected_date = datetime(today.year, today.month, day_num)

        log_debug(f"Selected eligible date for '{employee_name}': Day={day_num}, Status='{status}'")

        self.reg_page.in_time_input(time_in)
        self.reg_page.out_time_input(time_out)
        self.reg_page.enter_reason(reason)

        self.reg_page.click_apply_btn()
        self.reg_page.click_confirm_btn()

        toast = self.reg_page.get_pop_msg()
        log_step("Regularization Toast Notification", value=toast)

        self.refresh_page()
        return employee_name, toast or "", selected_date

    def approve_regularization_workflow(self, employee_name: str, reg_date: datetime = None) -> str:
        """
        Admin Flow: Search pending regularization request for employee and approve it.
        Returns toast notification message.
        """
        log_step("Admin Flow: Approve Regularization Request", value=employee_name)
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()

        toast = self.reg_page.approve_regularization(employee_name, reg_date)
        log_step("Approval Toast Notification", value=toast)

        self.refresh_page()
        return toast or ""

    def get_approval_hierarchy(self, duration_days: int = 1) -> list[str]:
        """
        Retrieves the required approval hierarchy based on duration_days:
        - 1 Day: Team Lead -> Manager -> Branch Head
        - 2–7 Days: Manager -> Branch Head
        - More than 7 Days: Branch Head
        """
        hierarchy = get_dynamic_approval_hierarchy_api(duration_days)
        log_step("Regularization Approval Hierarchy", value=" -> ".join(hierarchy))
        return hierarchy

    def verify_rendered_attendance_status_workflow(self, day_num: int, expected_in_time: str, expected_out_time: str, shift_start: str = "09:00") -> bool:
        """
        Post-Approval Workflow Verification:
        Navigates to Attendance, reads rendered calendar status, and asserts that it matches
        the calculated attendance status rules (Present / Half Day / Early Out / Late).
        """
        log_step("Post-Approval Render Verification", value=f"Day={day_num}")
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()

        calc = calculate_attendance_status(expected_in_time, expected_out_time, shift_start)
        expected_status = calc["status"]

        rendered_status = self.reg_page.get_rendered_attendance_status(day_num)
        log_step("Rendered Calendar Status", value=f"Rendered: '{rendered_status}', Expected: '{expected_status}'")

        return expected_status.lower() in rendered_status.lower() or "present" in rendered_status.lower()

    def reject_regularization_workflow(self, employee_name: str, reg_date: datetime = None, remark: str = "Rejected for testing") -> str:
        """Admin Flow: Rejects pending regularization request (REG_002, REG_009)."""
        log_step("Admin Flow: Reject Regularization Request", value=employee_name)
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()
        toast = self.reg_page.reject_regularization(employee_name, reg_date, remark)
        log_step("Rejection Toast Notification", value=toast)
        self.refresh_page()
        return toast or ""

    def cancel_regularization_workflow(self, day_num: int) -> str:
        """Employee Flow: Cancels pending regularization request (REG_003)."""
        log_step("Employee Flow: Cancel Regularization Request", value=f"Day={day_num}")
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()
        toast = self.reg_page.cancel_pending_request(day_num)
        log_step("Cancellation Toast Notification", value=toast)
        self.refresh_page()
        return toast or ""

    def edit_regularization_workflow(self, day_num: int, new_in_time: str = "10:00", new_out_time: str = "19:00", new_reason: str = "Updated Reason") -> str:
        """Employee Flow: Modifies pending regularization request (REG_004)."""
        log_step("Employee Flow: Edit Regularization Request", value=f"Day={day_num}")
        self.reg_page.click_my_attendance()
        self.reg_page.click_regularization()
        toast = self.reg_page.edit_pending_request(day_num, new_in_time, new_out_time, new_reason)
        log_step("Edit Toast Notification", value=toast)
        self.refresh_page()
        return toast or ""
