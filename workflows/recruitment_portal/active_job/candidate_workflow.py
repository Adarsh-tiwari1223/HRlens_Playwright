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

    def generate_and_send_offer_workflow(self, candidate_name: str, doj: str = None, gross_salary: str = "20000") -> dict:
        """Validates salary and generates/sends the offer letter (LOI) to the candidate."""
        now = datetime.now()
        date_of_joining = doj or now.strftime("%Y-%m-%d")

        logger.info(f"[WORKFLOW] Generating offer letter (LOI) for candidate '{candidate_name}' with salary {gross_salary}")
        self.page.reload()
        self.page.wait_for_load_state("networkidle")
        res = self.candidate_page.generate_and_validate_offer(
            candidate_name=candidate_name,
            doj=date_of_joining,
            gross_salary=gross_salary
        )
        logger.info(f"[WORKFLOW] Offer letter (LOI) successfully sent to '{candidate_name}'")
        return res

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

    def seed_multi_stage_candidates_workflow(self, job_id: str, dummy_resume_path: str) -> dict:
        """
        Seeds candidates across 3 HR-controlled stage states under job_id:
        1. Applied: Candidate added (Applied status).
        2. Interview Scheduled: Candidate added + Interview Scheduled.
        3. LOI Sent / Shared: Candidate added + Interview Scheduled + LOI Generated and Sent by HR.
        Returns dict of candidate records.
        """
        from testdata.dynamic.candidate_data import generate_candidate_data
        logger.info(f"[WORKFLOW] Seeding 3 stage candidates (Applied, Interview Scheduled, LOI Sent) under Job ID '{job_id}'...")

        # 1. Candidate 1: Applied
        data_applied = generate_candidate_data(is_experienced=False)
        c1_name = data_applied["name"]
        self.add_candidate_for_specific_job(job_id, data_applied, dummy_resume_path)
        logger.info(f"[WORKFLOW] Candidate 1 (Applied) created: {c1_name}")

        # 2. Candidate 2: Interview Scheduled
        data_scheduled = generate_candidate_data(is_experienced=False)
        c2_name = data_scheduled["name"]
        self.add_candidate_for_specific_job(job_id, data_scheduled, dummy_resume_path)
        self.schedule_interview_workflow(c2_name)
        logger.info(f"[WORKFLOW] Candidate 2 (Interview Scheduled) created: {c2_name}")

        # 3. Candidate 3: LOI Sent / Shared
        data_loi = generate_candidate_data(is_experienced=True)
        c3_name = data_loi["name"]
        self.add_candidate_for_specific_job(job_id, data_loi, dummy_resume_path)
        self.schedule_interview_workflow(c3_name)
        self.generate_and_send_offer_workflow(c3_name, gross_salary="25000")
        logger.info(f"[WORKFLOW] Candidate 3 (LOI Sent / Shared) created: {c3_name}")

        return {
            "applied": c1_name,
            "interview_scheduled": c2_name,
            "loi_sent": c3_name
        }

    def check_resubmission_preconditions(self, candidate_status: str, days_since_submission: int) -> bool:
        """
        S.No 1 Pre-Validation Check (BOTH conditions MUST be True):
        Condition 1: candidate_status.strip().lower() == 'applied'
        Condition 2: days_since_submission > 30
        Returns True ONLY if BOTH conditions are fulfilled.
        """
        is_applied_status = candidate_status.strip().lower() == "applied"
        is_after_30_days = days_since_submission > 30

        if is_applied_status and is_after_30_days:
            logger.info(f"[PRE-CHECK] Resubmission ELIGIBLE=True! Status='{candidate_status}', Days={days_since_submission} (> 30)")
            return True
        else:
            reasons = []
            if not is_applied_status:
                reasons.append(f"Status '{candidate_status}' is not 'Applied'")
            if not is_after_30_days:
                reasons.append(f"Days {days_since_submission} <= 30-day waiting period")
            logger.warning(f"[PRE-CHECK] Resubmission ELIGIBLE=False! Reasons: {', '.join(reasons)}")
            return False

    def simulate_candidate_resubmission_ownership_workflow(
        self, candidate_name: str, previous_owner: str, new_owner: str, days_since_submission: int, candidate_status: str = "Applied"
    ) -> dict:
        """
        Executes CRS_001 to CRS_006 Ownership & Re-submission Rules:
        - Evaluates (status == 'Applied') AND (days > 30) formula.
        - If ELIGIBLE: Transfers ownership to new_owner, updates submission date to today, resets 30-day timer.
        - If NOT ELIGIBLE: Retains previous_owner, locks submission date, blocks re-submission.
        Returns detailed result dictionary.
        """
        from datetime import datetime
        is_eligible = self.check_resubmission_preconditions(candidate_status, days_since_submission)

        if is_eligible:
            today_str = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"[WORKFLOW] Ownership Transferred: '{previous_owner}' -> '{new_owner}'. Submission Date Reset to: {today_str}")
            return {
                "is_eligible": True,
                "owner": new_owner,
                "previous_owner": previous_owner,
                "submission_date": today_str,
                "timer_reset": True,
                "immediate_resubmission_allowed": False
            }
        else:
            logger.warning(f"[WORKFLOW] Re-submission Blocked! Ownership retained by: '{previous_owner}'")
            return {
                "is_eligible": False,
                "owner": previous_owner,
                "previous_owner": previous_owner,
                "submission_date": "Original Date",
                "timer_reset": False,
                "immediate_resubmission_allowed": False
            }

    def get_or_seed_30_day_old_candidate_workflow(self, min_days_old: int = 35) -> dict:
        """
        Hybrid Approach (1 + 3):
        - Approach 1: Queries backend API to find existing candidate created > 30 days ago with status 'Applied'.
        - Approach 3: If not found, seeds backdated candidate via API (created 35 days ago).
        """
        from utils.api.candidate_api import find_or_seed_old_candidate_hybrid
        logger.info(f"[WORKFLOW] Executing Approach 1 + 3 Hybrid Candidate Discovery (min_days_old={min_days_old})...")
        candidate_record = find_or_seed_old_candidate_hybrid(min_days_old=min_days_old)
        logger.info(f"[WORKFLOW] Hybrid Discovery Result: '{candidate_record.get('fullName') or candidate_record.get('name')}' (Days Old={candidate_record.get('days_old')})")
        return candidate_record
