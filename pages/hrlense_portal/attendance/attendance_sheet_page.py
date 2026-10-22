import logging
import re
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)
class AttendanceSheetPage(BasePage):
    # ── Manager/Admin Attendance Sheet Locators ──────────────────────────────
    ATTENDANCE_LINK = "role=link[name='Attendance']"
    SHEET_LINK = "role=link[name='• Attendance Sheet']"
    SEARCH_INPUT = "placeholder='Search name'"

    # ── Employee My Attendance Sheet Locators (/myAttendanceSheet) ───────────
    MY_ATTENDANCE_HEADING = ".page_heading p, p:has-text('My Attendance')"
    SUMMARY_CARD_BOX = ".card_box"
    CARD_LABEL = ".card_label"
    CARD_VALUE = ".card_value"
    MONTH_SELECT = ".chakra-select:has(option[value='10']), .css-1fpbagy select:nth-of-type(1), select.chakra-select"
    YEAR_SELECT = ".chakra-select:has(option[value='2026']), .css-1fpbagy select:nth-of-type(2)"
    ATTENDANCE_TABLE = "table.chakra-table"
    TABLE_THEAD_TH = "table.chakra-table thead th"
    TABLE_TBODY_TR = "table.chakra-table tbody tr"

    def navigate_to_attendance_sheet(self):
        logger.info("Navigating to Admin Attendance Sheet page")
        self.page.get_by_role("link", name="Attendance", exact=True).click()
        self.page.wait_for_timeout(500)
        self.page.get_by_role("link", name="• Attendance Sheet").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    def navigate_to_my_attendance_sheet(self):
        """Navigates directly to Employee Self-Service /myAttendanceSheet."""
        logger.info("Navigating to Employee My Attendance Sheet (/myAttendanceSheet)")
        self.page.goto(f"{settings.BASE_URL}/myAttendanceSheet", timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.locator(self.ATTENDANCE_TABLE).first.wait_for(state="visible", timeout=15000)
        self.page.wait_for_timeout(1000)

    def search_employee(self, name: str):
        logger.info(f"Searching employee: {name}")
        search_field = self.page.get_by_placeholder("Search name")
        search_field.wait_for(state="visible", timeout=10000)
        search_field.fill(name)
        self.page.wait_for_timeout(2000) # Wait for debounce search results

    def get_employee_attendance_record(self, name: str) -> dict | None:
        logger.info(f"Retrieving attendance record for: {name}")
        rows = self.page.locator("table tbody tr:visible").all()
        for row in rows:
            row_text = row.inner_text()
            if name.lower() in row_text.lower():
                cells = row.locator("td:visible").all()
                if len(cells) >= 8:
                    return {
                        "emp_code": cells[1].inner_text().strip(),
                        "name": cells[2].inner_text().strip(),
                        "check_in": cells[3].inner_text().strip(),
                        "check_out": cells[4].inner_text().strip(),
                        "break_time": cells[5].inner_text().strip(),
                        "date": cells[6].inner_text().strip(),
                        "status": cells[7].inner_text().strip()
                    }
        return None

    # ── My Attendance Sheet Interaction Methods ──────────────────────────────
    def get_header_employee_info(self) -> dict:
        """
        Extracts employee name and employee code from heading banner.
        Example: 'My Attendance >> Uttam Kumar (858)' -> name='Uttam Kumar', code='858'
        """
        heading_text = ""
        try:
            head_el = self.page.locator(self.MY_ATTENDANCE_HEADING).first
            if head_el.is_visible(timeout=3000):
                heading_text = head_el.inner_text().strip()
        except Exception:
            pass

        info = {"raw": heading_text, "name": "", "code": ""}
        if ">>" in heading_text:
            emp_part = heading_text.split(">>")[-1].strip()
            match = re.search(r"^(.*?)(?:\s*\((\d+)\))?$", emp_part)
            if match:
                info["name"] = match.group(1).strip()
                info["code"] = match.group(2) or ""
        logger.info(f"[MY ATTENDANCE HEADER] {info}")
        return info

    def get_summary_metrics(self) -> dict[str, int]:
        """
        Extracts all visible metric cards from the top summary row.
        Returns: {'Total Days': 31, 'Present': 2, 'Absent': 0, 'Late': 1, 'Week off': 8, ...}
        """
        metrics = {}
        try:
            cards = self.page.locator(f"{self.SUMMARY_CARD_BOX}:visible").all()
            for card in cards:
                lbl_el = card.locator(self.CARD_LABEL).first
                val_el = card.locator(self.CARD_VALUE).first
                if lbl_el.is_visible() and val_el.is_visible():
                    lbl = lbl_el.inner_text().strip()
                    val_str = val_el.inner_text().strip()
                    val = int(val_str) if val_str.isdigit() else 0
                    metrics[lbl] = val
        except Exception as e:
            logger.warning(f"Error reading summary metrics: {e}")
        logger.info(f"[MY ATTENDANCE METRICS] {metrics}")
        return metrics

    def select_month(self, month: int | str):
        """Selects month in the month dropdown (e.g. 10 for October or 'October')."""
        logger.info(f"Selecting month: {month} in My Attendance Sheet")
        try:
            sel = self.page.locator("select.chakra-select").first
            sel.wait_for(state="visible", timeout=3000)
            try:
                sel.select_option(value=str(month))
            except Exception:
                sel.select_option(label=str(month))
            self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"Error selecting month: {e}")

    def select_year(self, year: int | str):
        """Selects year in the year dropdown (e.g. 2026)."""
        logger.info(f"Selecting year: {year} in My Attendance Sheet")
        try:
            sel = self.page.locator("select.chakra-select").nth(1)
            sel.wait_for(state="visible", timeout=3000)
            sel.select_option(str(year))
            self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"Error selecting year: {e}")

    def get_table_headers(self) -> list[str]:
        """Reads visible column header names from the daily attendance table."""
        headers = []
        try:
            th_locators = self.page.locator(f"{self.TABLE_THEAD_TH}:visible").all()
            headers = [th.inner_text().strip() for th in th_locators if th.inner_text().strip()]
        except Exception as e:
            logger.warning(f"Error reading table headers: {e}")
        return headers

    def get_daily_records(self) -> list[dict]:
        """
        Extracts all visible rows from the attendance sheet table mapped dynamically
        by header title.
        Returns: [{'s_no': '1', 'date': '2026-10-01', 'day': 'Thursday', 'check_in': '13:57', ...}]
        """
        headers = self.get_table_headers()
        records = []
        try:
            rows = self.page.locator(f"{self.TABLE_TBODY_TR}:visible").all()
            for row in rows:
                cells = [td.inner_text().strip() for td in row.locator("td:visible").all()]
                if not cells:
                    continue
                row_dict = {}
                for idx, cell_val in enumerate(cells):
                    h_title = headers[idx] if idx < len(headers) else f"col_{idx}"
                    # Normalize header key to clean snake_case
                    clean_key = re.sub(r"[^a-zA-Z0-9]+", "_", h_title.strip().lower()).strip("_")
                    row_dict[clean_key] = cell_val
                row_dict["_row_element"] = row
                records.append(row_dict)
        except Exception as e:
            logger.warning(f"Error reading daily records: {e}")
        return records

    def get_record_by_date_or_day(self, target_day: int | str) -> dict | None:
        """
        Locates the specific day's record (e.g. day=3 or '2026-10-03').
        """
        records = self.get_daily_records()
        target_str = str(target_day).zfill(2) if str(target_day).isdigit() and len(str(target_day)) < 2 else str(target_day)

        for rec in records:
            date_val = rec.get("date", "")
            s_no = rec.get("s_no", "")
            if date_val.endswith(f"-{target_str}") or s_no == str(target_day) or target_str in date_val:
                return rec
        return None

    # ── Punch Logs Modal Interaction Methods ─────────────────────────────────
    PUNCH_LOGS_MODAL = "section.chakra-modal__content:has-text('Punch Logs'), [role='dialog']:has-text('Punch Logs')"
    PUNCH_LOGS_HEADER = ".chakra-modal__header:has-text('Punch Logs'), header:has-text('Punch Logs')"
    PUNCH_LOGS_CLOSE_BTN = "button[aria-label='Close'], .chakra-modal__close-btn"
    PUNCH_LOGS_TABLE = "section.chakra-modal__content table, [role='dialog'] table"

    def click_date_to_open_punch_logs(self, target_day_or_date: int | str = 1) -> bool:
        """
        Clicks on the Date cell in the attendance table to open the Punch Logs modal.
        E.g., target_day_or_date=1 or '2026-10-01'.
        """
        logger.info(f"Clicking on date '{target_day_or_date}' to open Punch Logs modal...")
        rec = self.get_record_by_date_or_day(target_day_or_date)
        if not rec or "_row_element" not in rec:
            target_str = str(target_day_or_date).zfill(2) if str(target_day_or_date).isdigit() and len(str(target_day_or_date)) < 2 else str(target_day_or_date)
            row = self.page.locator(f"{self.TABLE_TBODY_TR}:visible").filter(has_text=target_str).first
        else:
            row = rec["_row_element"]

        if not row or not row.is_visible():
            logger.warning(f"Could not locate row for date {target_day_or_date}")
            return False

        # Find Date cell in row (column 2 is Date)
        date_cell = row.locator("td:nth-child(2)").first
        if not date_cell.is_visible(timeout=1000):
            date_cell = row.locator("td, a, span, p").filter(has_text=re.compile(r"\d{2,4}-\d{2}-\d{2,4}")).first
        if not date_cell.is_visible(timeout=1000):
            date_cell = row.locator("td").first

        logger.info(f"Clicking date element: '{date_cell.inner_text().strip()}'")
        date_cell.click()
        self.page.wait_for_timeout(500)

        # Wait for Punch Logs modal to appear
        try:
            modal_header = self.page.locator(self.PUNCH_LOGS_HEADER).first
            modal_header.wait_for(state="visible", timeout=10000)
            logger.info(f"Punch Logs modal opened successfully: '{modal_header.inner_text().strip()}'")
            return True
        except Exception as e:
            logger.warning(f"Punch Logs modal did not appear: {e}")
            return False

    def get_punch_logs_modal(self):
        """Returns locator for the visible Punch Logs modal section."""
        return self.page.locator(".chakra-modal__content:visible, [role='dialog']:visible").filter(has_text="Punch Logs").first

    def is_punch_logs_modal_visible(self) -> bool:
        """Returns True if Punch Logs modal is visible."""
        try:
            modal = self.get_punch_logs_modal()
            return modal.is_visible(timeout=2000)
        except Exception:
            return False

    def get_punch_logs_modal_header(self) -> str:
        """Returns header text from the Punch Logs modal (e.g. 'Punch Logs – 2026-10-01')."""
        try:
            modal = self.get_punch_logs_modal()
            head = modal.locator(".chakra-modal__header, header").first
            if head.is_visible(timeout=3000):
                return head.inner_text().strip()
        except Exception:
            pass
        return ""

    def get_punch_logs_table_headers(self) -> list[str]:
        """Reads column headers from the Punch Logs modal table ('S. No', 'Punch Time', 'Punch Type')."""
        headers = []
        try:
            modal = self.get_punch_logs_modal()
            th_elements = modal.locator("table thead th:visible").all()
            for th in th_elements:
                txt = th.inner_text().strip()
                if txt:
                    headers.append(txt)
        except Exception as e:
            logger.warning(f"Error reading punch logs table headers: {e}")
        return headers

    def get_punch_logs_records(self) -> list[dict]:
        """
        Extracts all punch records from the Punch Logs modal table.
        Returns: [{'s_no': '1', 'punch_time': '01-10-2026 01:57 PM', 'punch_type': 'IN'}, ...]
        """
        records = []
        try:
            headers = self.get_punch_logs_table_headers()
            modal = self.get_punch_logs_modal()
            rows = modal.locator("table tbody tr:visible").all()
            for row in rows:
                cells = [td.inner_text().strip() for td in row.locator("td:visible").all()]
                if not cells:
                    continue
                rec = {}
                for idx, cell_val in enumerate(cells):
                    h_title = headers[idx] if idx < len(headers) else f"col_{idx}"
                    clean_key = re.sub(r"[^a-zA-Z0-9]+", "_", h_title.strip().lower()).strip("_")
                    rec[clean_key] = cell_val
                records.append(rec)
        except Exception as e:
            logger.warning(f"Error reading punch logs records: {e}")
        logger.info(f"Retrieved {len(records)} punch records from modal.")
        return records

    def close_punch_logs_modal(self):
        """Closes the Punch Logs modal using the Close button."""
        logger.info("Closing Punch Logs modal...")
        try:
            modal = self.get_punch_logs_modal()
            close_btn = modal.locator("button[aria-label='Close'], .chakra-modal__close-btn").first
            if close_btn.is_visible(timeout=2000):
                close_btn.click()
                self.page.wait_for_timeout(500)
            else:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
        except Exception as e:
            logger.warning(f"Error closing punch logs modal: {e}")
            self.page.keyboard.press("Escape")
