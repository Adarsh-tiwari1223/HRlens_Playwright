from pages.base_page import BasePage
import logging

logger = logging.getLogger(__name__)

class IncrementSummaryPage(BasePage):
    """
    Stub class for IncrementSummaryPage to resolve import errors during test collection.
    Real implementation should locate and perform actions on the increment summary page elements.
    """
    GRID_SELECTOR = ".increment-summary-grid, table"
    TL_SELECTOR = "select[name='tl'], [data-testid='tl-select']"
    EMPLOYEE_SELECTOR = "select[name='employee'], [data-testid='employee-select']"
    ASSESSMENT_FORM_BTN = "button:has-text('Assessment Form'), [data-testid='assessment-form-btn']"

    def wait_for_grid(self):
        logger.info("Waiting for increment summary grid to be visible...")
        self.page.locator(self.GRID_SELECTOR).first.wait_for(state="visible", timeout=10000)

    def select_tl(self, name: str):
        logger.info(f"Selecting TL: {name}")
        self.page.locator(self.TL_SELECTOR).select_option(label=name)

    def select_employee(self, name: str):
        logger.info(f"Selecting Employee: {name}")
        self.page.locator(self.EMPLOYEE_SELECTOR).select_option(label=name)

    def open_assessment_form(self):
        logger.info("Opening assessment form...")
        self.click(self.ASSESSMENT_FORM_BTN)
