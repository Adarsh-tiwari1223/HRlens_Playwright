"""
ESIC Salary Calculation API Validation Test Suite.
Validates:
1. Dynamic retrieval of salary calculation settings for (Company, Branch, Department).
2. Toggling is_ESIC_Required via PUT /SalaryCalculationSettings/{id}/esic-status.
3. Employee salary calculation when ESIC is Disabled (is_ESIC_Required == False).
4. Employee salary calculation when ESIC is Enabled (is_ESIC_Required == True, Gross <= limit).
   - Employee ESIC: Gross * 0.75% (deducted from Net)
   - Employer ESIC: Gross * 3.25% (added to CTC)
5. Employee salary calculation when Gross > ESIC Wage Limit (ESIC auto-suppressed to 0).
6. Scope isolation: Setting changes apply strictly to the targeted Company/Branch/Department.
7. Clean automatic teardown restoring baseline setting and employee salary.
"""

import copy
import logging
import pytest
from typing import Dict, Any, Tuple
from core.config import settings
from utils.api.payroll.salary_settings_api import (
    get_salary_calculation_settings,
    update_esic_status,
    update_employee_salary_api,
    _get_api_token
)
from utils.api.payroll.payroll_api import get_employee_detail, get

logger = logging.getLogger(__name__)


def _build_salary_payload(
    emp_id: int,
    gross_salary: float,
    basic_salary: float,
    hra: float,
    employee_pf: float,
    employer_pf: float,
    esic_applicable: bool,
    esic_employee: float,
    esic_employer: float,
    employment_type: str = "EMPLOYEE"
) -> Dict[str, Any]:
    """Builds a complete PostEditEmpSalary payload matching backend C# ViewModel."""
    total_deductions = employee_pf + esic_employee
    net_salary = round(gross_salary - total_deductions, 2)
    monthly_ctc = round(gross_salary + employer_pf + esic_employer, 2)
    annual_ctc = round(monthly_ctc * 12.0, 2)
    gross_annual = round(gross_salary * 12.0, 2)

    return {
        "empId": emp_id,
        "gross_Salary": gross_salary,
        "net_Salary": net_salary,
        "annualCTC": annual_ctc,
        "basic_salary": basic_salary,
        "conveyance": 0.0,
        "employerPF": employer_pf,
        "employeePF": employee_pf,
        "esic_Applicable": esic_applicable,
        "esicEmployee": esic_employee,
        "esicEmployer": esic_employer,
        "gross_Salary_per_anum": gross_annual,
        "hra": hra,
        "monthlyCTC": monthly_ctc,
        "meal_Allowance_Applied": False,
        "meal_Allowance_Amount": 0.0,
        "transport_Allowance_Applied": False,
        "transport_Allowance_Amount": 0.0,
        "health_Insurance_Applied": False,
        "health_Insurance_Amount": 0.0,
        "net_Take_Home_Salary": net_salary,
        "basic_Salary_For_PF": 15000.0,
        "includePF": True,
        "employement_Type": employment_type,
        "intern_Payment_Type": None
    }


@pytest.fixture(scope="module")
def scoped_employee_and_setting() -> Dict[str, Any]:
    """
    Finds or resolves a matching (Company, Branch, Department) setting with active wage limit
    and an active employee belonging to that exact hierarchy.
    Captures initial baseline state for guaranteed teardown.
    """
    # Target verified scope: GVR Infotek LLC / Noida / US Account (Setting 1208, Emp 2708)
    recs = get_salary_calculation_settings()
    setting = next((r for r in recs if r.get("id") == 1208), None)
    emp_id = 2708

    # Fallback to dynamic resolution if setting 1208 is not present
    if not setting:
        rec_map = {
            (r.get("company_Name", "").strip().lower(),
             r.get("branch_Name", "").strip().lower(),
             r.get("department_Name", "").strip().lower()): r
            for r in recs if (r.get("esiC_Wage_Limit") or 0) > 0
        }
        emps = get("DropDown/getEmployeeList") or []
        for e in emps[:100]:
            d = get_employee_detail(e["id"])
            if not d or not isinstance(d, dict):
                continue
            key = (
                (d.get("us_Company") or "").strip().lower(),
                (d.get("branch") or "").strip().lower(),
                (d.get("department") or "").strip().lower()
            )
            if key in rec_map:
                setting = rec_map[key]
                emp_id = e["id"]
                break

    assert setting, "No salary calculation setting with active ESIC wage limit found!"
    assert emp_id, "No active employee found matching the salary calculation setting scope!"

    baseline_detail = get_employee_detail(emp_id)
    assert baseline_detail, f"Could not fetch baseline employeerDetail for employee {emp_id}"

    baseline_esic_required = setting.get("is_ESIC_Required", False)
    wage_limit = float(setting.get("esiC_Wage_Limit") or 21000.0)
    emp_pct = float(setting.get("esiC_Employee_Percentage") or 0.75)
    empr_pct = float(setting.get("esiC_Employer_Percentage") or 3.25)
    min_basic = float(setting.get("min_Basic") or 16870.0)

    context = {
        "setting_id": setting["id"],
        "emp_id": emp_id,
        "company": setting.get("company_Name"),
        "branch": setting.get("branch_Name"),
        "department": setting.get("department_Name"),
        "wage_limit": wage_limit,
        "emp_pct": emp_pct,
        "empr_pct": empr_pct,
        "min_basic": min_basic,
        "baseline_detail": copy.deepcopy(baseline_detail),
        "baseline_esic_required": baseline_esic_required
    }

    logger.info(
        f"[TEST FIXTURE] Resolved scope -> Company: '{context['company']}' | "
        f"Branch: '{context['branch']}' | Dept: '{context['department']}' | "
        f"Setting ID: {context['setting_id']} | Employee ID: {context['emp_id']}"
    )

    yield context

    # ── Final Teardown after all tests in module ──────────────────────────────
    logger.info(f"[MODULE TEARDOWN] Restoring Setting {context['setting_id']} and Employee {context['emp_id']}")
    update_esic_status(context["setting_id"], context["baseline_esic_required"])

    b = context["baseline_detail"]
    baseline_payload = _build_salary_payload(
        emp_id=context["emp_id"],
        gross_salary=float(b.get("gross_Salary_Per_Month") or 25000.0),
        basic_salary=float(b.get("basic_salary") or min_basic),
        hra=float(b.get("hra") or 8130.0),
        employee_pf=float(b.get("employeePF") or 1800.0),
        employer_pf=float(b.get("employerPF") or 1800.0),
        esic_applicable=bool(b.get("esic_Member", False)),
        esic_employee=float(b.get("esicEmployee") or 0.0),
        esic_employer=float(b.get("esicEmployer") or 0.0)
    )
    update_employee_salary_api(context["emp_id"], baseline_payload)


@pytest.fixture(autouse=True)
def per_test_cleanup(scoped_employee_and_setting):
    """Guarantees per-test clean state before and after each test."""
    ctx = scoped_employee_and_setting
    yield
    # Restore setting to baseline
    update_esic_status(ctx["setting_id"], ctx["baseline_esic_required"])


@pytest.mark.api
@pytest.mark.salary
def test_esic_status_toggle_idempotency(scoped_employee_and_setting):
    """
    Validates that PUT /SalaryCalculationSettings/{id}/esic-status updates the toggle
    and preserves other setting fields without corruption.
    """
    ctx = scoped_employee_and_setting
    setting_id = ctx["setting_id"]

    # Toggle to True
    res_true = update_esic_status(setting_id, True)
    assert res_true.get("is_ESIC_Required") is True
    assert "successfully" in res_true.get("message", "").lower()

    # Verify setting in settings list
    recs = get_salary_calculation_settings()
    s = next((r for r in recs if r.get("id") == setting_id), None)
    assert s is not None
    assert s.get("is_ESIC_Required") is True
    assert float(s.get("esiC_Wage_Limit") or 0.0) == ctx["wage_limit"]

    # Toggle to False
    res_false = update_esic_status(setting_id, False)
    assert res_false.get("is_ESIC_Required") is False

    recs_after = get_salary_calculation_settings()
    s_after = next((r for r in recs_after if r.get("id") == setting_id), None)
    assert s_after.get("is_ESIC_Required") is False


@pytest.mark.api
@pytest.mark.salary
def test_esic_disabled_when_setting_is_false(scoped_employee_and_setting):
    """
    RULE: When is_ESIC_Required == False and Gross <= Wage Limit,
    ESIC must NOT be deducted or contributed (esicEmployee = 0, esicEmployer = 0).
    """
    ctx = scoped_employee_and_setting
    emp_id = ctx["emp_id"]
    setting_id = ctx["setting_id"]

    # 1. Ensure Setting is False
    update_esic_status(setting_id, False)

    # 2. Update employee with Gross = 20000 (<= 21000 limit)
    test_gross = 20000.0
    basic = ctx["min_basic"]
    hra = test_gross - basic
    emp_pf = 1800.0
    empr_pf = 1800.0

    payload = _build_salary_payload(
        emp_id=emp_id,
        gross_salary=test_gross,
        basic_salary=basic,
        hra=hra,
        employee_pf=emp_pf,
        employer_pf=empr_pf,
        esic_applicable=False,
        esic_employee=0.0,
        esic_employer=0.0
    )
    success = update_employee_salary_api(emp_id, payload)
    assert success, f"Failed to update employee salary for emp_id={emp_id}"

    # 3. Fetch employeerDetail from backend and assert
    detail = get_employee_detail(emp_id)
    assert float(detail["gross_Salary_Per_Month"]) == test_gross
    assert float(detail["esicEmployee"]) == 0.0, "ESIC Employee must be 0 when setting is False"
    assert float(detail["esicEmployer"]) == 0.0, "ESIC Employer must be 0 when setting is False"

    expected_net = test_gross - emp_pf
    expected_monthly_ctc = test_gross + empr_pf
    assert float(detail["netTakeHomeSalary"]) == expected_net
    assert float(detail["monthlyCTC"]) == expected_monthly_ctc
    assert float(detail["annualCTC"]) == expected_monthly_ctc * 12.0


@pytest.mark.api
@pytest.mark.salary
def test_esic_calculated_when_setting_is_true_and_eligible(scoped_employee_and_setting):
    """
    RULE: When is_ESIC_Required == True and Gross <= Wage Limit:
    - Employee ESIC = Gross * 0.75% (Deducted from Net)
    - Employer ESIC = Gross * 3.25% (Added to Monthly CTC)
    - Net Take Home = Gross - (PF + Employee ESIC)
    - Monthly CTC   = Gross + Employer PF + Employer ESIC
    - Annual CTC    = Monthly CTC * 12
    """
    ctx = scoped_employee_and_setting
    emp_id = ctx["emp_id"]
    setting_id = ctx["setting_id"]

    # 1. Enable ESIC on Setting
    update_esic_status(setting_id, True)

    # 2. Update employee with Gross = 20000 (<= 21000 limit)
    test_gross = 20000.0
    basic = ctx["min_basic"]
    hra = test_gross - basic
    emp_pf = 1800.0
    empr_pf = 1800.0

    expected_esic_emp = round(test_gross * (ctx["emp_pct"] / 100.0), 2)   # 20000 * 0.0075 = 150.0
    expected_esic_empr = round(test_gross * (ctx["empr_pct"] / 100.0), 2) # 20000 * 0.0325 = 650.0

    payload = _build_salary_payload(
        emp_id=emp_id,
        gross_salary=test_gross,
        basic_salary=basic,
        hra=hra,
        employee_pf=emp_pf,
        employer_pf=empr_pf,
        esic_applicable=True,
        esic_employee=expected_esic_emp,
        esic_employer=expected_esic_empr
    )
    success = update_employee_salary_api(emp_id, payload)
    assert success, f"Failed to update employee salary for emp_id={emp_id}"

    # 3. Validate recalculated values from backend
    detail = get_employee_detail(emp_id)
    assert float(detail["gross_Salary_Per_Month"]) == test_gross
    assert float(detail["esicEmployee"]) == expected_esic_emp, f"Expected Employee ESIC {expected_esic_emp}"
    assert float(detail["esicEmployer"]) == expected_esic_empr, f"Expected Employer ESIC {expected_esic_empr}"

    expected_deductions = emp_pf + expected_esic_emp
    expected_net = test_gross - expected_deductions
    expected_monthly_ctc = test_gross + empr_pf + expected_esic_empr
    expected_annual_ctc = expected_monthly_ctc * 12.0

    assert float(detail["total_Deduction"]) == expected_deductions
    assert float(detail["netTakeHomeSalary"]) == expected_net
    assert float(detail["monthlyCTC"]) == expected_monthly_ctc
    assert float(detail["annualCTC"]) == expected_annual_ctc


@pytest.mark.api
@pytest.mark.salary
def test_esic_suppressed_when_gross_exceeds_wage_limit(scoped_employee_and_setting):
    """
    RULE: When Gross > Wage Limit (e.g., 25000 > 21000):
    Even if is_ESIC_Required == True, ESIC must be 0 (ineligible).
    """
    ctx = scoped_employee_and_setting
    emp_id = ctx["emp_id"]
    setting_id = ctx["setting_id"]

    # 1. Enable ESIC on Setting
    update_esic_status(setting_id, True)

    # 2. Update employee with Gross = 25000 (> 21000 limit)
    test_gross = 25000.0
    basic = ctx["min_basic"]
    hra = test_gross - basic
    emp_pf = 1800.0
    empr_pf = 1800.0

    # Ineligible because Gross > Wage Limit
    payload = _build_salary_payload(
        emp_id=emp_id,
        gross_salary=test_gross,
        basic_salary=basic,
        hra=hra,
        employee_pf=emp_pf,
        employer_pf=empr_pf,
        esic_applicable=False,
        esic_employee=0.0,
        esic_employer=0.0
    )
    success = update_employee_salary_api(emp_id, payload)
    assert success, f"Failed to update employee salary for emp_id={emp_id}"

    # 3. Validate ESIC is 0 in backend
    detail = get_employee_detail(emp_id)
    assert float(detail["gross_Salary_Per_Month"]) == test_gross
    assert float(detail["esicEmployee"]) == 0.0, "ESIC Employee must be 0 when Gross exceeds wage limit"
    assert float(detail["esicEmployer"]) == 0.0, "ESIC Employer must be 0 when Gross exceeds wage limit"

    expected_net = test_gross - emp_pf
    expected_monthly_ctc = test_gross + empr_pf
    assert float(detail["netTakeHomeSalary"]) == expected_net
    assert float(detail["monthlyCTC"]) == expected_monthly_ctc


@pytest.mark.api
@pytest.mark.salary
def test_esic_setting_scope_isolation(scoped_employee_and_setting):
    """
    RULE: Changes to a setting in (Company A, Branch A, Dept A)
    must NOT alter or contaminate employees belonging to a different branch/department.
    """
    ctx = scoped_employee_and_setting
    other_emp_id = 10599  # Ritesh Yadav (Agra Branch / IT Department)

    other_baseline = get_employee_detail(other_emp_id)
    assert other_baseline, f"Could not fetch employeerDetail for other employee {other_emp_id}"

    other_branch = other_baseline.get("branch")
    other_dept = other_baseline.get("department")
    assert (other_branch, other_dept) != (ctx["branch"], ctx["department"]), \
        "Other employee must belong to a different branch/department for isolation test"

    # Toggle our scoped setting
    update_esic_status(ctx["setting_id"], True)

    # Verify other employee's salary structure remains completely unchanged
    other_after = get_employee_detail(other_emp_id)
    assert float(other_after["gross_Salary_Per_Month"]) == float(other_baseline["gross_Salary_Per_Month"])
    assert float(other_after["netTakeHomeSalary"]) == float(other_baseline["netTakeHomeSalary"])
    assert float(other_after["monthlyCTC"]) == float(other_baseline["monthlyCTC"])
