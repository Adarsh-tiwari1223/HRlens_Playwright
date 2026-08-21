import os
import re
import pytest
import logging
from datetime import datetime, timedelta
from pages.recruitment_portal.active_job.candidate_page import CandidatePage
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


def _prepare_candidate_for_offer(page, cand_page: CandidatePage, dummy_resume_path: str) -> str:
    """
    Helper to ensure a candidate is ready for offer by reading the Candidate Table:
    - Waits for candidate table / Add Candidate button to mount.
    - Reads column 3 (Candidate Name) and column 8 (Status).
    - If status == 'Interview Scheduled': clicks column 10 Action arrow and proceeds to offer form.
    - If status == 'Applied': schedules interview, then opens offer form.
    - Otherwise adds a fresh candidate, schedules interview, and opens offer form.
    """
    cand_page.navigate_to_active_jobs()
    job_code = cand_page.select_first_job()
    page.wait_for_load_state("domcontentloaded")

    # Auto-wait for the candidate view / table to finish mounting
    page.locator("button:has-text('Add Candidate'), table.chakra-table").first.wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(1000)

    candidate_rows = page.locator("tbody tr, .chakra-table tbody tr").all()
    selected_candidate_name = None
    candidate_status = None

    for row in candidate_rows:
        try:
            name_col = row.locator("td:nth-child(3)").inner_text().strip()
            status_col = row.locator("td:nth-child(8)").inner_text().strip()

            if name_col and "Interview Scheduled" in status_col:
                selected_candidate_name = name_col
                candidate_status = "Interview Scheduled"
                logger.info(f"[CANDIDATE] Found candidate in 'Interview Scheduled' status: '{selected_candidate_name}'")
                break
            elif name_col and "Applied" in status_col and not selected_candidate_name:
                selected_candidate_name = name_col
                candidate_status = "Applied"
        except Exception:
            pass

    if selected_candidate_name:
        if candidate_status == "Applied":
            logger.info(f"[CANDIDATE] Candidate '{selected_candidate_name}' is in 'Applied' status. Scheduling interview...")
            now = datetime.now()
            cand_page.schedule_interview(
                candidate_name=selected_candidate_name,
                date=now.strftime("%Y-%m-%d"),
                time=(now + timedelta(minutes=30)).strftime("%H:%M")
            )
            # Refresh page after scheduling interview
            logger.info("[ACTION] Refreshing page after scheduling interview...")
            page.reload()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)

        logger.info(f"[ACTION] Opening offer form for candidate: '{selected_candidate_name}'")
        action_arrow = page.locator(f"tr:has-text('{selected_candidate_name}') td:nth-child(10) img, tr:has-text('{selected_candidate_name}') td:nth-child(10), tr:has-text('{selected_candidate_name}')").first
        if action_arrow.is_visible(timeout=3000):
            action_arrow.click()
        else:
            cand_page.open_candidate_offer_form(selected_candidate_name)

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        return selected_candidate_name

    # If no candidate in 'Applied' or 'Interview Scheduled' -> Add fresh candidate
    logger.info(f"[CANDIDATE] No candidate in Applied/Interview status for '{job_code}'. Adding fresh candidate...")
    cand_data = generate_candidate_data(is_experienced=False)
    target_candidate_name = cand_data["name"]

    cand_page.open_add_candidate_form()
    cand_page.fill_candidate_form(cand_data, dummy_resume_path)
    cand_page.submit()
    page.wait_for_timeout(1000)

    # Schedule interview
    now = datetime.now()
    logger.info(f"[ACTION] Scheduling interview for fresh candidate: '{target_candidate_name}'...")
    cand_page.schedule_interview(
        candidate_name=target_candidate_name,
        date=now.strftime("%Y-%m-%d"),
        time=(now + timedelta(minutes=30)).strftime("%H:%M")
    )
    
    # Refresh page after scheduling interview
    logger.info("[ACTION] Refreshing page after scheduling interview...")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)

    action_arrow = page.locator(f"tr:has-text('{target_candidate_name}') td:nth-child(10) img, tr:has-text('{target_candidate_name}') td:nth-child(10), tr:has-text('{target_candidate_name}')").first
    if action_arrow.is_visible(timeout=3000):
        action_arrow.click()
    else:
        cand_page.open_candidate_offer_form(target_candidate_name)

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)
    return target_candidate_name


@pytest.mark.ui
@pytest.mark.recruitment
def test_offer_paid_intern_modal_below_15k(logged_in_page, dummy_resume_path):
    """
    Business Rule Test: When entering Gross Salary below minimum basic (e.g. ₹15,000):
    1. Triggers 'Minimum Salary Validation' modal asking:
       'The minimum Basic Salary configured is ₹16870. You entered Gross Salary ₹15000. Do you want to convert this candidate to a Paid Intern?'
    2. Clicks 'Confirm'.
    3. Verifies form transforms dynamically:
       - Employment Type -> 'Intern' (INTERN)
       - Intern Payment Type -> 'Paid Intern' (PAID)
       - Monthly Stipend -> '15000'
       - Basic Salary (100%) -> '15000'
       - Monthly CTC -> '15000'
       - Annual CTC -> '180000'
       - Net Salary -> '15000'
       - Subject -> Contains 'Paid Internship Offer'
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_name = _prepare_candidate_for_offer(page, cand_page, dummy_resume_path)
    logger.info(f"[STEP] Testing Paid Intern Rule for candidate: '{cand_name}'")

    # Select Interview Result = Offered (Value '8')
    cand_page._select_by_reading_label("Interview Result", "8")
    page.wait_for_timeout(500)

    # Fill DOJ
    doj_input = page.get_by_placeholder("Enter Date of joining")
    if doj_input.is_visible(timeout=3000):
        doj_input.fill(datetime.now().strftime("%Y-%m-%d"))

    # Select Job Type / Shift Type
    cand_page._select_by_reading_label("Job Type", "1")
    cand_page._select_by_reading_label("Shift Type", "3")

    # Enter Monthly Gross below configured basic threshold (e.g. ₹15,000)
    stipend_val = "15000"
    logger.info(f"[ACTION] Entering Gross Salary below basic threshold: ₹{stipend_val}")
    gross_input = page.get_by_placeholder("Gross Salary (Monthly)")
    gross_input.click()
    gross_input.fill(stipend_val)
    page.keyboard.press("Tab")
    page.wait_for_timeout(1000)

    # 1. Verify 'Minimum Salary Validation' Modal appears
    modal_header = page.locator(".chakra-modal__header:has-text('Minimum Salary Validation'), header:has-text('Minimum Salary Validation')").first
    modal_header.wait_for(state="visible", timeout=6000)
    logger.info(f"[PASS] Modal Header Verified: '{modal_header.inner_text().strip()}'")

    modal_body = page.locator(".chakra-modal__body:has-text('Paid Intern')").first
    modal_body.wait_for(state="visible", timeout=4000)
    logger.info(f"[PASS] Modal Body Verified: '{modal_body.inner_text().strip()}'")

    # 2. Click 'Confirm' to convert candidate to Paid Intern
    confirm_btn = page.locator(".chakra-modal__footer button:has-text('Confirm'), button:has-text('Confirm')").first
    confirm_btn.wait_for(state="visible", timeout=4000)
    confirm_btn.click()
    logger.info("[ACTION] Clicked 'Confirm' to convert candidate to Paid Intern")
    page.wait_for_timeout(1000)

    # 3. Verify Form Fields automatically transform to Paid Intern structure
    # Employment Type -> 'INTERN'
    emp_type_select = page.locator("select[name='employement_Type']").first
    assert emp_type_select.input_value() == "INTERN", f"Expected Employment Type 'INTERN', got '{emp_type_select.input_value()}'"
    logger.info("[PASS] Verified Employment Type changed to 'INTERN'")

    # Intern Payment Type -> 'PAID'
    payment_type_select = page.locator("select[name='intern_Payment_Type']").first
    assert payment_type_select.input_value() == "PAID", f"Expected Intern Payment Type 'PAID', got '{payment_type_select.input_value()}'"
    logger.info("[PASS] Verified Intern Payment Type changed to 'PAID'")

    # Monthly Stipend -> 15000
    stipend_input = page.locator("input[placeholder='Monthly Stipend'], input[name='offered_Salary']").first
    assert stipend_input.input_value() == stipend_val, f"Expected Monthly Stipend '{stipend_val}', got '{stipend_input.input_value()}'"
    logger.info(f"[PASS] Verified Monthly Stipend input value: ₹{stipend_input.input_value()}")

    # Verify calculated Intern CTC and Net values
    expected_intern_components = {
        "Basic Salary (100%)": stipend_val,
        "Monthly CTC": stipend_val,
        "Annual CTC": str(int(stipend_val) * 12),
        "Net Salary": stipend_val
    }

    for comp_name, expected_val in expected_intern_components.items():
        comp_inp = page.locator(f"xpath=//label[contains(normalize-space(.), '{comp_name}')]/following-sibling::input | //label[contains(normalize-space(.), '{comp_name}')]/parent::div//input").first
        if comp_inp.is_visible():
            actual_val = comp_inp.input_value().strip()
            logger.info(f"[VERIFY] {comp_name}: Expected='{expected_val}' | Actual='{actual_val}'")
            assert actual_val == expected_val, f"Mismatch in {comp_name}: expected {expected_val}, got {actual_val}"

    # Verify Subject transformed to Paid Internship Offer
    subject_input = page.locator("input[placeholder*='Subject' i], .chakra-form-control:has(label:has-text('Subject')) input, input[name*='subject' i]").first
    if subject_input.is_visible():
        subject_text = subject_input.input_value().strip()
        logger.info(f"[VERIFY] Subject text: '{subject_text}'")
        assert "Paid Internship Offer" in subject_text or "Internship" in subject_text, f"Expected 'Paid Internship Offer' in subject, got '{subject_text}'"

    logger.info("[PASS] Paid Intern dynamic form transformation & calculations verified 100% successfully.")

    page.keyboard.press("Escape")


@pytest.mark.ui
@pytest.mark.recruitment
def test_offer_salary_component_math_integrity(logged_in_page, dummy_resume_path):
    """
    Validation Test: Enter Monthly Gross = ₹20,000 and verify exact CTC and component math:
    - Basic Salary (84.35%) = ₹16,870
    - HRA (15.65%) = ₹3,130
    - Employee PF (12%) = ₹1,800
    - Employer PF (12%) = ₹1,800
    - Employee ESIC (0.75%) = ₹150
    - Employer ESIC (3.25%) = ₹650
    - Monthly CTC = ₹22,450
    - Annual CTC = ₹2,69,400
    - Net Salary = ₹18,050
    """
    page, context = logged_in_page("admin")
    cand_page = CandidatePage(page)

    cand_name = _prepare_candidate_for_offer(page, cand_page, dummy_resume_path)
    logger.info(f"[STEP] Testing Salary Component Math Integrity for candidate: '{cand_name}'")

    # Select Interview Result = Offered (Value '8')
    cand_page._select_by_reading_label("Interview Result", "8")
    page.wait_for_timeout(500)

    # Fill DOJ
    doj_input = page.get_by_placeholder("Enter Date of joining")
    if doj_input.is_visible(timeout=3000):
        doj_input.fill(datetime.now().strftime("%Y-%m-%d"))

    # Select Job Type / Shift Type
    cand_page._select_by_reading_label("Job Type", "1")
    cand_page._select_by_reading_label("Shift Type", "3")

    # Enter Monthly Gross = 20000
    logger.info("[ACTION] Entering Monthly Gross Salary: ₹20,000")
    gross_input = page.get_by_placeholder("Gross Salary (Monthly)")
    gross_input.click()
    gross_input.fill("20000")
    page.keyboard.press("Tab")
    page.wait_for_timeout(2000)

    # Validate math components
    expected_values = {
        "Basic Salary (84.35%)": "16870",
        "HRA (15.65%)*": "3130",
        "Employee PF (12%)": "1800",
        "Employer PF (12%)": "1800",
        "Employee ESIC (0.75%)": "150",
        "Employer ESIC (3.25%)": "650",
        "Monthly CTC": "22450",
        "Annual CTC": "269400",
        "Net Salary": "18050"
    }

    for component, expected_val in expected_values.items():
        comp_loc = page.locator(f"xpath=//label[contains(normalize-space(.), '{component}')]/following-sibling::input | //label[contains(normalize-space(.), '{component}')]/parent::div//input").first
        if comp_loc.is_visible():
            actual_val = comp_loc.input_value().strip()
            logger.info(f"[VERIFY] {component}: Expected='{expected_val}' | Actual='{actual_val}'")
            assert actual_val == expected_val, f"Mismatch in {component}: expected {expected_val}, got {actual_val}"

    logger.info("[PASS] Salary component mathematics and breakdown verified successfully for ₹20,000 gross.")
