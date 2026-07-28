"""
Candidate Management Workflow Layer.

Encapsulates reusable business workflows for Candidate management:
- Adding candidates (Fresher vs Experienced)
- Candidate job assignment (latest vs specific job)
- Interview scheduling workflow
- Offer generation & LOI workflow
- Complete candidate onboarding lifecycle
"""

import logging
from datetime import datetime, timedelta
from playwright.sync_api import Page
from pages.recruitment_portal.active_job.candidate_page import CandidatePage

logger = logging.getLogger(__name__)

class CandidateWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.candidate_page = CandidatePage(page)

    def add_candidate_for_latest_job(self, candidate_data: dict, resume_path: str) -> str:
        """Navigates to active jobs, selects the first job, opens form, fills data, and submits."""
        logger.info("[WORKFLOW] Initiating Candidate Creation Flow for Latest Job")
        job_name = self.candidate_page.navigate_to_add_candidate_for_job()
        self.candidate_page.fill_candidate_form(candidate_data, resume_path)
        self.candidate_page.submit()
        logger.info(f"[WORKFLOW] Candidate '{candidate_data['name']}' added to job '{job_name}'")
        return job_name

    def add_candidate_for_specific_job(self, job_id: str, candidate_data: dict, resume_path: str) -> str:
        """Navigates to active jobs, selects a specific job ID, fills data, and submits."""
        logger.info(f"[WORKFLOW] Initiating Candidate Creation for Job ID: {job_id}")
        job_name = self.candidate_page.navigate_to_add_candidate_for_specific_job(job_id)
        self.candidate_page.fill_candidate_form(candidate_data, resume_path)
        self.candidate_page.submit()
        logger.info(f"[WORKFLOW] Candidate '{candidate_data['name']}' added to job ID '{job_id}' ({job_name})")
        return job_name

    def schedule_interview_workflow(self, candidate_name: str, date: str = None, time: str = None):
        """Schedules an interview for a given candidate."""
        now = datetime.now()
        interview_date = date or now.strftime("%Y-%m-%d")
        interview_time = time or (now + timedelta(minutes=35)).strftime("%H:%M")

        logger.info(f"[WORKFLOW] Scheduling interview for candidate '{candidate_name}' at {interview_date} {interview_time}")
        self.candidate_page.schedule_interview(
            candidate_name=candidate_name,
            date=interview_date,
            time=interview_time
        )
        logger.info(f"[WORKFLOW] Interview scheduled successfully for '{candidate_name}'")

    def generate_and_send_offer_workflow(self, candidate_name: str, doj: str = None, gross_salary: str = "20000"):
        """Validates salary and generates/sends the offer letter (LOI) to the candidate."""
        now = datetime.now()
        date_of_joining = doj or now.strftime("%Y-%m-%d")

        logger.info(f"[WORKFLOW] Generating offer letter (LOI) for candidate '{candidate_name}' with salary {gross_salary}")
        self.page.reload()
        self.page.wait_for_load_state("networkidle")
        self.candidate_page.generate_and_validate_offer(
            candidate_name=candidate_name,
            doj=date_of_joining,
            gross_salary=gross_salary
        )
        logger.info(f"[WORKFLOW] Offer letter (LOI) successfully sent to '{candidate_name}'")

    def end_to_end_candidate_onboarding_workflow(self, candidate_data: dict, resume_path: str, job_id: str = None):
        """
        Complete Candidate Lifecycle Workflow:
        Add candidate -> Schedule interview -> Generate and send offer letter (LOI).
        """
        logger.info(f"[WORKFLOW] Starting full E2E Candidate Onboarding for '{candidate_data['name']}'")
        if job_id:
            self.add_candidate_for_specific_job(job_id, candidate_data, resume_path)
        else:
            self.add_candidate_for_latest_job(candidate_data, resume_path)

        self.schedule_interview_workflow(candidate_data['name'])
        self.generate_and_send_offer_workflow(candidate_data['name'])
        logger.info(f"[WORKFLOW] E2E Candidate Onboarding completed for '{candidate_data['name']}'")
