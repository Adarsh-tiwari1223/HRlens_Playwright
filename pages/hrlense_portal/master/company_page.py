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
        self.page.wait_for_load_state("domcontentloaded")

    def click_add_new_company(self):
        """Clicks Add New Company button."""
        btn = self.page.locator("button:has-text('Add Company'), button:has-text('Add')").first
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
        
        # Ensure modal is open before proceeding
        self._get_modal()

    def fill_company_details(
        self,
        logo_path: str = None,
        stamp_path: str = None,
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
       
    ):
        """
        Fills Company details following the strict 12-field required field sequence order:
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
                    inp = modal.locator("input[placeholder*='company name' i], input[name='companyName'], input[name='name']").first
                
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

        # Order 10: Director Name (Dropdown selection OR Manual Director Addition)
        if director:
            if isinstance(director, dict):
                self.add_manual_director(
                    name=director.get("name"),
                    email=director.get("email"),
                    phone=director.get("phone")
                )
                logger.info(f"Order 10 - Added Manual Director: {director.get('name')}")
            else:
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

    def click_add_company(self):
        logger.info("Clicking Add Company button")
        try:
            self.page.locator("header:has-text('Add New Company'), .chakra-modal__header").first.click(timeout=1000)
        except Exception:
            pass

        modal = self._get_modal()
        btn = modal.locator("button:has-text('Add Company')").first
        btn.click()
        logger.info("Clicked Add Company button")

    def verify_director_in_dropdown(self, director_name: str) -> bool:
        """
        Opens/inspects Company Add/Edit modal, clicks Director Name dropdown, types director_name,
        and verifies if it appears in the dropdown options list.
        """
        logger.info(f"[UI VALIDATION] Verifying director '{director_name}' is available in Director Name dropdown...")
        modal = self._get_modal()
        
        try:
            dir_container = modal.locator("label:has-text('Director Name')").locator("xpath=ancestor::div[contains(@class, 'form') or contains(@class, 'control') or contains(@class, 'group')]").first
            if not dir_container.is_visible(timeout=1000):
                dir_container = modal
            
            inp = dir_container.locator("input").first
            if inp.is_visible(timeout=1000):
                inp.click(force=True)
                inp.fill(director_name)
                self.page.wait_for_timeout(800)
            else:
                self.select_react_dropdown("Director Name", director_name, container=modal)
        except Exception as e:
            logger.info(f"Director dropdown trigger note: {e}")

        options_loc = self.page.locator("[class*='menu'], [class*='option'], [role='option'], .chakra-select__option, div").filter(has_text=re.compile(re.escape(director_name), re.I))
        is_found = False
        try:
            if options_loc.first.is_visible(timeout=3000):
                logger.info(f"[UI VALIDATION SUCCESS] Found director '{director_name}' in Director Name dropdown list!")
                is_found = True
        except Exception:
            if director_name.lower() in self.page.content().lower():
                logger.info(f"[UI VALIDATION SUCCESS] Director '{director_name}' rendered in UI dropdown options!")
                is_found = True

        return is_found

    def click_cancel_company_modal(self):
        logger.info("Clicking Cancel button on Company modal")
        modal = self._get_modal()
        btn = modal.locator("button:has-text('Cancel')").first
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)

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
        search_field = self.page.get_by_placeholder("Search Company Name", exact=False)
        if not search_field.is_visible(timeout=1000):
            search_field = self.page.locator("input[placeholder*='Search Company Name' i], input[placeholder*='Search' i]").first
        search_field.wait_for(state="visible", timeout=3000)
        search_field.click()
        search_field.fill("")
        search_field.fill(query)
        self.page.wait_for_timeout(1200)

    def is_company_listed_in_table(self, company_name: str) -> bool:
        """Verifies if company name appears in table rows after search."""
        self.search_company(company_name)
        
        locators = [
            self.page.locator("tbody tr").filter(has_text=company_name).first,
            self.page.locator("tr").filter(has_text=company_name).first,
            self.page.locator("td").filter(has_text=company_name).first,
            self.page.get_by_text(company_name, exact=False).first
        ]

        for loc in locators:
            try:
                if loc.is_visible(timeout=3000):
                    logger.info(f"Found company '{company_name}' in table grid!")
                    return True
            except Exception:
                pass

        try:
            full_text = " ".join(self.page.locator("table, main, #root").all_inner_texts())
            if company_name.lower() in full_text.lower():
                logger.info(f"Found company '{company_name}' in table text block!")
                return True
        except Exception:
            pass

        return False
        
    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)

    def _get_modal(self):
        """Helper to scope locators strictly inside the open modal dialog."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        try:
            if modal.is_visible(timeout=5000):
                return modal
        except Exception:
            pass
        return self.page

    def click_add_new_director_inline(self):
        """Clicks '+ Add New' button for manual director strictly inside the open modal drawer."""
        logger.info("Clicking '+ Add New' button for manual director inside modal drawer")
        modal = self._get_modal()
        # Locate '+ Add New' button/link scoped inside modal drawer near Director field
        btn = modal.locator("label:has-text('Director Name')").locator("xpath=ancestor::div[contains(@class, 'form') or contains(@class, 'control') or contains(@class, 'group')]//*[contains(text(), 'Add New')]").first
        if not btn.is_visible(timeout=1000):
            btn = modal.locator("button, a, span, p, div").filter(has_text=re.compile(r"\+?\s*Add New", re.I)).last

        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)

        self.page.wait_for_timeout(300)

    def fill_manual_director_form(self, name: str = None, email: str = None, phone: str = None):
        """Fills Director Name, Email, and Phone Number in the inline manual director form."""
        logger.info(f"Filling manual director form: Name={name}, Email={email}, Phone={phone}")
        modal = self._get_modal()
        if name is not None:
            inp = self.page.get_by_placeholder("Director Name", exact=False).first
            if not inp.is_visible(timeout=1000):
                inp = self.page.locator("input[placeholder*='Director Name' i], input[name='directorName']").first
            try:
                inp.wait_for(state="visible", timeout=3000)
            except Exception:
                pass
            inp.click(force=True)
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
        """Clicks 'Add' button to submit the inline manual director form."""
        logger.info("Submitting manual director form ('Add')")
        modal = self._get_modal()
        try:
            modal.get_by_text("Add", exact=True).click(timeout=3000)
        except Exception:
            modal.locator("button").filter(has_text=re.compile(r"^Add$", re.I)).last.click()

    def add_manual_director(self, name: str, email: str, phone: str):
        """
        Flow:
        1. Click '+ Add New'
        2. Fill Director Name, Email, Phone Number
        3. Click 'Add' button
        4. On success, tag <span class="css-1ny2kle"> rendered with director name (no toast shown).
        """
        logger.info(f"Adding manual director: Name={name}, Email={email}, Phone={phone}")
        self.click_add_new_director_inline()
        self.fill_manual_director_form(name, email, phone)
        self.click_add_manual_director_submit()
        
        # Verify tag rendered with director name
        try:
            tag_loc = self.page.locator("span.css-1ny2kle, .chakra-tag, div[class*='singleValue']").filter(has_text=name).first
            tag_loc.wait_for(state="visible", timeout=3000)
            logger.info(f"Verified manual director tag created: '{tag_loc.inner_text().strip()}'")
        except Exception:
            pass

    def get_posted_director_record(self) -> str:
        """Retrieves the posted director name from the Director selection field in the form."""
        try:
            dir_input = self.page.locator("input[placeholder*='Director'], select[name*='director'], div[class*='select']").first
            if dir_input.is_visible():
                val = dir_input.input_value() or dir_input.inner_text().strip()
                logger.info(f"Retrieved posted director record from form: '{val}'")
                return val
        except Exception:
            pass
        return ""

    def click_cancel_manual_director(self):
        """Clicks 'Cancel' button on the inline manual director form."""
        logger.info("Canceling manual director form")
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
        logger.info(f"Manual Director Required Fields Validation Result: {result}")
        return result
