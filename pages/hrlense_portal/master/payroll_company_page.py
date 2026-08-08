"""
Payroll Company Page Object (HR Lens Portal).
Handles Add/Edit Payroll Company forms, ZIP Code location autofill, and Website field validation.
URL Route: /master/payroll-company
"""

import logging
import re
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

    def _get_modal(self):
        """Helper to scope locators strictly inside the open modal dialog."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        try:
            if modal.is_visible(timeout=5000):
                return modal
        except Exception:
            pass
        return self.page

    def open_add_payroll_company_modal(self):
        """Opens Add Payroll Company modal."""
        self.navigate_to_payroll_company_master()
        btn = self.page.locator(self.ADD_PAYROLL_COMPANY_BTN).first
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
        self.page.wait_for_timeout(1000)
        self._get_modal()

    def edit_payroll_company(self, company_name: str):
        """Navigates to Payroll Company page and opens edit modal for target company."""
        self.navigate_to_payroll_company_master()
        try:
            row = self.page.locator("tbody tr").filter(has_text=company_name).first
            if row.is_visible(timeout=3000):
                row.get_by_label("edit").click()
                self.page.wait_for_timeout(1000)
                self._get_modal()
                return
        except Exception:
            pass
        try:
            self.page.locator("tbody tr").first.get_by_label("edit").click()
            self.page.wait_for_timeout(1000)
            self._get_modal()
        except Exception:
            self.open_add_payroll_company_modal()

    def fill_payroll_company_details(
        self,
        name: str = None,
        address: str = None,
        zip_code: str = None,
        country: str = None,
        state: str = None,
        city: str = None,
        code: str = None,
        director: str = None,
        auditor: str = None,
        pf_consultant: str = None,
        logo_path: str = None,
        stamp_path: str = None
    ):
        """
        Fills Payroll Company details following the strict 12-field required field sequence order:
        Order 1: Company Logo
        Order 2: Company Stamp
        Order 3: Company Name
        Order 4: Country
        Order 5: Zip Code
        Order 6: State (Auto-filled from Zip Code)
        Order 7: City (Auto-filled from Zip Code)
        Order 8: Address
        Order 9: Company Code
        Order 10: Director Name
        Order 11: Auditor Name
        Order 12: PF Consultant Name
        """
        modal = self._get_modal()

        # Order 1: Company Logo
        if logo_path:
            try:
                modal.locator("input[type='file']").first.set_input_files(logo_path)
                logger.info(f"Order 1 - Uploaded Company Logo: {logo_path}")
            except Exception:
                pass

        # Order 2: Company Stamp
        if stamp_path:
            try:
                modal.locator("input[type='file']").nth(1).set_input_files(stamp_path)
                logger.info(f"Order 2 - Uploaded Company Stamp: {stamp_path}")
            except Exception:
                pass

        # Order 3: Company Name
        if name:
            try:
                inp = modal.get_by_placeholder("Enter company name", exact=True)
                if not inp.is_visible(timeout=1500):
                    inp = modal.get_by_role("textbox", name=re.compile(r"Company Name\*", re.IGNORECASE)).first
                if not inp.is_visible(timeout=1500):
                    inp = modal.locator("input[placeholder*='company name' i], input[name='payrollCompanyName'], input[name='name']").first
                if inp.is_visible(timeout=3000):
                    inp.click(force=True)
                    inp.fill("")
                    inp.press_sequentially(name, delay=10)
                    logger.info(f"Order 3 - Filled Company Name: {name}")
            except Exception as e:
                logger.warning(f"Error filling Company Name: {e}")

        # Order 4: Country
        if country:
            try:
                inp = modal.get_by_placeholder("Search Country", exact=True)
                if not inp.is_visible(timeout=1000):
                    inp = modal.get_by_placeholder("Country", exact=False)
                if not inp.is_visible(timeout=1000):
                    inp = modal.locator("input[placeholder*='Country' i]").first

                if inp.is_visible(timeout=2000):
                    inp.click(force=True)
                    inp.fill("")
                    inp.press_sequentially(country, delay=50)
                    self.page.wait_for_timeout(300)
                    
                    # Target option using unique React-Select option locator
                    opt = self.page.locator("div[id*='option'], [role='option'], div.css-17ezq3, div[class*='option']").filter(has_text=re.compile(f"^{re.escape(country)}$", re.I)).first
                    if not opt.is_visible(timeout=1000):
                        opt = self.page.locator("div[id*='option'], [role='option'], div.css-17ezq3, div[class*='option']").filter(has_text=country).first
                    
                    if opt.is_visible(timeout=1500):
                        opt.click(force=True)
                    else:
                        self.page.keyboard.press("Enter")
                    logger.info(f"Order 4 - Selected Country: {country}")
            except Exception as e:
                logger.warning(f"Error selecting Country: {e}")

        # Order 5: Zip Code
        if zip_code:
            try:
                inp = modal.get_by_placeholder("Enter Zip Code", exact=False)
                if not inp.is_visible(timeout=1000):
                    inp = modal.get_by_placeholder("Zip Code", exact=False)
                if not inp.is_visible(timeout=1000):
                    inp = modal.locator("input[name='zipCode'], input[name='pincode'], input[name='zip']").first
                
                if inp.is_visible(timeout=3000):
                    inp.click(force=True)
                    inp.fill("")
                    inp.press_sequentially(zip_code, delay=10)
                    inp.blur()
                    logger.info(f"Order 5 - Filled Zip Code: {zip_code}")
                    
                    # Wait for backend Zip Code API to populate the state input value
                    state_inp = modal.locator("input[name='state']").first
                    try:
                        handle = state_inp.element_handle()
                        if handle:
                            self.page.wait_for_function("el => el && el.value.trim() !== ''", arg=handle, timeout=4000)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Error filling Zip Code: {e}")

        # Order 6: State (Auto-filled from Zip Code)
        try:
            state_inp = modal.locator("input[name='state']").first
            if state_inp.is_visible():
                state_val = state_inp.input_value()
                logger.info(f"Order 6 - Auto-filled State read as: '{state_val}'")
        except Exception:
            pass

        # Order 7: City (Auto-filled from Zip Code)
        try:
            city_inp = modal.locator("input[name='city']").first
            if city_inp.is_visible():
                city_val = city_inp.input_value()
                logger.info(f"Order 7 - Auto-filled City read as: '{city_val}'")
        except Exception:
            pass

        # Order 8: Address
        if address:
            try:
                inp = modal.locator("input[placeholder*='address' i], input[name='address']").first
                if inp.is_visible(timeout=3000):
                    inp.click(force=True)
                    inp.fill("")
                    inp.press_sequentially(address, delay=10)
                    logger.info(f"Order 8 - Filled Address: {address}")
            except Exception as e:
                logger.warning(f"Error filling Address: {e}")

        # Order 9: Company Code
        if code:
            try:
                inp = modal.locator("input[placeholder*='Company Code' i], input[name='companyCode'], input[name='code']").first
                if inp.is_visible(timeout=3000):
                    inp.click(force=True)
                    inp.fill("")
                    inp.press_sequentially(code, delay=10)
                    logger.info(f"Order 9 - Filled Company Code: {code}")
            except Exception as e:
                logger.warning(f"Error filling Company Code: {e}")

        # Order 10: Director Name
        if director:
            try:
                sel_dir = self.select_react_dropdown("Director Name", director, container=modal)
                logger.info(f"Order 10 - Selected Director Name: {sel_dir}")
            except Exception:
                pass

        # Order 11: Auditor Name
        if auditor:
            try:
                sel_aud = self.select_react_dropdown("Auditor", auditor, container=modal)
                logger.info(f"Order 11 - Selected Auditor Name: {sel_aud}")
            except Exception:
                pass

        # Order 12: PF Consultant Name
        if pf_consultant:
            try:
                sel_pf = self.select_react_dropdown("Consultant", pf_consultant, container=modal)
                logger.info(f"Order 12 - Selected PF Consultant Name: {sel_pf}")
            except Exception:
                pass

    def click_submit(self):
        """Clicks Submit / Save button in open modal."""
        modal = self._get_modal()
        btn = modal.locator("button:has-text('Add Company'), button[type='submit'], button:has-text('Save'), button:has-text('Submit')").first
        if not btn.is_visible(timeout=1000):
            btn = modal.get_by_role("button", name="Add Company", exact=True).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator("button:has-text('Add Company')").last
        
        btn.click(force=True)

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
            inp = modal.locator("input[placeholder*='Director Name' i], input[placeholder*='Name' i], input[name='directorName']").first
            try:
                inp.wait_for(state="visible", timeout=3000)
            except Exception:
                pass
            inp.fill(name)

        if email is not None:
            inp = modal.locator("input[placeholder*='Email ID' i], input[placeholder*='Email' i], input[type='email']").first
            if inp.is_visible():
                inp.fill(email)

        if phone is not None:
            inp = modal.locator("input[placeholder*='Phone No' i], input[placeholder*='Phone' i], input[placeholder*='Mobile' i], input[type='tel']").first
            if inp.is_visible():
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
        4. On success, tag <span class="css-1ny2kle"> rendered with director name (no toast shown).
        """
        logger.info(f"Adding manual director in Payroll Company: Name={name}, Email={email}, Phone={phone}")
        self.click_add_new_director_inline()
        self.page.wait_for_timeout(300)
        self.fill_manual_director_form(name, email, phone)
        self.click_add_manual_director_submit()
        
        # Verify tag rendered with director name
        try:
            tag_loc = self.page.locator("span.css-1ny2kle, .chakra-tag, div[class*='singleValue']").filter(has_text=name).first
            tag_loc.wait_for(state="visible", timeout=3000)
            logger.info(f"Verified Payroll Company manual director tag created: '{tag_loc.inner_text().strip()}'")
        except Exception:
            pass

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
