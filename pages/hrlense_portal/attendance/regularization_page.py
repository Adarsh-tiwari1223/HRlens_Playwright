import random
from datetime import datetime
from pages.base_page import BasePage


class RegularizationPage(BasePage):
    # Side nav
    MY_ATTENDANCE_NAV = "a:has-text('Attendance')"
    REGULARIZATION_NAV = ".submenu_item[href='/regularizationRequest'], .submenu_item[href='/regularisation']"

    # Calendar (react-calendar)
    DATE_CELL = ".react-calendar__month-view__days button:not([disabled])"

    # Form
    IN_TIME = "(//input[@placeholder='HH : MM'])[1]"
    OUT_TIME = "(//input[@placeholder='HH : MM'])[2]"
    REASON_INPUT = "(//textarea[@placeholder='Reason'])[1]"
    APPLY_BTN = "(//button[contains(@class,'chakra-button')])[5]"
    CONFIRM_BTN = "(//button[normalize-space()='Confirm'])[1]"

    # Toast (Chakra UI)
    TOAST = "div[id^='toast-'][id*='-title']"

    # Logged-in user
    LOGGED_IN_USER = ".user-name"

    def click_my_attendance(self):
        self.click(self.MY_ATTENDANCE_NAV)

    def click_regularization(self):
        self.click(self.REGULARIZATION_NAV)

    def get_logged_in_employee_name(self) -> str:
        return self.get_text(self.LOGGED_IN_USER)

    def date_pick(self, day: int | None = None):
        cells = self.page.locator(self.DATE_CELL).all()
        available = [c for c in cells if c.inner_text().strip().isdigit()]
        if day is None:
            cell = random.choice(available)
        else:
            cell = next((c for c in available if c.inner_text().strip() == str(day)), None)
            assert cell, f"Day {day} not found in calendar"
        cell.click()

    def in_time_input(self, time_str: str, index: int = 1):
        locator = f"(//input[@placeholder='HH : MM'])[{2 * index - 1}]"
        self.page.locator(locator).fill(time_str)

    def out_time_input(self, time_str: str, index: int = 1):
        locator = f"(//input[@placeholder='HH : MM'])[{2 * index}]"
        self.page.locator(locator).fill(time_str)

    def enter_reason(self, reason: str | None = None, index: int = 1):
        if reason is None:
            reason = random.choice(["Late", "Work from home", "Half day"])
        locator = f"(//textarea[@placeholder='Reason'])[{index}]"
        self.page.locator(locator).fill(reason)

    def fill_regularization_row(self, index: int, time_in: str, time_out: str, reason: str):
        self.in_time_input(time_in, index)
        self.out_time_input(time_out, index)
        self.enter_reason(reason, index)

    def click_apply_btn(self):
        self.click(self.APPLY_BTN)

    def click_confirm_btn(self):
        self.click(self.CONFIRM_BTN)

    def get_pop_msg(self) -> str | None:
        toast = self.page.locator(self.TOAST)
        toast.wait_for(state="visible")
        return toast.inner_text().strip().lower() if toast.is_visible() else None

    def get_matched_employee_row(self, employee_name: str, reg_date: datetime | str | None = None):
        date_str = reg_date.strftime("%Y-%m-%d") if hasattr(reg_date, "strftime") else str(reg_date) if reg_date else None
        rows = self.page.locator("tbody tr").all()
        for row in rows:
            emp = row.locator("td:nth-child(4)").inner_text().strip()
            status = row.locator("td:nth-child(9)").inner_text().strip().lower()
            if employee_name not in emp:
                continue
            if date_str:
                date_cell = row.locator("td:nth-child(5)").inner_text().strip()
                if date_str not in date_cell:
                    continue
            if "pending" not in status:
                continue
            return row
        return None

    def approve_regularization(self, employee_name: str, reg_date: datetime | str | None = None):
        row = self.get_matched_employee_row(employee_name, reg_date)
        assert row, f"No pending regularization found for {employee_name} on {reg_date}"
        row.locator("select").select_option("Approve")
        self.click_confirm_btn()
        toast = self.get_pop_msg()
        assert toast and "successfully" in toast, f"Approval failed. Toast: {toast}"
