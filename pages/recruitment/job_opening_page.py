from playwright.sync_api import Page, expect
import re
from pages.base_page import BasePage

class JobOpeningPage(BasePage):
    # --- Selectors ---
    CREATE_JOB_BTN = "button:has-text('Create New Job Opening')"
    BUSINESS_PROCESS = "label:has-text('Business Process *')"
    PAYROLL_COMPANY = "label:has-text('Payroll Company *')"
    BRANCH = "label:has-text('Branch *')"
    DEPARTMENT = "label:has-text('Department *')"
    JOB_TITLE = "label:has-text('Job Title *')"
    NUM_OPENINGS = "[placeholder='Enter Number of Openings']"
    EMPLOYMENT_TYPE = "label:has-text('Employement Type *')"
    OPENING_DATE = "[placeholder='Select Job Opening Date']"
    CLOSING_DATE = "[placeholder='Select Job Closing Date']"
    SALARY_MIN = "[placeholder='Enter Salary Min']"
    SALARY_MAX = "[placeholder='Enter Salary Max']"
    URGENCY_LEVEL = "label:has-text('Urgency Level *')"
    WORK_MODE = "label:has-text('Work Mode *')"
    EXPECTED_JOIN_DATE = "[placeholder*='Select Expected Date of']"
    EXP_MIN = "label:has-text('Experience (in years) Min*')"
    EXP_MAX = "label:has-text('Experience (in years) Max*')"
    PUBLISH_BTN = "button:has-text('Publish Job')"
    CONFIRM_BTN = "button:has-text('Confirm')"
    ADDITIONAL_DETAILS = "text=Additional Details"

    def navigate_to_job_openings(self):
        """Navigate to the job openings page. (Requires prior navigation setup based on routing)"""
        # Assuming URL routing or navigation steps exist.
        pass

    def create_job_opening(self, job_data: dict):
        """
        Creates a new job opening using the provided dictionary.
        job_data expects string representations of option values or text inputs.
        """
        self.page.locator(self.CREATE_JOB_BTN).click()
        self.page.wait_for_load_state("networkidle")

        # Select dropdowns
        self.page.locator(self.BUSINESS_PROCESS).select_option(job_data.get("business_process", "4"))
        self.page.locator(self.PAYROLL_COMPANY).select_option(job_data.get("payroll_company", "10"))
        self.page.locator(self.BRANCH).select_option(job_data.get("branch", "1"))
        self.page.locator(self.DEPARTMENT).select_option(job_data.get("department", "1"))
        self.page.locator(self.JOB_TITLE).select_option(job_data.get("job_title", "32"))

        # Fill openings
        self.page.locator(self.NUM_OPENINGS).fill(job_data.get("openings", "10"))

        # Employment Type
        self.page.locator(self.EMPLOYMENT_TYPE).select_option(job_data.get("employment_type", "1"))

        # Dates
        self.page.locator(self.OPENING_DATE).fill(job_data.get("opening_date", "2026-05-30"))
        self.page.locator(self.CLOSING_DATE).fill(job_data.get("closing_date", "2026-05-31"))

        # Salary
        self.page.locator(self.SALARY_MIN).fill(job_data.get("salary_min", "15000"))
        self.page.locator(self.SALARY_MAX).fill(job_data.get("salary_max", "20000"))

        # Meta
        self.page.locator(self.URGENCY_LEVEL).select_option(job_data.get("urgency", "2"))
        self.page.locator(self.WORK_MODE).select_option(job_data.get("work_mode", "4"))
        self.page.locator(self.EXPECTED_JOIN_DATE).fill(job_data.get("expected_join", "2026-06-06"))

        # Additional Details
        self.page.locator(self.ADDITIONAL_DETAILS).click()
        self.page.locator(self.EXP_MIN).fill(job_data.get("exp_min", "0"))
        self.page.locator(self.EXP_MAX).fill(job_data.get("exp_max", "1"))

        # Job Summary (Rich Text or complex div)
        summary = job_data.get("summary", "Enter the JD")
        self.page.locator("div").filter(has_text=re.compile(r"^Enter Job Summary$")).locator("div").first.fill(summary)

        # Publish
        self.page.locator(self.PUBLISH_BTN).click()
        self.page.locator(self.CONFIRM_BTN).click()
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def get_latest_job_id(self) -> str:
        """
        Reads the newly created Job Posting ID from the grid.
        Assumes the job IDs follow the pattern 'JOB_POSTING-XXX' and the newest is first.
        """
        # Look for any text matching the JOB_POSTING- prefix
        job_id_locator = self.page.locator("text=/JOB_POSTING-\d+/").first
        job_id_locator.wait_for(state="visible", timeout=5000)
        return job_id_locator.inner_text().strip()
