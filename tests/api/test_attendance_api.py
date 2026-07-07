import calendar
import pytest
import requests
from core.config import settings
from utils.api.attendance_api import get_attendance_summary
from utils.api.payroll_api import get_payroll_list, find_branch_id

YEAR         = 2026
MONTH        = 4
FROM_DATE    = f"{YEAR}-{MONTH:02d}-01"
TO_DATE      = f"{YEAR}-{MONTH:02d}-{calendar.monthrange(YEAR, MONTH)[1]}"
BRANCH_NAME  = "Varanasi"
COMPANY_NAME = "TEK Inspirations LLC"

@pytest.fixture(scope="module")
def branch_id():
    return find_branch_id(BRANCH_NAME, COMPANY_NAME)

REQUIRED_ATTENDANCE_FIELDS = {"employeeId", "employeeName", "present", "absent", "halfDay", "totalDays"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def payroll_records(branch_id):
    """Only generated records have meaningful salary data."""
    records = get_payroll_list(year=YEAR, month=MONTH, branch_id=branch_id).get("data", [])
    generated = [r for r in records if r.get("status") == "generated"]
    if not generated:
        pytest.skip("No generated payroll records — skipping attendance tests.")
    return generated


@pytest.fixture(scope="module")
def attendance_records():
    """All attendance records keyed by employeeId."""
    return {r["employeeId"]: r for r in get_attendance_summary(FROM_DATE, TO_DATE)}


# ── Attendance validations ────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.attendance
def test_attendance_records_present(attendance_records):
    assert len(attendance_records) > 0, "No attendance records returned"


@pytest.mark.api
@pytest.mark.attendance
def test_attendance_required_fields(attendance_records):
    for emp_id, a in attendance_records.items():
        missing = REQUIRED_ATTENDANCE_FIELDS - set(a.keys())
        assert not missing, f"employeeId={emp_id}: missing fields {missing}"


@pytest.mark.api
@pytest.mark.attendance
def test_attendance_no_negative_values(attendance_records):
    for a in attendance_records.values():
        for field in ("present", "absent", "halfDay", "totalDays"):
            assert a[field] >= 0, f"{a['employeeName']}: {field}={a[field]} is negative"


@pytest.mark.api
@pytest.mark.attendance
def test_attendance_present_plus_absent_within_total(attendance_records):
    for a in attendance_records.values():
        assert a["present"] + a["absent"] <= a["totalDays"], (
            f"{a['employeeName']}: present={a['present']} + absent={a['absent']} "
            f"> totalDays={a['totalDays']}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_attendance_invalid_token():
    response = requests.get(
        f"{settings.API_BASE_URL}/Hrlense_Attendance/employee-attendance-summary",
        headers={"Authorization": "Bearer invalid_token"},
        params={"name": "", "from": FROM_DATE, "to": TO_DATE, "filters": "{}"}
    )
    assert response.status_code in (401, 403)


# ── LOP formula ───────────────────────────────────────────────────────────────

def _safe_float(val) -> float:
    """Convert API value to float, returning 0.0 for null/-- /empty."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _compute(absent: float, half_day: float, balance_leave: float, gross: float, total_days: int,
             incentive: float, other_earning: float,
             conveyance: float, health_ins: float, transport: float, meal: float,
             emp_pf: float, esic_emp: float, tds: float, other_deduction: float):
    leave_required  = absent + (half_day / 2)
    leave_used      = min(balance_leave, leave_required)
    lop             = leave_required - leave_used
    paid_days       = total_days - lop
    new_balance     = balance_leave - leave_used
    per_day_salary  = gross / total_days if total_days else 0
    earned_salary   = paid_days * per_day_salary
    allowances      = conveyance + health_ins + transport + meal
    total_earnings  = earned_salary + incentive + other_earning + allowances
    total_deductions = emp_pf + esic_emp + tds + other_deduction
    net_salary      = total_earnings - total_deductions
    return {
        "leave_required": leave_required,
        "leave_used": leave_used,
        "lop": lop,
        "paid_days": paid_days,
        "new_balance": new_balance,
        "per_day_salary": per_day_salary,
        "earned_salary": earned_salary,
        "total_earnings": total_earnings,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
    }


# ── Payroll formula validations ──────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.attendance
def test_total_deductions_formula(payroll_records):
    """totalDeductions == employee_PF + esic_Employee + tds + otherDeduction"""
    for p in payroll_records:
        expected = round(p["employee_PF"] + p["esic_Employee"] + p["tds"] + p["otherDeduction"], 2)
        actual   = round(p["totalDeductions"], 2)
        assert abs(actual - expected) < 0.01, (
            f"{p['employeeName']}: totalDeductions={actual} != "
            f"employee_PF={p['employee_PF']} + esic_Employee={p['esic_Employee']} "
            f"+ tds={p['tds']} + otherDeduction={p['otherDeduction']} = {expected}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_net_salary_formula(payroll_records):
    """netSalary == grossSalary - (employee_PF + esic_Employee)"""
    for p in payroll_records:
        gross    = _safe_float(p["grossSalary"])
        expected = round(gross - (p["employee_PF"] + p["esic_Employee"]), 2)
        actual   = round(p["netSalary"], 2)
        assert abs(actual - expected) < 0.01, (
            f"{p['employeeName']}: netSalary={actual} != "
            f"grossSalary={gross} - (employee_PF={p['employee_PF']} + esic_Employee={p['esic_Employee']}) = {expected}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_net_salary_matches_employee_detail(payroll_records):
    """payroll.netSalary == employeeDetail.netTakeHomeSalary"""
    from utils.api.payroll_api import get_employee_detail
    for p in payroll_records:
        detail = get_employee_detail(p["employeeId"])
        net_take_home = detail.get("netTakeHomeSalary") or 0
        if net_take_home == 0:
            continue
        assert p["netSalary"] == net_take_home, (
            f"{p['employeeName']}: payroll netSalary={p['netSalary']} != "
            f"detail netTakeHomeSalary={net_take_home}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_per_day_salary(payroll_records):
    """perDaySalary = netSalary / totalDaysInMonth — must be > 0 for all generated records."""
    for p in payroll_records:
        if not p["totalDaysInMonth"] or not p["netSalary"]:
            continue
        per_day = round(p["netSalary"] / p["totalDaysInMonth"], 2)
        assert per_day > 0, (
            f"{p['employeeName']}: perDaySalary={per_day} "
            f"(netSalary={p['netSalary']} / totalDaysInMonth={p['totalDaysInMonth']})"
        )


# ── Payroll month validation ──────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.attendance
def test_payroll_month_is_previous_month(payroll_records):
    """payrollMonth must equal the run month (YYYY-MM-01)."""
    for p in payroll_records:
        expected = f"{p['year']}-{p['month']:02d}-01"
        actual   = p["payrollMonth"][:10]
        assert actual != "0001-01-01", (
            f"{p['employeeName']}: payrollMonth is unset (0001-01-01) — backend did not populate it"
        )
        assert actual == expected, (
            f"{p['employeeName']}: payrollMonth={actual} != expected={expected}"
        )


# ── Attendance ↔ Payroll cross-validation ─────────────────────────────────────

@pytest.mark.api
@pytest.mark.attendance
def test_attendance_fetched_for_all_payroll_employees(payroll_records, attendance_records):
    missing = [p["employeeName"] for p in payroll_records if p["employeeId"] not in attendance_records]
    assert not missing, f"No attendance data for: {missing}"


@pytest.mark.api
@pytest.mark.attendance
def test_lop_matches_payroll(payroll_records, attendance_records):
    for p in payroll_records:
        a = attendance_records.get(p["employeeId"])
        if a is None:
            continue
        c = _compute(
            a["absent"], a["halfDay"], _safe_float(p["balance_Leave"]),
            _safe_float(p["grossSalary"]), p["totalDaysInMonth"],
            p["incentive"], p["otherEarning"],
            p["conveyance_Allowance"], p["health_Insurance_Amount"],
            p["transport_Allowance_Amount"], p["meal_Allowance_Amount"],
            p["employee_PF"], p["esic_Employee"], p["tds"], p["otherDeduction"],
        )
        assert abs(p["lop"] - c["lop"]) < 0.01, (
            f"{p['employeeName']}: absent={a['absent']} halfDay={a['halfDay']} "
            f"balance_Leave={p['balance_Leave']} → computed lop={c['lop']} != payroll lop={p['lop']}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_paid_days_matches_payroll(payroll_records, attendance_records):
    for p in payroll_records:
        a = attendance_records.get(p["employeeId"])
        if a is None:
            continue
        c = _compute(
            a["absent"], a["halfDay"], _safe_float(p["balance_Leave"]),
            _safe_float(p["grossSalary"]), p["totalDaysInMonth"],
            p["incentive"], p["otherEarning"],
            p["conveyance_Allowance"], p["health_Insurance_Amount"],
            p["transport_Allowance_Amount"], p["meal_Allowance_Amount"],
            p["employee_PF"], p["esic_Employee"], p["tds"], p["otherDeduction"],
        )
        assert abs(p["paidDays"] - c["paid_days"]) < 0.01, (
            f"{p['employeeName']}: computed paidDays={c['paid_days']} != payroll paidDays={p['paidDays']}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_total_earnings_matches_payroll(payroll_records, attendance_records):
    for p in payroll_records:
        a = attendance_records.get(p["employeeId"])
        if a is None:
            continue
        c = _compute(
            a["absent"], a["halfDay"], _safe_float(p["balance_Leave"]),
            _safe_float(p["grossSalary"]), p["totalDaysInMonth"],
            p["incentive"], p["otherEarning"],
            p["conveyance_Allowance"], p["health_Insurance_Amount"],
            p["transport_Allowance_Amount"], p["meal_Allowance_Amount"],
            p["employee_PF"], p["esic_Employee"], p["tds"], p["otherDeduction"],
        )
        assert abs(p["totalEarnings"] - c["total_earnings"]) < 0.01, (
            f"{p['employeeName']}: computed totalEarnings={c['total_earnings']} != payroll={p['totalEarnings']}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_total_deductions_matches_payroll(payroll_records, attendance_records):
    for p in payroll_records:
        a = attendance_records.get(p["employeeId"])
        if a is None:
            continue
        c = _compute(
            a["absent"], a["halfDay"], _safe_float(p["balance_Leave"]),
            _safe_float(p["grossSalary"]), p["totalDaysInMonth"],
            p["incentive"], p["otherEarning"],
            p["conveyance_Allowance"], p["health_Insurance_Amount"],
            p["transport_Allowance_Amount"], p["meal_Allowance_Amount"],
            p["employee_PF"], p["esic_Employee"], p["tds"], p["otherDeduction"],
        )
        assert abs(p["totalDeductions"] - c["total_deductions"]) < 0.01, (
            f"{p['employeeName']}: computed totalDeductions={c['total_deductions']} != payroll={p['totalDeductions']}"
        )


@pytest.mark.api
@pytest.mark.attendance
def test_net_salary_matches_payroll(payroll_records, attendance_records):
    for p in payroll_records:
        a = attendance_records.get(p["employeeId"])
        if a is None:
            continue
        c = _compute(
            a["absent"], a["halfDay"], _safe_float(p["balance_Leave"]),
            _safe_float(p["grossSalary"]), p["totalDaysInMonth"],
            p["incentive"], p["otherEarning"],
            p["conveyance_Allowance"], p["health_Insurance_Amount"],
            p["transport_Allowance_Amount"], p["meal_Allowance_Amount"],
            p["employee_PF"], p["esic_Employee"], p["tds"], p["otherDeduction"],
        )
        assert abs(p["netSalary"] - c["net_salary"]) < 0.01, (
            f"{p['employeeName']}: computed netSalary={c['net_salary']} != payroll={p['netSalary']}"
        )
