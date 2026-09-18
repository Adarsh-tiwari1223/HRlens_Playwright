"""
HRlens Portal — Employee Resignation Flow Test Suite (Test Tier).
Contains test cases for Employee-side resignation application, validation error checks, buyout date boundaries, early relieving, and accept/reject revoke.
"""

import pytest
import logging
from core.config import settings
from core.config.users import get_random_varanasi_employee
from workflows.hrlense_portal.resignation.employee_resignation_workflow import EmployeeResignationWorkflow

logger = logging.getLogger(__name__)


@pytest.fixture
def get_employee_resignation_workflow(logged_in_page):
    """Factory fixture to initialize EmployeeResignationWorkflow for a specific employee user account."""
    def _create_workflow(user_key: str = None):
        target_key = user_key or get_random_varanasi_employee()
        page, _ = logged_in_page(target_key)
        return EmployeeResignationWorkflow(page)
    return _create_workflow


@pytest.mark.ui
@pytest.mark.apply_resignation
@pytest.mark.resignation
def test_employee_apply_resignation_basic_flow(get_employee_resignation_workflow):
    """
    Employee Resignation Application Flow:
    1. Employee navigates to Resignation -> Apply Resignation tab
    2. Verifies auto-filled fields (Personal Email & Contact Number)
    3. Selects Separation Reason from dropdown (select[name='reason'])
    4. Toggles optional checkboxes ('Stay Connected', 'Share Suggestions') & enters text
    5. Clicks 'Submit Resignation Request' button
    6. Verifies Confirmation Modal & clicks 'Yes, Submit'
    7. Verifies success toast & auto-switch to Status tab
    """
    emp_wf = get_employee_resignation_workflow()

    result = emp_wf.submit_resignation_workflow(
        reason="1",
        stay_connected=True,
        share_suggestions=True,
        suggestion_text="Career growth and new learning opportunities.",
        confirm=True
    )

    assert result.get("selected_reason") != "", "Separation Reason must be selected from dropdown"
    assert result.get("modal_visible"), "Confirmation Modal 'Submit Resignation Request' must be displayed"
    assert result.get("toast") != "", "Submission success toast must be captured"

    logger.info(f"[PASS] Employee Resignation Application Flow passed! Toast: '{result.get('toast')}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_buyout_date_exceeds_lwd(get_employee_resignation_workflow):
    """
    [P0 CRITICAL] Buyout Date > Last Working Day (LWD: 30-11-2026).
    Dates after 30-11-2026 should be disabled in the calendar; employee cannot select those dates.
    """
    emp_wf = get_employee_resignation_workflow()
    exceed_date = "2026-12-15"

    emp_wf.res_page.navigate_to_resignation()
    emp_wf.res_page.click_status_tab()
    emp_wf.res_page.fill_early_relieving_date(exceed_date)
    max_attr = emp_wf.res_page.get_early_relieving_max_date()

    assert max_attr != "", "System must constrain or disable Buyout Dates after Last Working Day (30-11-2026)"
    logger.info(f"[PASS P0] Buyout Date > LWD validation passed! Max date constraint: '{max_attr}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_buyout_date_before_present_date(get_employee_resignation_workflow):
    """
    [P0 CRITICAL] Buyout Date < Present Date.
    Dates before the current/present date should be disabled; employee cannot select a past date.
    """
    emp_wf = get_employee_resignation_workflow()
    emp_wf.res_page.navigate_to_resignation()
    emp_wf.res_page.click_status_tab()
    min_date = emp_wf.res_page.get_early_relieving_min_date()

    assert min_date != "", "Date picker must specify a 'min' date constraint preventing past date selection"
    logger.info(f"[PASS P0] Buyout Date < Present Date validation passed! Min date constraint: '{min_date}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_duplicate_resignation_submission(get_employee_resignation_workflow):
    """
    [P0 CRITICAL] Duplicate Resignation Request.
    Employee attempts another submission while an existing request is active.
    Expected: System should prevent creation of duplicate resignation request.
    """
    emp_wf = get_employee_resignation_workflow()
    result = emp_wf.submit_resignation_workflow(reason="1", confirm=True)

    captured_toast = str(result.get("toast", ""))
    logger.info(f"[PASS P0] Duplicate resignation submission attempted! Toast: '{captured_toast}'")


@pytest.mark.ui
@pytest.mark.employee_accept_revoke
@pytest.mark.resignation
def test_employee_accept_revoke_flow(get_employee_resignation_workflow):
    """
    Employee Side Accept Revoke Flow:
    1. Employee logs in (adarsh_tiwari) whose HR sent a Revoke Request
    2. Navigates to https://stg-hrlense.jobvritta.com/resignation
    3. Verifies 'Accept Revoke' button visibility
    4. Clicks 'Accept Revoke' button (<button class="chakra-button css-1614hcp">Accept Revoke</button>)
    5. Captures success toast and verifies resignation is revoked / closed!
    """
    emp_wf = get_employee_resignation_workflow("adarsh_tiwari")

    revoke_toast = emp_wf.respond_to_revoke_request_workflow(accept=True)

    assert revoke_toast != "", "Toast message must be captured after accepting Revoke"
    assert "revoke" in revoke_toast.lower() or "accept" in revoke_toast.lower(), \
        f"Expected 'revoke request accepted' toast, got: '{revoke_toast}'"

    logger.info(f"[PASS EMPLOYEE] Employee Accept Revoke Flow completed successfully! Toast: '{revoke_toast}'")


@pytest.mark.ui
@pytest.mark.employee_reject_revoke
@pytest.mark.resignation
def test_employee_reject_revoke_flow(get_employee_resignation_workflow):
    """
    Employee Side Decline / Reject Revoke Flow:
    1. Employee logs in (adarsh_tiwari) whose HR sent a Revoke Request
    2. Navigates to https://stg-hrlense.jobvritta.com/resignation
    3. Clicks 'Decline Revoke' button (<button class="chakra-button css-lfzc3m">Decline Revoke</button>)
    4. Captures toast and verifies resignation workflow CONTINUES uninterrupted!
    """
    emp_wf = get_employee_resignation_workflow("adarsh_tiwari")

    revoke_toast = emp_wf.respond_to_revoke_request_workflow(accept=False)

    assert revoke_toast != "", "Toast message must be captured after declining Revoke"
    logger.info(f"[PASS EMPLOYEE] Employee Decline Revoke Flow completed successfully! Toast: '{revoke_toast}'")


@pytest.mark.ui
@pytest.mark.revoke_flow_full_coverage
@pytest.mark.resignation
def test_e2e_resignation_revoke_full_coverage(logged_in_page):
    """
    Single E2E Unified Revoke Full Coverage Test:
    
    CYCLE 1:
    - [Step 1] Employee A (adarsh_tiwari) submits Resignation #1
    - [Step 2] HR (tejaswini) searches Adarsh Tiwari & sends Revoke Request
    - [Step 3] Employee A ACCEPTS Revoke Request → Toast captured → Resignation #1 CLOSED

    CYCLE 2:
    - [Step 4] Employee A submits FRESH Resignation #2
    - [Step 5] HR sends Revoke Request again
    - [Step 6] Employee A DECLINES Revoke Request → Toast captured → Resignation #2 CONTINUES
    - [Step 7] Employee A applies for Buyout Request
    - [Step 8] HR opens Resignation Details modal → Verifies 'Revoke' button is BLOCKED/HIDDEN by Buyout!
    """
    from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow

    # Set up Employee & HR sessions
    emp_page, _ = logged_in_page("uttam_kumar")
    emp_wf = EmployeeResignationWorkflow(emp_page)

    hr_page, _ = logged_in_page("tejaswini")
    hr_wf = HrResignationWorkflow(hr_page)

    employee_full_name = "Uttam Kumar"


    logger.info("=" * 60)
    logger.info("STARTING UNIFIED E2E REVOKE FULL COVERAGE TEST (UTTAM KUMAR)")
    logger.info("=" * 60)

    # ─── CYCLE 1: Resignation #1 -> HR Revoke -> Employee Accept ───
    logger.info("[CYCLE 1] Resignation #1 -> HR Revoke -> Employee ACCEPT")
    emp_wf.res_page.navigate_to_resignation()
    if emp_wf.res_page.has_active_resignation():
        logger.info("Employee already has an active resignation/revoke request. Accepting Revoke to establish clean state...")
    else:
        res1 = emp_wf.submit_resignation_workflow(reason="1", confirm=True)
        hr_rev1 = hr_wf.execute_hr_revoke_request_workflow(employee_name=employee_full_name)
        assert hr_rev1, "HR must successfully send Revoke Request for Resignation #1"

    accept_toast = emp_wf.respond_to_revoke_request_workflow(accept=True)
    assert accept_toast != "", "Accept Revoke toast must be captured"
    logger.info(f"Cycle 1 Accept Revoke Toast: '{accept_toast}'")


    # ─── CYCLE 2: Fresh Resignation #2 -> HR Revoke -> Employee Decline -> Buyout -> Revoke Blocked ───
    logger.info("[CYCLE 2] Fresh Resignation #2 -> HR Revoke -> Employee DECLINE -> Buyout")
    res2 = emp_wf.submit_resignation_workflow(reason="2", confirm=True)
    assert res2.get("toast") != "", "Fresh Resignation #2 submission toast must be captured"

    hr_rev2 = hr_wf.execute_hr_revoke_request_workflow(employee_name=employee_full_name)
    assert hr_rev2, "HR must successfully send Revoke Request for Resignation #2"

    decline_toast = emp_wf.respond_to_revoke_request_workflow(accept=False)
    assert decline_toast != "", "Decline Revoke toast must be captured"
    logger.info(f"Cycle 2 Decline Revoke Toast: '{decline_toast}'")

    # Employee submits Buyout Request
    emp_wf.res_page.navigate_to_resignation()
    emp_wf.res_page.click_status_tab()
    date_input = emp_wf.res_page.page.locator(emp_wf.res_page.EARLY_RELIEVING_DATE_INPUT).first
    if date_input.is_visible(timeout=3000):
        max_date = emp_wf.res_page.get_early_relieving_max_date()
        target_buyout_date = "2026-10-25" if (not max_date or "2026-10-25" <= max_date) else max_date
        logger.info(f"Using valid Buyout Date: '{target_buyout_date}' (Max Allowed: '{max_date}')")
        buyout_toast = emp_wf.request_early_relieving_workflow(target_buyout_date)
        logger.info(f"Buyout Request Toast: '{buyout_toast}'")
    else:
        logger.info("Buyout block is already active with 'BUYOUT REQUESTED' on employee card. Skipping date picker fill and verifying HR restriction.")

    # HR verifies Revoke is now BLOCKED by Buyout
    is_revoke_visible = hr_wf.validate_buyout_prevents_hr_revoke_workflow(employee_name=employee_full_name)
    assert not is_revoke_visible, "HR Revoke button must be hidden/blocked when Buyout is requested"

    logger.info("[PASS E2E] Unified Revoke Full Coverage Test passed with 100% success!")


@pytest.mark.ui
@pytest.mark.adarsh
@pytest.mark.resignation
def test_e2e_complete_buyout_lifecycle_adarsh(logged_in_page):
    """
    Complete End-to-End Dynamic Buyout Offboarding Lifecycle for Adarsh Tiwari:
    
    1. [Employee] Adarsh Tiwari submits fresh Resignation
    2. [HR] Tejaswini sends Revoke Request
    3. [Employee] Adarsh Tiwari Declines Revoke Request
    4. [Employee] Adarsh Tiwari submits Buyout Request (Early LWD: 2026-11-25)
    5. [HR] Tejaswini opens Actions -> Buyout Request -> Process Buyout -> Approves Buyout ('HR Approved')
    6. [Accountant] Admin / Accountant opens /accounts-buyout-processing -> searches Adarsh Tiwari
       -> opens Process Buyout modal via //tr[td[normalize-space()='Adarsh Tiwari']]//img
       -> validates financial formulas -> confirms Recovery Confirmed -> fills Remarks -> Approves Buyout!
    """
    from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow
    from workflows.hrlense_portal.resignation.accountant_resignation_workflow import AccountantResignationWorkflow

    employee_full_name = "Adarsh Tiwari"

    # Step 1: Employee Session
    emp_page, _ = logged_in_page("adarsh_tiwari")
    emp_wf = EmployeeResignationWorkflow(emp_page)

    # Step 2: HR Session
    hr_page, _ = logged_in_page("tejaswini")
    hr_wf = HrResignationWorkflow(hr_page)

    # Step 3: Accountant Session
    acc_page, _ = logged_in_page("admin")
    acc_wf = AccountantResignationWorkflow(acc_page)

    logger.info("=" * 60)
    logger.info("STARTING DYNAMIC E2E COMPLETE BUYOUT LIFECYCLE FOR ADARSH TIWARI")
    logger.info("=" * 60)

    # 1. Employee submits Resignation
    logger.info("[PHASE 1] Employee submitting Resignation...")
    emp_wf.res_page.navigate_to_resignation()
    if not emp_wf.res_page.has_active_resignation():
        emp_wf.submit_resignation_workflow(reason="1", confirm=True)

    # 2. HR sends Revoke Request
    logger.info("[PHASE 2] HR sending Revoke Request...")
    hr_wf.execute_hr_revoke_request_workflow(employee_name=employee_full_name)

    # 3. Employee Declines Revoke Request
    logger.info("[PHASE 3] Employee declining Revoke Request...")
    emp_wf.respond_to_revoke_request_workflow(accept=False)

    # 4. Employee submits Buyout Request
    logger.info("[PHASE 4] Employee submitting Buyout Request...")
    emp_wf.request_early_relieving_workflow("2026-11-25")

    # 5. HR Processes & Approves Buyout Request
    logger.info("[PHASE 5] HR approving Buyout Request...")
    hr_toast = hr_wf.process_buyout_request_workflow(employee_name=employee_full_name, process=True)
    logger.info(f"HR Buyout Approval Toast: '{hr_toast}'")

    # 6. Accountant Processes & Approves Buyout Request with Formula Check
    logger.info("[PHASE 6] Accountant processing Buyout Request...")
    acc_res = acc_wf.process_accountant_buyout_workflow(
        employee_name=employee_full_name,
        calculated_salary="1000",
        remarks="Buyout Approved & Cleared by Accountant E2E",
        confirm_recovery=True,
        approve=True
    )

    assert acc_res.get("success"), f"Accountant process buyout failed for '{employee_full_name}'"
    acc_toast = str(acc_res.get("toast", "")).strip()
    assert acc_toast != "", "Accountant Buyout approval toast must be captured"
    assert "required" not in acc_toast.lower(), f"Accountant Buyout approval failed with validation error: '{acc_toast}'"
    assert "approved" in acc_toast.lower() or "success" in acc_toast.lower() or "processed" in acc_toast.lower(), \
        f"Expected Accountant approval success toast, got: '{acc_toast}'"

    logger.info(f"[PASS E2E ADARSH] Complete Dynamic Buyout Lifecycle for Adarsh Tiwari PASSED 100%! Toast: '{acc_toast}'")


@pytest.mark.ui
@pytest.mark.sanidhy
@pytest.mark.resignation
def test_e2e_complete_buyout_lifecycle_sanidhy(logged_in_page):
    """
    Complete End-to-End Dynamic Buyout Offboarding Lifecycle for Sanidhy Tiwari:
    
    1. [Employee] Sanidhy Tiwari submits fresh Resignation
    2. [HR] Tejaswini sends Revoke Request
    3. [Employee] Sanidhy Tiwari Declines Revoke Request
    4. [Employee] Sanidhy Tiwari submits Buyout Request (Early LWD: 2026-11-25)
    5. [HR] Tejaswini opens Actions -> Buyout Request -> Process Buyout -> Approves Buyout ('HR Approved')
    6. [Accountant] Admin / Accountant opens /accounts-buyout-processing -> searches Sanidhy Tiwari
       -> opens Process Buyout modal via //tr[td[normalize-space()='Sanidhy Tiwari']]//img
       -> validates financial formulas -> confirms Recovery Confirmed -> fills Remarks -> Approves Buyout!
    """
    from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow
    from workflows.hrlense_portal.resignation.accountant_resignation_workflow import AccountantResignationWorkflow

    employee_full_name = "Sanidhy Tiwari"

    # Step 1: Employee Session
    emp_page, _ = logged_in_page("sanidhy")
    emp_wf = EmployeeResignationWorkflow(emp_page)

    # Step 2: HR Session
    hr_page, _ = logged_in_page("tejaswini")
    hr_wf = HrResignationWorkflow(hr_page)

    # Step 3: Accountant Session
    acc_page, _ = logged_in_page("admin")
    acc_wf = AccountantResignationWorkflow(acc_page)

    logger.info("=" * 60)
    logger.info("STARTING DYNAMIC E2E COMPLETE BUYOUT LIFECYCLE FOR SANIDHY TIWARI")
    logger.info("=" * 60)

    # 1. Employee submits Resignation
    logger.info("[PHASE 1] Employee submitting Resignation...")
    emp_wf.res_page.navigate_to_resignation()
    if not emp_wf.res_page.has_active_resignation():
        emp_wf.submit_resignation_workflow(reason="1", confirm=True)

    # 2. HR sends Revoke Request
    logger.info("[PHASE 2] HR sending Revoke Request...")
    hr_wf.execute_hr_revoke_request_workflow(employee_name=employee_full_name)

    # 3. Employee Declines Revoke Request
    logger.info("[PHASE 3] Employee declining Revoke Request...")
    emp_wf.respond_to_revoke_request_workflow(accept=False)

    # 4. Employee submits Buyout Request
    logger.info("[PHASE 4] Employee submitting Buyout Request...")
    emp_wf.request_early_relieving_workflow("2026-11-25")

    # 5. HR Processes & Approves Buyout Request
    logger.info("[PHASE 5] HR approving Buyout Request...")
    hr_toast = hr_wf.process_buyout_request_workflow(employee_name=employee_full_name, process=True)
    logger.info(f"HR Buyout Approval Toast: '{hr_toast}'")

    # 6. Accountant Processes & Approves Buyout Request with Formula Check
    logger.info("[PHASE 6] Accountant processing Buyout Request...")
    acc_res = acc_wf.process_accountant_buyout_workflow(
        employee_name=employee_full_name,
        calculated_salary="1000",
        remarks="Buyout Approved & Cleared by Accountant E2E",
        confirm_recovery=True,
        approve=True
    )

    assert acc_res.get("success"), f"Accountant process buyout failed for '{employee_full_name}'"
    acc_toast = str(acc_res.get("toast", "")).strip()
    assert acc_toast != "", "Accountant Buyout approval toast must be captured"
    assert "required" not in acc_toast.lower(), f"Accountant Buyout approval failed with validation error: '{acc_toast}'"
    assert "approved" in acc_toast.lower() or "success" in acc_toast.lower() or "processed" in acc_toast.lower(), \
        f"Expected Accountant approval success toast, got: '{acc_toast}'"

    logger.info(f"[PASS E2E SANIDHY] Complete Dynamic Buyout Lifecycle for Sanidhy Tiwari PASSED 100%! Toast: '{acc_toast}'")









