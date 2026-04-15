from pages.base_page import BasePage


class IncrementPage(BasePage):
    # Locators
    INCREMENT_MODULE = "text=Increment"
    CYCLE_YEAR_DROPDOWN = "[data-testid='cycle-year']"
    DEPARTMENT_DROPDOWN = "[data-testid='department']"
    SUBMIT_BTN = "button:has-text('Submit')"
    SUCCESS_TOAST = "text=Saved Successfully"

    def navigate_to_increment(self):
        self.click(self.INCREMENT_MODULE)

    def select_cycle_year(self, year: str):
        self.page.locator(self.CYCLE_YEAR_DROPDOWN).select_option(year)

    def select_department(self, department: str):
        self.page.locator(self.DEPARTMENT_DROPDOWN).select_option(department)

    def submit(self):
        self.click(self.SUBMIT_BTN)

    def is_success_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_TOAST)
