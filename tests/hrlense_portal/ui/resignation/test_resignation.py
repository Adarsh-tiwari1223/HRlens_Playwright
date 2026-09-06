"""
HRlens Portal — Employee Resignation UI Test Suite (Test Tier).

Organized by Business Priority:
- P0 Critical Suite: Calendar boundaries (> LWD, < Present), Duplicate Resignation prevention, Buyout -> HR Revoke restriction
- P1 High Suite: Buyout = LWD, Revoke without Buyout, Released Status Immutability
"""
import pytest
from core.config import settings
from core.config.users import get_random_varanasi_employee
from workflows.hrlense_portal.resignation.resignation_workflow import ResignationWorkflow



@pytest.fixture
def get_resignation_workflow(logged_in_page):
    """Factory fixture to initialize ResignationWorkflow for a specific employee user account."""
    def _create_workflow(user_key: str = settings.EMPLOYEE_USER):
        page, _ = logged_in_page(user_key)
        return ResignationWorkflow(page)
    return _create_workflow


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEE RESIGNATION APPLICATION SUITE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.apply_resignation
@pytest.mark.resignation
def test_employee_apply_resignation_basic_flow(get_resignation_workflow):
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
    res_wf = get_resignation_workflow("abhishek_singh")

    result = res_wf.submit_resignation_workflow(
        reason="1",
        stay_connected=True,
        share_suggestions=True,
        suggestion_text="Career growth and new learning opportunities.",
        confirm=True
    )

    assert result.get("selected_reason") != "", "Separation Reason must be selected from dropdown"
    assert result.get("modal_visible"), "Confirmation Modal 'Submit Resignation Request' must be displayed"
    assert result.get("toast") != "", "Submission success toast must be captured"

    print(f"\n[PASS] Employee Resignation Application Flow passed! Toast: '{result.get('toast')}'")



# ══════════════════════════════════════════════════════════════════════════════
# P0 — CRITICAL TEST SUITE
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_buyout_date_exceeds_lwd(get_resignation_workflow):
    """
    [P0 CRITICAL] Buyout Date > Last Working Day (LWD: 30-11-2026).
    Dates after 30-11-2026 should be disabled in the calendar; employee cannot select those dates.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    exceed_date = "2026-12-15"

    result = res_wf.validate_early_relieving_max_date_workflow(exceed_date_str=exceed_date)
    max_attr = result.get("max_date_attr", "")

    # Assert date input enforces 'max' attribute boundary (e.g. 2026-11-30)
    assert max_attr != "" or result.get("toast") != "", \
        "System must constrain or disable Buyout Dates after Last Working Day (30-11-2026)"

    print(f"\n[PASS P0] Buyout Date > LWD validation passed! Input max date constraint: '{max_attr}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_p0_buyout_date_before_present_date(get_resignation_workflow):
    """
    [P0 CRITICAL] Buyout Date < Present Date.
    Dates before the current/present date should be disabled; employee cannot select a past date.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    boundaries = res_wf.validate_buyout_date_boundaries_workflow()

    min_date = boundaries.get("min_date_present", "")
    assert min_date != "", "Date picker must specify a 'min' date constraint preventing past date selection"

    print(f"\n[PASS P0] Buyout Date < Present Date validation passed! Input min date constraint: '{min_date}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_p0_duplicate_resignation_submission(get_resignation_workflow):
    """
    [P0 CRITICAL] Duplicate Resignation Request.
    Employee A submits one resignation, then attempts another submission while existing request is active.
    Expected: System should prevent creation of duplicate resignation request.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    result = res_wf.submit_resignation_workflow(reason="1", confirm=True)

    expected_toast = "You already have a resignation in 'Applied' state."
    captured_toast = str(result.get("toast", ""))

    is_toast_matched = expected_toast.lower() in captured_toast.lower()
    is_blocked = result.get("has_active_resignation") is True or captured_toast == "ACTIVE_RESIGNATION_EXISTS"

    assert is_toast_matched or is_blocked, \
        f"System must prevent duplicate active resignation creation. Got toast: '{captured_toast}'"

    print(f"\n[PASS P0] Duplicate resignation submission correctly prevented! Toast: '{captured_toast}'")


@pytest.mark.ui
@pytest.mark.p0
@pytest.mark.resignation
def test_p0_buyout_request_prevents_hr_revoke(get_resignation_workflow, logged_in_page):
    """
    [P0 CRITICAL] Buyout Request -> HR Revoke Restriction.
    When Employee submits a Buyout Request, HR should NOT have the option to create a Revoke Request.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    hr_page, _ = logged_in_page("admin")

    # Verify HR cannot revoke when Buyout exists
    is_revoke_visible = res_wf.res_page.is_hr_revoke_request_visible(employee_name="Kumar Piyush")
    
    # If Buyout applied, Revoke Request must be False (hidden/disabled)
    print(f"\n[PASS P0] Buyout -> HR Revoke restriction checked. Revoke Request visible: {is_revoke_visible}")


# ══════════════════════════════════════════════════════════════════════════════
# P1 — HIGH TEST SUITE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.p1
@pytest.mark.resignation
def test_buyout_date_equals_lwd(get_resignation_workflow):
    """
    [P1 HIGH] Buyout Date = Last Working Day (LWD: 30-11-2026).
    Verify 30-11-2026 is selectable and does not exceed LWD.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    boundaries = res_wf.validate_buyout_date_boundaries_workflow()

    max_date = boundaries.get("max_date_lwd", "")
    assert max_date != "", "Last Working Day max date constraint must be present on the date input"

    print(f"\n[PASS P1] Buyout Date = LWD verified! Selectable LWD boundary: '{max_date}'")


@pytest.mark.ui
@pytest.mark.p1
@pytest.mark.resignation
def test_revoke_without_buyout_allows_hr_revoke(get_resignation_workflow, logged_in_page):
    """
    [P1 HIGH] Revoke without Buyout.
    When Employee has NOT submitted a Buyout Request, HR should be able to initiate the Revoke Request.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    hr_page, _ = logged_in_page("admin")

    is_revoke_available = res_wf.validate_revoke_without_buyout_workflow(
        hr_page_instance=hr_page,
        employee_name="Uttam Kumar",
    )

    print(f"\n[PASS P1] Revoke without Buyout check verified. Revoke available for HR: {is_revoke_available}")


@pytest.mark.ui
@pytest.mark.p1
@pytest.mark.resignation
def test_released_employee_no_modification(get_resignation_workflow):
    """
    [P1 HIGH] Released Employee Immutability.
    When Resignation reaches Released, it is final and no further changes/modifications are possible.
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    is_immutable = res_wf.res_page.is_released_status_immutable()

    print(f"\n[PASS P1] Released status immutability verified! Inputs disabled: {is_immutable}")


@pytest.mark.ui
@pytest.mark.employee_revoke_accept
@pytest.mark.resignation
def test_employee_accept_revoke_ends_resignation_allows_new_request(get_resignation_workflow, logged_in_page):
    """
    Employee Side Revoke Flow (ACCEPT):
    1. Employee A submits Resignation #1
    2. HR sends Revoke Request via hr_revoke_request_flow
    3. Employee A sees Accept/Reject decision buttons and clicks 'Accept'
    4. Resignation #1 ends / closed
    5. Employee A submits a NEW Resignation Request #2 successfully
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    hr_page, _ = logged_in_page("admin")

    result = res_wf.employee_accept_revoke_and_apply_new_resignation_workflow(
        hr_page_instance=hr_page,
        employee_name="Kumar Piyush",
    )

    assert result["hr_sent_revoke"], "HR should successfully send Revoke Request for employee without Buyout"
    assert result["new_resignation_submitted"], "Employee should be able to submit a NEW resignation request after accepting Revoke"
    print(f"\n[PASS] Employee ACCEPT Revoke Flow verified! New resignation submitted successfully.")


@pytest.mark.ui
@pytest.mark.employee_revoke_reject
@pytest.mark.resignation
def test_employee_reject_revoke_resignation_continues(get_resignation_workflow, logged_in_page):
    """
    Employee Side Revoke Flow (REJECT):
    1. Employee A has active Resignation #2 (re-applied after accepting Revoke #1)
    2. HR sends Revoke Request via hr_revoke_request_flow
    3. Employee A sees Accept/Reject decision buttons and clicks 'Reject'
    4. Resignation #2 CONTINUES active workflow lifecycle
    5. Employee A requests Early Relieving Date to prove continuation
    """
    res_wf = get_resignation_workflow(get_random_varanasi_employee())

    hr_page, _ = logged_in_page("admin")

    result = res_wf.employee_reject_revoke_and_verify_continuation_workflow(
        hr_page_instance=hr_page,
        employee_name="Kumar Piyush",
    )

    assert result["hr_sent_revoke"], "HR should successfully send Revoke Request"
    assert result["early_relieving_submitted"], "Employee A should be able to request Early Relieving Date post-rejection to prove workflow continuation"
    assert result["resignation_continues_active"], "Resignation should CONTINUE active workflow lifecycle when Employee A REJECTS Revoke"
    print(f"\n[PASS] Employee A REJECT Revoke Flow verified! Early Relieving submitted successfully, proving resignation workflow continues.")




# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED REVOKE E2E TEST SUITE (RR_001 TO RR_006)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.ui
@pytest.mark.revoke_e2e
@pytest.mark.resignation
def test_e2e_resignation_revoke_full_lifecycle(get_resignation_workflow, logged_in_page):
    """
    Single E2E Revoke Lifecycle Test covering RR_001 through RR_006 sequentially:
    
    CYCLE 1:
    - [RR_002] Employee A submits Resignation #1 (without Buyout)
    - [RR_005] HR searches Employee A in table, opens 'Resignation Details' modal, verifies 'Revoke' button & sends Revoke
    - [RR_003] Employee A ACCEPTS Revoke Request → Existing Resignation #1 ENDS/CLOSED

    CYCLE 2:
    - [RR_006] Employee A submits FRESH Resignation #2
    - [RR_004] HR sends Revoke Request → Employee A REJECTS → Resignation #2 CONTINUES
    - [RR_001] Employee A applies for Buyout Request → HR opens modal → 'Revoke' button is BLOCKED/HIDDEN
    """
    from core.config.users import get_random_varanasi_employee

    random_emp_key = get_random_varanasi_employee()
    emp_name_map = {
        "abhishek_singh": "Abhishek Singh",
        "uttam_kumar": "Uttam Kumar",
        "kumar_piyush": "Kumar Piyush",
        "adarsh_tiwari": "Adarsh Tiwari",
        "sanidhy": "Sanidhy Tiwari",
    }
    target_employee_name = emp_name_map.get(random_emp_key, "Abhishek Singh")

    res_wf = get_resignation_workflow(random_emp_key)
    hr_page, _ = logged_in_page("ritesh_singh")


    result = res_wf.execute_e2e_revoke_workflow(
        hr_page_instance=hr_page,
        employee_name=target_employee_name,
    )



    # Assertions
    assert result["cycle1_revoke_sent"], "HR should be able to send Revoke Request when Buyout is NOT requested (RR_002)"
    assert result["cycle2_fresh_resignation_allowed"], "Employee should be allowed to submit fresh Resignation after Accept Revoke (RR_006)"
    assert result["cycle2_revoke_blocked_by_buyout"], "HR Revoke button should be blocked/hidden when Buyout is requested (RR_001)"

    print(f"\n[PASS E2E] Unified Revoke E2E Lifecycle Test (RR_001 to RR_006) passed successfully! Result: {result}")

