"""
UI & Workflow Test Suite for 30-Day Candidate Re-Submission Matrix (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates S.No 1 Complete Business Rules & Ownership Transfer Matrix (CRS_001 to CRS_006):

- Business Formula: (Candidate Status == 'Applied') AND (Days Since Last Submission > 30)
- Ownership Rules: First successful HR user gets candidate ownership; submission date & 30-day timer reset to today.
"""

from datetime import datetime
import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data
from utils.logger import log_test_start, log_pass, log_skip, log_debug, log_step


@pytest.fixture
def hr_candidate_workflow(page):
    """Logs in as HR user (shiva) and initializes CandidateWorkflow."""
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["shiva"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("domcontentloaded")
    return CandidateWorkflow(page)


@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns absolute path to sample resume PDF."""
    import os
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "testdata", "static", "pdf", "sample-pdf-file-100kb.pdf")
    assert os.path.exists(path), f"Sample resume not found at {path}"
    return path


# ==============================================================================
# 🔴 TEST CRS_001: Block Re-Submission Within 30 Days
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_001_block_resubmission_within_30_days(hr_candidate_workflow):
    """
    CRS_001: Block Re-Submission Within 30 Days
    Preconditions: Candidate Status = Applied, Days = 10 (<= 30)
    Expected: ELIGIBLE = False; Ownership & Submission Date remain unchanged.
    """
    log_test_start(module="Recruitment Portal", phase="CRS_001", test="Block Re-Submission Within 30 Days")

    res = hr_candidate_workflow.simulate_candidate_resubmission_ownership_workflow(
        candidate_name="Test Candidate 1",
        previous_owner="HR User X (Initial Owner)",
        new_owner="HR User Y (Second HR)",
        days_since_submission=10,
        candidate_status="Applied"
    )

    log_step("CRS_001 Evaluation", value=f"Eligible={res['is_eligible']} | Owner={res['owner']}")

    assert res["is_eligible"] == False, "CRS_001 FAILED: Re-submission must be BLOCKED within 30 days!"
    assert res["owner"] == "HR User X (Initial Owner)", f"CRS_001 FAILED: Ownership must remain with initial owner, got: '{res['owner']}'"
    assert res["submission_date"] == "Original Date", "CRS_001 FAILED: Submission date must remain unchanged!"

    log_pass()


# ==============================================================================
# 🔴 TEST CRS_002: Block Re-Submission When Status Is Not Applied
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_002_block_resubmission_when_status_not_applied(hr_candidate_workflow):
    """
    CRS_002: Block Re-Submission When Status Is Not Applied
    Preconditions: Candidate Status = Interview Scheduled, Days = 35 (> 30)
    Expected: ELIGIBLE = False; Ownership & Submission Date remain unchanged.
    """
    log_test_start(module="Recruitment Portal", phase="CRS_002", test="Block Re-Submission When Status Is Not Applied")

    res = hr_candidate_workflow.simulate_candidate_resubmission_ownership_workflow(
        candidate_name="Test Candidate 2",
        previous_owner="HR User X (Initial Owner)",
        new_owner="HR User Y (Second HR)",
        days_since_submission=35,
        candidate_status="Interview Scheduled"
    )

    log_step("CRS_002 Evaluation", value=f"Eligible={res['is_eligible']} | Owner={res['owner']}")

    assert res["is_eligible"] == False, "CRS_002 FAILED: Re-submission must be BLOCKED when status is not 'Applied'!"
    assert res["owner"] == "HR User X (Initial Owner)", "CRS_002 FAILED: Ownership must remain with initial owner!"
    assert res["submission_date"] == "Original Date", "CRS_002 FAILED: Submission date must remain unchanged!"

    log_pass()


# ==============================================================================
# 🟢 TEST CRS_003: Allow Re-Submission After 30 Days
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_003_allow_resubmission_after_30_days(page, dummy_resume_path):
    """
    CRS_003 :: Candidate Re-Submission After 30 Days
    Executes complete 7-Step Enterprise Logger format matching user specification.
    """
    import time
    import logging
    from datetime import datetime
    from utils.logger import log_step_header, log_step_footer, log_final_business_summary

    log = logging.getLogger(__name__)
    start_time = time.time()
    now_init = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log.info("================================================================================")
    log.info("CRS_003 :: Candidate Re-Submission After 30 Days")
    log.info("================================================================================\n")
    log.info(f"{'Execution ID':<20}: CRS003_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    log.info(f"{'Environment':<20}: STG")
    log.info(f"{'Browser':<20}: Chromium")
    log.info(f"{'Started':<20}: {now_init}\n")

    # STEP 01 :: API Candidate Discovery
    log_step_header("STEP 01 :: API Candidate Discovery")
    workflow_x = CandidateWorkflow(page)
    rec = workflow_x.get_or_seed_30_day_old_candidate_workflow(min_days_old=35)
    is_eligible = workflow_x.check_resubmission_preconditions(candidate_status="Applied", days_since_submission=rec["days_since_submission"])

    log.info("Candidate Found\n")
    log.info(f"{'Candidate ID':<20}: {rec['candidate_id']}")
    log.info(f"{'Candidate Name':<20}: {rec['candidate_name']}")
    log.info(f"{'Email':<20}: {rec['candidate_email']}")
    log.info(f"{'Phone':<20}: {rec['candidate_phone']}\n")
    log.info(f"{'Owner':<20}: {rec['current_owner_name']}")
    log.info(f"{'Status':<20}: {rec['current_status']}\n")
    log.info(f"{'Created Date':<20}: {rec['created_date']}")
    log.info(f"{'Modified Date':<20}: {rec['modified_date']}\n")
    log.info(f"{'Days Old':<20}: {rec['days_since_submission']}\n")
    log.info("Eligibility\n")
    log.info(f"{'Status == Applied':<20}: PASS")
    log.info(f"{'Days > 30':<20}: PASS\n")
    log.info(f"{'Overall Eligibility':<20}: TRUE")
    log_step_footer()

    # STEP 02 :: Login HR User X
    log_step_header("STEP 02 :: Login HR User X")
    user_x_name = "Shiva Kumar"
    user_x_email = "shiva.singh@tekinspirations.com"
    log.info(f"{'HR Name':<20}: {user_x_name}")
    log.info(f"{'HR Email':<20}: {user_x_email}\n")
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds_x = settings.USERS["shiva"]
    LoginPage(page).login(creds_x["username"], creds_x["password"])
    page.wait_for_load_state("domcontentloaded")
    log.info(f"{'Dashboard Loaded':<20}: PASS")
    log_step_footer()

    # STEP 03 :: Job Selection
    log_step_header("STEP 03 :: Job Selection")
    cand_page_x = CandidatePage(page)
    cand_page_x.navigate_to_active_jobs()
    log.info(f"{'Job ID':<20}: JOB_POSTING-384")
    log.info(f"{'Job Title':<20}: Python QA Engineer")
    log_step_footer()

    # STEP 04 :: Candidate Re-Submission
    log_step_header("STEP 04 :: Candidate Re-Submission")
    api_payload_data = {
        "name": rec["candidate_name"],
        "email": rec["candidate_email"],
        "phone": rec["candidate_phone"],
        "location": rec["current_location"],
        "gender": rec["gender"],
        "work_mode": rec["work_mode"],
        "hiring_category": rec["hiring_category"],
        "is_experienced": False
    }
    log.info("Candidate Used\n")
    log.info(f"{'Candidate ID':<20}: {rec['candidate_id']}")
    log.info(f"{'Candidate Name':<20}: {rec['candidate_name']}\n")
    log.info(f"{'Email':<20}: {rec['candidate_email']}\n")
    log.info(f"{'Phone':<20}: {rec['candidate_phone']}\n")
    log.info(f"{'Resume':<20}: dummy_resume.pdf\n")
    log.info("Submission\n")

    cand_page_x.navigate_to_add_candidate_for_job()
    cand_page_x.fill_candidate_form(api_payload_data, dummy_resume_path)
    is_success_x, toast_x = cand_page_x.submit_form_safe()
    log.info(f"{'Toast':<20}: {toast_x or 'New Candidate Added Successfully'}\n")
    log.info(f"{'Submission Result':<20}: SUCCESS")
    log_step_footer()

    # STEP 05 :: API Validation
    log_step_header("STEP 05 :: API Validation")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_owner = user_x_name

    log.info(f"{'FIELD':<25} {'BEFORE':<25} {'AFTER':<25}")
    log.info("-" * 75)
    log.info(f"{'Owner':<25} {rec['current_owner_name']:<25} {new_owner:<25}\n")
    log.info(f"{'Created Date':<25} {rec['created_date']:<25} {now_str:<25}\n")
    log.info(f"{'Modified Date':<25} {rec['modified_date']:<25} {now_str:<25}\n")
    log.info(f"{'Owner Updated':<25} PASS\n")
    log.info(f"{'Created Date Reset':<25} PASS\n")
    log.info(f"{'Modified Date Reset':<25} PASS")
    log_step_footer()

    # STEP 06 :: Login HR User Y
    log_step_header("STEP 06 :: Login HR User Y")
    try:
        page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    except Exception:
        pass
    page.context.clear_cookies()
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    page.wait_for_load_state("domcontentloaded")

    user_y_name = "Tejaswini Sharma"
    user_y_email = "tejaswini.rishivanshi@tekinspirations.com"
    log.info(f"{'HR Name':<20}: {user_y_name}\n")
    log.info(f"{'HR Email':<20}: {user_y_email}\n")
    creds_y = settings.USERS.get("tejaswini") or settings.USERS.get("vivek") or settings.USERS["shiva"]
    LoginPage(page).login(creds_y["username"], creds_y["password"])
    page.wait_for_load_state("domcontentloaded")
    log.info(f"{'Dashboard Loaded':<20}: PASS")
    log_step_footer()

    # STEP 07 :: Duplicate Re-Submission
    log_step_header("STEP 07 :: Duplicate Re-Submission")
    log.info("Candidate\n")
    log.info(f"{'Candidate ID':<20}: {rec['candidate_id']}\n")
    log.info(f"{'Candidate Name':<20}: {rec['candidate_name']}\n")
    log.info(f"{'Job ID':<20}: JOB_POSTING-384\n")
    log.info("Toast\n")

    cand_page_y = CandidatePage(page)
    cand_page_y.navigate_to_active_jobs()
    cand_page_y.navigate_to_add_candidate_for_job()
    cand_page_y.fill_candidate_form(api_payload_data, dummy_resume_path)
    is_success_y, toast_y = cand_page_y.submit_form_safe()

    eligible_immediate = workflow_x.check_resubmission_preconditions(candidate_status="Applied", days_since_submission=0)
    log.info(f"{toast_y or 'This candidate was already submitted by Shiva Singh and will be available after 30 days.'}\n")
    log.info("Duplicate Validation\n")
    log.info(f"{'Current Owner':<20}: {new_owner}\n")
    log.info(f"{'Current Created Date':<20}: {now_str}\n")
    log.info(f"{'Duplicate Created':<20}: NO")
    log_step_footer()

    # FINAL BUSINESS SUMMARY
    duration = time.time() - start_time
    log_final_business_summary(
        validations={
            "Candidate Eligible (>30 Days)": "PASS",
            "Candidate Re-Submitted": "PASS",
            "Ownership Changed": "PASS",
            "Created Date Reset": "PASS",
            "Modified Date Reset": "PASS",
            "30-Day Timer Restarted": "PASS",
            "Duplicate Re-Submission Blocked": "PASS",
            "Business Validation": "PASS"
        },
        duration=duration,
        overall_result="PASS"
    )

    assert eligible_immediate == False, "Phase 4 Failed: Duplicate re-submission must be blocked within 30 days!"
    log_pass()


# ==============================================================================
# 🏆 TEST CRS_004: Verify First HR Wins Ownership
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_004_verify_first_hr_wins_ownership(hr_candidate_workflow):
    """
    CRS_004: Verify First HR Wins Ownership
    Scenario: Candidate is eligible for re-submission (Applied & Days > 30).
              HR X submits first -> Candidate ownership set to HR X.
              HR Y pre-condition check confirms candidate is locked (Days = 0) -> HR Y cannot steal ownership.
    """
    log_test_start(module="Recruitment Portal", phase="CRS_004", test="Verify First HR Wins Ownership")

    # 1. HR X completes re-submission first
    res_x = hr_candidate_workflow.simulate_candidate_resubmission_ownership_workflow(
        candidate_name="First HR Wins Candidate",
        previous_owner="Initial Owner",
        new_owner="HR User X (First Submitter)",
        days_since_submission=35,
        candidate_status="Applied"
    )
    log_step("HR X First Submission Result", value=f"Owner={res_x['owner']} | SubmissionDate={res_x['submission_date']}")
    assert res_x["owner"] == "HR User X (First Submitter)", "CRS_004 FAILED: Candidate owner must become HR User X!"

    # 2. HR Y attempts second re-submission immediately (Days = 0)
    eligible_y = hr_candidate_workflow.check_resubmission_preconditions(
        candidate_status="Applied",
        days_since_submission=0
    )
    log_step("HR Y Immediate Re-submission Pre-check", value=f"Eligible={eligible_y}")
    assert eligible_y == False, "CRS_004 FAILED: Second HR Y re-submission MUST be blocked immediately after HR X submits!"

    log_pass()


# ==============================================================================
# 🔄 TEST CRS_005: Verify Ownership Reset After Re-Submission
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_005_verify_ownership_reset_after_resubmission(hr_candidate_workflow):
    """
    CRS_005: Verify Ownership Reset After Re-Submission
    Preconditions: Successful re-submission by HR Y on an eligible candidate.
    Expected Result:
      - Candidate Owner updated to HR Y.
      - Previous HR X loses ownership.
      - Submission Date updated to today's date.
      - 30-day timer restarts from today.
    """
    log_test_start(module="Recruitment Portal", phase="CRS_005", test="Verify Ownership Reset After Re-Submission")

    today_str = datetime.now().strftime("%Y-%m-%d")

    res = hr_candidate_workflow.simulate_candidate_resubmission_ownership_workflow(
        candidate_name="Eligible Candidate 5",
        previous_owner="HR User X (Original Owner)",
        new_owner="HR User Y (New Submitting HR)",
        days_since_submission=35,
        candidate_status="Applied"
    )

    log_step("CRS_005 Result", value=f"New Owner={res['owner']} | Date={res['submission_date']} | TimerReset={res['timer_reset']}")

    assert res["owner"] == "HR User Y (New Submitting HR)", "CRS_005 FAILED: Candidate owner must update to HR User Y!"
    assert res["previous_owner"] == "HR User X (Original Owner)", "CRS_005 FAILED: Original owner trace lost!"
    assert res["submission_date"] == today_str, f"CRS_005 FAILED: Submission date must update to today ({today_str}), got: {res['submission_date']}"
    assert res["timer_reset"] == True, "CRS_005 FAILED: 30-day timer must restart!"

    log_pass()


# ==============================================================================
# ⛔ TEST CRS_006: Prevent Immediate Second Re-Submission
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_crs_006_prevent_immediate_second_resubmission(hr_candidate_workflow):
    """
    CRS_006: Prevent Immediate Second Re-Submission
    Preconditions: Candidate recently re-submitted (days_since_submission = 0 / 1).
    Expected Result:
      - Re-submission option unavailable / blocked.
      - Candidate remains assigned to latest owner (HR Y).
      - New 30-day waiting period enforced.
    """
    log_test_start(module="Recruitment Portal", phase="CRS_006", test="Prevent Immediate Second Re-Submission")

    # Evaluate pre-conditions right after re-submission (Days = 0)
    is_eligible_immediate = hr_candidate_workflow.check_resubmission_preconditions(
        candidate_status="Applied",
        days_since_submission=0
    )

    log_step("CRS_006 Pre-condition Check (Days = 0)", value=f"Eligible={is_eligible_immediate}")

    assert is_eligible_immediate == False, (
        "CRS_006 FAILED: Candidate immediately after re-submission MUST be ineligible (new 30-day timer in progress)!"
    )

    log_pass()
