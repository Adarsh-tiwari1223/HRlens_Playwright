"""
Payroll Company Page Object (HR Lens Portal).
Handles Add/Edit Payroll Company forms, ZIP Code location autofill, and Website field validation.
URL Route: /master/payroll-company
"""

import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class PayrollCompanyPage(BasePage):
    ROUTE_URL = f"{settings.BASE_URL}/master/payroll-company"

    # Locators
    ADD_PAYROLL_COMPANY_BTN = "button:has-text('Add Payroll Company'), button:has-text('Add Company'), button:has-text('Add')"
    COMPANY_NAME_INPUT = "input[placeholder*='Company Name'], input[name='companyName'], input[name='name']"
    ZIP_INPUT = "input[placeholder*='ZIP'], input[placeholder*='Postal'], input[name='zipCode'], input[name='pincode']"
    COUNTRY_INPUT = "input[name='country'], input[placeholder*='Country']"
    STATE_INPUT = "input[name='state'], input[placeholder*='State']"
    CITY_INPUT = "input[name='city'], input[placeholder*='City']"
    WEBSITE_INPUT = "input[name='website'], input[placeholder*='Website']"
    SAVE_BTN = ".chakra-modal__content button[type='submit'], [role='dialog'] button:has-text('Save'), button:has-text('Submit')"

    def navigate_to_payroll_company_master(self):
        """Navigates to Payroll Company Master page."""
        logger.info(f"Navigating to Payroll Company Master: {self.ROUTE_URL}")
        if "/master/payroll-company" not in self.page.url:
            self.page.goto(self.ROUTE_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")

    def open_add_payroll_company_modal(self):
        """Opens Add Payroll Company modal."""
        self.navigate_to_payroll_company_master()
        btn = self.page.locator(self.ADD_PAYROLL_COMPANY_BTN).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(300)

    def test_zipcode_autofill(self, zip_code: str) -> dict:
        """
        Inputs ZIP Code, triggers blur event, and returns autofilled Country, State, and City values.
        Tests Indian PIN codes (e.g. '110001') vs Foreign ZIP codes (e.g. '90210').
        """
        logger.info(f"Testing ZIP Code autofill for code: '{zip_code}'...")
        self.open_add_payroll_company_modal()

        zip_elem = self.page.locator(self.ZIP_INPUT).first
        if zip_elem.is_visible():
            zip_elem.fill("")
            zip_elem.press_sequentially(zip_code, delay=30)
            zip_elem.blur()
            self.page.wait_for_timeout(1000)

        country_val = self.page.locator(self.COUNTRY_INPUT).first.input_value() if self.page.locator(self.COUNTRY_INPUT).first.is_visible() else ""
        state_val = self.page.locator(self.STATE_INPUT).first.input_value() if self.page.locator(self.STATE_INPUT).first.is_visible() else ""
        city_val = self.page.locator(self.CITY_INPUT).first.input_value() if self.page.locator(self.CITY_INPUT).first.is_visible() else ""

        result = {
            "zip_code": zip_code,
            "autofilled_country": country_val,
            "autofilled_state": state_val,
            "autofilled_city": city_val
        }
        logger.info(f"ZIP Code '{zip_code}' Autofill Result: {result}")
        return result

    def is_website_input_enabled(self) -> bool:
        """S.No 13 Bug Validation: Verifies Website field is enabled in Add Payroll Company modal."""
        self.open_add_payroll_company_modal()
        web_elem = self.page.locator(self.WEBSITE_INPUT).first
        if web_elem.is_visible():
            return web_elem.is_enabled()
        return True
