import re
import logging
from datetime import date, datetime
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LeavePage(BasePage):

    FROM_DATE_TRIGGER = "//p[normalize-space()='Start Date*']/ancestor::div[1]//input[contains(@id,'popover-trigger')]"
    TO_DATE_TRIGGER = "//p[normalize-space()='End Date*']/ancestor::div[1]//input[contains(@id,'popover-trigger')]"
    APPROVER_NAME = "//p[normalize-space()='Approval Manager']/ancestor::div[1]//input"
    LEAVE_TYPE = "//p[contains(normalize-space(),'Reason for Leave')]/ancestor::div[1]//select"
    APPROVE_BTN = "button:has-text('Approve')"
    EMPLOYEE_COL = "td:nth-child(3)"
    FROM_DATE_COL = "td:nth-child(4)"
    TO_DATE_COL = "td:nth-child(6)"
    TOAST = "#chakra-toast-manager-top-right"

    
    

    def click_my_leave(self):
        logger.info("Clicking MyLeaves nav link")
        self.page.get_by_role("link", name=re.compile(r"MyLeaves", re.IGNORECASE)).click()

    def click_leave_apply(self):
        logger.info("Clicking Leave Apply sub-menu")
        self.page.get_by_role("link", name="• Leave Apply").click()

    def click_attendance(self):
        logger.info("Clicking Attendance nav link")
        self.page.get_by_role("link", name="Attendance", exact=True).click()
    def click_leave_request(self, employee_name: str = None):
        logger.info("Clicking Leaves Request sub-menu")
        self.page.get_by_role("link", name="• Leaves Request").click()
        if employee_name:
            logger.info(f"Searching for employee: {employee_name}")
            search = self.page.get_by_role("textbox", name="Search Employee by name....")
            search.click()
            for char in employee_name:
                search.type(char)
                self.page.wait_for_timeout(50)
            self.page.wait_for_load_state("networkidle")
            self.page.locator(f"tbody tr:has-text('{employee_name}')").first.wait_for(state="visible")
            logger.info(f"Employee {employee_name} found in table")



    def get_logged_in_employee_name(self) -> str:
        name = self.page.locator("button[aria-haspopup='menu']:has(h1)").first.locator("h1").inner_text().strip()
        logger.info(f"Logged in employee: {name}")
        return name

    def get_approver_name(self) -> str:
        self.page.locator(self.APPROVER_NAME).wait_for()
        name = self.page.locator(self.APPROVER_NAME).input_value().strip()
        logger.info(f"Approver name: {name}")
        return name

    def _select_date_from_calendar(self, trigger_locator: str, target_date: date):
        logger.info(f"Selecting date: {target_date}")
        self.page.locator(trigger_locator).click()
        calendar = self.page.locator(".react-calendar:visible")
        calendar.wait_for(state="visible")

        day = target_date.day
        target_label = target_date.strftime(f"%B {day}, %Y")

        day_locator = calendar.locator(
            f"button:not(:disabled):not(.react-calendar__month-view__days__day--neighboringMonth)"
            f":has(abbr[aria-label='{target_label}'])"
        )

        if day_locator.count() == 0:
            raise AssertionError(f"Date not selectable: {target_label}")

        day_locator.first.click()
        logger.info(f"Date selected: {target_label}")

    def select_leave_type(self, leave_type: str):
        logger.info(f"Selecting leave type: {leave_type}")
        self.page.locator(self.LEAVE_TYPE).click()
        self.page.locator(self.LEAVE_TYPE).select_option(label=leave_type)

    def enter_subject(self, subject: str):
        logger.info(f"Entering subject: {subject}")
        self.page.get_by_placeholder("e.g., Leave Application - Personal Reasons").fill(subject)

    def fill_mail_body(self, body: str):
        logger.info(f"Filling mail body: {body}")
        editor = self.page.locator(".sun-editor-editable")
        editor.click()
        self.page.wait_for_timeout(500)
        self.page.evaluate(
            "(text) => navigator.clipboard.writeText(text)",
            body
        )
        self.page.keyboard.press("Control+v")

    def click_submit(self):
        logger.info("Clicking Submit/Apply button")
        self.page.locator("button").filter(has_text="Apply").first.click()

    def click_confirm(self):
        logger.info("Clicking Confirm button")
        self.page.get_by_text("Confirm").click()

    def extract_dates_from_toast(self, toast: str) -> tuple[date, date] | None:
        match = re.search(r'from (\d{1,2} \w{3} \d{4}) to (\d{1,2} \w{3} \d{4})', toast)
        if match:
            from_date = datetime.strptime(match.group(1), "%d %b %Y").date()
            to_date = datetime.strptime(match.group(2), "%d %b %Y").date()
            logger.info(f"Extracted dates from toast: {from_date} → {to_date}")
            return from_date, to_date
        return None

    def get_leave_days(self) -> int:
        from_value = self.page.locator(self.FROM_DATE_TRIGGER).input_value().strip()
        to_value = self.page.locator(self.TO_DATE_TRIGGER).input_value().strip()
        if not from_value or not to_value:
            raise ValueError("FROM or TO date field is empty")
        try:
            from_date = datetime.strptime(from_value, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_value, "%Y-%m-%d").date()
        except ValueError:
            from_date = datetime.strptime(from_value, "%d/%m/%Y").date()
            to_date = datetime.strptime(to_value, "%d/%m/%Y").date()
        days = (to_date - from_date).days + 1
        logger.info(f"Leave days: {days}")
        return days

    def approve_leave(self, employee_name: str, from_date: date, to_date: date) -> bool:
        from_str = from_date.strftime("%d-%m-%Y")
        to_str = to_date.strftime("%d-%m-%Y")
        logger.info(f"Approving leave for {employee_name} from {from_str} to {to_str}")
        rows = self.page.locator("tbody tr").all()

        # Pass 1 — exact match
        for row in rows:
            name = row.locator(self.EMPLOYEE_COL).inner_text().strip()
            row_from = row.locator(self.FROM_DATE_COL).inner_text().strip()
            row_to = row.locator(self.TO_DATE_COL).inner_text().strip()
            status = row.locator("td:nth-child(12)").inner_text().strip().lower()
            if employee_name in name and from_str in row_from and to_str in row_to and "pending" in status:
                logger.info(f"Exact match found for {employee_name}, approving...")
                row.locator("select").select_option(label="Approve")
                self.click_confirm()
                return "successfully" in self.wait_for_toast(self.TOAST).lower()

        # Pass 2 — overlap
        logger.info(f"No exact match, trying overlap for {employee_name}")
        for row in rows:
            name = row.locator(self.EMPLOYEE_COL).inner_text().strip()
            row_from_str = row.locator(self.FROM_DATE_COL).inner_text().strip()
            row_to_str = row.locator(self.TO_DATE_COL).inner_text().strip()
            status = row.locator("td:nth-child(12)").inner_text().strip().lower()
            if employee_name not in name or "pending" not in status:
                continue
            try:
                row_from_dt = datetime.strptime(row_from_str, "%d-%m-%Y").date()
                row_to_dt = datetime.strptime(row_to_str, "%d-%m-%Y").date()
                if row_from_dt <= to_date and row_to_dt >= from_date:
                    logger.info(f"Overlap match found for {employee_name}, approving...")
                    row.locator("select").select_option(label="Approve")
                    self.click_confirm()
                    return "successfully" in self.wait_for_toast(self.TOAST).lower()
            except ValueError:
                continue

        logger.warning(f"No matching pending leave found for {employee_name}")
        return False
