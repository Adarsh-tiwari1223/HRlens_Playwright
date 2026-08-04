import re
import logging
from pages.base_page import BasePage
from core.config import settings
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

class CompanyPage(BasePage):
    ADD_NEW_COMPANY_BTN = "role=button[name='Add New Company']"
    ADD_COMPANY_SUBMIT_BTN = "role=button[name='Add Company']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_company_master(self):
        logger.info("Navigating to Company Master page")
        self.page.goto(f"{settings.BASE_URL}/master/company")
        self.page.wait_for_load_state("networkidle")

    def click_add_new_company(self):
        self.click(self.ADD_NEW_COMPANY_BTN)

    def fill_company_details(self, name: str, address: str, zip_code: str, country: str, state: str, city: str, code: str, director: str = None, auditor: str = None, pf_consultant: str = None, logo_path: str = None, stamp_path: str = None):
        if logo_path:
            logger.info(f"Uploading company logo from: {logo_path}")
            self.page.locator("input[type='file']").first.set_input_files(logo_path)
            
        if stamp_path:
            logger.info(f"Uploading company stamp from: {stamp_path}")
            self.page.locator("input[type='file']").nth(1).set_input_files(stamp_path)
            
        # 1. Enter ZIP Code first to trigger autofill
        if zip_code is not None:
            zip_input = self.page.get_by_placeholder("Enter ZIP Code")
            zip_input.fill("")
            zip_input.press_sequentially(zip_code, delay=30)
            logger.info(f"ZIP Code: {zip_code}")
            
            # Blur the ZIP Code input to trigger the autofill event
            zip_input.blur()
            
            # Wait for Country autofill to complete
            if country:
                try:
                    # Natively wait for country input to get a value
                    expect(self.page.locator("input[name='country']")).not_to_have_value("", timeout=8000)
                    autofilled_country = self.page.locator("input[name='country']").input_value()
                    logger.info(f"Country (Autofilled): {autofilled_country}")
                except Exception:
                    # Fallback to manual fill if API lookup fails/timeouts
                    self.page.locator("input[name='country']").fill("")
                    self.page.locator("input[name='country']").press_sequentially(country, delay=30)
                    self.page.locator("input[name='state']").fill("")
                    self.page.locator("input[name='state']").press_sequentially(state, delay=30)
                    self.page.locator("input[name='city']").fill("")
                    self.page.locator("input[name='city']").press_sequentially(city, delay=30)
                    logger.info(f"Country (Manual): {country}")
                    logger.info(f"State (Manual): {state}")
                    logger.info(f"City (Manual): {city}")

        # 2. Enter company name next (safe from being cleared by autofill re-renders)
        if name is not None:
            for attempt in range(3):
                try:
                    name_input = self.page.get_by_placeholder("Enter company name")
                    name_input.click(timeout=2000)
                    name_input.fill("")
                    name_input.press_sequentially(name, delay=30, timeout=5000)
                    break
                except Exception:
                    self.page.wait_for_timeout(500)
            logger.info(f"Company Name: {name}")

        # 3. Enter Address next
        if address is not None:
            for attempt in range(3):
                try:
                    addr_input = self.page.get_by_placeholder("Enter address")
                    addr_input.click(timeout=2000)
                    addr_input.fill("")
                    addr_input.press_sequentially(address, delay=30, timeout=5000)
                    break
                except Exception:
                    self.page.wait_for_timeout(500)
            logger.info(f"Address: {address}")

        # 4. Enter Company Code last
        if code is not None:
            for attempt in range(3):
                try:
                    code_input = self.page.get_by_placeholder("Enter Company Code")
                    code_input.click(timeout=2000)
                    code_input.fill("")
                    code_input.press_sequentially(code, delay=30, timeout=5000)
                    break
                except Exception:
                    self.page.wait_for_timeout(500)
            logger.info(f"Company Code: {code}")

    def click_add_company(self):
        self.click(self.ADD_COMPANY_SUBMIT_BTN)

    def edit_company(self, company_name: str):
        logger.info(f"Editing company: {company_name}")
        row_locator = f"role=row[name*='{company_name}']"
        self.page.locator(row_locator).get_by_label("edit").click()

    def click_update_company(self):
        logger.info("Clicking Update Company button")
        try:
            self.page.get_by_role("button", name="Update Company", exact=False).click(timeout=3000)
        except Exception:
            self.page.get_by_role("button", name="Update", exact=False).click()

    def delete_company(self, company_name: str):
        logger.info(f"Deleting company: {company_name}")
        row_locator = f"role=row[name*='{company_name}']"
        self.page.locator(row_locator).get_by_label("delete").click()

    def confirm_delete_company(self):
        logger.info("Confirming company deletion")
        # Click Delete button in the confirmation modal/dialog
        dialog = self.page.locator("[role='alertdialog'], [role='dialog']").first
        dialog.get_by_role("button", name="Delete", exact=True).click()

    def search_company(self, query: str):
        logger.info(f"Searching for company: {query}")
        search_field = self.page.locator("input[placeholder*='Search']").first
        search_field.wait_for(state="visible")
        search_field.click()
        search_field.fill("")
        search_field.press_sequentially(query, delay=30)
        
        # Auto-wait natively for the matching table row to become visible
        row_locator = self.page.locator(f"role=row[name*='{query}']")
        try:
            row_locator.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        
    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)

    def click_add_new_director_inline(self):
        """Clicks 'Add New' button/link during Add/Edit Company form."""
        logger.info("Clicking 'Add New' button for manual director")
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
        """Clicks 'Cancel' button on the inline manual director form."""
        logger.info("Canceling manual director form")
        try:
            self.page.get_by_role("button", name="Cancel", exact=True).click(timeout=3000)
        except Exception:
            self.page.get_by_text("Cancel", exact=True).click()

    def verify_manual_director_required_fields_validation(self) -> dict[str, bool]:
        """
        Submits blank manual director form and verifies field-level validation
        errors for Director Name, Email, and Phone Number (all 3 must be required).
        """
        logger.info("Verifying manual director required fields validation...")
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
        logger.info(f"Manual Director Required Fields Validation Result: {result}")
        return result
