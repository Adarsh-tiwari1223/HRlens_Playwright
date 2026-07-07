import logging
from core.config import settings
from pages.base_page import BasePage
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

ROW = "table tbody tr"
CELL = "td"

# 0-based column indices — verify against actual UI column order
COL = {
    "emp_code":      0,
    "employee_name": 1,
    "basic":         2,
    "hra":           3,
    "net_salary":    4,
    "tds":           5,
}


class PayrollPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_payroll(self):
        self.page.goto(f"{settings.BASE_URL}/payroll")
        self.page.wait_for_load_state("networkidle")

    def apply_branch_filter(self, branch: str = "Varanasi - Inf"):
        self.page.get_by_role("img", name="Filter").click()
        self.page.get_by_text("Branch", exact=True).click()
        self.page.locator("label").filter(has_text=branch).locator("span").first.click()
        self.page.get_by_role("button", name="Apply").click()
        self.page.wait_for_load_state("networkidle")

    def run_payroll(self):
        """Click Run-Payroll → Confirm, then poll Reload → Confirm until table loads."""
        self.page.get_by_role("button", name="Run-Payroll").click()
        self.page.get_by_role("button", name="Confirm").click()

        # Wait for "Payroll generation started" toast
        self.page.get_by_text("Payroll generation started").wait_for(state="visible", timeout=15000)
        logger.info("Payroll generation started")

        self._poll_reload(max_attempts=10, timeout_per_attempt=30000)

    def _poll_reload(self, max_attempts: int = 10, timeout_per_attempt: int = 30000):
        """Keep clicking Reload → Confirm until the data table appears."""
        for attempt in range(1, max_attempts + 1):
            reload_btn = self.page.get_by_role("button", name="Reload")

            # If no Reload button visible, data is ready
            if not reload_btn.is_visible():
                logger.info("No Reload button — data ready after %d attempt(s)", attempt - 1)
                return

            logger.info("Reload attempt %d/%d", attempt, max_attempts)
            reload_btn.click()
            self.page.get_by_role("button", name="Confirm").click()

            # Wait briefly for the page to respond before checking again
            try:
                self.page.locator(ROW).first.wait_for(state="visible", timeout=timeout_per_attempt)
                logger.info("Table rows visible after reload attempt %d", attempt)
                return
            except Exception:
                logger.info("Table not ready yet, will reload again...")
                continue

        raise TimeoutError(f"Payroll table not ready after {max_attempts} reload attempts")

    def get_table_rows(self) -> list[dict]:
        self.page.locator(ROW).first.wait_for(state="visible")
        result = []
        for row in self.page.locator(ROW).all():
            cells = row.locator(CELL).all_inner_texts()
            if len(cells) <= max(COL.values()):
                continue
            result.append({
                "emp_code":      cells[COL["emp_code"]].strip(),
                "employee_name": cells[COL["employee_name"]].strip(),
                "basic":         _to_num(cells[COL["basic"]]),
                "hra":           _to_num(cells[COL["hra"]]),
                "net_salary":    _to_num(cells[COL["net_salary"]]),
                "tds":           _to_num(cells[COL["tds"]]),
            })
        return result


def _to_num(value: str) -> float:
    cleaned = value.replace(",", "").replace("₹", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
