from pages.base_page import BasePage


class IncrementPage(BasePage):

    INCREMENT_LINK = "a:text-is('Increment')"
    COMPANY_DROPDOWN = "select >> nth=0"
    BRANCH_DROPDOWN = "select >> nth=1"
    DEPT_DROPDOWN = "select >> nth=2"
    DATE_RANGE = "input[placeholder='Select Date Range'] >> nth=0"
    ASSESSMENT_STATUS = "div:has-text('Assessments Open')"
    RUN_ASSESSMENT_BTN = "button:has-text('Run Assessment')"

    def go_to_increment(self):
        self.click(self.INCREMENT_LINK)

    def select_company(self, value: str):
        self.page.locator("select").nth(0).select_option(label=value)

    def select_branch(self, value: str):
        self.page.locator("select").nth(1).select_option(label=value)

    def select_department(self, value: str):
        self.page.locator("select").nth(2).select_option(label=value)

    def select_date_range(self, day: str):
        self.click(self.DATE_RANGE)
        self.page.get_by_role("paragraph").filter(has_text=day).first.click()

    def run_assessment(self):
        self.page.locator(self.RUN_ASSESSMENT_BTN).first.click()

    def get_assessment_status(self) -> str:
        return self.get_text(self.ASSESSMENT_STATUS)

    def is_assessment_open(self) -> bool:
        return self.is_visible(self.ASSESSMENT_STATUS)
