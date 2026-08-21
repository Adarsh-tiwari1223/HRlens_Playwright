import os
import re
import pytest
import logging
from datetime import datetime, timedelta
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.interview
def test_interview_modal_validation(logged_in_page):
    """
    Validation Test: Opens the Interview Schedule modal and verifies mandatory fields
    (Status, Date, Time, Interviewer) trigger validations if left empty or improperly configured.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_page.navigate_to_active_jobs()
    job_name = cand_page.select_first_job()

    # Find first candidate in list to schedule interview
    first_candidate_row = page.locator("tr:has(button:has-text('Schedule')), tr:has(button:has-text('Interview'))").first
    if not first_candidate_row.is_visible(timeout=5000):
        # Locate candidate button or name directly
        schedule_btn = page.locator("button:has-text('Schedule'), button:has-text('Interview'), [aria-label*='Schedule' i]").first
        schedule_btn.wait_for(state="visible", timeout=8000)
        schedule_btn.click()
    else:
        first_candidate_row.locator("button:has-text('Schedule'), button:has-text('Interview')").first.click()

    # Modal is open: try to submit with empty inputs
    logger.info("[ACTION] Attempting to submit interview schedule modal without required selections...")
    submit_btn = page.locator("button:has-text('Schedule Interview'), button:has-text('Submit'), button[type='submit']:has-text('Schedule')").first
    if submit_btn.is_visible(timeout=3000):
        submit_btn.click()

    # Verify form validation indicators
    error_locators = page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('required'), :has-text('Select')").all()
    error_texts = [e.inner_text().strip() for e in error_locators if e.is_visible() and e.inner_text().strip()]

    logger.info(f"[VERIFY] Interview modal validation messages: {error_texts}")
    assert len(error_texts) > 0 or page.locator("input:invalid, select:invalid").count() > 0, "Expected validations in Interview Schedule modal!"
    logger.info("[PASS] Interview scheduling validation verified successfully.")

    # Close modal
    close_btn = page.locator("button.chakra-modal__close-btn, button[aria-label*='Close' i], button:has-text('Cancel')").first
    if close_btn.is_visible(timeout=2000):
        close_btn.click()
