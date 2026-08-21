from datetime import datetime
import re
from pathlib import Path
from typing import Any
from pages.base_page import BasePage

_ALLOWED_UPLOAD_BASE = Path("testdata").resolve()


def _safe_upload_path(filepath: str) -> str:
    path = Path(filepath).resolve()
    if not str(path).startswith(str(_ALLOWED_UPLOAD_BASE)):
        raise ValueError(f"Invalid upload path — must be within testdata/: {filepath}")
    return str(path)


class EmployeePage(BasePage):
    # Side nav
    EMPLOYEE_NAV = "a:has-text('Employees')"

    # Employee list
    ADD_NEW_EMP_BTN = "button:has-text('Add New Employee')"

    # Toast (Chakra UI)
    TOAST = "div[id^='toast-'][id*='-title']"

    # Stepper
    SAVE_NEXT_BTN = "button:has-text('Save & Next')"
    SUBMIT_BTN = "button:has-text('Submit')"

    # --- Basic Details ---
    FIRST_NAME = "[name='fullName']"
    OFFICIAL_EMAIL = "[name='officialEmail']"
    PERSONAL_EMAIL = "[name='personalEmail']"
    US_PHONE = "[name='usPhone']"
    PHONE_NUMBER = "[name='phoneNumber']"
    DATE_OF_BIRTH = "[name='dob']"
    DATE_OF_JOINING = "[name='joiningDate']"
    CURRENT_ADDRESS = "[name='current_Address']"
    PERMANENT_ADDRESS = "[name='Permanent_Address']"
    PHOTO_UPLOAD = "input[type='file']"
    BLOOD_GROUP = "[name='blood_Group_Id']"
    EMERGENCY_CONTACT_NAME = "[name='emergency_Contact_Name']"
    EMERGENCY_CONTACT_NUMBER = "[name='emergency_Contact_Number']"

    # Basic Details dropdowns (standard <select>)
    GENDER = "(//select[starts-with(@id,'field-')])[1]"
    US_COMPANY = "(//select[starts-with(@id,'field-')])[2]"
    BRANCH_DROPDOWN = "(//select[starts-with(@id,'field-')])[3]"
    DEPARTMENT = "(//select[starts-with(@id,'field-')])[4]"
    DESIGNATION = "(//select[starts-with(@id,'field-')])[5]"
    SHIFT = "(//select[starts-with(@id,'field-')])[6]"

    # Role (button-based multi-select)
    ROLE_BTN = "(//button[starts-with(@id,'menu-button-')])[2]"

    # --- Employment & Experience ---
    PAYROLL_COMPANY = "(//select[starts-with(@id,'field-')])[1]"
    BUSINESS_PROCESS = "(//select[starts-with(@id,'field-')])[2]"
    REFERENCE = "(//select[starts-with(@id,'field-')])[3]"
    LAST_ORGANIZATION = "[name='lastOrganisation']"
    EXPERIENCE = "[name='experience']"
    TEAM_LEADER = "(//input[contains(@id,'field-')])[3]"
    MANAGER = "(//input[contains(@id,'field-')])[4]"

    # --- Education Detail ---
    EDUCATION_CATEGORY = "//label[normalize-space()='Education Category*']/following::select[1]"
    EDUCATION_DEGREE = "//label[normalize-space()='Education Degree*']/following::select[1]"
    COURSE_STREAM = "//label[normalize-space()='Course/Stream*']/following::input[@placeholder='Enter course/stream']"
    INSTITUTE_NAME = "//label[normalize-space()='Institute Name*']/following::input[@placeholder='Enter institute name']"
    PERCENTAGE_CGPA = "//label[normalize-space()='Percentage / CGPA*']/following::input[1]"
    PASSING_YEAR = "//label[normalize-space()='Passing Year*']/following::input[@type='date']"
    UPLOAD_CERTIFICATE = "//label[normalize-space()='Upload Certificate']/following::input[@type='file']"

    # --- Family Detail ---
    FAMILY_RELATION = "(//select[starts-with(@id,'field-')])[1]"
    FAMILY_FULL_NAME = "(//input[contains(@id,'field-')])[1]"
    FAMILY_GENDER = "(//input[contains(@id,'field-')])[2]"
    FAMILY_DOB = "(//input[starts-with(@id,'field-')])[2]"
    ADD_MORE_FAMILY_BTN = "button:has-text('Add More')"

    # --- Salary & Compensation ---
    GROSS_SALARY = "(//input[starts-with(@id,'field-')])[1]"

    # --- Identity & Bank ---
    AADHAR_NUMBER = "(//input[starts-with(@id,'field-')])[1]"
    PAN_NUMBER = "(//input[starts-with(@id,'field-')])[2]"
    UAN_NUMBER = "(//input[starts-with(@id,'field-')])[3]"
    ACCOUNT_NUMBER = "(//input[starts-with(@id,'field-')])[4]"
    IFSC_CODE = "(//input[starts-with(@id,'field-')])[5]"
    BRANCH_BANK = "(//input[starts-with(@id,'field-')])[6]"
    BANK_NAME = "(//select[starts-with(@id,'field-')])[2]"

    # --- Document Upload ---
    DOC_TYPE_1 = "(//select[contains(@class,'chakra-select')])[1]"
    DOC_NAME_1 = "(//select[contains(@class,'chakra-select')])[2]"
    DOC_NUMBER_1 = "(//input[@placeholder='Enter Document Number'])[1]"
    DOC_UPLOAD_1 = "input#file-upload-0"
    DOC_TYPE_2 = "(//select[contains(@class,'chakra-select')])[3]"
    DOC_NAME_2 = "(//select[contains(@class,'chakra-select')])[4]"
    DOC_NUMBER_2 = "(//input[@placeholder='Enter Document Number'])[2]"
    DOC_EXPIRY_2 = "input[type='date']"
    DOC_UPLOAD_2 = "input#file-upload-1"

    # -------------------------------------------------------------------------

    @staticmethod
    def _format_date(date_str: str | None) -> str | None:
        if not date_str:
            return None
        try:
            parts = date_str.split("-")
            if len(parts) == 3:
                year, month, day = parts
                return f"{month}/{day}/{year}"
        except ValueError:
            pass
        return date_str

    def click_employee_module(self):
        self.page.locator(self.EMPLOYEE_NAV).scroll_into_view_if_needed()
        self.page.locator(self.EMPLOYEE_NAV).click()

    def click_add_new_employee(self):
        self.page.locator(self.ADD_NEW_EMP_BTN).click()

    def _save_and_next(self):
        self.page.locator(self.SAVE_NEXT_BTN).click()
        self.wait_for_toast(self.TOAST)

    def _select_role(self, roles: list[str]):
        self.page.locator(self.ROLE_BTN).click()
        for role in roles:
            # Use exact text match via filter to avoid XSS risk with f-string in locator
            self.page.locator("span").filter(has_text=re.compile(f"^{re.escape(role)}$")).click()
        self.page.locator(self.ROLE_BTN).click()

    def _fill_autocomplete(self, locator: str, value: str):
        self.page.locator(locator).fill(value)
        self.page.locator(locator).press("Tab")

    # -------------------------------------------------------------------------

    def fill_basic_details(self, data: dict[str, Any]):
        self.page.locator(self.FIRST_NAME).fill(data["full_name"])
        self.page.locator(self.OFFICIAL_EMAIL).fill(data["official_email"])
        self.page.locator(self.PERSONAL_EMAIL).fill(data.get("personal_email", ""))
        self.page.locator(self.US_PHONE).fill(data.get("us_phone", ""))
        self.page.locator(self.PHONE_NUMBER).fill(data["phone_number"])
        self.page.locator(self.DATE_OF_BIRTH).fill(self._format_date(data.get("date_of_birth")))
        self.page.locator(self.DATE_OF_JOINING).fill(self._format_date(data["date_of_joining"]))
        self.page.locator(self.CURRENT_ADDRESS).fill(data.get("current_address", ""))
        self.page.locator(self.PERMANENT_ADDRESS).fill(data.get("permanent_address", ""))

        self.page.locator(self.GENDER).select_option(data["gender"])
        self.page.locator(self.US_COMPANY).select_option(data.get("us_company", ""))
        self.page.locator(self.BRANCH_DROPDOWN).select_option(data["branch"])
        self.page.locator(self.DEPARTMENT).select_option(data["department"])
        self.page.locator(self.DESIGNATION).select_option(data["designation"])
        self.page.locator(self.SHIFT).select_option(data["shift"])

        if data.get("role"):
            roles = [data["role"]] if isinstance(data["role"], str) else data["role"]
            self._select_role(roles)

        if data.get("blood_group"):
            self.page.locator(self.BLOOD_GROUP).select_option(data["blood_group"])
        if data.get("emergency_contact_name"):
            self.page.locator(self.EMERGENCY_CONTACT_NAME).fill(data["emergency_contact_name"])
        if data.get("emergency_contact_number"):
            self.page.locator(self.EMERGENCY_CONTACT_NUMBER).fill(data["emergency_contact_number"])

    def fill_employment_experience(self, data: dict[str, Any]):
        if data.get("payroll_company"):
            self.page.locator(self.PAYROLL_COMPANY).select_option(data["payroll_company"])
        if data.get("business_process"):
            self.page.locator(self.BUSINESS_PROCESS).select_option(data["business_process"])
        if data.get("reference"):
            self.page.locator(self.REFERENCE).select_option(data["reference"])

        experience = self.page.locator(self.EXPERIENCE).input_value()
        if experience != "0" and data.get("last_organization"):
            self.page.locator(self.LAST_ORGANIZATION).fill(data["last_organization"])

        if data.get("team_leader"):
            self._fill_autocomplete(self.TEAM_LEADER, data["team_leader"])
        if data.get("manager"):
            self._fill_autocomplete(self.MANAGER, data["manager"])

    def fill_education_detail(self, data: dict[str, Any]):
        if not data:
            return
        if data.get("education_category"):
            self.page.locator(self.EDUCATION_CATEGORY).select_option(data["education_category"])
        if data.get("education_degree"):
            self.page.locator(self.EDUCATION_DEGREE).select_option(data["education_degree"])
        if data.get("course_stream"):
            self.page.locator(self.COURSE_STREAM).fill(data["course_stream"])
        if data.get("institute_name"):
            self.page.locator(self.INSTITUTE_NAME).fill(data["institute_name"])
        if data.get("percentage_cgpa"):
            self.page.locator(self.PERCENTAGE_CGPA).fill(data["percentage_cgpa"])
        if data.get("passing_year"):
            self.page.locator(self.PASSING_YEAR).fill(data["passing_year"])
        if data.get("certificate_file"):
            self.page.locator(self.UPLOAD_CERTIFICATE).set_input_files(_safe_upload_path(data["certificate_file"]))

    def fill_family_detail(self, family_data: list[dict[str, Any]]):
        for i, member in enumerate(family_data):
            self.page.locator(self.FAMILY_RELATION).select_option(member["relation"])
            self.page.locator(self.FAMILY_FULL_NAME).fill(member["full_name"])
            self.page.locator(self.FAMILY_GENDER).fill(member.get("gender", ""))
            self.page.locator(self.FAMILY_DOB).fill(self._format_date(member.get("dob")))
            if i < len(family_data) - 1:
                self.page.locator(self.ADD_MORE_FAMILY_BTN).click()

    def fill_salary_compensation(self, data: dict[str, Any]):
        self.page.locator(self.GROSS_SALARY).fill(str(data["gross_salary"]))

    def fill_identity_bank(self, data: dict[str, Any]):
        self.page.locator(self.AADHAR_NUMBER).fill(data.get("aadhar_number", ""))
        self.page.locator(self.PAN_NUMBER).fill(data.get("pan_number", ""))
        self.page.locator(self.UAN_NUMBER).fill(data.get("uan_number", ""))
        self.page.locator(self.ACCOUNT_NUMBER).fill(data.get("account_number", ""))
        self.page.locator(self.IFSC_CODE).fill(data.get("ifsc_code", ""))
        self.page.locator(self.BRANCH_BANK).fill(data.get("branch", ""))
        if data.get("bank_name"):
            self.page.locator(self.BANK_NAME).select_option(data["bank_name"])

    def upload_documents(self, data: dict[str, Any]):
        if data.get("document_type_1"):
            self.page.locator(self.DOC_TYPE_1).select_option(data["document_type_1"])
        if data.get("document_name_1"):
            self.page.locator(self.DOC_NAME_1).select_option(data["document_name_1"])
        if data.get("document_number_1"):
            self.page.locator(self.DOC_NUMBER_1).fill(data["document_number_1"])
        if data.get("document_file_1"):
            self.page.locator(self.DOC_UPLOAD_1).set_input_files(_safe_upload_path(data["document_file_1"]))

        if data.get("document_type_2"):
            self.page.locator(self.DOC_TYPE_2).select_option(data["document_type_2"])
        if data.get("document_name_2"):
            self.page.locator(self.DOC_NAME_2).select_option(data["document_name_2"])
        if data.get("document_number_2"):
            self.page.locator(self.DOC_NUMBER_2).fill(data["document_number_2"])
        if data.get("expiry_date_2"):
            self.page.locator(self.DOC_EXPIRY_2).fill(self._format_date(data["expiry_date_2"]))
        if data.get("document_file_2"):
            self.page.locator(self.DOC_UPLOAD_2).set_input_files(_safe_upload_path(data["document_file_2"]))

    # -------------------------------------------------------------------------

    def add_new_employee(self, employee_data: dict[str, Any]):
        self.click_employee_module()
        self.click_add_new_employee()

        self.fill_basic_details(employee_data["basic_details"])
        self._save_and_next()

        self.fill_employment_experience(employee_data.get("employment_experience", {}))
        self._save_and_next()

        self.fill_family_detail(employee_data.get("family_detail", []))
        self._save_and_next()

        self.fill_salary_compensation(employee_data["salary_compensation"])
        self._save_and_next()

        self.fill_identity_bank(employee_data.get("identity_bank", {}))
        self._save_and_next()

        self.upload_documents(employee_data.get("document_upload", {}))
        self.page.locator(self.SUBMIT_BTN).click()

        toast = self.wait_for_toast(self.TOAST)
        assert "successfully" in toast.lower(), f"Employee creation failed. Toast: {toast}"
