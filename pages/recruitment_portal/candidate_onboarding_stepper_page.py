import os
import logging
from typing import Optional
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CandidateOnboardingStepperPage(BasePage):
    """
    Page Object for the 5-Stepper Candidate Onboarding Wizard.
    Step 1: Basic Details
    Step 2: (To be defined)
    Step 3: (To be defined)
    Step 4: (To be defined)
    Step 5: (To be defined)
    """

    def __init__(self, page: Page):
        super().__init__(page)
        # Stepper Header Indicators
        self.step_indicator = self.page.locator("p.step_text, p:has-text('Step')")
        self.form_title = self.page.locator("p.form_title")

        # Step 1: Basic Details Locators
        self.input_full_name = self.page.locator("input[name='fullName']")
        self.input_dob = self.page.locator("input[name='dob']")
        self.input_email = self.page.locator("input[name='email']")
        self.input_phone = self.page.locator("input[name='phone']")

        # Current Address
        self.input_current_zipcode = self.page.locator("input[name='current_Zipcode']")
        self.input_current_country = self.page.locator("input[name='current_Country']")
        self.input_current_state = self.page.locator("input[name='current_State']")
        self.input_current_city = self.page.locator("input[name='current_City']")
        self.input_current_address = self.page.locator("input[name='current_Address']")

        # Permanent Address
        self.same_as_current_checkbox = self.page.locator("label:has-text('Same as Current'), .chakra-checkbox:has-text('Same as Current')")
        self.input_permanent_zipcode = self.page.locator("input[name='permanent_Zipcode']")
        self.input_permanent_country = self.page.locator("input[name='permanent_Country']")
        self.input_permanent_state = self.page.locator("input[name='permanent_State']")
        self.input_permanent_city = self.page.locator("input[name='permanent_City']")
        self.input_permanent_address = self.page.locator("input[name='permanent_Address']")

        # Personal / Demographic Details
        self.select_gender = self.page.locator("select[name='gender']")
        self.select_marital_status = self.page.locator("select[name='marital_Status']")
        self.input_emergency_contact_name = self.page.locator("input[name='emergencyContactName']")
        self.input_emergency_contact_number = self.page.locator("input[name='emergencyContactNumber']")

        # Common Stepper Controls
        self.save_and_next_btn = self.page.locator("button:has-text('Save & Next')")
        self.prev_btn = self.page.locator("button:has-text('Previous')")
        self.add_more_btn = self.page.locator("button:has-text('Add More')")

        # Step 2: Family Details Locators
        self.select_family_relation = self.page.locator("select[name*='relation'], select[name='familyDetails.0.relation']")
        self.select_family_gender = self.page.locator("select[name*='familyDetails'][name*='gender'], select[name='familyDetails.0.gender']")
        self.input_family_name = self.page.locator("input[name*='familyDetails'][name*='name'], input[name='familyDetails.0.name']")
        self.input_family_dob = self.page.locator("input[name*='familyDetails'][name*='dob'], input[name='familyDetails.0.dob']")

        # Step 3: Education Details Locators
        self.select_edu_category = self.page.locator("select[name*='education_Category_Id'], select[name='educations.0.education_Category_Id']")
        self.select_edu_degree = self.page.locator("select[name*='education_Degree_Id'], select[name='educations.0.education_Degree_Id']")
        self.input_edu_institute = self.page.locator("input[name*='instituteName'], input[name='educations.0.instituteName']")
        self.input_edu_course = self.page.locator("input[name*='course'], input[name='educations.0.course']")
        self.input_edu_grade = self.page.locator("input[name*='grade'], input[name='educations.0.grade']")
        self.input_edu_passing_year = self.page.locator("input[name*='passingYear'], input[name='educations.0.passingYear']")

        # Step 4: Identity & Bank Details Locators
        self.select_bank_name = self.page.locator("select[name='bank_Name']")
        self.input_branch_name = self.page.locator("input[name='branch_Name']")
        self.input_account_number = self.page.locator("input[name='account_Number']")
        self.input_ifsc_code = self.page.locator("input[name='ifsc_Code']")
        self.input_aadhaar = self.page.locator("input[name='aadhaar']")
        self.input_pan = self.page.locator("input[name='pan']")
        self.input_uan = self.page.locator("input[name='uan']")

        # Step 5: Document Upload Locators
        self.select_doc_type = self.page.locator("select[name*='type'], select[name='documents.0.type']")
        self.select_doc_name = self.page.locator("select[name*='name'], select[name='documents.0.name']")
        self.input_file_upload = self.page.locator("input[type='file'], input#file-upload-0")
        self.save_and_submit_btn = self.page.locator("button:has-text('Save & Submit'), button.btn:has-text('Save & Submit')")

        # Submission Confirmation Modal Locators
        self.submit_modal = self.page.locator("section[role='alertdialog']:has-text('Submit Application')")
        self.btn_confirm_submit = self.page.locator("button:has-text('Yes, Submit')")
        self.btn_cancel_submit = self.page.locator("button:has-text('Cancel')")

        # Success Screen Locators
        self.success_card = self.page.locator(".success_card")
        self.success_title = self.page.locator(".success_card p.title, p:has-text('Thank You !')")
        self.success_subtitle = self.page.locator(".success_card p.subtitle, p:has-text('successfully submitted')")

    def get_current_step_text(self) -> str:
        """Returns the current step text, e.g. 'Step 1/5'."""
        try:
            return self.step_indicator.first.inner_text().strip()
        except Exception:
            return ""

    def fill_step_1_basic_details(self, data: Optional[dict] = None):
        """
        Fills Step 1: Basic Details.
        Pre-filled fields (fullName, email, phone) are preserved if already set.
        """
        payload = data or {}
        logger.info("[ONBOARDING STEP 1] Filling Basic Details...")

        # 1. Full Name (ensure filled)
        if not self.input_full_name.input_value():
            self.input_full_name.fill(payload.get("name", "Kavya Prakash"))

        # 2. Date of Birth (mandatory, YYYY-MM-DD, e.g. 2000-05-15)
        dob = payload.get("dob", "2000-05-15")
        self.input_dob.fill(dob)
        logger.info(f"  • Date of Birth: {dob}")

        # 3. Email & Phone (verify or fill)
        if not self.input_email.input_value():
            self.input_email.fill(payload.get("email", "q.a.te.k.in.spir.at.i.on.s@gmail.com"))
        if not self.input_phone.input_value():
            self.input_phone.fill(payload.get("phone", "8807022612"))

        # 4. Current Address
        zipcode = payload.get("current_zipcode", "201301")
        country = payload.get("current_country", "India")
        state = payload.get("current_state", "Uttar Pradesh")
        city = payload.get("current_city", "Noida")
        address = payload.get("current_address", "Sector 62, Industrial Area")

        self.input_current_zipcode.fill(zipcode)
        self.input_current_country.fill(country)
        self.input_current_state.fill(state)
        self.input_current_city.fill(city)
        self.input_current_address.fill(address)
        logger.info(f"  • Current Address: {address}, {city}, {state} - {zipcode}")

        # 5. Permanent Address: Click 'Same as Current'
        try:
            self.same_as_current_checkbox.first.click()
            logger.info("  • Clicked 'Same as Current' for Permanent Address.")
        except Exception:
            pass

        # If permanent address fields are still editable and empty, fill manually
        try:
            if self.input_permanent_zipcode.is_enabled() and not self.input_permanent_zipcode.input_value():
                self.input_permanent_zipcode.fill(zipcode)
                self.input_permanent_country.fill(country)
                self.input_permanent_state.fill(state)
                self.input_permanent_city.fill(city)
                self.input_permanent_address.fill(address)
                logger.info(f"  • Permanent Address manually filled: {address}, {city}, {state} - {zipcode}")
        except Exception:
            pass

        # 6. Gender & Marital Status
        # Gender options: 1=Male, 2=Female, 3=Transgender
        gender_val = str(payload.get("gender_val", "2"))
        self.select_gender.select_option(gender_val)

        # Marital Status options: 1=Married, 2=Unmarried, 3=Divorced
        marital_val = str(payload.get("marital_status_val", "2"))
        self.select_marital_status.select_option(marital_val)
        logger.info(f"  • Gender: {gender_val} | Marital Status: {marital_val}")

        # 7. Emergency Contact
        emg_name = payload.get("emergency_contact_name", "Ramesh Prakash")
        emg_phone = payload.get("emergency_contact_number", "9876543210")
        self.input_emergency_contact_name.fill(emg_name)
        self.input_emergency_contact_number.fill(emg_phone)
        logger.info(f"  • Emergency Contact: {emg_name} ({emg_phone})")

    def fill_step_2_family_details(self, data: Optional[dict] = None):
        """
        Fills Step 2: Family Details.
        Relation: 1=Father, 2=Mother, 3=Spouse, 4=Siblings, 5=Child, 6=Others
        Gender: 1=Male, 2=Female, 3=Transgender
        """
        payload = data or {}
        logger.info("[ONBOARDING STEP 2] Filling Family Details...")

        relation = str(payload.get("relation", "1"))  # Father by default
        gender = str(payload.get("family_gender", "1"))  # Male
        name = payload.get("family_name", "Ramesh Prakash")
        dob = payload.get("family_dob", "1972-04-10")

        self.select_family_relation.first.wait_for(state="visible", timeout=15000)
        self.select_family_relation.first.select_option(relation)
        self.select_family_gender.first.select_option(gender)
        self.input_family_name.first.fill(name)
        self.input_family_dob.first.fill(dob)

        logger.info(f"  • Family Member: {name} (Relation={relation}, Gender={gender}, DOB={dob})")

    def fill_step_3_education_details(self, data: Optional[dict] = None):
        """
        Fills Step 3: Education Details.
        Category: 1=Postgraduate, 2=Matriculation, 3=Intermediate, 4=Diploma, 5=Undergraduate, 6=Doctorate, 7=Graduation
        """
        payload = data or {}
        logger.info("[ONBOARDING STEP 3] Filling Education Details...")

        category_val = str(payload.get("education_category", "7"))  # Graduation
        self.select_edu_category.first.select_option(category_val)
        self.page.wait_for_timeout(1000)

        # Select degree (pick first valid option after loading)
        try:
            degrees = self.select_edu_degree.first.locator("option").all()
            for deg in degrees:
                val = deg.get_attribute("value") or ""
                if val:
                    self.select_edu_degree.first.select_option(val)
                    break
        except Exception:
            pass

        institute = payload.get("institute", "Delhi University")
        course = payload.get("course", "Bachelor of Commerce")
        grade = str(payload.get("grade", "85"))
        passing_year = str(payload.get("passing_year", "2023"))

        self.input_edu_institute.first.fill(institute)
        self.input_edu_course.first.fill(course)
        self.input_edu_grade.first.fill(grade)
        self.input_edu_passing_year.first.fill(passing_year)

        logger.info(f"  • Education: {institute} | {course} | {grade}% | Year: {passing_year}")

    def fill_step_4_identity_bank_details(self, data: Optional[dict] = None):
        """
        Fills Step 4: Identity & Bank Details.
        Bank: 50=HDFC, 53=ICICI, 104=SBI
        """
        payload = data or {}
        logger.info("[ONBOARDING STEP 4] Filling Identity & Bank Details...")

        bank_val = str(payload.get("bank_id", "50"))  # HDFC Bank
        branch = payload.get("branch_name", "Noida Branch")
        acc_no = str(payload.get("account_number", "50100234567890"))
        ifsc = payload.get("ifsc", "HDFC0000128")
        aadhaar = str(payload.get("aadhaar", "987654321098"))
        pan = payload.get("pan", "ABCDE1234F")
        uan = payload.get("uan", "")

        self.select_bank_name.first.select_option(bank_val)
        self.input_branch_name.first.fill(branch)
        self.input_account_number.first.fill(acc_no)
        self.input_ifsc_code.first.fill(ifsc)
        self.input_aadhaar.first.fill(aadhaar)
        self.input_pan.first.fill(pan)
        if uan:
            self.input_uan.first.fill(uan)

        logger.info(f"  • Bank: {bank_val} | IFSC: {ifsc} | Aadhaar: {aadhaar} | PAN: {pan}")

    def click_save_and_next(self):
        """Clicks 'Save & Next' button and waits for step transition."""
        logger.info("[UI] Clicking 'Save & Next'...")
        self.save_and_next_btn.first.scroll_into_view_if_needed()
        self.save_and_next_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    def fill_step_5_document_upload(self, data: Optional[dict] = None):
        """
        Fills Step 5: Document Upload and attaches candidate documents.
        Type: 1=Identity Document, 4=Education Document
        """
        payload = data or {}
        logger.info("[ONBOARDING STEP 5] Filling Document Upload...")

        doc_type = str(payload.get("doc_type", "1"))  # 1 = Identity Document
        default_file = os.path.abspath("testdata/static/resume/resume 1.pdf")
        doc_file_path = payload.get("file_path", default_file)

        # 1. Select Document Type
        self.select_doc_type.first.select_option(doc_type)
        try:
            self.page.wait_for_function(
                "() => document.querySelectorAll('select[name*=\"name\"] option').length > 1",
                timeout=7000
            )
        except Exception:
            self.page.wait_for_timeout(2000)

        # 2. Select Document Name (wait for options to populate)
        options = self.select_doc_name.first.locator("option").all()
        doc_name_val = payload.get("doc_name_val")
        available_opts = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val:
                available_opts.append(f"{val}:{text}")
                if not doc_name_val:
                    doc_name_val = val

        logger.info(f"  • Available Document Names: {available_opts}")

        if doc_name_val:
            self.select_doc_name.first.select_option(str(doc_name_val))
            logger.info(f"  • Selected Document Type: {doc_type} | Document Name Value: {doc_name_val}")

        # 3. Upload File
        if os.path.exists(doc_file_path):
            self.input_file_upload.first.set_input_files(doc_file_path)
            logger.info(f"  • Uploaded Document: {doc_file_path}")
        else:
            logger.warning(f"  • Document file path not found: {doc_file_path}")

    def click_save_and_submit(self):
        """Clicks 'Save & Submit' button and waits for submission to complete."""
        logger.info("[UI] Clicking 'Save & Submit'...")
        self.save_and_submit_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    def confirm_submission(self):
        """Clicks 'Yes, Submit' on the confirmation modal dialog."""
        logger.info("[UI] Confirming submission on modal dialog...")
        self.btn_confirm_submit.first.wait_for(state="visible", timeout=7000)
        self.btn_confirm_submit.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(3000)

    def is_submission_successful(self, timeout: int = 15000) -> bool:
        """Verifies that the post-submission success card ('Thank You !') is visible."""
        try:
            self.success_title.first.wait_for(state="visible", timeout=timeout)
            logger.info("[UI] Candidate Onboarding verified: 'Thank You !' success card is visible.")
            return True
        except Exception:
            return False
