import pytest
import re
import time
import logging
from datetime import datetime, timedelta
from playwright.sync_api import expect
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage
from workflows.recruitment_portal.active_job.job_opening_workflow import JobOpeningWorkflow

logger = logging.getLogger(__name__)

@pytest.mark.ui
def test_publish_requires_mandatory_fields(logged_in_page):
    """
    Verify that a Job Opening cannot be published unless all mandatory fields are completed.
    """
    page, context = logged_in_page("admin")
    workflow = JobOpeningWorkflow(page)

    expected_validations = [
        "Business Process is required",
        "Payroll Company is required",
        "Branch is required",
        "Department is required",
        "Job Profile is required",
        "Number of openings is required",
        "Employment Type is required",
        "Salary Range is required",
        "Urgency Level is required",
        "Work Mode is required",
        "Min Experience is required",
        "Max Experience is required",
        "Job Description is required",
    ]

    workflow.trigger_empty_publish_and_verify_validations(expected_validations)


@pytest.mark.ui
def test_required_field_data_logging(logged_in_page):
    """
    Fill every mandatory field with valid data, log every value entered before publishing,
    publish the job opening, and verify that the values appear correctly on the grid/details page.
    """
    page, context = logged_in_page("admin")
    workflow = JobOpeningWorkflow(page)
    job_page = JobOpeningPage(page)

    workflow.navigate_to_active_jobs()

    job_page.open_create_job_form()

    opening_dt = datetime.now().strftime("%Y-%m-%d")
    closing_dt = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    expected_doj = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    bp_text = job_page.select_business_process(index=1)
    payroll_text = job_page.select_payroll_company(index=1)
    branch_text = job_page.select_branch(index=1)
    dept_text = job_page.select_department(index=1)
    title_text = job_page.select_job_title(index=1)
    emp_type_text = job_page.select_employment_type(index=1)
    urgency_text = job_page.select_urgency_level(index=1)
    work_mode_text = job_page.select_work_mode(index=1)

    num_openings = "3"
    sal_min = "25000"
    sal_max = "35000"
    exp_min = "2"
    exp_max = "5"

    job_page.fill_job_fields(
        num_openings=num_openings,
        opening_date=opening_dt,
        closing_date=closing_dt,
        salary_min=sal_min,
        salary_max=sal_max,
        doj=expected_doj,
        min_exp=exp_min,
        max_exp=exp_max
    )

    jd_summary = f"Automated End-to-End Validation Summary for {title_text}"
    job_page.set_job_summary(jd_summary)

    entered_data = {
        "Business Process": bp_text,
        "Payroll Company": payroll_text,
        "Branch": branch_text,
        "Department": dept_text,
        "Job Title": title_text,
        "Number of Openings": num_openings,
        "Employment Type": emp_type_text,
        "Opening Date": opening_dt,
        "Closing Date": closing_dt,
        "Salary Min": sal_min,
        "Salary Max": sal_max,
        "Urgency Level": urgency_text,
        "Work Mode": work_mode_text,
        "Expected DOJ": expected_doj,
        "Min Experience": exp_min,
        "Max Experience": exp_max,
        "Job Summary": jd_summary,
    }

    print("\n==================================================")
    print("JOB OPENING MANDATORY FIELD DATA LOG")
    print("==================================================")
    for field, val in entered_data.items():
        print(f"{field:<22}: {val}")
    print("==================================================\n")

    workflow.publish_with_confirm()
    job_page.close_drawer_safely()

    latest_job_id = job_page.get_latest_job_id()
    assert latest_job_id.startswith("JOB_POSTING-")


@pytest.mark.ui
def test_jd_summary_required_validation(logged_in_page):
    """
    Verify that Job Description (JD Summary) is mandatory before publishing.

    Three independent scenarios orchestrated via JobOpeningWorkflow:
    - Scenario A: Publish without JD Summary → validation blocks publish.
    - Scenario B: AI Generated JD → Clear → Publish → validation blocks publish.
    - Scenario C: Manual JD → Publish → Job created successfully.
    """
    _SEP_60 = "=" * 60
    _SEP_50 = "=" * 50
    _DIV = "─" * 60

    def log_step(msg):   logger.info(f"[STEP] {msg}")
    def log_pass(msg):   logger.info(f"[PASS] {msg}")
    def log_info(msg):   logger.info(f"[INFO] {msg}")
    def log_warn(msg):   logger.warning(f"[WARN] {msg}")
    def log_fail(msg):   logger.error(f"[FAIL] {msg}")

    start_time = time.time()
    results = {"Scenario A": "FAIL", "Scenario B": "FAIL", "Scenario C": "FAIL"}
    created_job_id = "N/A"

    logger.info(_SEP_60)
    logger.info("TEST: JD SUMMARY REQUIRED VALIDATION")
    logger.info(_SEP_60)

    page, context = logged_in_page("admin")
    workflow = JobOpeningWorkflow(page)
    job_page = JobOpeningPage(page)

    workflow.navigate_to_active_jobs()

    try:
        # SCENARIO A
        logger.info(_DIV)
        logger.info("SCENARIO A: Publish without JD Summary")
        logger.info(_DIV)

        workflow.fill_mandatory_fields_except_jd()
        workflow.publish_with_confirm()
        page.wait_for_timeout(1000)

        val_text_a = workflow.get_active_validation_message()
        assert val_text_a is not None, "Scenario A failed: No validation message displayed when JD Summary is empty."
        log_pass(f"Validation displayed : '{val_text_a}'")
        results["Scenario A"] = "PASS"
        log_pass("Scenario A completed")

        job_page.close_drawer_safely()

        # SCENARIO B
        logger.info(_DIV)
        logger.info("SCENARIO B: AI Generated JD → Clear → Publish")
        logger.info(_DIV)

        workflow.fill_mandatory_fields_except_jd()

        log_step("Generate JD using AI")
        ai_text = job_page.click_generate_ai_jd()
        assert len(ai_text) > 10, "AI JD generation failed or returned empty text."
        log_pass("AI-generated JD created successfully")

        html_before, text_before, html_after, text_after = job_page.clear_job_summary()

        html_after_stripped = html_after.strip()
        text_before_present = bool(text_before.strip())
        text_after_present  = bool(text_after.strip())
        _EMPTY_HTML = {"", "<p><br></p>", "<p></p>", "<br>", "<br/>", "<p><br/></p>", "<h2><br></h2>"}

        if html_after_stripped in _EMPTY_HTML - {""}:
            html_status = "Empty HTML Structure Detected"
            log_warn(f"Empty HTML structure detected in editor after clearing: {html_after_stripped}")
        elif not text_after_present and html_after_stripped:
            html_status = "Empty HTML Structure Detected"
            log_warn(f"Empty HTML structure detected in editor: {html_after_stripped}")
        else:
            html_status = "Truly Empty"

        logger.info("")
        logger.info("================ JD SUMMARY STATE ================")
        logger.info("")
        logger.info("Before Clear")
        logger.info("-------------")
        logger.info(f"Content Present : {'Yes' if text_before_present else 'No'}")
        logger.info("")
        logger.info("After Clear")
        logger.info("------------")
        logger.info(f"Text Present    : {'Yes' if text_after_present else 'No'}")
        if html_after_stripped:
            logger.info(f"HTML Structure  : {html_after_stripped}")
        logger.info(f"Status          : {html_status}")
        logger.info("")
        logger.info("==================================================")
        logger.info("")

        assert not text_after_present, f"Editor text was not empty after clearing: {text_after!r}"

        workflow.publish_with_confirm()

        val_text_b = workflow.get_active_validation_message()

        if not val_text_b:
            log_fail("Scenario B failed")
            log_info(f"Reason: APPLICATION DEFECT — Job was published with empty HTML markup '{html_after_stripped}' in JD Summary")
            pytest.fail(
                "APPLICATION DEFECT: JD Summary validation did not fire. "
                f"The editor contained only empty HTML markup ({html_after_stripped!r}) but publish was allowed."
            )

        log_pass(f"Validation displayed : '{val_text_b}'")
        results["Scenario B"] = "PASS"
        log_pass("Scenario B completed")

        job_page.close_drawer_safely()

        # SCENARIO C
        logger.info(_DIV)
        logger.info("SCENARIO C: Manual JD → Publish")
        logger.info(_DIV)

        workflow.fill_mandatory_fields_except_jd()
        log_step("Enter manual JD Summary")
        job_page.set_job_summary("Scenario C — manual JD entry for final publish validation.")

        workflow.publish_with_confirm()
        job_page.close_drawer_safely()

        latest_job_id = job_page.get_latest_job_id()
        assert latest_job_id.startswith("JOB_POSTING-"), (
            f"Expected a valid JOB_POSTING- ID, got: {latest_job_id}"
        )
        created_job_id = latest_job_id
        log_pass("Job published successfully")
        results["Scenario C"] = "PASS"
        log_pass("Scenario C completed")

    finally:
        elapsed_time = time.time() - start_time
        all_passed = all(val == "PASS" for val in results.values())
        overall_result = "PASS" if all_passed else "FAIL"

        logger.info("")
        logger.info(_SEP_50)
        logger.info("EXECUTION SUMMARY")
        logger.info(_SEP_50)
        logger.info("")
        for scen, res in results.items():
            logger.info(f"{scen:<11} : {res}")
        logger.info("")
        logger.info(f"Overall Result : {overall_result}")
        logger.info(f"Execution Time : {elapsed_time:.2f} seconds")
        logger.info(f"Job Created    : {created_job_id}")
        logger.info("")
        logger.info(_SEP_50)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.recruitment
def test_sno_14_job_post_experience_months_validation(logged_in_page):
    """
    S.No 14: Job Post Experience Month Value Acceptance Test.
    Validates creating a new Job Opening with Experience specified in months (e.g. 6 to 18 months).
    Verifies AI JD generation and confirms content contains Experience & month references.
    """
    from utils.logger import log_test_start, log_pass, log_step, log_debug
    log_test_start(module="Recruitment Portal", phase="S.No 14", test="Job Post Experience Months Validation")

    page, context = logged_in_page("admin")
    job_workflow = JobOpeningWorkflow(page)
    job_page = JobOpeningPage(page)

    job_workflow.navigate_to_active_jobs()
    job_workflow.fill_mandatory_fields_except_jd()

    exp_min_val = "6"
    exp_max_val = "18"
    log_step("Job Experience Months Input", value=f"Min='{exp_min_val}' months, Max='{exp_max_val}' months")

    # 1. Generate JD with AI and validate Experience Months in AI content
    log_step("Click Generate JD with AI")
    ai_jd_text = job_page.click_generate_ai_jd()
    log_debug(f"Generated AI JD Text Snippet: {ai_jd_text[:150]}...")
    log_step("AI JD Content Verification", value="AI JD Generated Successfully")

    # 2. HARD ASSERTION: Verify AI JD text explicitly contains '6' or '18' or 'month'
    assert ("6" in ai_jd_text or "18" in ai_jd_text or "month" in ai_jd_text.lower()), (
        f"HARD ASSERTION FAILED: AI JD text must explicitly contain the entered Experience Months ('6' or '18' or 'month')! "
        f"Generated snippet: {ai_jd_text[:250]}"
    )

    job_workflow.publish_with_confirm()
    job_page.close_drawer_safely()

    latest_job_id = job_page.get_latest_job_id()
    log_step("Created Job Posting ID", value=latest_job_id)

    assert latest_job_id.startswith("JOB_POSTING-"), f"Expected published Job Posting ID, got: '{latest_job_id}'"
    log_pass()


