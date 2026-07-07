import pytest
from utils.api.payroll_api import get_payroll_list, wait_for_payroll_complete, find_branch_id
from pages.payroll.payroll_page import PayrollPage

YEAR = 2026
MONTH = 4
BRANCH_NAME = "Varanasi"
COMPANY_NAME = "TEK Inspirations LLC"
BRANCH_ID = find_branch_id(BRANCH_NAME, COMPANY_NAME)


# ── Step 1: Run payroll via UI ────────────────────────────────────────────────

@pytest.fixture(scope="module")
def payroll_page(logged_in_page):
    page, _ = logged_in_page("admin")
    payroll = PayrollPage(page)
    payroll.navigate_to_payroll()
    payroll.apply_branch_filter("Varanasi - Inf")
    payroll.run_payroll()
    return payroll


@pytest.fixture(scope="module")
def ui_rows(payroll_page):
    return payroll_page.get_table_rows()


# ── Step 2: Poll status until complete, then fetch API data ───────────────────

@pytest.fixture(scope="module")
def api_response(payroll_page):
    wait_for_payroll_complete(year=YEAR, month=MONTH, branch_id=BRANCH_ID)
    return get_payroll_list(year=YEAR, month=MONTH, branch_id=BRANCH_ID)


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
    for row in ui_rows:
        api_rec = api_map.get(row["emp_code"])
        assert api_rec is not None, f"employeeCode {row['emp_code']} not found in API"
        assert row[ui_key] == str(api_rec[api_key]).strip(), (
            f"{ui_key}: UI='{row[ui_key]}' API='{api_rec[api_key]}'"
        )


@pytest.mark.ui
@pytest.mark.payroll
@pytest.mark.parametrize("ui_key,api_key", [
    ("basic", "basic"),
    ("hra", "hra"),
    ("tds", "tds"),
])
def test_numeric_field_exact_match(ui_rows, api_records, ui_key, api_key):
    api_map = {r["employeeCode"]: r for r in api_records}
    for row in ui_rows:
        api_rec = api_map.get(row["emp_code"])
        assert api_rec is not None
        assert abs(row[ui_key] - float(api_rec[api_key])) < 0.01, (
            f"{ui_key} emp={row['emp_code']}: UI={row[ui_key]} API={api_rec[api_key]}"
        )


# ── Net salary ────────────────────────────────────────────────────────────────

@pytest.mark.ui
@pytest.mark.payroll
def test_net_salary_ui_matches_api(ui_rows, api_records):
    api_map = {r["employeeCode"]: r for r in api_records}
    for row in ui_rows:
        api_rec = api_map.get(row["emp_code"])
        assert api_rec is not None
        assert abs(row["net_salary"] - float(api_rec["netSalary"])) < 0.01, (
            f"netSalary emp={row['emp_code']}: UI={row['net_salary']} API={api_rec['netSalary']}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_net_salary_formula(api_records):
    """netSalary == totalEarnings - totalDeductions"""
    for r in api_records:
        expected = round(r["totalEarnings"] - r["totalDeductions"], 2)
        assert abs(round(r["netSalary"], 2) - expected) < 0.01, (
            f"{r['employeeName']}: netSalary={r['netSalary']} expected={expected}"
        )
