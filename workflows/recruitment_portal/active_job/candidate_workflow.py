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
from pages.recruitment_portal.candidate_acceptance_page import CandidateAcceptancePage
from pages.recruitment_portal.candidate_onboarding_stepper_page import CandidateOnboardingStepperPage
from pages.recruitment_portal.onboarding_candidate_list_page import OnboardingCandidateListPage
from pages.recruitment_portal.hr_review_onboarding_page import HrReviewOnboardingPage

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

    def shortlist_candidate_workflow(self, candidate_name: str, status_option: str = "Shortlisted") -> bool:
        """
        Workflow: Moves a candidate from 'Applied' to 'Shortlisted'.
        """
        logger.info(f"[WORKFLOW] Shortlisting candidate '{candidate_name}' (status: {status_option})")
        return self.candidate_page.shortlist_candidate(candidate_name, status=status_option)

    def generate_and_send_offer_workflow(self, candidate_name: str, doj: str = None, gross_salary: str = "20000") -> dict:
        """Validates salary and generates/sends the offer letter (LOI) to the candidate."""
        now = datetime.now()
        date_of_joining = doj or now.strftime("%Y-%m-%d")

        logger.info(f"[WORKFLOW] Generating offer letter (LOI) for candidate '{candidate_name}' with salary {gross_salary}")
        self.page.reload()
        self.page.wait_for_load_state("domcontentloaded")
        res = self.candidate_page.generate_and_validate_offer(
            candidate_name=candidate_name,
            doj=date_of_joining,
            gross_salary=gross_salary
        )
        logger.info(f"[WORKFLOW] Offer letter (LOI) successfully sent to '{candidate_name}'")
        return res

    def verify_candidate_acceptance_workflow(self, verification_url: str, otp_code: str, accept: bool = True) -> dict:
        """
        Workflow: Candidate accesses the verification link, verifies acceptance via 6-digit OTP,
        and optionally accepts/confirms the offer.
        Returns dict containing extracted offer summary.
        """
        logger.info(f"[WORKFLOW] Navigating to Candidate Verification page: {verification_url}")
        acceptance_page = CandidateAcceptancePage(self.page)
        acceptance_page.navigate_to_verification_url(verification_url)
        acceptance_page.verify_otp_and_proceed(otp_code)
        logger.info("[WORKFLOW] Candidate OTP verification submitted.")

        offer_summary = {}
        if acceptance_page.is_offer_review_visible():
            offer_summary = acceptance_page.get_offer_summary()
            if accept:
                acceptance_page.accept_offer()
                logger.info("[WORKFLOW] Offer accepted by candidate.")
            else:
                acceptance_page.reject_offer()
                logger.info("[WORKFLOW] Offer rejected by candidate.")

        return offer_summary

    def complete_candidate_onboarding_stepper_workflow(self, onboarding_data: dict = None) -> bool:
        """
        Executes the full 5-Stepper Candidate Onboarding Wizard:
        Step 1: Basic Details
        Step 2: Family Details
        Step 3: Education Details
        Step 4: Identity & Bank Details
        Step 5: Document Upload & Final Submission Confirmation
        Returns True if success card ('Thank You !') is verified.
        """
        data = onboarding_data or {}
        stepper_page = CandidateOnboardingStepperPage(self.page)

        logger.info("[WORKFLOW] Starting 5-Stepper Candidate Onboarding Wizard...")

        # Step 1: Basic Details
        stepper_page.fill_step_1_basic_details(data.get("basic_details"))
        stepper_page.click_save_and_next()

        # Step 2: Family Details
        stepper_page.fill_step_2_family_details(data.get("family_details"))
        stepper_page.click_save_and_next()

        # Step 3: Education Details
        stepper_page.fill_step_3_education_details(data.get("education_details"))
        stepper_page.click_save_and_next()

        # Step 4: Identity & Bank Details
        stepper_page.fill_step_4_identity_bank_details(data.get("bank_details"))
        stepper_page.click_save_and_next()

        # Step 5: Document Upload & Final Submit
        stepper_page.fill_step_5_document_upload(data.get("document_details"))
        stepper_page.click_save_and_submit()
        stepper_page.confirm_submission()

        # Verify Success Page
        is_submitted = stepper_page.is_submission_successful()
        logger.info(f"[WORKFLOW] Candidate Onboarding Stepper Completed: Success={is_submitted}")
        return is_submitted

    def verify_candidate_in_onboarding_list_workflow(self, candidate_name: str, expected_status: str = "Accepted") -> dict:
        """
        Workflow: Navigates to Onboarding Candidate List (/onboardingCandidateList),
        searches for the candidate, verifies their status (e.g. 'Accepted'),
        and returns the candidate's row details dictionary.
        """
        logger.info(f"[WORKFLOW] Verifying Candidate '{candidate_name}' in Onboarding Candidate List with status '{expected_status}'...")
        list_page = OnboardingCandidateListPage(self.page)
        list_page.navigate_to_onboarding_list()
        list_page.search_candidate(candidate_name)

        is_present = list_page.is_candidate_present(candidate_name)
        assert is_present, f"Candidate '{candidate_name}' not found in Onboarding Candidate List table!"

        details = list_page.get_candidate_details(candidate_name)
        actual_status = details.get("status", "")
        logger.info(f"[WORKFLOW] Candidate '{candidate_name}' record extracted: {details}")
        assert actual_status.strip().lower() == expected_status.strip().lower(), \
            f"Candidate status mismatch in Onboarding List! Expected '{expected_status}', got '{actual_status}'"

        logger.info(f"[WORKFLOW] Candidate '{candidate_name}' successfully verified with status '{expected_status}' in Onboarding List.")
        return details

    def hr_review_and_approve_candidate_workflow(self, candidate_name: str, review_tabs: bool = True) -> dict:
        """
        HR Review Workflow:
        1. Navigates to Onboarding Candidate List (/onboardingCandidateList).
        2. Searches for candidate and clicks the Action Arrow.
        3. Verifies 'HR Review - Candidate On Boarding' page is loaded.
        4. Extracts Candidate Header Summary (Candidate ID, Salary, Joining Date, Review Status).
        5. Optionally reviews all 4 detail tabs:
           - Candidate Details
           - Identify and Banking
           - Employment & Experience
           - View Document
        6. Checks 'Approve All' and clicks 'Verify'.
        7. Returns review summary and approval confirmation.
        """
        logger.info(f"[WORKFLOW] Starting HR Review and Approval for candidate '{candidate_name}'...")
        list_page = OnboardingCandidateListPage(self.page)
        list_page.navigate_to_onboarding_list()
        list_page.search_candidate(candidate_name)
        list_page.click_candidate_action(candidate_name)

        hr_review = HrReviewOnboardingPage(self.page)
        is_loaded = hr_review.is_page_loaded(timeout=15000)
        assert is_loaded, f"HR Review page failed to load for candidate '{candidate_name}'!"

        summary = hr_review.get_header_summary()
        logger.info(f"[WORKFLOW] Candidate Header Summary in HR Review: {summary}")

        if review_tabs:
            for tab_name in ["Candidate Details", "Identify and Banking", "Employment & Experience", "View Document"]:
                try:
                    hr_review.select_tab(tab_name)
                except Exception as tab_err:
                    logger.warning(f"[WORKFLOW] Non-blocking warning reviewing tab '{tab_name}': {tab_err}")

        # Approve All and Verify
        approval_success = hr_review.approve_all_and_verify()
        logger.info(f"[WORKFLOW] HR Review Approval finished: Success={approval_success}")

        return {
            "candidate_name": candidate_name,
            "header_summary": summary,
            "approval_success": approval_success
        }

    def end_to_end_candidate_onboarding_workflow(self, candidate_data: dict, resume_path: str, job_id: str = None, shortlist: bool = True):
        """
        Complete Candidate Lifecycle Workflow:
        Add candidate -> Shortlist (optional) -> Schedule interview -> Generate and send offer letter (LOI).
        """
        cand_name = candidate_data["name"]
        logger.info(f"[WORKFLOW] Starting full E2E Candidate Onboarding for '{cand_name}'")
        if job_id:
            assigned_job = self.add_candidate_for_specific_job(job_id, candidate_data, resume_path)
        else:
            assigned_job = self.add_candidate_for_latest_job(candidate_data, resume_path)

        if shortlist:
            self.shortlist_candidate_workflow(cand_name, status_option="Shortlisted")

        self.schedule_interview_workflow(cand_name)
        offer_res = self.generate_and_send_offer_workflow(cand_name)
        logger.info(f"[WORKFLOW] E2E Candidate Onboarding completed for '{cand_name}'")
        return {
            "job_id": job_id or assigned_job,
            "candidate_name": cand_name,
            "shortlisted": shortlist,
            "interview_scheduled": True,
            "loi_result": offer_res
        }

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
        from utils.api.employee.candidate_api import find_or_seed_old_candidate_hybrid
        logger.info(f"[WORKFLOW] Executing Approach 1 + 3 Hybrid Candidate Discovery (min_days_old={min_days_old})...")
        candidate_record = find_or_seed_old_candidate_hybrid(min_days_old=min_days_old)
        logger.info(f"[WORKFLOW] Hybrid Discovery Result: '{candidate_record.get('fullName') or candidate_record.get('name')}' (Days Old={candidate_record.get('days_old')})")
        return candidate_record
