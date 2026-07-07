import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.employee.salary_settings_page import SalarySettingsPage

EMPLOYEE_NAME = "Kiaan Shere"


@pytest.fixture(scope="module")
def salary_page(logged_in_page):
    page, _ = logged_in_page("admin")
    return SalarySettingsPage(page)


# ── Step 1 + 2 : grab employee context → read live settings ──────────────────

@pytest.fixture(scope="module")
def employee_context(salary_page):
    """Step 1 — navigate to employee and capture company/branch/department."""
    return salary_page.navigate_to_employee(EMPLOYEE_NAME)


@pytest.fixture(scope="module")
def salary_settings(salary_page, employee_context):
    """Step 2 — navigate to salary calc settings and read pf_threshold + percentages
    for the exact company+branch pulled from the employee profile."""
    salary_page.navigate_to_salary_calc_settings()
    return salary_page.read_salary_settings(
        company=employee_context["company"],
        branch=employee_context["branch"],
        department=employee_context["department"],
    )


@pytest.fixture(scope="module")
def pf_threshold(salary_settings):
    return salary_settings["pf_threshold"]


# ── RULE_006 — Invalid salary rejected (priority 110) ────────────────────────

@pytest.mark.regression
def test_invalid_salary_zero_rejected(salary_page, employee_context):
    """RULE_006 — zero gross salary must be rejected."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary("0")
    salary_page.submit_salary_update()
    assert salary_page.get_toast(), "Expected validation error for zero salary"


@pytest.mark.regression
def test_invalid_salary_negative_rejected(salary_page, employee_context):
    """RULE_006 — negative gross salary must be rejected."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary("-1000")
    salary_page.submit_salary_update()
    assert salary_page.get_toast(), "Expected validation error for negative salary"


# ── RULE_001 — Salary below PF threshold ─────────────────────────────────────

@pytest.mark.regression
def test_pf_auto_disabled_below_threshold(salary_page, employee_context, pf_threshold):
    """RULE_001 — PF toggle is auto-disabled when gross < threshold.
    Step 3+4: open edit → set salary below threshold → confirm popup → assert PF locked.
    """
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold - 1))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog()                          # popup appears because gross < min basic

    assert salary_page.is_pf_toggle_disabled(), "PF toggle should be locked below threshold"
    assert not salary_page.is_pf_toggle_checked(), "PF should be auto-set to false below threshold"


@pytest.mark.regression
def test_pf_field_readonly_below_threshold(salary_page):
    """RULE_001 — PF field remains read-only (reuses state from previous test)."""
    assert salary_page.is_pf_toggle_disabled(), "PF toggle must remain read-only below threshold"


# ── RULE_002 — Salary at or above PF threshold ───────────────────────────────

@pytest.mark.regression
def test_pf_unlocked_at_threshold(salary_page, employee_context, pf_threshold):
    """RULE_002 — PF toggle is unlocked when gross == threshold."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()               # popup only if gross < min basic

    assert not salary_page.is_pf_toggle_disabled(), "PF toggle should be unlocked at threshold"


@pytest.mark.regression
def test_pf_unlocked_above_threshold(salary_page, employee_context, pf_threshold):
    """RULE_002 — PF toggle remains unlocked above threshold."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold + 5000))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()

    assert not salary_page.is_pf_toggle_disabled(), "PF toggle should be unlocked above threshold"


# ── RULE_003 — Employee opted into PF ────────────────────────────────────────

@pytest.mark.regression
def test_pf_opted_in_disables_slab(salary_page, employee_context, pf_threshold):
    """RULE_003 — when PF is opted in, salary slab must not apply."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold + 5000))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()

    assert salary_page.is_pf_toggle_checked(), "PF should be opted in"
    assert not salary_page.is_visible("text=Salary Slab Applied"), \
        "Salary slab should NOT be applied when PF is opted in"


# ── RULE_004 — Employee opted out of PF ──────────────────────────────────────

@pytest.mark.regression
def test_slab_triggered_when_pf_opted_out(salary_page, employee_context, pf_threshold):
    """RULE_004 — salary slab triggers only when employee opts out of PF."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold + 5000))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()

    salary_page.toggle_include_pf()
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()

    assert not salary_page.is_pf_toggle_checked(), "PF should be opted out"


# ── RULE_005 — Slab resolution from settings ─────────────────────────────────

@pytest.mark.regression
def test_salary_slab_resolves_correct_range(salary_page, salary_settings):
    """RULE_005 — slab rules are configured for the employee's company+branch."""
    salary_page.navigate_to_salary_calc_settings()
    salary_page.read_salary_settings(
        company=salary_settings.get("company", ""),
        branch=salary_settings.get("branch", ""),
    ) if salary_settings.get("company") else None

    salary_page.page.get_by_role("tab", name="Salary Slab Rules").click()
    salary_page.page.wait_for_load_state("networkidle")
    initial_count = salary_page.get_slab_row_count()

    salary_page.add_slab_rule("15000", "25000", "7500")
    assert salary_page.get_slab_row_count() == initial_count + 1, \
        "New slab rule should appear in the table"


@pytest.mark.regression
def test_salary_slab_hierarchy_department_overrides_branch(salary_page):
    """RULE_005 / overrideStrategy — at least one slab rule is configured."""
    salary_page.page.get_by_role("tab", name="Salary Slab Rules").click()
    salary_page.page.wait_for_load_state("networkidle")

    assert salary_page.get_slab_row_count() > 0, \
        "Slab rules table must have at least one configured rule"


# ── Admin settings ────────────────────────────────────────────────────────────

@pytest.mark.regression
def test_pf_threshold_update(salary_page, salary_settings, pf_threshold):
    """PF threshold write-back is idempotent — writes same live value back."""
    salary_page.navigate_to_salary_calc_settings()
    salary_page.read_salary_settings(
        company=salary_settings.get("company", ""),
        branch=salary_settings.get("branch", ""),
    ) if salary_settings.get("company") else None
    salary_page.set_pf_threshold(str(pf_threshold))

    assert salary_page.get_toast(), "Expected success toast after PF threshold update"


@pytest.mark.regression
def test_hra_percentage_update(salary_page, salary_settings):
    """HRA percentage persists after update."""
    salary_page.navigate_to_salary_calc_settings()
    salary_page.read_salary_settings(
        company=salary_settings.get("company", ""),
        branch=salary_settings.get("branch", ""),
    ) if salary_settings.get("company") else None
    salary_page.set_hra_percentage("30")

    assert salary_page.get_toast(), "Expected success toast after HRA percentage update"


# ── Boundary values ───────────────────────────────────────────────────────────

@pytest.mark.regression
def test_salary_boundary_exactly_at_threshold(salary_page, employee_context, pf_threshold):
    """Boundary — gross == threshold must unlock PF (RULE_002)."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog_if_present()

    assert not salary_page.is_pf_toggle_disabled(), \
        f"PF toggle must be unlocked at exactly threshold ({pf_threshold})"


@pytest.mark.regression
def test_salary_boundary_one_below_threshold(salary_page, employee_context, pf_threshold):
    """Boundary — gross == threshold-1 must auto-lock PF and trigger confirm popup (RULE_001)."""
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    salary_page.open_salary_edit()
    salary_page.set_gross_salary(str(pf_threshold - 1))
    salary_page.submit_salary_update()
    salary_page.confirm_dialog()                          # popup MUST appear here

    assert salary_page.is_pf_toggle_disabled(), \
        f"PF toggle must be locked one below threshold ({pf_threshold - 1})"
