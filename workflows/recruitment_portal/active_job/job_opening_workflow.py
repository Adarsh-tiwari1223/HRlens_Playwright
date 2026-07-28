"""
Job Opening Workflow Layer.

Encapsulates reusable business workflows for the Job Opening module:
- Form filling with random dynamic selections
- Publish with confirmation handling
- Validation error message extraction
- AI JD generation and clearing workflows

Layering Architecture:
- Page Objects → Locators + UI interactions only (pages/recruitment_portal/active_job/job_opening_page.py)
- Workflows → Reusable business flows and workflow orchestration (workflows/recruitment_portal/active_job/job_opening_workflow.py)
- Tests → Scenario assertions and execution reporting (tests/recruitment_portal/ui/active_job/...)
- Aggregator → Test delegation imports (tests/recruitment_portal/ui/active_job/test_job_opening.py)
"""

import random
import logging
from datetime import datetime, timedelta
from playwright.sync_api import Page, expect
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage

logger = logging.getLogger(__name__)

class JobOpeningWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.job_page = JobOpeningPage(page)

    def navigate_to_active_jobs(self):
        """Navigates to Recruitment Portal -> Job Openings -> Active Jobs."""
        self.page.get_by_role("button", name="Recruitment Portal").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Job Openings").click()
        self.page.get_by_role("link", name="• Active Jobs").click()
        self.page.wait_for_load_state("networkidle")

    def select_random_dropdown_option(self, label_selector: str) -> str:
        """Selects a random dropdown option (excluding default placeholder) by label selector."""
        loc = self.page.locator(label_selector)
        idx = random.randint(1, 3)
        try:
            loc.select_option(index=idx)
        except Exception:
            idx = 1
            loc.select_option(index=1)
        return f"Option #{idx}"

    def fill_mandatory_fields_except_jd(self) -> dict:
        """
        Opens a fresh Job Opening form and populates all mandatory fields dynamically
        with random dropdown selections, leaving Job Summary empty.
        """
        logger.info("[STEP] Open New Job Opening")
        self.job_page.click_create_new_job_opening()
        if self.job_page.is_draft_modal_visible():
            self.job_page.start_new_instead()

        logger.info("[STEP] Fill mandatory fields")

        bp_opt = self.select_random_dropdown_option(self.job_page.BUSINESS_PROCESS)
        payroll_opt = self.select_random_dropdown_option(self.job_page.PAYROLL_COMPANY)
        branch_opt = self.select_random_dropdown_option(self.job_page.BRANCH)

        selected_dept = self.select_random_dropdown_option(self.job_page.DEPARTMENT)
        self.page.wait_for_timeout(1000)

        selected_title = self.select_random_dropdown_option(self.job_page.JOB_TITLE)
        emp_type_opt = self.select_random_dropdown_option(self.job_page.EMPLOYMENT_TYPE)

        self.page.locator(self.job_page.NUM_OPENINGS).fill("1")
        self.page.locator(self.job_page.OPENING_DATE).fill(datetime.now().strftime("%Y-%m-%d"))
        self.page.locator(self.job_page.CLOSING_DATE).fill(
            (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        )
        self.page.locator(self.job_page.SALARY_MIN).fill("15000")
        self.page.locator(self.job_page.SALARY_MAX).fill("20000")

        urgency_opt = self.select_random_dropdown_option(self.job_page.URGENCY_LEVEL)
        work_mode_opt = self.select_random_dropdown_option(self.job_page.WORK_MODE)

        logger.info(
            f"Dynamic Selections → BusinessProcess: {bp_opt}, PayrollCompany: {payroll_opt}, "
            f"Branch: {branch_opt}, Dept: {selected_dept}, JobTitle: {selected_title}, "
            f"EmpType: {emp_type_opt}, Urgency: {urgency_opt}, WorkMode: {work_mode_opt}"
        )

        self.page.locator(self.job_page.EXPECTED_JOIN_DATE).fill(
            (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        )
        self.page.locator(self.job_page.ADDITIONAL_DETAILS).click()
        self.page.locator(self.job_page.EXP_MIN).fill("1")
        self.page.locator(self.job_page.EXP_MAX).fill("3")

        return {
            "business_process": bp_opt,
            "payroll_company": payroll_opt,
            "branch": branch_opt,
            "department": selected_dept,
            "job_title": selected_title,
        }

    def publish_with_confirm(self):
        """Clicks Publish Job and handles the optional confirmation dialog."""
        logger.info("[STEP] Click Publish")
        self.page.locator(self.job_page.PUBLISH_BTN).click()
        confirm_btn = self.page.locator(self.job_page.CONFIRM_BTN)
        if confirm_btn.is_visible(timeout=3000):
            logger.info("[INFO] Publish confirmation dialog detected → Confirm clicked")
            confirm_btn.click()

    def get_active_validation_message(self) -> str | None:
        """Extracts visible form validation messages while excluding non-error labels."""
        error_elements = self.page.locator(".chakra-form__error-message, [class*='error-message']").all()
        for el in error_elements:
            if el.is_visible():
                txt = el.inner_text().strip()
                if txt and txt.lower() != "required skills":
                    return txt

        ignore_labels = {"required skills", "job summary *", "job summary*", "basic information", "additional details", "job description"}
        locs = self.page.locator("text=/required/i").all()
        for loc in locs:
            if loc.is_visible():
                txt = loc.inner_text().strip()
                if txt.lower() not in ignore_labels and ("required" in txt.lower() or "please" in txt.lower()):
                    return txt
        return None
