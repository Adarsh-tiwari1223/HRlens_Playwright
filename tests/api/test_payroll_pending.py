import os
import pytest
from datetime import datetime
from utils.api.payroll_api import (
    get_payroll_status,
    get_payroll_list,
    get_employee_detail,
    get_bank_detail,
    get_balance_leave,
    get_branches,
    find_branch_id,
)

YEAR = 2026
MONTH = 4
BRANCH_NAME = "Varanasi"
COMPANY_NAME = "TEK Inspirations LLC"  # set to None if branch name is unique
BRANCH_ID = find_branch_id(BRANCH_NAME, COMPANY_NAME)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pending_employees():
    status_list = get_payroll_status(year=YEAR, month=MONTH, branch_id=BRANCH_ID)
    pending_count = next(
        (s["count"] for s in status_list if s.get("status") == "pending"), 0
    )
    if pending_count == 0:
        pytest.skip("No pending employees — payroll fully generated.")
    response = get_payroll_list(year=YEAR, month=MONTH, branch_id=BRANCH_ID, status="pending")
    records = response.get("data", [])
    assert records, f"Status shows {pending_count} pending but /Payroll returned empty list"
    return records


@pytest.fixture(scope="module")
def pending_employee_data(pending_employees):
    result = []
    for emp in pending_employees:
        result.append({
            "employeeId":   emp["employeeId"],
            "employeeName": emp["employeeName"].strip(),
            "employeeCode": emp["employeeCode"],
            "record":       emp,
            "detail":       get_employee_detail(emp["employeeId"]),
            "bank":         get_bank_detail(emp["employeeId"]),
            "leave":        get_balance_leave(emp["employeeId"]),
        })
    return result


# ── Blocker checker ───────────────────────────────────────────────────────────

def _missing_blockers(e: dict) -> list[str]:
    r  = e["record"]   # payroll list record  — fields 1-4
    d  = e["detail"]   # employee detail      — fields 5, 6, 7, 9
    b  = e["bank"]     # bank detail          — field 10
    lv = e["leave"]    # balance leave        — field 8

    missing = []

    # 1. Payroll Company — from payroll record
    if not r.get("payrollCompanyId"):
        missing.append("Payroll Company (payrollCompanyId is null/0)")

    # 2. Company — from payroll record
    if not r.get("companyId"):
        missing.append("Company (companyId is null/0)")

    # 3. Branch — from payroll record
    if not r.get("branchId"):
        missing.append("Branch (branchId is null/0)")

    # 4. Department — from payroll record
    if not r.get("departmentId"):
        missing.append("Department (departmentId is null/0)")

    # 5. Shift — from employee detail (shift is an int ID, 0 means not set)
    if not d.get("shift"):
        missing.append("Shift (shift is null/0)")

    # 6. Business Process — from employee detail (empty string is also a blocker)
    if not (d.get("business_Process") or "").strip():
        missing.append("Business Process (business_Process is null/empty)")

    # 7. Date of Joining — from employee detail
    if not d.get("date_Of_Joining"):
        missing.append("Date of Joining (date_Of_Joining is null)")

    # 8. Balance Leave — balanceLeaves key, empty list = not configured
    if not lv.get("balanceLeaves"):
        missing.append("Balance Leave (balanceLeaves is empty)")

    # 9. Salary — basic_salary from employee detail must be > 0
    if not (d.get("basic_salary") or 0) > 0:
        missing.append(
            f"Salary (basic_salary={d.get('basic_salary')}, "
            f"gross_Salary_Per_Month={d.get('gross_Salary_Per_Month')})"
        )

    # 10. Bank Details — returns {"message": "No Data Found"} when missing
    account = b.get("account_Number")
    ifsc    = b.get("ifsc_Code")
    if not account or not ifsc:
        parts = []
        if not account: parts.append("account_Number")
        if not ifsc:    parts.append("ifsc_Code")
        missing.append(f"Bank Details ({', '.join(parts)} is null/missing)")

    return missing


# ── Single test: full report ──────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.payroll
def test_pending_payroll_blocker_report(pending_employee_data):
    total = len(pending_employee_data)
    blocked_by = {}  # field -> list of names
    all_blocked = []

    for e in pending_employee_data:
        missing = _missing_blockers(e)
        name = f"{e['employeeName']} (code: {e['employeeCode']})"
        if missing:
            all_blocked.append(name)
            for m in missing:
                # extract clean field name before the first '('
                field = m.split(" (")[0]
                blocked_by.setdefault(field, []).append(name)

    # ── Resolve branch + company name from branch list ───────────────────────────
    branches = get_branches()
    branch_info = next((b for b in branches if b["id"] == BRANCH_ID), {})
    branch_name  = branch_info.get("branch_Name", f"Branch {BRANCH_ID}")
    company_name = branch_info.get("company_Name", "Unknown Company")

    # ── Build summary report ──────────────────────────────────────────────────
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"PENDING PAYROLL BLOCKER REPORT — {company_name} | {branch_name} | Month: {MONTH}/{YEAR} — {total} employees")
    lines.append(f"{'='*70}")

    if all_blocked:
        lines.append(f"\n{len(all_blocked)}/{total} BLOCKED:")
        for i, name in enumerate(all_blocked, 1):
            lines.append(f"  {i}. {name}")

    lines.append("\nBLOCKER BREAKDOWN:")
    for field, names in sorted(blocked_by.items(), key=lambda x: -len(x[1])):
        lines.append(f"\n  {len(names)} missing '{field}':")
        for i, name in enumerate(names, 1):
            lines.append(f"    {i}. {name}")

    lines.append(f"\n{'='*70}")
    report = "\n".join(lines)

    # ── Save to reports/payroll_release_<YYYY-MM-DD>.txt ───────────────────────
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/payroll_release_{datetime.today().strftime('%Y-%m-%d')}.txt"
    section_marker = f"{company_name} | {branch_name} | Month: {MONTH}/{YEAR}"

    if os.path.exists(filename):
        existing = open(filename, "r", encoding="utf-8").read()
        if section_marker in existing:
            # Replace the existing section for this branch+month
            import re
            pattern = re.compile(
                r"={70}\nPENDING PAYROLL BLOCKER REPORT — " + re.escape(section_marker) + r".*?={70}",
                re.DOTALL
            )
            updated = pattern.sub(report.strip().lstrip("\n"), existing)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(updated)
        else:
            # Append new section for different branch/month
            with open(filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + report)
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

    if all_blocked:
        pytest.fail(report)
