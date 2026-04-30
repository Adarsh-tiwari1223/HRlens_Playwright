import re
from datetime import date, datetime
from pages.base_page import BasePage


class LeavePage(BasePage):
    # Side nav
    MY_LEAVE_NAV = "nav a:has-text('My Leave')"
    LEAVE_APPLY_BTN = "button:has-text('Apply Leave')"
    ATTENDANCE_NAV = "nav a:has-text('Attendance')"
    LEAVE_REQUEST_NAV = "nav a:has-text('Leave Request')"

    # Apply leave form
    LEAVE_TYPE_DROPDOWN = "[data-testid='leave-type']"
    FROM_DATE_INPUT = "input[placeholder='From Date']"
    TO_DATE_INPUT = "input[placeholder='To Date']"
    SUBMIT_BTN = "button:has-text('Submit')"
    CONFIRM_BTN = "button:has-text('Confirm')"

    # Toast
    TOAST = ".ant-message-notice-content"

    # Logged-in user / approver
    LOGGED_IN_USER = ".user-name"
    APPROVER_NAME = "[data-testid='approver-name']"

    # Admin leave table
    EMPLOYEE_COL = "td:nth-child(1)"
    FROM_DATE_COL = "td:nth-child(2)"
    TO_DATE_COL = "td:nth-child(3)"
    APPROVE_BTN = "button:has-text('Approve')"

    def click_my_leave(self):
        self.click(self.MY_LEAVE_NAV)

    def click_leave_apply(self):
        self.click(self.LEAVE_APPLY_BTN)

    def click_attendance(self):
        self.click(self.ATTENDANCE_NAV)

    def click_leave_request(self):
        self.click(self.LEAVE_REQUEST_NAV)

    def get_logged_in_employee_name(self) -> str:
        return self.get_text(self.LOGGED_IN_USER)

    def get_approver_name(self) -> str:
        return self.get_text(self.APPROVER_NAME)

    def apply_leave_and_get_message(self, from_date: date, to_date: date, leave_type: str) -> str:
        self.page.locator(self.LEAVE_TYPE_DROPDOWN).select_option(leave_type)
        self.fill(self.FROM_DATE_INPUT, from_date.strftime("%Y-%m-%d"))
        self.fill(self.TO_DATE_INPUT, to_date.strftime("%Y-%m-%d"))
        self.click(self.SUBMIT_BTN)
        self.click(self.CONFIRM_BTN)
        self.page.locator(self.TOAST).wait_for(state="visible")
        return self.get_text(self.TOAST)

    def extract_dates_from_toast(self, toast: str) -> tuple[date, date] | None:
        match = re.search(r'from (\d{1,2} \w{3} \d{4}) to (\d{1,2} \w{3} \d{4})', toast)
        if match:
            from_date = datetime.strptime(match.group(1), "%d %b %Y").date()
            to_date = datetime.strptime(match.group(2), "%d %b %Y").date()
            return from_date, to_date
        return None

    def approve_leave(self, employee_name: str, from_date: date, to_date: date) -> bool:
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")
        rows = self.page.locator("tbody tr").all()
        for row in rows:
            name = row.locator(self.EMPLOYEE_COL).inner_text().strip()
            row_from = row.locator(self.FROM_DATE_COL).inner_text().strip()
            row_to = row.locator(self.TO_DATE_COL).inner_text().strip()
            if employee_name in name and from_str in row_from and to_str in row_to:
                row.locator(self.APPROVE_BTN).click()
                self.page.locator(self.TOAST).wait_for(state="visible")
                return "successfully" in self.get_text(self.TOAST).lower()
        return False
