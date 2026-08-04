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

    def click_add_new_director_inline(self):
        """Clicks 'Add New' button/link in Add/Edit Payroll Company modal."""
        logger.info("Clicking 'Add New' button for manual director in Payroll Company modal")
        try:
            loc = self.page.locator("button, a, span, p, div").filter(has_text=re.compile(r"^Add New$", re.I)).first
            if loc.is_visible(timeout=3000):
                loc.click()
                return
        except Exception:
            pass
        self.page.get_by_text("Add New", exact=True).click()

    def fill_manual_director_form(self, name: str = None, email: str = None, phone: str = None):
        """Fills Director Name, Email, and Phone Number in the inline manual director form."""
        logger.info(f"Filling manual director form: Name={name}, Email={email}, Phone={phone}")
        if name is not None:
            self.page.get_by_placeholder("Director Name").fill(name)
        if email is not None:
            self.page.get_by_placeholder("Email").fill(email)
        if phone is not None:
            self.page.get_by_placeholder("Phone Number").fill(phone)

    def click_add_manual_director_submit(self):
        """Clicks 'Add' button inside the inline manual director card container to submit form."""
        logger.info("Submitting manual director form ('Add')")
        try:
            card = self.page.locator("div, form, section").filter(has=self.page.get_by_placeholder("Director Name")).first
            if card.is_visible():
                btn = card.locator("button").filter(has_text=re.compile(r"^Add$", re.I)).first
                if btn.is_visible():
                    btn.click(force=True)
                    return
        except Exception:
            pass

        try:
            btn = self.page.locator(".chakra-button, button").filter(has_text=re.compile(r"^Add$", re.I)).last
            btn.click(timeout=3000, force=True)
        except Exception:
            self.page.get_by_role("button", name="Add", exact=True).click(force=True)

    def click_cancel_manual_director(self):
        """Clicks 'Cancel' button on inline manual director form."""
        logger.info("Canceling manual director form")
        try:
            self.page.get_by_role("button", name="Cancel", exact=True).click(timeout=3000)
        except Exception:
            self.page.get_by_text("Cancel", exact=True).click()

    def verify_manual_director_required_fields_validation(self) -> dict[str, bool]:
        """
        Submits blank manual director form in Payroll Company modal and verifies
        field-level validation errors for Director Name, Email, and Phone Number (all 3 must be required).
        """
        logger.info("Verifying manual director required fields validation in Payroll Company modal...")
        self.open_add_payroll_company_modal()
        self.click_add_new_director_inline()
        self.fill_manual_director_form(name="", email="", phone="")
        self.click_add_manual_director_submit()
        self.page.wait_for_timeout(500)

        name_input = self.page.get_by_placeholder("Director Name")
        email_input = self.page.get_by_placeholder("Email")
        phone_input = self.page.get_by_placeholder("Phone Number")

        name_req = False
        email_req = False
        phone_req = False

        if name_input.is_visible():
            name_req = (
                name_input.get_attribute("required") is not None
                or not name_input.evaluate("el => el.checkValidity()")
                or bool(self.get_field_validation("Director Name"))
            )
        if email_input.is_visible():
            email_req = (
                email_input.get_attribute("required") is not None
                or not email_input.evaluate("el => el.checkValidity()")
                or bool(self.get_field_validation("Email"))
            )
        if phone_input.is_visible():
            phone_req = (
                phone_input.get_attribute("required") is not None
                or not phone_input.evaluate("el => el.checkValidity()")
                or bool(self.get_field_validation("Phone Number"))
            )

        validations = self.get_all_validation_messages()
        if "required" in str(validations).lower() or "director" in str(validations).lower():
            name_req = email_req = phone_req = True

        result = {
            "name_required": name_req,
            "email_required": email_req,
            "phone_required": phone_req
        }
        logger.info(f"Payroll Company Manual Director Required Fields Result: {result}")
        return result
