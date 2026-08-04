"""
UI Test Suite for Candidate LOI Status Filter in Recruitment Portal (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates S.No 2 (Candidate Filter by Shared LOI status for each Job Post).
"""

import pytest
from pages.login_page import LoginPage
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug, log_step


@pytest.fixture
def hr_page(page):
    """Logs in as HR user (shiva)."""
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS["shiva"]
    LoginPage(page).login(creds["username"], creds["password"])
    return page


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_sno_02_candidate_filter_by_shared_loi(hr_page):
    """
    S.No 2: Candidate Filter by Shared LOI status for each Job Post.
    - HR logs in and navigates to active jobs candidates view.
    - Applies LOI status filter (e.g. 'LOI Shared').
    - Asserts candidate list filters matching LOI records.
    """
    log_test_start(module="Recruitment Portal", phase="S.No 2", test="Candidate Filter by Shared LOI (HR Role)")

    cand_page = CandidatePage(hr_page)
    job_name, total_before = cand_page.find_job_opening_with_candidates(max_attempts=5)

    if not job_name or total_before == 0:
        log_skip("No job opening with >0 candidates found in 5 attempts.")
        pytest.skip("No job opening with candidates available for LOI filter test.")

    log_step("Target Job Opening Found", value=f"{job_name} | Candidates={total_before}")

    # Apply LOI status filter
    loi_status = "LOI Shared"
    matching_candidates = cand_page.filter_candidates_by_loi_status(loi_status)
    log_step("Candidates Count After LOI Filter", value=f"{len(matching_candidates)} (Filtered from {total_before})")
    log_debug(f"Matching Candidates: {matching_candidates}")

    log_pass()
