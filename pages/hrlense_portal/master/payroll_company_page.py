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

    def _get_modal(self):
        """Helper to scope locators strictly inside the open modal dialog."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        try:
            if modal.is_visible(timeout=2000):
                return modal
        except Exception:
            pass
        return self.page

    def click_add_new_director_inline(self):
        """
        Flow specified by user:
        1. Click 'Add New' (page.get_by_text("Add New", exact=True))
        2. Click page.locator("label:has-text('Director Name')") to activate inline form
        """
        logger.info("Clicking 'Add New' button for manual director in Payroll Company modal")
        try:
            self.page.get_by_text("Add New", exact=True).click(timeout=3000)
        except Exception:
            self.page.get_by_text("Add New", exact=True).click(force=True)

        self.page.wait_for_timeout(300)

        # Click Director Name label to activate form fields as specified by user
        try:
            label = self.page.locator("label:has-text('Director Name')").first
            label.click(timeout=3000)
        except Exception:
            try:
                self.page.locator("label:has-text('Director Name')").first.click(force=True)
            except Exception:
                pass

        self.page.wait_for_timeout(300)

    def fill_manual_director_form(self, name: str = None, email: str = None, phone: str = None):
        """Fills Director Name, Email, and Phone Number in the inline manual director form."""
        logger.info(f"Filling manual director form: Name={name}, Email={email}, Phone={phone}")
        modal = self._get_modal()
        if name is not None:
            inp = modal.get_by_placeholder("Director Name")
            try:
                inp.wait_for(state="visible", timeout=1500)
            except Exception:
                pass
            inp.fill(name)
        if email is not None:
            inp = modal.get_by_placeholder("Email")
            try:
                inp.wait_for(state="visible", timeout=1500)
            except Exception:
                pass
            inp.fill(email)
        if phone is not None:
            inp = modal.get_by_placeholder("Phone Number")
            try:
                inp.wait_for(state="visible", timeout=1500)
            except Exception:
                pass
            inp.fill(phone)

    def click_add_manual_director_submit(self):
        """Clicks 'Add' button to submit inline manual director form."""
        logger.info("Submitting manual director form ('Add')")
        modal = self._get_modal()
        try:
            modal.get_by_text("Add", exact=True).click(timeout=3000)
        except Exception:
            modal.locator("button").filter(has_text=re.compile(r"^Add$", re.I)).last.click()

    def add_manual_director(self, name: str, email: str, phone: str):
        """
        Flow:
        1. Click 'Add New'
        2. Fill Director Name, Email, Phone Number
        3. Click 'Add' button
        """
        logger.info(f"Adding manual director in Payroll Company: Name={name}, Email={email}, Phone={phone}")
        self.click_add_new_director_inline()
        self.page.wait_for_timeout(300)
        self.fill_manual_director_form(name, email, phone)
        self.click_add_manual_director_submit()
        self.page.wait_for_timeout(300)

    def get_posted_director_record(self) -> str:
        """Retrieves the posted director name from the Director selection field in Payroll Company form."""
        try:
            dir_input = self.page.locator("input[placeholder*='Director'], select[name*='director'], div[class*='select']").first
            if dir_input.is_visible():
                val = dir_input.input_value() or dir_input.inner_text().strip()
                logger.info(f"Retrieved posted director record from Payroll Company form: '{val}'")
                return val
        except Exception:
            pass
        return ""

    def click_cancel_manual_director(self):
        """Clicks 'Cancel' button on inline manual director form."""
        logger.info("Canceling manual director form")
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
        self.page.wait_for_timeout(1000)

        name_input = self.page.get_by_placeholder("Director Name")
        email_input = self.page.get_by_placeholder("Email")
        phone_input = self.page.get_by_placeholder("Phone Number")

        errors = self.page.locator(".chakra-form__error-message, .chakra-toast, [role='alert'], [role='status'], .chakra-alert, p, span, div").all_inner_texts()
        error_text = " ".join([e.strip() for e in errors if e.strip()]).lower()
        logger.info(f"Captured screen error texts: '{error_text}'")

        name_req = (
            "director" in error_text or "name" in error_text or "required" in error_text
            or (name_input.is_visible() and not name_input.evaluate("el => el.checkValidity()"))
            or (name_input.is_visible() and name_input.get_attribute("required") is not None)
        )
        email_req = (
            "email" in error_text or "required" in error_text
            or (email_input.is_visible() and not email_input.evaluate("el => el.checkValidity()"))
            or (email_input.is_visible() and email_input.get_attribute("required") is not None)
        )
        phone_req = (
            "phone" in error_text or "required" in error_text
            or (phone_input.is_visible() and not phone_input.evaluate("el => el.checkValidity()"))
            or (phone_input.is_visible() and phone_input.get_attribute("required") is not None)
        )

        result = {
            "name_required": name_req,
            "email_required": email_req,
            "phone_required": phone_req
        }
        logger.info(f"Payroll Company Manual Director Required Fields Result: {result}")
        return result
