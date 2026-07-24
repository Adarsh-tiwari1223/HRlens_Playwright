import logging
import re
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AttendanceSheetPage(BasePage):
    ATTENDANCE_LINK = "role=link[name='Attendance']"
    SHEET_LINK = "role=link[name='• Attendance Sheet']"
    SEARCH_INPUT = "placeholder='Search name'"

    def navigate_to_attendance_sheet(self):
        logger.info("Navigating to Attendance Sheet page")
        self.page.get_by_role("link", name="Attendance", exact=True).click()
        self.page.wait_for_timeout(500)
        self.page.get_by_role("link", name="• Attendance Sheet").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    def search_employee(self, name: str):
        logger.info(f"Searching employee: {name}")
        search_field = self.page.get_by_placeholder("Search name")
        search_field.wait_for(state="visible", timeout=10000)
        search_field.fill(name)
        self.page.wait_for_timeout(2000) # Wait for debounce search results

    def get_employee_attendance_record(self, name: str) -> dict | None:
        logger.info(f"Retrieving attendance record for: {name}")
        rows = self.page.locator("table tbody tr").all()
        for row in rows:
            row_text = row.inner_text()
            if name.lower() in row_text.lower():
                cells = row.locator("td").all()
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
