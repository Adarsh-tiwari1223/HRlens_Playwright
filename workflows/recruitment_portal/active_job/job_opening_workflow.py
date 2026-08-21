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
        self.job_page.navigate_to_active_jobs()

    def select_random_dropdown_option(self, label_selector: str) -> str:
        """Selects a random dropdown option (excluding default placeholder) by label selector."""
        loc = self.page.locator(label_selector).first
        loc.wait_for(state="visible", timeout=8000)
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
        self.job_page.open_create_job_form()

        logger.info("[STEP] Fill mandatory fields")

        bp_opt = self.select_random_dropdown_option(self.job_page.BUSINESS_PROCESS)
        payroll_opt = self.select_random_dropdown_option(self.job_page.PAYROLL_COMPANY)
        branch_opt = self.select_random_dropdown_option(self.job_page.BRANCH)

        selected_dept = self.select_random_dropdown_option(self.job_page.DEPARTMENT)
        self.page.locator(self.job_page.JOB_TITLE).wait_for(state="visible", timeout=3000)

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
        self.page.locator(self.job_page.ADDITIONAL_DETAILS).first.click()
        self.page.locator(self.job_page.EXP_MIN).first.wait_for(state="visible", timeout=5000)
        self.page.locator(self.job_page.EXP_MIN).first.fill("6")

        self.page.locator(self.job_page.EXP_MAX).first.wait_for(state="visible", timeout=5000)
        self.page.locator(self.job_page.EXP_MAX).first.fill("18")

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
        pub_btn = self.page.locator(self.job_page.PUBLISH_BTN).first
        pub_btn.wait_for(state="visible", timeout=8000)
        pub_btn.scroll_into_view_if_needed()
        pub_btn.click()
        confirm_btn = self.page.locator(self.job_page.CONFIRM_BTN).first
        if confirm_btn.is_visible(timeout=2000):
            logger.info("[INFO] Publish confirmation dialog detected → Confirm clicked")
            confirm_btn.click()

    def get_active_validation_message(self) -> str | None:
        """
        Returns the first visible validation error message on the page, or None if none displayed.
        """
        try:
            loc = self.page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('is required'), :has-text('Job Description is required')").first
            if loc.is_visible(timeout=3000):
                return loc.inner_text().strip()
        except Exception:
            pass
        return None

    def trigger_empty_publish_and_verify_validations(self, expected_validations: list[str]):
        """
        Business Workflow: Attempts to publish an empty form and verifies each expected validation message is visible.
        """
        self.navigate_to_active_jobs()
        self.job_page.open_create_job_form()
        self.publish_with_confirm()

        for msg in expected_validations:
            self.job_page.verify_validation_message_visible(msg)

        self.job_page.close_drawer_safely(save_draft=False)

    def trigger_empty_publish_workflow(self) -> list[str]:
        """
        Business Workflow: Attempts to publish an empty Job Opening form.
        Returns the list of all field-level validation error messages.
        """
        self.navigate_to_active_jobs()
        self.job_page.open_create_job_form()
        self.publish_with_confirm()

        errors = self.job_page.get_all_error_messages()
        self.job_page.close_drawer_safely(save_draft=False)
        return errors

    def create_manual_job_opening_workflow(self, summary_text: str = None) -> str:
        """
        Business Workflow: Creates a new Job Opening with manually provided or generated JD summary.
        
        Steps:
        1. Navigate to Active Jobs
        2. Open fresh Job Opening creation form (handling draft modal if present)
        3. Fill mandatory fields with valid selections
        4. Set custom Job Summary in rich text editor
        5. Publish job and confirm
        6. Return created Job ID (e.g. 'JOB_POSTING-XXXX')
        """
        if not summary_text:
            summary_text = "Manual Job Description: Responsible for managing core tasks."

        self.navigate_to_active_jobs()
        self.job_page.open_create_job_form()

        self.job_page.select_business_process(index=1)
        self.job_page.select_payroll_company(index=1)
        self.job_page.select_branch(index=1)
        self.job_page.select_department(index=1)
        self.job_page.select_job_title(index=1)
        self.job_page.select_employment_type(index=1)
        self.job_page.select_urgency_level(index=1)
        self.job_page.select_work_mode(index=1)

        opening_dt = datetime.now().strftime("%Y-%m-%d")
        closing_dt = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        expected_doj = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        self.job_page.fill_job_fields(
            num_openings="5",
            opening_date=opening_dt,
            closing_date=closing_dt,
            salary_min="20000",
            salary_max="30000",
            doj=expected_doj,
            min_exp="1",
            max_exp="3"
        )

        self.job_page.set_job_summary(summary_text)
        self.publish_with_confirm()
        latest_id = self.job_page.get_latest_job_id()
        return latest_id

    def create_job_with_ai_jd_workflow(self) -> dict:
        """
        Business Workflow: Fills mandatory fields, generates AI JD summary, and publishes the job.
        Returns {'job_id': job_id, 'summary': summary_text}.
        """
        self.navigate_to_active_jobs()
        self.job_page.open_create_job_form()

        self.job_page.select_business_process(index=1)
        self.job_page.select_payroll_company(index=1)
        self.job_page.select_branch(index=1)
        self.job_page.select_department(index=1)
        self.job_page.select_job_title(index=1)
        self.job_page.select_employment_type(index=1)
        self.job_page.select_urgency_level(index=1)
        self.job_page.select_work_mode(index=1)

        opening_dt = datetime.now().strftime("%Y-%m-%d")
        closing_dt = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        expected_doj = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        self.job_page.fill_job_fields(
            num_openings="5",
            opening_date=opening_dt,
            closing_date=closing_dt,
            salary_min="20000",
            salary_max="30000",
            doj=expected_doj,
            min_exp="1",
            max_exp="3"
        )

        summary_text = self.job_page.click_generate_ai_jd()
        self.publish_with_confirm()
        latest_id = self.job_page.get_latest_job_id()

        return {"job_id": latest_id, "summary": summary_text}

    def handle_draft_modal(self, action: str = "start_new", draft_index: int = 0) -> dict | None:
        """
        Standardized Draft Modal Handler for all Job Opening workflows:
        - action='start_new': Clicks 'Start New Instead' to open a blank job creation form.
        - action='resume_random': Picks a random draft from the modal list and opens it for editing.
        - action='resume': Picks the draft at draft_index (default 0 for first) and opens it for editing.
        - action='get_all': Returns list of all draft cards without taking action.
        """
        if not self.job_page.is_draft_modal_visible():
            logger.info("[INFO] No pending drafts modal detected.")
            return None

        if action == "start_new":
            self.job_page.start_new_instead()
            return None
        elif action == "resume_random":
            return self.job_page.resume_random_draft()
        elif action == "resume":
            return self.job_page.resume_draft_by_index(draft_index)
        elif action == "get_all":
            return {"drafts": self.job_page.get_all_draft_items()}
        else:
            raise ValueError(f"Unknown draft modal action: {action}")

    def save_partial_draft_workflow(self, select_job_title: bool = True) -> dict:
        """
        Business Workflow: Partially fills the form and saves it as a draft.
        Returns the saved draft details from the draft list.
        """
        self.navigate_to_active_jobs()
        self.job_page.click_create_new_job_opening()
        self.handle_draft_modal(action="start_new")

        self.job_page.select_department(index=1)
        title_text = ""
        if select_job_title:
            title_text = self.job_page.select_job_title(index=1)

        self.job_page.close_drawer_safely(save_draft=True)
        self.job_page.click_create_new_job_opening()
        draft_details = self.job_page.get_first_draft_details()
        return draft_details
