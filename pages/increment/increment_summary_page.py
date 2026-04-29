from pages.base_page import BasePage


class IncrementSummaryPage(BasePage):

    ASSESSMENT_GRID = ".grid_container.css-1wgptd8 > .css-rklm6r"
    LOADING = "div:has-text('Loading...')"

    def select_tl(self, tl_name: str):
        self.click(f"text={tl_name}")

    def select_employee(self, emp_name: str):
        self.click(f"text={emp_name}")

    def wait_for_grid(self):
        self.page.locator(self.LOADING).wait_for(state="hidden")
        self.wait_for_visible(self.ASSESSMENT_GRID)

    def open_assessment_form(self):
        self.wait_for_grid()
        self.click(self.ASSESSMENT_GRID)
