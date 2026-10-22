"""
HRlens Portal — End-to-End Resignation Withdrawal & Buyout Conflict Lifecycle Test Suite.

Executes and verifies:
1. Employee Resignation Application & Withdrawal Lifecycle.
2. Conflict & Gating Validation:
   - Employee applies for both Buyout (Early Relieving Date) and Withdrawal request.
   - HR processes and approves the Buyout request.
   - System Gating Check: Verifies that after Buyout is processed, HR CANNOT perform
     any action over the Withdrawal request, and the Employee's withdrawal option is blocked.
"""

from datetime import datetime
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger
from workflows.hrlense_portal.resignation.employee_resignation_workflow import EmployeeResignationWorkflow
from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow

logger = logging.getLogger(__name__)

CANDIDATE_EMPLOYEES = [
    {
        "name": "Uttam Kumar",
        "user_key": "uttam_kumar",
        "hr_key": "tejaswini",
        "branch": "Varanasi",
    },
    {
        "name": "Sanidhy Tiwari",
        "user_key": "sanidhy",
        "hr_key": "tejaswini",
        "branch": "Varanasi",
    },
    {
        "name": "Radhika Nayak",
        "user_key": "radhika_nayak",
        "hr_key": "tejaswini",
        "branch": "Varanasi",
    },
]


@pytest.mark.ui
@pytest.mark.resignation
@pytest.mark.e2e_withdrawal_lifecycle
@pytest.mark.parametrize(
    "candidate_employee",
    CANDIDATE_EMPLOYEES,
    ids=[e["name"].lower().replace(" ", "_") for e in CANDIDATE_EMPLOYEES]
)
def test_buyout_approval_blocks_withdrawal_action(logged_in_page, request, candidate_employee):
    """
    Business Gating Test:
    Employee requests Buyout AND Withdrawal -> HR processes Buyout ->
    System enforces that NO action can be performed over Withdrawal request.
    """
    story = TestStoryLogger(
        "Buyout Approval Gating over Resignation Withdrawal",
        module="Resignation",
        phase="Gating & Conflict Resolution"
    )
    story.start()

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: RESOLVE CANDIDATE EMPLOYEE
    # ══════════════════════════════════════════════════════════════════════
    selected_emp = candidate_employee
    emp_opt = request.config.getoption("--employee", default=None)
    if emp_opt:
        match = next((e for e in CANDIDATE_EMPLOYEES if e["name"].lower() == emp_opt.lower()), None)
        if match:
            selected_emp = match

    emp_name = selected_emp["name"]
    emp_key = selected_emp["user_key"]
    hr_key = selected_emp.get("hr_key", "tejaswini")
    branch = selected_emp.get("branch", "Varanasi")

    logger.info("=" * 80)
    logger.info(f"TARGET EMPLOYEE: '{emp_name}' ({emp_key}) | Branch: {branch} | HR: {hr_key}")
    logger.info("=" * 80)
    story.log_step(
        "Resolve Candidate Employee",
        record=f"Employee: '{emp_name}' ({emp_key}) | HR: {hr_key}",
        expected="Candidate employee identified",
        actual=emp_name,
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: VERIFY ACTIVE RESIGNATION OR SUBMIT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 2] Checking active resignation state for '{emp_name}'...")
    emp_page, _ = logged_in_page(emp_key)
    emp_wf = EmployeeResignationWorkflow(emp_page)
    emp_wf.res_page.navigate_to_resignation()

    if not emp_wf.res_page.has_active_resignation():
        logger.info(f"Submitting fresh resignation for '{emp_name}'...")
        res_res = emp_wf.submit_resignation_workflow(
            reason="1",
            stay_connected=True,
            share_suggestions=False,
            confirm=True
        )
        story.log_step(
            "Submit Resignation",
            record=f"Resignation submitted. Toast: '{res_res.get('toast', '')}'",
            expected="Resignation submitted",
            actual="Submitted",
            status="PASS"
        )
    else:
        logger.info(f"Active resignation already present for '{emp_name}'.")
        story.log_step(
            "Verify Active Resignation",
            record=f"Active resignation found for '{emp_name}'",
            expected="Active resignation present",
            actual="Present",
            status="PASS"
        )

    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: EMPLOYEE REQUESTS BUYOUT (EARLY RELIEVING DATE)
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 3] Employee '{emp_name}' requesting Buyout (Early Relieving Date)...")
    emp_wf.res_page.navigate_to_resignation()
    emp_wf.res_page.click_status_tab()

    early_date = datetime.now().strftime("%Y-%m-%d")
    is_date_visible = emp_wf.res_page.is_early_relieving_date_input_visible(timeout=3000)
    buyout_toast = ""

    if is_date_visible:
        buyout_toast = emp_wf.request_early_relieving_workflow(early_date)
        logger.info(f"Employee Buyout submission result toast: '{buyout_toast}'")
        story.log_step(
            "Employee Request Buyout",
            record=f"Requested Early Relieving Date: {early_date} | Toast: '{buyout_toast}'",
            expected="Buyout request submitted",
            actual=buyout_toast or "Requested",
            status="PASS"
        )
    else:
        logger.info(f"Early Relieving Date input not visible (already submitted or past initial state)")
        story.log_step(
            "Employee Request Buyout",
            record="Early Relieving Date input already processed or not visible",
            expected="Buyout state checked",
            actual="Checked",
            status="PASS"
        )

    # ══════════════════════════════════════════════════════════════════════
    # STEP 4: EMPLOYEE ATTEMPTS / SUBMITS WITHDRAWAL REQUEST SIMULTANEOUSLY
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 4] Employee '{emp_name}' attempting to submit Withdrawal request concurrently...")
    emp_wf.res_page.navigate_to_resignation()
    emp_wf.res_page.click_status_tab()

    is_withdraw_visible = emp_wf.res_page.is_withdrawal_button_visible(timeout=3000)
    withdraw_res = {"visible": is_withdraw_visible, "toast": ""}

    if is_withdraw_visible:
        logger.info(f"'Request Withdrawal' button is VISIBLE. Submitting withdrawal request...")
        withdraw_res = emp_wf.request_resignation_withdrawal_workflow()
        logger.info(f"Concurrent Withdrawal Submission Result: {withdraw_res}")
        story.log_step(
            "Concurrent Withdrawal Submission",
            record=f"Withdrawal submitted alongside Buyout. Toast: '{withdraw_res.get('toast', '')}'",
            expected="Withdrawal request submitted concurrently",
            actual=withdraw_res.get("toast", "Submitted"),
            status="PASS"
        )
    else:
        logger.info(f"'Request Withdrawal' button is not visible at this stage (visible={is_withdraw_visible}).")
        story.log_step(
            "Concurrent Withdrawal Submission",
            record="Withdrawal button not visible (UI may prohibit dual submission)",
            expected="Withdrawal submission attempted",
            actual=f"Visible: {is_withdraw_visible}",
            status="PASS"
        )

    # ══════════════════════════════════════════════════════════════════════
    # STEP 5: HR PROCESSES AND APPROVES BUYOUT REQUEST
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 5] HR ({hr_key}) navigating to /resignation-approval to process Buyout...")
    hr_page, _ = logged_in_page(hr_key)
    hr_wf = HrResignationWorkflow(hr_page)
    hr_wf.res_page.navigate_to_hr_resignation_approval()
    hr_wf.res_page.search_employee_in_hr_table(emp_name)

    status_before_buyout = hr_wf.res_page.get_hr_table_employee_status(emp_name)
    logger.info(f"HR Table Status before processing Buyout for '{emp_name}': '{status_before_buyout}'")

    hr_buyout_toast = ""
    if "buyout requested" in status_before_buyout.lower() or "buyout" in status_before_buyout.lower():
        hr_buyout_toast = hr_wf.process_buyout_request_workflow(employee_name=emp_name, process=True)
        logger.info(f"HR Process Buyout Result Toast: '{hr_buyout_toast}'")
        story.log_step(
            "HR Process Buyout",
            record=f"Status: '{status_before_buyout}' -> Buyout Processed. Toast: '{hr_buyout_toast}'",
            expected="Buyout approved by HR",
            actual=hr_buyout_toast or "Processed",
            status="PASS"
        )
    else:
        logger.info(f"Employee status is '{status_before_buyout}' (not 'BUYOUT REQUESTED'). Checking drawer...")
        drawer_opened = hr_wf.res_page.open_hr_buyout_request_drawer(emp_name)
        if drawer_opened:
            hr_buyout_toast = hr_wf.res_page.process_or_reject_hr_buyout(process=True)
            logger.info(f"HR Process Buyout from Drawer: '{hr_buyout_toast}'")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 6: VERIFICATION — HR CANNOT PERFORM ACTION OVER WITHDRAW REQUEST
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 6 - GATING AUDIT] Verifying HR CANNOT perform action over Withdraw Request...")
    hr_wf.res_page.navigate_to_hr_resignation_approval()
    hr_wf.res_page.search_employee_in_hr_table(emp_name)

    post_buyout_status = hr_wf.res_page.get_hr_table_employee_status(emp_name)
    logger.info(f"HR Table Status post-buyout processing: '{post_buyout_status}'")

    # Inspect Actions dropdown menu
    available_actions = hr_wf.get_hr_available_actions_workflow(emp_name)
    logger.info(f"HR Available Actions Menu Items for '{emp_name}': {available_actions}")

    has_withdraw_action = any(
        "withdraw" in act.lower() or "approve withdraw" in act.lower() or "reject withdraw" in act.lower()
        for act in available_actions
    )

    story.log_step(
        "HR Withdrawal Action Gating Verification",
        record=f"Status: '{post_buyout_status}' | Actions: {available_actions}",
        expected="Actions menu MUST NOT contain any action for Withdrawal approval/rejection",
        actual=f"Withdrawal Action Present: {has_withdraw_action} (Actions: {available_actions})",
        status="PASS" if not has_withdraw_action else "FAIL"
    )

    # HARD GATING ASSERTION: HR cannot perform action over withdraw request
    assert not has_withdraw_action, (
        f"GATING VIOLATION [FRD RULE]: HR should NOT be able to perform action over Withdraw request "
        f"after Buyout has been processed! Found conflicting actions: {available_actions}"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STEP 7: VERIFICATION — EMPLOYEE CANNOT PERFORM WITHDRAWAL AFTER BUYOUT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STEP 7 - EMPLOYEE GATING AUDIT] Verifying Employee CANNOT withdraw after Buyout...")
    emp_page_verify, _ = logged_in_page(emp_key)
    emp_wf_verify = EmployeeResignationWorkflow(emp_page_verify)
    emp_wf_verify.res_page.navigate_to_resignation()
    emp_wf_verify.res_page.click_status_tab()

    emp_withdraw_btn_visible = emp_wf_verify.res_page.is_withdrawal_button_visible(timeout=3000)
    logger.info(f"Employee 'Request Withdrawal' button visibility post-buyout: {emp_withdraw_btn_visible}")

    story.log_step(
        "Employee Withdrawal Button Gating Verification",
        record=f"Withdrawal Button Visible: {emp_withdraw_btn_visible}",
        expected="'Request Withdrawal' button must be HIDDEN or DISABLED after Buyout",
        actual=f"Visible: {emp_withdraw_btn_visible}",
        status="PASS" if not emp_withdraw_btn_visible else "FAIL"
    )

    # HARD GATING ASSERTION: Employee cannot withdraw after buyout processed
    assert not emp_withdraw_btn_visible, (
        f"GATING VIOLATION [FRD RULE]: Employee should NOT have 'Request Withdrawal' option "
        f"after HR has processed Buyout!"
    )

    story.finish()
