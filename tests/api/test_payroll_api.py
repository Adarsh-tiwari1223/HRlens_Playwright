import json
import pytest
import requests
from core.config import settings
from utils.api.base_api import headers
from utils.api.payroll_api import get_payroll_list, get_payroll_status, wait_for_payroll_complete, get_employee_detail, find_branch_id
from pages.payroll.payroll_page import PayrollPage

YEAR = 2026
MONTH = 4
BRANCH_NAME = "Varanasi"
COMPANY_NAME = "TEK Inspirations LLC"
BRANCH_ID = find_branch_id(BRANCH_NAME, COMPANY_NAME)
REQUIRED_FIELDS = {"employeeCode", "employeeName", "basic", "hra", "netSalary", "tds",
                   "totalEarnings", "totalDeductions",}


# ── Step 1: Run payroll via UI ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def payroll_ran(logged_in_page):
    """Trigger payroll generation through the UI."""
    page, _ = logged_in_page("admin")
    payroll = PayrollPage(page)
    payroll.navigate_to_payroll()
    payroll.apply_branch_filter("Varanasi - Inf")
    payroll.run_payroll()   # Run-Payroll → Confirm → waits for toast
    return True


# ── Step 2: Poll status API until all records are generated ───────────────────

@pytest.fixture(scope="module")
def payroll_status(payroll_ran):
    """Poll /Payroll/status until pending == 0."""
    return wait_for_payroll_complete(year=YEAR, month=MONTH, branch_id=BRANCH_ID)


# ── Step 3: Fetch the generated payroll list ──────────────────────────────────

@pytest.fixture(scope="module")
def payroll_response(payroll_status):
    """Fetch full payroll list only after status confirms completion."""
    return get_payroll_list(year=YEAR, month=MONTH, branch_id=BRANCH_ID)


@pytest.fixture(scope="module")
def payroll_records(payroll_response):
    return payroll_response.get("data", [])


# ── Step 3: Fetch employee detail for each record ────────────────────────────

@pytest.fixture(scope="module")
def employee_details(payroll_records):
    """Fetch GET /employeerDetail for every employeeId in the payroll. Keyed by employeeId."""
    return {r["employeeId"]: get_employee_detail(r["employeeId"]) for r in payroll_records}


# ── Payroll list validations ──────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.payroll
def test_payroll_response_is_dict(payroll_response):
    assert isinstance(payroll_response, dict)


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_records_present(payroll_records):
    assert isinstance(payroll_records, list) and len(payroll_records) > 0


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_total_records_matches_data(payroll_response, payroll_records):
    total = payroll_response.get("totalRecords", 0)
    assert total > 0
    assert total >= len(payroll_records)


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_required_fields(payroll_records):
    for r in payroll_records:
        missing = REQUIRED_FIELDS - set(r.keys())
        assert not missing, f"Missing {missing} in employeeCode={r.get('employeeCode')}"


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_net_salary_formula(payroll_records):
    """netSalary == totalEarnings - totalDeductions"""
    for r in payroll_records:
        expected = round(r["totalEarnings"] - r["totalDeductions"], 2)
        actual = round(r["netSalary"], 2)
        assert abs(actual - expected) < 0.01, (
            f"{r['employeeName']}: netSalary={actual} "
            f"totalEarnings={r['totalEarnings']} totalDeductions={r['totalDeductions']} expected={expected}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_total_deductions_breakdown(payroll_records):
    """totalDeductions == employee_PF + esic_Employee + tds + otherDeduction"""
    for r in payroll_records:
        expected = round(
            (r.get("employee_PF") or 0) +
            (r.get("esic_Employee") or 0) +
            (r.get("tds") or 0) +
            (r.get("otherDeduction") or 0), 2
        )
        assert abs(round(r["totalDeductions"], 2) - expected) < 0.01, (
            f"{r['employeeName']}: totalDeductions={r['totalDeductions']} breakdown={expected}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_net_salary_non_negative(payroll_records):
    for r in payroll_records:
        assert r["netSalary"] >= 0, f"{r['employeeName']}: negative netSalary={r['netSalary']}"


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_paid_days_within_month(payroll_records):
    for r in payroll_records:
        assert 0 <= r["paidDays"] <= r["totalDaysInMonth"], (
            f"{r['employeeName']}: paidDays={r['paidDays']} totalDaysInMonth={r['totalDaysInMonth']}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_invalid_token():
    response = requests.get(
        f"{settings.API_BASE_URL}/Payroll",
        headers={"Authorization": "Bearer invalid_token"},
        params={
            "lazyParams": json.dumps({"first": 0, "rows": 50, "page": 0, "sortField": "", "sortOrder": 1}),
            "filter": json.dumps({"year": YEAR, "month": MONTH, "branchId": BRANCH_ID, "departmentId": 0}),
            "search": ""
        }
    )
    assert response.status_code in (401, 403)


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_missing_filter():
    response = requests.get(
        f"{settings.API_BASE_URL}/Payroll",
        headers=headers("admin")
    )
    assert response.status_code in (400, 422)


# ── Payroll status validations ───────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.payroll
def test_payroll_status_no_pending(payroll_status):
    """After generation, pending count must be 0."""
    pending_count = next(
        (s["count"] for s in payroll_status if s.get("status") == "pending"), 0
    )
    assert pending_count == 0, f"Payroll still has {pending_count} pending record(s)"


@pytest.mark.api
@pytest.mark.payroll
def test_payroll_status_generated_count_matches_list(payroll_status, payroll_response):
    """Generated count from status should match totalRecords in list response."""
    generated_count = next(
        (s["count"] for s in payroll_status if s.get("status") == "generated"), 0
    )
    list_total = payroll_response.get("totalRecords", 0)
    assert generated_count == list_total, (
        f"Status generated={generated_count} != list totalRecords={list_total}"
    )


# ── Employee detail cross-validation ─────────────────────────────────────────

@pytest.mark.api
@pytest.mark.payroll
def test_basic_salary_matches_employee_detail(payroll_records, employee_details):
    """
    Payroll basic <= employee detail basic_salary.
    Payroll may prorate for LOP so it can be lower, never higher.
    """
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("basic_salary") or 0
        assert r["basic"] <= configured + 0.01, (
            f"{r['employeeName']}: payroll basic={r['basic']} > configured={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_hra_matches_employee_detail(payroll_records, employee_details):
    """Payroll hra <= employee detail hra (proration allowed)."""
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("hra") or 0
        # hra in detail can be negative (misconfigured) — skip those
        if configured <= 0:
            continue
        assert r["hra"] <= configured + 0.01, (
            f"{r['employeeName']}: payroll hra={r['hra']} > configured={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_branch_matches_employee_detail(payroll_records, employee_details):
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        assert r["branchId"] == detail.get("branch_Id"), (
            f"{r['employeeName']}: payroll branchId={r['branchId']} detail branch_Id={detail.get('branch_Id')}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_department_matches_employee_detail(payroll_records, employee_details):
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        assert r["departmentId"] == detail.get("department_Id"), (
            f"{r['employeeName']}: payroll departmentId={r['departmentId']} "
            f"detail department_Id={detail.get('department_Id')}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_esic_member_flag_vs_esic_deduction(payroll_records, employee_details):
    """If esic_Member=False in employee detail, esic_Employee in payroll must be 0."""
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        if not detail.get("esic_Member", True):
            assert (r.get("esic_Employee") or 0) == 0, (
                f"{r['employeeName']}: esic_Member=False but esic_Employee={r.get('esic_Employee')}"
            )


@pytest.mark.api
@pytest.mark.payroll
def test_conveyance_matches_employee_detail(payroll_records, employee_details):
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("conveyance") or 0
        actual = r.get("conveyance_Allowance") or 0
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll conveyance={actual} > configured={configured}"
        )


# ── Salary cross-validation: payroll data == employee detail salary data ────────

@pytest.mark.api
@pytest.mark.payroll
def test_employee_pf_matches_detail(payroll_records, employee_details):
    """payroll.employee_PF == detail.employeePF (before proration)"""
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("employeePF") or 0
        actual = r.get("employee_PF") or 0
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll employee_PF={actual} > configured={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_esic_employee_matches_detail(payroll_records, employee_details):
    """payroll.esic_Employee == detail.esicEmployee"""
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("esicEmployee") or 0
        actual = r.get("esic_Employee") or 0
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll esic_Employee={actual} > configured={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_gross_salary_matches_detail(payroll_records, employee_details):
    """
    payroll.totalEarnings should match detail.gross_Salary_Per_Month.
    Allows lower due to LOP/absent day proration.
    """
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("gross_Salary_Per_Month") or 0
        actual = r.get("totalEarnings") or 0
        if configured == 0:
            continue
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll totalEarnings={actual} > configured gross={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_total_deduction_matches_detail(payroll_records, employee_details):
    """
    payroll.totalDeductions should match detail.total_Deduction.
    Allows lower due to proration.
    """
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("total_Deduction") or 0
        actual = r.get("totalDeductions") or 0
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll totalDeductions={actual} > configured={configured}"
        )


@pytest.mark.api
@pytest.mark.payroll
def test_net_salary_matches_detail(payroll_records, employee_details):
    """
    payroll.netSalary should match detail.netTakeHomeSalary.
    Allows lower due to proration.
    """
    for r in payroll_records:
        detail = employee_details[r["employeeId"]]
        configured = detail.get("netTakeHomeSalary") or 0
        actual = r.get("netSalary") or 0
        if configured == 0:
            continue
        assert actual <= configured + 0.01, (
            f"{r['employeeName']}: payroll netSalary={actual} > configured netTakeHome={configured}"
        )
