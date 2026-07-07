import logging
import re
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class UnauthorizedAbsencePage(BasePage):
    # Navigation
    ATTENDANCE_NAV = "a:has-text('Attendance')"
    ABSENCE_MGMT_NAV = "a:has-text('Absence Management')"
    
    # Dashboard stats
    OPEN_CASES_TEXT = "Open Cases"
    DUE_FOR_ACTION_TEXT = "Due For Action"
    UNDER_REVIEW_TEXT = "Under Review"
    ABSCONDED_TEXT = "Absconded This Month"

    # Search and Table
    SEARCH_INPUT = "input[placeholder*='Search employee']"
    TABLE_ROWS = "tbody tr"
    TOAST = "div[id^='toast-'][id*='-title']"

    # Settings Page Locators
    CONFIG_SCOPE_SELECT = "select"  # Dropdown for branch selection
    SAVE_SETTINGS_BTN = "button:has-text('Save Settings')"
    BRANCH_OVERRIDE_LABEL = "text='Branch override active'"

    def click_attendance_menu(self):
        logger.info("Expanding Attendance side menu")
        self.page.get_by_role("link", name="Attendance", exact=True).click()
        self.page.wait_for_timeout(500)

    def click_absence_management(self):
        logger.info("Clicking Absence Management submenu link")
        self.page.get_by_role("link", name="• Absence Management").click()
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(2000)

    def navigate_to_settings(self):
        logger.info("Navigating directly to settings page")
        from core.config import settings
        self.page.goto(f"{settings.BASE_URL}/absence-settings")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(2000)

    def navigate_to_absence_management(self):
        logger.info("Navigating directly to absence management dashboard")
        from core.config import settings
        self.page.goto(f"{settings.BASE_URL}/absence-management")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(2000)

    # --- Dashboard Actions ---

    def get_metric_count(self, metric_name: str) -> int:
        logger.info(f"Getting metric count for: {metric_name}")
        xpath_selector = (
            f"//*[normalize-space()='{metric_name}']/parent::div//h2 | "
            f"//*[normalize-space()='{metric_name}']/parent::div//span | "
            f"//*[normalize-space()='{metric_name}']/preceding-sibling::*[1]"
        )
        locator = self.page.locator(xpath_selector).first
        locator.wait_for(state="visible")
        text_val = locator.inner_text().strip()
        logger.info(f"Raw count text for {metric_name}: '{text_val}'")
        return int(text_val)

    def click_metric_card(self, metric_name: str):
        logger.info(f"Clicking metric card: {metric_name}")
        xpath_selector = f"//*[normalize-space()='{metric_name}']/parent::div"
        self.page.locator(xpath_selector).first.click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("load")

    # --- Search and Table ---

    def search_employee(self, query: str):
        logger.info(f"Searching for employee: '{query}'")
        search_field = self.page.locator(self.SEARCH_INPUT)
        search_field.wait_for(state="visible")
        search_field.click()
        search_field.fill("")
        search_field.press_sequentially(query, delay=100)
        self.page.wait_for_timeout(1500)
        self.page.wait_for_load_state("load")

    def get_table_rows_count(self) -> int:
        count = self.page.locator(self.TABLE_ROWS).count()
        logger.info(f"Table row count: {count}")
        if count == 1:
            first_row_text = self.page.locator(self.TABLE_ROWS).first.inner_text().lower()
            if "no record" in first_row_text or "no cases" in first_row_text:
                return 0
        return count

    def get_employee_row_data(self, employee_name: str) -> dict | None:
        rows = self.page.locator(self.TABLE_ROWS).all()
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) < 8:
                continue
            emp_info = cells[0].inner_text().strip()
            if employee_name.lower() in emp_info.lower():
                return {
                    "employee": emp_info,
                    "branch_dept": cells[2].inner_text().strip(),
                    "start_date": cells[3].inner_text().strip(),
                    "absent_days": cells[4].inner_text().strip(),
                    "communications": cells[5].inner_text().strip(),
                    "last_contact": cells[6].inner_text().strip(),
                    "status": cells[7].inner_text().strip(),
                    "view_button": row.get_by_label("View").first
                }
        return None

    def click_view_button_for_employee(self, employee_name: str):
        logger.info(f"Clicking view details button for: {employee_name}")
        row = self.page.locator(self.TABLE_ROWS).filter(has_text=employee_name).first
        row.get_by_label("View").click()
        self.page.wait_for_timeout(1500)
        self.page.wait_for_load_state("load")

    # --- Case Details Drawer/Modal Actions ---

    def get_modal_status(self) -> str:
        logger.info("Reading case status from modal details")
        status_label = self.page.locator("div").filter(has_text=re.compile(r"^(OPEN|UNDER REVIEW|ABSCONDED)", re.IGNORECASE)).first
        status_label.wait_for(state="visible")
        return status_label.inner_text().strip()

    def click_send_email(self):
        logger.info("Clicking Send Email button in details modal")
        send_btn = self.page.get_by_role("button", name="Send Email").first
        send_btn.wait_for(state="visible")
        send_btn.click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("load")

    def click_close_modal(self):
        logger.info("Closing details modal")
        close_btn = self.page.get_by_role("button", name="Close").first
        close_btn.wait_for(state="visible")
        close_btn.click()
        self.page.wait_for_timeout(1000)

    # --- Settings Page Actions ---

    def select_configuration_scope(self, scope_name: str):
        logger.info(f"Selecting configuration scope/branch: '{scope_name}'")
        select_locator = self.page.locator(self.CONFIG_SCOPE_SELECT).first
        select_locator.wait_for(state="visible")
        
        options = select_locator.locator("option").all()
        target_value = None
        for opt in options:
            text = opt.inner_text().strip()
            val = opt.get_attribute("value")
            if scope_name.lower() in text.lower():
                target_value = val
                logger.info(f"Found match: '{text}' -> value: '{val}'")
                break
                
        if target_value is not None:
            select_locator.select_option(value=target_value)
        else:
            logger.warning(f"No option matching '{scope_name}' found. Falling back to direct selection.")
            select_locator.select_option(label=scope_name)
            
        self.page.wait_for_timeout(1500)
        self.page.wait_for_load_state("load")

    def set_continuous_absent_days(self, days: int):
        logger.info(f"Setting continuous absent days threshold to: {days}")
        
        # Ensure Continuous Absent Days container is loaded
        container = self.page.locator("//div[contains(., 'Continuous Absent Days')]").first
        container.wait_for(state="visible")
        
        btn = self.page.get_by_text(f"{days} days", exact=False).first
        if btn.is_visible():
            btn.click()
            logger.info(f"Clicked pre-configured option for {days} days")
        else:
            input_locator = self.page.locator("//div[contains(., 'Continuous Absent Days')]//input").first
            input_locator.wait_for(state="visible")
            input_locator.fill(str(days))
            logger.info(f"Filled custom input with {days} days")
        self.page.wait_for_timeout(300)

    def set_minimum_communication_attempts(self, attempts: int):
        logger.info(f"Setting minimum communication attempts to: {attempts}")
        input_locator = self.page.locator("//div[contains(., 'Attempts')]//input").first
        input_locator.wait_for(state="visible")
        input_locator.fill(str(attempts))
        self.page.wait_for_timeout(300)

    def set_reminder_frequency(self, freq_text: str):
        logger.info(f"Setting reminder frequency to button: '{freq_text}'")
        btn = self.page.get_by_text(freq_text, exact=False).first
        btn.wait_for(state="visible")
        btn.click()
        self.page.wait_for_timeout(300)

    def set_toggle_switch(self, label_text: str, enable: bool):
        logger.info(f"Setting switch '{label_text}' to state: {enable}")
        input_locator = self.page.locator(f"//*[normalize-space()='{label_text}']/ancestor::div[1]//input[@type='checkbox']")
        input_locator.wait_for(state="attached")
        is_checked = input_locator.is_checked()
        
        if is_checked != enable:
            track_locator = self.page.locator(f"//*[normalize-space()='{label_text}']/ancestor::div[1]//span[contains(@class,'chakra-switch__track')]").first
            track_locator.click()
            logger.info(f"Switch '{label_text}' toggled to {enable}")
        else:
            logger.info(f"Switch '{label_text}' is already in state: {enable}")
        self.page.wait_for_timeout(300)

    def save_settings(self) -> str | None:
        logger.info("Saving settings")
        self.page.locator(self.SAVE_SETTINGS_BTN).click()
        self.page.wait_for_load_state("load")
        try:
            toast = self.page.locator(self.TOAST)
            toast.wait_for(state="visible", timeout=3000)
            msg = toast.inner_text().strip()
            logger.info(f"Toast message on save: '{msg}'")
            return msg
        except Exception:
            logger.warning("No toast dialog appeared after save settings")
            return None

    def is_branch_override_label_visible(self) -> bool:
        loc = self.page.locator(self.BRANCH_OVERRIDE_LABEL)
        return loc.is_visible()
