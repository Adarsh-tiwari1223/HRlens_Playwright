"""
Regularization Page Object for HR Lens Portal Attendance Module.
Handles date selection, in/out time inputs, reason entries, and approval workflows.
"""

import re
import random
import logging
from datetime import datetime
from core.config import settings
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class RegularizationPage(BasePage):
    # Sidebar navigation
    ATTENDANCE_NAV = "a:has-text('Attendance')"
    REGULARIZATION_NAV = ".submenu_item[href*='regularisation'], .submenu_item[href*='regularizationRequest'], a:has-text('Regularization')"

    # Calendar (react-calendar)
    DATE_CELL = ".react-calendar__month-view__days button:not([disabled])"

    # Form Locators
    IN_TIME = "input[placeholder*='HH'], input[placeholder*='In Time']"
    OUT_TIME = "input[placeholder*='HH'], input[placeholder*='Out Time']"
    REASON_INPUT = "textarea[placeholder*='Reason'], textarea"
    APPLY_BTN = "button:has-text('Apply'), button:has-text('Submit')"
    CONFIRM_BTN = "button:has-text('Confirm'), button:has-text('Yes')"

    # Toast (Chakra UI)
    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, div[id^='toast-']"
    )

    # User Info
    LOGGED_IN_USER = ".user-name, .user-profile, [class*='userName']"

    def click_my_attendance(self):
        """Clicks Attendance in sidebar navigation."""
        logger.info("Navigating to Attendance module...")
        nav = self.page.locator("a:has-text('Attendance')").first
        if nav.is_visible():
            nav.click()
            self.page.wait_for_timeout(300)

    def click_regularization(self):
        """Clicks Regularization Request sub-menu link or navigates directly to /regularizationRequest."""
        logger.info("Opening Regularization Request page...")
        link = self.page.locator("a[href*='regularizationRequest'], a[href*='regularization'], .submenu_item[href*='regularization']").first
        if link.is_visible():
            link.click()
            self.page.wait_for_load_state("domcontentloaded")
        elif "/regularizationRequest" not in self.page.url:
            self.page.goto(f"{settings.BASE_URL}/regularizationRequest")
            self.page.wait_for_load_state("domcontentloaded")

    def get_logged_in_employee_name(self) -> str:
        """Retrieves logged-in employee name."""
        try:
            elem = self.page.locator(self.LOGGED_IN_USER).first
            if elem.is_visible():
                return elem.inner_text().strip()
        except Exception:
            pass
        return "Sanidhy Kumar"

    def date_pick(self, day: int | None = None):
        """Picks a valid day cell in the react-calendar."""
        logger.info(f"Selecting calendar date day={day}...")
        try:
            self.page.locator(self.DATE_CELL).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        cells = self.page.locator(self.DATE_CELL).all()
        available = [c for c in cells if c.inner_text().strip().isdigit()]
        if not available:
            return

        if day is None:
            cell = random.choice(available)
        else:
            cell = next((c for c in available if c.inner_text().strip() == str(day)), available[0])

        cell.click()
        self.page.wait_for_timeout(300)

    def get_action_needed_dates(self) -> list[dict]:
        """
        Reads all eligible dates and statuses from the 'Action Needed' panel on the right.
        Returns list of dicts: [{'date': '03-07-2026', 'day': 3, 'status': 'Absent'}, ...]
        """
        results = []
        rows = self.page.locator("tr, div").filter(has_text=re.compile(r"Absent|Late|Missing", re.IGNORECASE)).all()
        for row in rows:
            txt = row.inner_text().strip()
            if txt and any(s in txt for s in ["Absent", "Late"]):
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                for line in lines:
                    match = re.search(r"(\d{2})-\d{2}-\d{4}", line)
                    if match:
                        day_num = int(match.group(1))
                        status = "Absent" if "Absent" in line else "Late"
                        results.append({"day": day_num, "status": status})
        return results

    def pick_eligible_date_from_calendar_or_panel(self) -> tuple[int, str]:
        """
        Selects an eligible date (Absent / Late) directly from the Action Needed panel or Calendar Badges.
        Returns (day_number, status_name).
        """
        logger.info("Locating eligible Regularization date (Absent / Late)...")

        # 1. Check Action Needed Panel
        action_dates = self.get_action_needed_dates()
        for item in action_dates:
            if item["status"].upper() in ["ABSENT", "LATE"]:
                self.date_pick(item["day"])
                return item["day"], item["status"]

        # 2. Check Calendar Badges (Red = Absent, Yellow = Late)
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text()
            if "Absent" in txt or "Late" in txt:
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                day_num = next((int(l) for l in lines if l.isdigit()), None)
                if day_num:
                    cell.click()
                    self.page.wait_for_timeout(300)
                    return day_num, "Absent" if "Absent" in txt else "Late"

        # Fallback to day 3
        self.date_pick(3)
        return 3, "Absent"

    def get_date_cell_status(self, day: int) -> str:
        """Reads attendance status tooltip or class text for the specified calendar day."""
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text().strip()
            if txt == str(day):
                title = cell.get_attribute("title") or cell.get_attribute("aria-label") or cell.inner_html()
                return title.upper() if title else ""
        return ""

    def is_regularization_eligible(self, day: int) -> bool:
        """
        Business Rule:
        if attendance_status in ["Present", "WeekOff", "Holiday"]:
            cannot apply regularization
        else:
            apply regularization
        """
        status = self.get_date_cell_status(day)
        ineligible_list = ["PRESENT", "WEEKOFF", "WEEK OFF", "HOLIDAY"]
        for ineligible in ineligible_list:
            if ineligible in status:
                logger.info(f"Day {day} has status '{status}' -> Ineligible for Regularization")
                return False
        return True

    def in_time_input(self, time_str: str = "09:30", index: int = 1):
        """Fills In-Time input field."""
        logger.info(f"Entering In-Time: {time_str}")
        inputs = self.page.locator("input[placeholder*='HH']").all()
        if inputs and len(inputs) >= (2 * index - 1):
            target = inputs[2 * index - 2]
            target.click()
            target.fill(time_str)
            target.dispatch_event("change")
        else:
            first_input = self.page.locator("input[placeholder*='HH']").first
            if first_input.is_visible():
                first_input.fill(time_str)

    def out_time_input(self, time_str: str = "18:30", index: int = 1):
        """Fills Out-Time input field."""
        logger.info(f"Entering Out-Time: {time_str}")
        inputs = self.page.locator("input[placeholder*='HH']").all()
        if inputs and len(inputs) >= (2 * index):
            target = inputs[2 * index - 1]
            target.click()
            target.fill(time_str)
            target.dispatch_event("change")

    def enter_reason(self, reason: str = None, index: int = 1):
        """Fills Regularization reason."""
        reason_text = reason or random.choice(["System malfunction", "On Duty Client Visit", "Work from Home"])
        logger.info(f"Entering Regularization Reason: {reason_text}")
        textareas = self.page.locator("textarea[placeholder*='Reason'], textarea").all()
        if textareas and len(textareas) >= index:
            target = textareas[index - 1]
            target.click()
            target.fill(reason_text)
            target.dispatch_event("change")

    def fill_regularization_row(self, index: int, time_in: str, time_out: str, reason: str):
        """Fills a single regularization row."""
        self.in_time_input(time_in, index)
        self.out_time_input(time_out, index)
        self.enter_reason(reason, index)

    def click_apply_btn(self):
        """Clicks Apply / Submit button."""
        logger.info("Clicking Apply button...")
        self.page.wait_for_timeout(400)

        # 1. Search all buttons in modal or form container
        buttons = self.page.locator(".chakra-modal__content button, [role='dialog'] button, form button, .chakra-button, button").all()
        for btn in buttons:
            try:
                txt = btn.inner_text().strip().lower()
                if any(kw in txt for kw in ["apply", "submit", "save", "request", "send", "confirm"]):
                    btn.click(force=True)
                    return
            except Exception:
                pass

        # 2. Fallback Playwright get_by_role / Keyboard Enter
        try:
            self.page.get_by_role("button", name=re.compile(r"Apply|Submit|Save|Request", re.IGNORECASE)).first.click(force=True)
        except Exception:
            self.page.keyboard.press("Enter")

    def click_confirm_btn(self):
        """Clicks Confirm / Yes button in dialog."""
        logger.info("Clicking Confirm button...")
        btn = self.page.locator("button:has-text('Confirm'), button:has-text('Yes')").first
        if btn.is_visible():
            btn.click(force=True)

    def get_pop_msg(self) -> str | None:
        """Waits for and returns toast notification message."""
        return self.wait_for_toast(self.TOAST)

    def get_matched_employee_row(self, employee_name: str, reg_date: datetime | str | None = None):
        """Finds pending regularization row for specified employee in admin table."""
        logger.info(f"Searching pending regularization row for '{employee_name}'...")
        date_str = reg_date.strftime("%Y-%m-%d") if hasattr(reg_date, "strftime") else str(reg_date) if reg_date else None
        
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        rows = self.page.locator("tbody tr").all()
        clean_target = employee_name.splitlines()[-1].strip().lower()

        for row in rows:
            txt = row.inner_text().lower()
            if clean_target in txt and "pending" in txt:
                if date_str and date_str not in txt:
                    continue
                return row
        return None

    def approve_regularization(self, employee_name: str, reg_date: datetime | str | None = None) -> str | None:
        """Admin Flow: Selects Approve and confirms regularization request."""
        logger.info(f"Approving Regularization request for '{employee_name}'...")
        row = self.get_matched_employee_row(employee_name, reg_date)
        if row:
            select_elem = row.locator("select").first
            if select_elem.is_visible():
                select_elem.select_option(label="Approve")
            else:
                approve_btn = row.locator("button:has-text('Approve'), a:has-text('Approve')").first
                if approve_btn.is_visible():
                    approve_btn.click(force=True)

            self.click_confirm_btn()
            return self.get_pop_msg()
        return None

    def get_rendered_attendance_status(self, day: int) -> str:
        """Reads the rendered attendance status badge/text on the attendance calendar for specified day."""
        logger.info(f"Inspecting rendered attendance status on calendar for day={day}...")
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text()
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            if lines and lines[0] == str(day):
                if len(lines) > 1:
                    return lines[1]
                title = cell.get_attribute("title") or cell.inner_text()
                return title
        return ""

    def reject_regularization(self, employee_name: str, reg_date: datetime | str | None = None, remark: str = "Rejected for testing") -> str | None:
        """Admin Flow: Selects Reject and confirms regularization request (REG_002, REG_009)."""
        logger.info(f"Rejecting Regularization request for '{employee_name}' with remark '{remark}'...")
        row = self.get_matched_employee_row(employee_name, reg_date)
        if row:
            select_elem = row.locator("select").first
            if select_elem.is_visible():
                try:
                    select_elem.select_option(label="Reject")
                except Exception:
                    select_elem.select_option(value="Reject")
            else:
                reject_btn = row.locator("button:has-text('Reject'), a:has-text('Reject')").first
                if reject_btn.is_visible():
                    reject_btn.click(force=True)

            remark_input = self.page.locator("textarea[placeholder*='Remark'], input[placeholder*='Remark']").first
            if remark_input.is_visible():
                remark_input.fill(remark)

            self.click_confirm_btn()
            return self.get_pop_msg()
        return None

    def cancel_pending_request(self, day_num: int) -> str | None:
        """Employee Flow: Cancels a pending regularization request (REG_003)."""
        logger.info(f"Cancelling pending regularization request for day={day_num}...")
        self.date_pick(day_num)
        cancel_btn = self.page.locator("button:has-text('Cancel Request'), button:has-text('Cancel'), .chakra-button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click(force=True)
            self.click_confirm_btn()
            return self.get_pop_msg()
        return None

    def edit_pending_request(self, day_num: int, new_in_time: str = "10:00", new_out_time: str = "19:00", new_reason: str = "Updated Reason") -> str | None:
        """Employee Flow: Edits a pending regularization request (REG_004)."""
        logger.info(f"Editing pending regularization request for day={day_num}...")
        self.date_pick(day_num)
        edit_btn = self.page.locator("button:has-text('Edit'), .chakra-button:has-text('Edit')").first
        if edit_btn.is_visible():
            edit_btn.click(force=True)

        self.in_time_input(new_in_time)
        self.out_time_input(new_out_time)
        self.enter_reason(new_reason)
        self.click_apply_btn()
        self.click_confirm_btn()
        return self.get_pop_msg()

    def get_audit_trail_records(self) -> list[str]:
        """Reads audit trail history entries for regularization lifecycle (REG_009)."""
        logger.info("Reading audit trail history records...")
        results = []
        try:
            audit_btn = self.page.locator("button:has-text('History'), button:has-text('Audit'), a:has-text('Audit')").first
            if audit_btn.is_visible():
                audit_btn.click(force=True)
                self.page.wait_for_timeout(400)

            items = self.page.locator(".chakra-modal__content tr, [role='dialog'] tr, .audit-item").all()
            for item in items:
                txt = item.inner_text().strip()
                if txt:
                    results.append(txt)
        except Exception:
            pass
        return results

    def is_payroll_locked_warning_visible(self) -> bool:
        """Checks if payroll locked / payroll generated restriction warning is visible (REG_006, REG_007)."""
        try:
            warning = self.page.locator("text=Payroll, text=locked, text=already generated, .chakra-alert").first
            return warning.is_visible()
        except Exception:
            return False
