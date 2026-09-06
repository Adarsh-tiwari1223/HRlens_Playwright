import pytest
from utils.salary_calculator import calculate_salary_structure
from utils.api.salary_settings_api import get_salary_settings_for_company


@pytest.fixture(scope="module")
def api_salary_settings():
    """Dynamically fetches salary calculation settings from API: GET /SalaryCalculationSettings"""
    return get_salary_settings_for_company(employment_type="Employee")


def test_normal_salary_calculation_dynamic_api(api_salary_settings):
    """
    Test Case 1: When calculated basic >= configured minimum basic (from API).
    Expected: Action is NORMAL_SALARY_CALCULATION, is_allowed is True.
    """
    min_basic_config = api_salary_settings["configured_minimum_basic_salary"]
    min_gross_config = api_salary_settings["configured_minimum_gross_salary"]

    # Calculate gross where basic >= min_basic_config
    test_gross = max(25000.0, (min_basic_config / 0.8435) + 2000.0)

    result = calculate_salary_structure(
        gross_salary=test_gross,
        configured_minimum_basic_salary=min_basic_config,
        configured_minimum_gross_salary=min_gross_config
    )
    assert result["action"] == "NORMAL_SALARY_CALCULATION"
    assert result["status"] == "APPROVED"
    assert result["is_allowed"] is True
    assert result["requires_confirmation"] is False


def test_minimum_basic_below_threshold_paid_intern_alert_dynamic_api(api_salary_settings):
    """
    Test Case 2: When basic < configured basic AND gross >= configured_minimum_gross_salary (from API).
    Expected: Action is SHOW_MINIMUM_SALARY_ALERT, triggers Paid Intern conversion prompt.
    """
    min_basic_config = api_salary_settings["configured_minimum_basic_salary"]
    min_gross_config = api_salary_settings["configured_minimum_gross_salary"]

    # Test gross salary equal to or slightly above minimum gross salary
    test_gross = min_gross_config

    result = calculate_salary_structure(
        gross_salary=test_gross,
        configured_minimum_basic_salary=min_basic_config,
        configured_minimum_gross_salary=min_gross_config
    )
    assert result["action"] == "SHOW_MINIMUM_SALARY_ALERT"
    assert result["status"] == "PAID_INTERN_PROMPT"
    assert result["is_allowed"] is True
    assert result["requires_confirmation"] is True
    
    intern_struct = result["converted_paid_intern_structure"]
    assert intern_struct["employment_type"] == "INTERN"
    assert intern_struct["intern_payment_type"] == "PAID"
    assert intern_struct["basic_salary"] == test_gross
    assert intern_struct["hra"] == 0.0


def test_gross_below_minimum_gross_salary_not_allowed_dynamic_api(api_salary_settings):
    """
    Test Case 3: When basic < configured basic AND gross < configured_minimum_gross_salary (from API).
    Expected: Action is SALARY_NOT_ALLOWED, is_allowed is False, status is REJECTED.
    """
    min_basic_config = api_salary_settings["configured_minimum_basic_salary"]
    min_gross_config = api_salary_settings["configured_minimum_gross_salary"]

    # Test gross salary strictly below minimum gross threshold
    test_gross = max(1000.0, min_gross_config - 3000.0)

    result = calculate_salary_structure(
        gross_salary=test_gross,
        configured_minimum_basic_salary=min_basic_config,
        configured_minimum_gross_salary=min_gross_config
    )
    assert result["action"] == "SALARY_NOT_ALLOWED"
    assert result["status"] == "REJECTED"
    assert result["is_allowed"] is False
    assert "below the minimum allowed gross salary threshold" in result["error_message"]
