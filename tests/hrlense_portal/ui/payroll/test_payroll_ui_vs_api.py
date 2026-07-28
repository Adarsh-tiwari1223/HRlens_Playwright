import pytest
from utils.api.payroll_api import get_payroll_list, wait_for_payroll_complete, find_branch_id
from workflows.hrlense_portal.payroll.payroll_workflow import PayrollWorkflow

YEAR = 2026
MONTH = 4
BRANCH_NAME = "Varanasi"
COMPANY_NAME = "TEK Inspirations LLC"

@pytest.fixture(scope="module")
def branch_id():
    return find_branch_id(BRANCH_NAME, COMPANY_NAME)


# ── Step 1: Run payroll via Workflow ──────────────────────────────────────────

@pytest.fixture(scope="module")
def payroll_workflow(logged_in_page):
    page, _ = logged_in_page("admin")
    workflow = PayrollWorkflow(page)
    workflow.process_monthly_payroll_workflow("Varanasi - Inf")
    return workflow


@pytest.fixture(scope="module")
def ui_rows(payroll_workflow):
    return payroll_workflow.get_payroll_ui_rows_workflow()


# ── Step 2: Poll status until complete, then fetch API data ───────────────────

@pytest.fixture(scope="module")
def api_response(payroll_workflow, branch_id):
    wait_for_payroll_complete(year=YEAR, month=MONTH, branch_id=branch_id)
    return get_payroll_list(year=YEAR, month=MONTH, branch_id=branch_id)


@pytest.fixture(scope="module")
def api_records(api_response):
    return api_response.get("data", [])


# ── Row count ─────────────────────────────────────────────────────────────────

@pytest.mark.ui
@pytest.mark.payroll
def test_row_count_matches_api(ui_rows, api_records):
    assert len(ui_rows) == len(api_records), (
        f"UI rows={len(ui_rows)} API records={len(api_records)}"
    )


# ── Field-level exact match ───────────────────────────────────────────────────

@pytest.mark.ui
@pytest.mark.payroll
@pytest.mark.parametrize("ui_key,api_key", [
    ("emp_code", "employeeCode"),
    ("employee_name", "employeeName"),
])
def test_string_field_exact_match(ui_rows, api_records, ui_key, api_key):
    api_map = {r["employeeCode"]: r for r in api_records}
    mismatches = []
    for row in ui_rows:
        code = row["emp_code"]
        if code not in api_map:
            mismatches.append(f"Emp {code} in UI but not API")
            continue
        ui_val = row[ui_key].strip()
        api_val = str(api_map[code].get(api_key, "")).strip()
        if ui_val != api_val:
            mismatches.append(f"Emp {code} [{ui_key}]: UI='{ui_val}' != API='{api_val}'")
    assert not mismatches, "\n".join(mismatches)


@pytest.mark.ui
@pytest.mark.payroll
@pytest.mark.parametrize("ui_key,api_key", [
    ("basic", "basic"),
    ("hra", "hra"),
    ("tds", "tds"),
])
def test_numeric_field_exact_match(ui_rows, api_records, ui_key, api_key):
    api_map = {r["employeeCode"]: r for r in api_records}
    mismatches = []
    for row in ui_rows:
        code = row["emp_code"]
        if code not in api_map:
            continue
        try:
            ui_val = float(row[ui_key].replace(",", ""))
            api_val = float(api_map[code].get(api_key, 0))
            if abs(ui_val - api_val) > 0.01:
                mismatches.append(f"Emp {code} [{ui_key}]: UI={ui_val} != API={api_val}")
        except ValueError:
            mismatches.append(f"Emp {code} [{ui_key}]: Unparseable UI val '{row[ui_key]}'")
    assert not mismatches, "\n".join(mismatches)


@pytest.mark.ui
@pytest.mark.payroll
def test_net_salary_ui_matches_api(ui_rows, api_records):
    api_map = {r["employeeCode"]: r for r in api_records}
    mismatches = []
    for row in ui_rows:
        code = row["emp_code"]
        if code not in api_map:
            continue
        try:
            ui_net = float(row["net_salary"].replace(",", ""))
            api_net = float(api_map[code].get("netSalary", 0))
            if abs(ui_net - api_net) > 0.01:
                mismatches.append(f"Emp {code} [net_salary]: UI={ui_net} != API={api_net}")
        except ValueError:
            mismatches.append(f"Emp {code}: Unparseable net salary '{row['net_salary']}'")
    assert not mismatches, "\n".join(mismatches)


@pytest.mark.ui
@pytest.mark.payroll
def test_net_salary_formula(ui_rows):
    mismatches = []
    for row in ui_rows:
        code = row["emp_code"]
        try:
            gross = float(row["gross"].replace(",", ""))
            deductions = float(row["total_deductions"].replace(",", ""))
            net = float(row["net_salary"].replace(",", ""))
            expected_net = round(gross - deductions, 2)
            if abs(net - expected_net) > 0.01:
                mismatches.append(f"Emp {code}: gross({gross}) - ded({deductions}) = {expected_net} != UI net({net})")
        except ValueError:
            mismatches.append(f"Emp {code}: Unparseable numeric in formula test")
    assert not mismatches, "\n".join(mismatches)
