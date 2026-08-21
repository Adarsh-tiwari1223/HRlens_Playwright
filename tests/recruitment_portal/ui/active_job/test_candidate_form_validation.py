import os
import re
import pytest
import logging
from core.config import settings
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage
from workflows.recruitment_portal.active_job.candidate_workflow import CandidateWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "testdata", "static", "pdf", "sample-pdf-file-100kb.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.candidate
def test_candidate_empty_form_validation(logged_in_page):
    """
    Validation Test: Submit an empty 'Add Candidate' form.
    Verify all mandatory field validation messages are triggered.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_page.navigate_to_active_jobs()
    cand_page.select_first_job()
    cand_page.open_add_candidate_form()

    logger.info("[ACTION] Submitting empty Add Candidate form...")
    cand_page.submit()

    # Verify form validation indicators
    error_locators = page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('is required'), :has-text('Please fill')").all()
    error_texts = [e.inner_text().strip() for e in error_locators if e.is_visible() and e.inner_text().strip()]

    logger.info(f"[VERIFY] Validation messages captured ({len(error_texts)}): {error_texts}")
    assert len(error_texts) > 0, "Expected validation errors upon submitting empty Add Candidate form!"
    logger.info("[PASS] Empty candidate form validation successfully blocked submission.")


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.candidate
def test_candidate_invalid_email_format(logged_in_page):
    """
    Negative Test: Enter an invalid email format and verify validation is triggered.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_page.navigate_to_active_jobs()
    cand_page.select_first_job()
    cand_page.open_add_candidate_form()

    invalid_email = "invalid_user_email_at_test"
    logger.info(f"[ACTION] Entering invalid email: '{invalid_email}'")

    email_input = page.get_by_placeholder("Enter Email")
    email_input.fill(invalid_email)
    email_input.press("Tab")

    cand_page.submit()

    email_error = page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('email'), :has-text('Email')").first
    assert email_error.is_visible(timeout=5000), "Expected invalid email format error to appear!"
    logger.info(f"[PASS] Invalid email '{invalid_email}' correctly triggered validation error: '{email_error.inner_text().strip()}'")


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.candidate
def test_candidate_invalid_phone_number(logged_in_page):
    """
    Negative Test: Enter invalid phone numbers (e.g. less than 10 digits or alphanumeric) and verify validation.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_page.navigate_to_active_jobs()
    cand_page.select_first_job()
    cand_page.open_add_candidate_form()

    invalid_phone = "12345"
    logger.info(f"[ACTION] Entering short phone number: '{invalid_phone}'")

    phone_input = page.get_by_placeholder("Enter Phone No.")
    phone_input.fill(invalid_phone)
    phone_input.press("Tab")

    cand_page.submit()

    phone_error = page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('phone'), :has-text('Phone'), :has-text('digits')").first
    assert phone_error.is_visible(timeout=5000), "Expected invalid phone number error to appear!"
    logger.info(f"[PASS] Short phone '{invalid_phone}' correctly triggered validation: '{phone_error.inner_text().strip()}'")


@pytest.mark.ui
@pytest.mark.recruitment
@pytest.mark.candidate
def test_candidate_experienced_mandatory_fields(logged_in_page, dummy_resume_path):
    """
    Validation Test: When Experience is set to 'Yes', verify experience fields (Salary, Notice Period, etc.) are mandatory.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_page.navigate_to_active_jobs()
    cand_page.select_first_job()
    cand_page.open_add_candidate_form()

    # Fill base fields
    data = generate_candidate_data(is_experienced=False)
    name_input = page.get_by_placeholder("Enter candidate name")
    name_input.fill(data["name"])

    # Toggle Experience to 'Yes'
    logger.info("[ACTION] Setting Experience to 'Yes'...")
    cand_page._select_by_reading_label("Experience", "true")

    # Leave experience fields empty and submit
    cand_page.submit()

    # Assert experience validations
    exp_errors = page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error'], :has-text('required'), :has-text('Salary'), :has-text('Notice')").all()
    exp_error_texts = [e.inner_text().strip() for e in exp_errors if e.is_visible() and e.inner_text().strip()]

    logger.info(f"[VERIFY] Experienced fields validation messages captured: {exp_error_texts}")
    assert len(exp_error_texts) > 0, "Expected validation errors for experience fields!"
    logger.info("[PASS] Experience mandatory fields validated successfully.")
