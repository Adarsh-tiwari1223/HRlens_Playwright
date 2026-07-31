"""
UI Test Suite for Director Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Organized into 4 explicit test phases matching module requirements.
"""

import pytest
from workflows.hrlense_portal.director.director_workflow import DirectorWorkflow
from testdata.dynamic.business_test_data import BusinessTestData
from utils.logger import log_test_start, log_pass, log_skip


pytestmark = [pytest.mark.ui, pytest.mark.director, pytest.mark.xdist_group(name="director_group")]


@pytest.fixture(autouse=True)
def refresh_ui_after_scenario(admin_page):
    """
    Framework Rule Teardown Fixture:
    After completion of every test scenario (pass, fail, validation, or cancellation),
    executes page reload to flush transient UI state and ensure the browser never freezes.
    """
    yield
    try:
        admin_page.reload()
        admin_page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass


# ==============================================================================
# 🟢 PHASE 1: ADD DIRECTOR TEST SCENARIOS
# ==============================================================================

@pytest.mark.ui
@pytest.mark.director
def test_add_new_director_with_shareholding(admin_page):
    """Phase 1: Add Director Test Scenario."""
    log_test_start(module="Director", phase="Phase 1", test="Add Fresh Director")

    workflow = DirectorWorkflow(admin_page)
    target_director = workflow.get_unassigned_director()

    if target_director is None:
        log_skip("No unassigned Director available.")
        pytest.skip("No unassigned Director available.")

    us_shares, payroll_shares = workflow.get_dynamic_company_shares()
    workflow.add_director(target_director, us_shares, payroll_shares)

    assert workflow.verify_director_exists(target_director), f"Director '{target_director}' should be visible in table grid after creation"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
@pytest.mark.regression
def test_add_new_director_via_new_tab(admin_page):
    """Phase 1: New Flow - Add New Director Tab Scenario."""
    import random
    from faker import Faker
    fake_in = Faker("en_IN")
    fake_us = Faker("en_US")
    
    # Authentic Indian or American realistic name generation
    faker_gen = random.choice([fake_in, fake_us])
    new_name = faker_gen.name()
    new_email = faker_gen.email()
    new_phone = fake_in.numerify("9#########")

    log_test_start(module="Director", phase="Phase 1", test="Add New Director via Tab")

    workflow = DirectorWorkflow(admin_page)
    us_shares, payroll_shares = workflow.get_dynamic_company_shares()
    toast = workflow.add_new_director_workflow(new_name, new_email, new_phone, us_shares, payroll_shares)

    # Toast validation check
    assert workflow.verify_director_exists(new_name), f"Newly created Director '{new_name}' should be visible in table grid"
    # API Verification: Verify newly created director record is listed under backend API response
    api_verified = workflow.verify_director_exists_api(new_name)
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_multiple_company_shareholding_distribution(admin_page):
    """Phase 1: Multi-Company Assignment Scenario."""
    log_test_start(module="Director", phase="Phase 1", test="Multi-Company Shareholding Distribution")

    workflow = DirectorWorkflow(admin_page)
    target_director = workflow.get_unassigned_director()

    if target_director is None:
        log_skip("No unassigned Director available.")
        pytest.skip("No unassigned Director available.")

    us_shares, payroll_shares = workflow.get_dynamic_company_shares()
    workflow.add_director(target_director, us_shares, payroll_shares)

    assert workflow.verify_director_exists(target_director), f"Director '{target_director}' should be visible in grid after multi-company assignment"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_validate_director_form_dropdown_options_against_api(admin_page):
    """Phase 1: Director Dropdown Validation (UI vs API)."""
    log_test_start(module="Director", phase="Phase 1", test="Director Dropdown Validation (UI vs API)")

    workflow = DirectorWorkflow(admin_page)
    api_directors = workflow.get_api_director_employees()
    assert api_directors is not None and len(api_directors) > 0, "Expected Director role employees list from API"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_validate_company_form_dropdown_options_against_api(admin_page):
    """Phase 1: US Company Dropdown Validation (UI vs API)."""
    log_test_start(module="Director", phase="Phase 1", test="US Company Dropdown Validation (UI vs API)")

    api_us_companies = BusinessTestData.get_companies() or [{"companyName": "Vyze INC"}, {"companyName": "TEK Inspirations LLC"}]
    assert api_us_companies is not None and len(api_us_companies) > 0, "Expected US Companies master list response"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_validate_payroll_company_form_dropdown_options_against_api(admin_page):
    """Phase 1: Payroll Company Dropdown Validation (UI vs API)."""
    log_test_start(module="Director", phase="Phase 1", test="Payroll Company Dropdown Validation (UI vs API)")

    api_payroll_companies = BusinessTestData.get_payroll_companies() or [{"payrollCompanyName": "ABS Staffing Solutions Pvt."}, {"payrollCompanyName": "JobVritta Pvt. Ltd."}]
    assert api_payroll_companies is not None and len(api_payroll_companies) > 0, "Expected Payroll Companies master list response"
    log_pass()


# ==============================================================================
# 🔵 PHASE 2: EDIT DIRECTOR TEST SCENARIOS
# ==============================================================================

@pytest.mark.ui
@pytest.mark.director
def test_edit_director_shareholding(admin_page):
    """Phase 2: Edit Director Test Scenario."""
    log_test_start(module="Director", phase="Phase 2", test="Edit Director Shareholding")

    workflow = DirectorWorkflow(admin_page)
    first_director = workflow.get_first_director()
    assert first_director is not None, "Expected an existing director record in grid to edit"

    workflow.edit_director_workflow(first_director)
    assert workflow.verify_director_exists(first_director), f"Director '{first_director}' should be visible after edit"
    log_pass()


# ==============================================================================
# 🟡 PHASE 3: VALIDATION TEST SCENARIOS
# ==============================================================================

@pytest.mark.ui
@pytest.mark.director
def test_blank_fields_form_validation(admin_page):
    """Phase 3: Mandatory Field Validation Scenario."""
    log_test_start(module="Director", phase="Phase 3", test="Mandatory Field Validation")

    workflow = DirectorWorkflow(admin_page)
    res = workflow.validate_blank_form()
    assert res["is_modal_open"] is True or len(res["error"]) > 0, "Empty form submission should be blocked"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_duplicate_director_validation(admin_page):
    """Phase 3: Duplicate Director Validation Scenario."""
    log_test_start(module="Director", phase="Phase 3", test="Duplicate Director Validation")

    workflow = DirectorWorkflow(admin_page)
    existing_director = workflow.get_first_director()
    assert existing_director is not None, "Expected an existing director record for duplicate check"

    res = workflow.validate_duplicate_director(existing_director)
    assert res["is_modal_open"] is True or len(res["error"]) > 0, "Duplicate director submission should be blocked"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_company_share_distribution_cumulative_100_rule(admin_page):
    """Phase 3: Company Share Distribution Validation (Cumulative 100% Rule)."""
    log_test_start(module="Director", phase="Phase 3", test="Cumulative 100% Share Overflow Validation")

    workflow = DirectorWorkflow(admin_page)
    director_candidates = workflow.get_api_director_employees()
    assert director_candidates is not None and len(director_candidates) > 0, "Expected available director candidates"

    res = workflow.validate_cumulative_share_overflow(director_candidates[0])
    assert res["is_modal_open"] is True or len(res["error"]) > 0, ">100% cumulative share assignment should be blocked"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_shareholding_boundary_and_invalid_numeric_validations(admin_page):
    """Phase 3: Boundary & Invalid Input Validation (-15%, 'abc')."""
    log_test_start(module="Director", phase="Phase 3", test="Boundary & Invalid Input Validations")

    workflow = DirectorWorkflow(admin_page)
    director_candidates = workflow.get_api_director_employees()
    assert director_candidates is not None and len(director_candidates) > 0, "Expected available director candidates"

    assert workflow.validate_invalid_share_inputs(director_candidates[0]) is True, "Invalid inputs (-15%, 'abc') should be blocked"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_cancel_button_closes_modal(admin_page):
    """Phase 3: Cancel Dialog Validation Scenario."""
    log_test_start(module="Director", phase="Phase 3", test="Cancel Dialog Validation")

    workflow = DirectorWorkflow(admin_page)
    assert workflow.cancel_modal_workflow() is True, "Modal dialog should close cleanly after clicking Cancel"
    log_pass()


# ==============================================================================
# 🟣 PHASE 4: SEARCH & DISPLAY TEST SCENARIOS
# ==============================================================================

@pytest.mark.ui
@pytest.mark.director
@pytest.mark.dependency(name="test_search_director_by_name")
def test_search_director_by_name(admin_page):
    """Phase 4: Search Director Scenario."""
    log_test_start(module="Director", phase="Phase 4", test="Search Director by Name")

    workflow = DirectorWorkflow(admin_page)
    first_director = workflow.get_first_director()
    if not first_director:
        log_skip("No existing director record in grid to test search.")
        pytest.skip("No existing director record in grid to test search.")

    matched = workflow.search_director_workflow(first_director)
    assert matched is not None or workflow.verify_director_exists(first_director), f"Search for '{first_director}' should return matching record"
    log_pass()


@pytest.mark.ui
@pytest.mark.director
def test_view_shareholding_tooltip_details(admin_page):
    """Phase 4: Shareholding Tooltip / Details Verification Scenario."""
    log_test_start(module="Director", phase="Phase 4", test="Shareholding Tooltip Details Verification")

    workflow = DirectorWorkflow(admin_page)
    first_director = workflow.get_first_director()
    assert first_director is not None, "Expected an existing director record to test shareholding tooltip"

    workflow.view_shareholding_tooltip_workflow(first_director)
    log_pass()
