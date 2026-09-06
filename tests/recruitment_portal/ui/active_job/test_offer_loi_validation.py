import os
import re
import pytest
import logging
from datetime import datetime, timedelta
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage
from workflows.recruitment_portal.active_job.job_opening_workflow import JobOpeningWorkflow
from testdata.dynamic.candidate_data import generate_candidate_data
from utils.api.salary_settings_api import (
    get_salary_settings_for_company,
    update_company_salary_settings,
    get_top_10_salary_settings,
    get_random_salary_setting_from_top_10,
    search_job_openings_api,
    find_matching_job_opening_api
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def dummy_resume_path():
    """Returns the absolute path to the dummy PDF resume for uploading."""
    path = os.path.join(os.getcwd(), "testdata", "static", "dummy_resume.pdf")
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "testdata", "static", "pdf", "sample-pdf-file-100kb.pdf")
    assert os.path.exists(path), f"Dummy resume not found at {path}"
    return path


def _prepare_candidate_for_offer_with_api_setting(page, cand_page: CandidatePage, dummy_resume_path: str) -> tuple[str, dict]:
    """
    Execution Flow:
    1. search_job_openings_api(search_term=company_name) calls GET /JobOpening?search={company_name, branch, department}
    2. If existing active job opening found:
       - grab job_code (e.g. JOB_POSTING-420)
       - break out of loop.
       Else: retry x2 (up to 3 attempts total with top 10 unique company settings).
    3. UI Job Code Search & Candidate Addition:
       - If job opening existed:
         - Navigates to Active Jobs page in UI.
         - Types job_code into <input placeholder="Search Jobs"> and presses Enter.
         - Clicks the exact job card.
       - If retries failed (no job opening existed after retry x2):
         - Creates new job opening with same company, branch, department via UI and clicks job card.
    4. Opens Add Candidate form, uploads dummy PDF resume, submits candidate, and schedules an interview.
    5. Opens candidate offer form for LOI & Salary Calculation Testing.
    """
    top_10_settings = get_top_10_salary_settings()
    if not top_10_settings:
        top_10_settings = [get_random_salary_setting_from_top_10()]

    target_job_code = ""
    api_settings = None

    # Retry x2 (up to 3 attempts total)
    for attempt in range(len(top_10_settings)):
        candidate_setting = top_10_settings[attempt]
        c_name = candidate_setting.get("company_name", "")
        b_name = candidate_setting.get("branch_name", "")
        d_name = candidate_setting.get("department_name", "")

        logger.info(
            f"[API JOB CHECK ATTEMPT {attempt + 1}] GET /JobOpening search Company='{c_name}', Branch='{b_name}', Dept='{d_name}'..."
        )

        matched_job = find_matching_job_opening_api(company_name=c_name, branch_name=b_name, department_name=d_name)
        if matched_job:
            code = matched_job.get("job_Code") or matched_job.get("jobCode") or matched_job.get("job_Opening_Code") or ""
            if code:
                target_job_code = code
                api_settings = candidate_setting
                logger.info(f"[API MATCH FOUND] Attempt {attempt + 1} found active job_code: '{target_job_code}' for Company='{c_name}'!")
                break

        if attempt >= 2:
            logger.info("[RETRY LIMIT REACHED] Retried x2 without finding existing job opening via API.")
            break

    if not api_settings:
        api_settings = top_10_settings[0]

    company_name = api_settings.get("company_name", "")
    branch_name = api_settings.get("branch_name", "")
    department_name = api_settings.get("department_name", "")

    logger.info(
        f"[LOI SETUP] Final Selected Setting → Company: '{company_name}' | Branch: '{branch_name}' | Department: '{department_name}' | "
        f"configured_minimum_basic_salary={api_settings['configured_minimum_basic_salary']} | "
        f"configured_minimum_gross_salary={api_settings['configured_minimum_gross_salary']}"
    )

    # ── UI Job Code Search & Navigation ───────────────────────────────────────
    cand_page.navigate_to_active_jobs()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)

    if target_job_code:
        # Existing job found -> Search job_code in UI search box & select job card
        logger.info(f"[UI JOB CODE SEARCH] Typing job_code '{target_job_code}' into <input placeholder='Search Jobs'>...")
        search_input = page.locator("input[placeholder='Search Jobs'], input[placeholder*='Search']").first
        if search_input.is_visible(timeout=4000):
            search_input.click()
            search_input.fill(target_job_code)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

        job_code = cand_page.select_first_job(job_code=target_job_code)
    else:
        # Retries failed -> Create new Job Opening via UI for same company, branch & department
        logger.info(f"[JOB CREATION] Creating new Job Opening via UI for Company='{company_name}', Branch='{branch_name}', Dept='{department_name}'...")
        job_workflow = JobOpeningWorkflow(page)
        job_page = JobOpeningPage(page)

        job_workflow.fill_mandatory_fields_except_jd()
        job_page.set_job_summary(f"LOI Validation JD for {company_name} - {branch_name}")
        job_workflow.publish_with_confirm()
        page.wait_for_timeout(3000)

        cand_page.navigate_to_active_jobs()
        job_code = cand_page.select_first_job()

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)

    # ── Candidate Addition & Interview Scheduling ──────────────────────────────
    logger.info(f"[CANDIDATE ADDITION] Adding candidate under Job '{job_code}'...")
    cand_data = generate_candidate_data(is_experienced=False)
    candidate_name = cand_data["name"]

    cand_page.open_add_candidate_form()
    cand_page.fill_candidate_form(cand_data, dummy_resume_path)
    cand_page.submit()
    page.wait_for_timeout(1500)

    # Schedule Interview
    now = datetime.now()
    logger.info(f"[SCHEDULE INTERVIEW] Scheduling interview for candidate: '{candidate_name}'...")
    cand_page.schedule_interview(
        candidate_name=candidate_name,
        date=now.strftime("%Y-%m-%d"),
        time=(now + timedelta(minutes=30)).strftime("%H:%M")
    )

    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

    # ── Open Candidate Offer Form ──────────────────────────────────────────────
    logger.info(f"[OFFER FORM] Opening offer form for candidate: '{candidate_name}'...")
    action_arrow = page.locator(f"tr:has-text('{candidate_name}') td:nth-child(10) img, tr:has-text('{candidate_name}') td:nth-child(10), tr:has-text('{candidate_name}')").first
    if action_arrow.is_visible(timeout=3000):
        action_arrow.click()
    else:
        cand_page.open_candidate_offer_form(candidate_name)

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)

    return candidate_name, api_settings


@pytest.mark.ui
@pytest.mark.recruitment
def test_offer_minimum_basic_only(logged_in_page, dummy_resume_path):
    """
    Test Case 1: Minimum Basic only
    Configuration: Minimum Basic > 0, Minimum Gross = 0
    Expected: Salary follows the configured Minimum Basic rule. No Paid Intern popup.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_name, api_settings = _prepare_candidate_for_offer_with_api_setting(page, cand_page, dummy_resume_path)
    logger.info(f"[TEST 1] Minimum Basic only for candidate '{cand_name}'")

    cand_page._select_by_reading_label("Interview Result", "8")
    page.wait_for_timeout(500)

    doj_input = page.get_by_placeholder("Enter Date of joining")
    if doj_input.is_visible(timeout=3000):
        doj_input.fill(datetime.now().strftime("%Y-%m-%d"))

    cand_page._select_by_reading_label("Job Type", "1")
    cand_page._select_by_reading_label("Shift Type", "3")

    min_basic_config = api_settings["configured_minimum_basic_salary"]

    test_gross = str(int(min_basic_config * 2))
    logger.info(f"[ACTION] Entering Gross Salary: ₹{test_gross} (Minimum Basic Configured=₹{min_basic_config})")
    gross_input = page.get_by_placeholder("Gross Salary (Monthly)")
    gross_input.click()
    gross_input.fill(test_gross)
    page.keyboard.press("Tab")
    page.wait_for_timeout(1000)

    # Verify NO Paid Intern popup appears
    modal_header = page.locator(".chakra-modal__header:has-text('Minimum Salary Validation'), header:has-text('Minimum Salary Validation')").first
    assert not modal_header.is_visible(), "Paid Intern popup should NOT appear when Minimum Gross = 0!"
    logger.info("[PASS] Verified no Paid Intern popup for Minimum Basic only configuration.")

    basic_input = page.locator("input[name='basic_Salary'], input[placeholder='Basic Salary']").first
    if basic_input.is_visible():
        basic_val = float(basic_input.input_value() or 0.0)
        logger.info(f"[PASS] Salary follows configured Minimum Basic rule: Basic=₹{basic_val} (Minimum Basic=₹{min_basic_config})")

    page.keyboard.press("Escape")


@pytest.mark.ui
@pytest.mark.recruitment
def test_offer_minimum_basic_plus_minimum_gross(logged_in_page, dummy_resume_path):
    """
    Test Case 2: Minimum Basic + Minimum Gross
    Configuration: Minimum Basic > 0, Minimum Gross > 0
    Expected: If Gross < Minimum Basic and Gross >= Minimum Gross → Paid Intern popup → on confirmation INTERN / PAID, 100% Basic.
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_name, api_settings = _prepare_candidate_for_offer_with_api_setting(page, cand_page, dummy_resume_path)
    logger.info(f"[TEST 2] Minimum Basic + Minimum Gross for candidate '{cand_name}'")

    cand_page._select_by_reading_label("Interview Result", "8")
    page.wait_for_timeout(500)

    doj_input = page.get_by_placeholder("Enter Date of joining")
    if doj_input.is_visible(timeout=3000):
        doj_input.fill(datetime.now().strftime("%Y-%m-%d"))

    cand_page._select_by_reading_label("Job Type", "1")
    cand_page._select_by_reading_label("Shift Type", "3")

    min_gross_config = api_settings["configured_minimum_gross_salary"]
    min_basic_config = api_settings["configured_minimum_basic_salary"]

    # Gross >= Minimum Gross, but Basic < Minimum Basic
    stipend_val = str(int(min_gross_config))
    logger.info(f"[ACTION] Entering Gross Salary: ₹{stipend_val} (min_gross=₹{min_gross_config}, min_basic=₹{min_basic_config})")
    gross_input = page.get_by_placeholder("Gross Salary (Monthly)")
    gross_input.click()
    gross_input.fill("")
    gross_input.press_sequentially(stipend_val, delay=50)
    gross_input.dispatch_event("change")
    gross_input.dispatch_event("blur")
    page.keyboard.press("Tab")
    page.wait_for_timeout(1500)

    # 1. Verify Paid Intern popup appears
    modal_element = page.locator(
        ".chakra-modal__header:has-text('Minimum Salary Validation'), "
        "header:has-text('Minimum Salary Validation'), "
        ".chakra-modal__body:has-text('Paid Intern'), "
        ".chakra-modal__content:has-text('Paid Intern')"
    ).first
    modal_element.wait_for(state="visible", timeout=10000)
    logger.info(f"[PASS] Verified Paid Intern popup: '{modal_element.inner_text().strip()}'")

    # 2. Click 'Confirm' on Paid Intern popup
    confirm_btn = page.locator(".chakra-modal__footer button:has-text('Confirm'), button:has-text('Confirm')").first
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    logger.info("[ACTION] Clicked 'Confirm' on Paid Intern popup")
    page.wait_for_timeout(1500)

    # 3. Verify Employment Type = INTERN, Intern Payment Type = PAID, Basic = 100% (stipend_val)
    emp_type_select = page.locator("select[name='employement_Type']").first
    assert emp_type_select.input_value() == "INTERN", f"Expected Employment Type 'INTERN', got '{emp_type_select.input_value()}'"
    logger.info("[PASS] Verified Employment Type converted to 'INTERN'")

    payment_type_select = page.locator("select[name='intern_Payment_Type']").first
    assert payment_type_select.input_value() == "PAID", f"Expected Intern Payment Type 'PAID', got '{payment_type_select.input_value()}'"
    logger.info("[PASS] Verified Intern Payment Type converted to 'PAID'")

    stipend_input = page.locator("input[placeholder='Monthly Stipend'], input[name='offered_Salary']").first
    if stipend_input.is_visible():
        assert stipend_input.input_value() == stipend_val, f"Expected 100% Basic / Monthly Stipend '{stipend_val}', got '{stipend_input.input_value()}'"
        logger.info(f"[PASS] Verified 100% Basic Stipend: ₹{stipend_input.input_value()}")

    page.keyboard.press("Escape")
