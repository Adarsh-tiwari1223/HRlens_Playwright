import logging
import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class CrossCompanyHierarchyPage(BasePage):
    ADMIN_CONTROL_MENU = "role=link[name='Admin Control']"
    CROSS_COMPANY_LINK = "role=link[name='• Cross Company Hierarchy']"

    def navigate_to_hierarchy(self):
        logger.info("Navigating to Cross Company Hierarchy page")
        self.page.locator(self.ADMIN_CONTROL_MENU).click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(self.CROSS_COMPANY_LINK).click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def get_table_data(self) -> list[dict]:
        """
        Reads and returns the list of rows currently displayed in the table.
        Each row is parsed as a dictionary:
        {
            "s_no": str,
            "employee": str,
            "default_company": str,
            "default_access": str,
            "assigned_branches": str
        }
        """
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=5000)
        row_locators = self.page.locator("tbody tr").all()
        table_rows = []
        for row in row_locators:
            cells = row.locator("td").all()
            if len(cells) >= 5:
                row_data = {
                    "s_no": cells[0].inner_text().strip(),
                    "employee": cells[1].inner_text().strip(),
                    "default_company": cells[2].inner_text().strip(),
                    "default_access": cells[3].inner_text().strip(),
                    "assigned_branches": cells[4].inner_text().strip()
                }
                table_rows.append(row_data)
        logger.info(f"Table content read: {len(table_rows)} rows found")
        return table_rows

    def edit_employee_hierarchy(self, employee_name: str):
        """
        Finds the row containing employee_name and clicks its Edit button.
        """
        logger.info(f"Opening hierarchy editor for employee: {employee_name}")
        row = self.page.locator("tr").filter(has_text=employee_name).first
        row.get_by_label("Edit").click()
        self.page.wait_for_selector("role=dialog", state="visible", timeout=8000)

    def toggle_exclude_employee(self, exclude: bool):
        """
        Toggles the switch track for excluding employee.
        """
        switch = self.page.locator(".chakra-switch__track")
        checkbox = self.page.locator(".chakra-switch__input")
        checkbox.wait_for(state="attached", timeout=5000)
        current_state = checkbox.is_checked()
        if current_state != exclude:
            switch.click()
            logger.info(f"Exclusion switch: {exclude}")
        else:
            logger.info(f"Exclusion switch: {exclude}")

    def select_branch(self, branch_name: str):
        """
        Selects branch_name from default access/assigned branches dropdown.
        """
        dropdown = self.page.get_by_placeholder("—")
        dropdown.click()
        self.page.get_by_label("Edit HierarchyUpdate employee").get_by_text(branch_name).click()
        logger.info(f"Assigned Branch: {branch_name}")

    def click_update(self):
        logger.info("Clicking Update button")
        self.page.get_by_role("button", name="Update").click()

    def wait_for_toast_success(self) -> str:
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast.wait_for(state="visible", timeout=8000)
        toast_text = toast.inner_text().strip()
        logger.info(f"toast → '{toast_text}'")
        return toast_text

    def navigate_page(self, page_number: int):
        logger.info(f"Navigating to page {page_number}")
        self.page.get_by_label(f"Page {page_number}").click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)
