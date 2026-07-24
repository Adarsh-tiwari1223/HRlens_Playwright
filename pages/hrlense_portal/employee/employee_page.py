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
        self.scroll_into_view(self.EMPLOYEE_NAV)
        self.click(self.EMPLOYEE_NAV)

    def click_add_new_employee(self):
        self.click(self.ADD_NEW_EMP_BTN)

    def _save_and_next(self):
        self.click(self.SAVE_NEXT_BTN)
        self.wait_for_toast(self.TOAST)

    def _select_role(self, roles: list[str]):
        self.click(self.ROLE_BTN)
        for role in roles:
            # Use exact text match via filter to avoid XSS risk with f-string in locator
            self.page.locator("span").filter(has_text=re.compile(f"^{re.escape(role)}$")).click()
        self.click(self.ROLE_BTN)

    def _fill_autocomplete(self, locator: str, value: str):
        self.fill(locator, value)
        self.page.locator(locator).press("Tab")

    # -------------------------------------------------------------------------

    def fill_basic_details(self, data: dict[str, Any]):
        self.fill(self.FIRST_NAME, data["full_name"])
        self.fill(self.OFFICIAL_EMAIL, data["official_email"])
        self.fill(self.PERSONAL_EMAIL, data.get("personal_email", ""))
        self.fill(self.US_PHONE, data.get("us_phone", ""))
        self.fill(self.PHONE_NUMBER, data["phone_number"])
        self.fill(self.DATE_OF_BIRTH, self._format_date(data.get("date_of_birth")))
        self.fill(self.DATE_OF_JOINING, self._format_date(data["date_of_joining"]))
        self.fill(self.CURRENT_ADDRESS, data.get("current_address", ""))
        self.fill(self.PERMANENT_ADDRESS, data.get("permanent_address", ""))

        self.select_option(self.GENDER, data["gender"])
        self.select_option(self.US_COMPANY, data.get("us_company", ""))
        self.select_option(self.BRANCH_DROPDOWN, data["branch"])
        self.select_option(self.DEPARTMENT, data["department"])
        self.select_option(self.DESIGNATION, data["designation"])
        self.select_option(self.SHIFT, data["shift"])

        if data.get("role"):
            roles = [data["role"]] if isinstance(data["role"], str) else data["role"]
            self._select_role(roles)

        if data.get("blood_group"):
            self.select_option(self.BLOOD_GROUP, data["blood_group"])
        if data.get("emergency_contact_name"):
            self.fill(self.EMERGENCY_CONTACT_NAME, data["emergency_contact_name"])
        if data.get("emergency_contact_number"):
            self.fill(self.EMERGENCY_CONTACT_NUMBER, data["emergency_contact_number"])

    def fill_employment_experience(self, data: dict[str, Any]):
        if data.get("payroll_company"):
            self.select_option(self.PAYROLL_COMPANY, data["payroll_company"])
        if data.get("business_process"):
            self.select_option(self.BUSINESS_PROCESS, data["business_process"])
        if data.get("reference"):
            self.select_option(self.REFERENCE, data["reference"])

        experience = self.page.locator(self.EXPERIENCE).input_value()
        if experience != "0" and data.get("last_organization"):
            self.fill(self.LAST_ORGANIZATION, data["last_organization"])

        if data.get("team_leader"):
            self._fill_autocomplete(self.TEAM_LEADER, data["team_leader"])
        if data.get("manager"):
            self._fill_autocomplete(self.MANAGER, data["manager"])

    def fill_education_detail(self, data: dict[str, Any]):
        if not data:
            return
        if data.get("education_category"):
            self.select_option(self.EDUCATION_CATEGORY, data["education_category"])
        if data.get("education_degree"):
            self.select_option(self.EDUCATION_DEGREE, data["education_degree"])
        if data.get("course_stream"):
            self.fill(self.COURSE_STREAM, data["course_stream"])
        if data.get("institute_name"):
            self.fill(self.INSTITUTE_NAME, data["institute_name"])
        if data.get("percentage_cgpa"):
            self.fill(self.PERCENTAGE_CGPA, data["percentage_cgpa"])
        if data.get("passing_year"):
            self.fill(self.PASSING_YEAR, data["passing_year"])
        if data.get("certificate_file"):
            self.upload_file(self.UPLOAD_CERTIFICATE, _safe_upload_path(data["certificate_file"]))

    def fill_family_detail(self, family_data: list[dict[str, Any]]):
        for i, member in enumerate(family_data):
            self.select_option(self.FAMILY_RELATION, member["relation"])
            self.fill(self.FAMILY_FULL_NAME, member["full_name"])
            self.fill(self.FAMILY_GENDER, member.get("gender", ""))
            self.fill(self.FAMILY_DOB, self._format_date(member.get("dob")))
            if i < len(family_data) - 1:
                self.click(self.ADD_MORE_FAMILY_BTN)

    def fill_salary_compensation(self, data: dict[str, Any]):
        self.fill(self.GROSS_SALARY, str(data["gross_salary"]))

    def fill_identity_bank(self, data: dict[str, Any]):
        self.fill(self.AADHAR_NUMBER, data.get("aadhar_number", ""))
        self.fill(self.PAN_NUMBER, data.get("pan_number", ""))
        self.fill(self.UAN_NUMBER, data.get("uan_number", ""))
        self.fill(self.ACCOUNT_NUMBER, data.get("account_number", ""))
        self.fill(self.IFSC_CODE, data.get("ifsc_code", ""))
        self.fill(self.BRANCH_BANK, data.get("branch", ""))
        if data.get("bank_name"):
            self.select_option(self.BANK_NAME, data["bank_name"])

    def upload_documents(self, data: dict[str, Any]):
        if data.get("document_type_1"):
            self.select_option(self.DOC_TYPE_1, data["document_type_1"])
        if data.get("document_name_1"):
            self.select_option(self.DOC_NAME_1, data["document_name_1"])
        if data.get("document_number_1"):
            self.fill(self.DOC_NUMBER_1, data["document_number_1"])
        if data.get("document_file_1"):
            self.upload_file(self.DOC_UPLOAD_1, _safe_upload_path(data["document_file_1"]))

        if data.get("document_type_2"):
            self.select_option(self.DOC_TYPE_2, data["document_type_2"])
        if data.get("document_name_2"):
            self.select_option(self.DOC_NAME_2, data["document_name_2"])
        if data.get("document_number_2"):
            self.fill(self.DOC_NUMBER_2, data["document_number_2"])
        if data.get("expiry_date_2"):
            self.fill(self.DOC_EXPIRY_2, self._format_date(data["expiry_date_2"]))
        if data.get("document_file_2"):
            self.upload_file(self.DOC_UPLOAD_2, _safe_upload_path(data["document_file_2"]))

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
        self.click(self.SUBMIT_BTN)

        toast = self.wait_for_toast(self.TOAST)
        assert "successfully" in toast.lower(), f"Employee creation failed. Toast: {toast}"
