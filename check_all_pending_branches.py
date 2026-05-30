import os
import re
import json
from datetime import datetime
from utils.api.payroll_api import (
    get_branches,
    get_payroll_status,
    get_payroll_list,
    get_employee_detail,
    get_bank_detail,
    get_balance_leave
)

YEAR = 2026
MONTH = 4

def _missing_blockers(e: dict) -> list[str]:
    r  = e["record"]   # payroll list record  — fields 1-4
    d  = e["detail"]   # employee detail      — fields 5, 6, 7, 9
    b  = e["bank"]     # bank detail          — field 10
    lv = e["leave"]    # balance leave        — field 8

    missing = []

    # 1. Payroll Company
    if not r.get("payrollCompanyId"):
        missing.append("Payroll Company (payrollCompanyId is null/0)")

    # 2. Company
    if not r.get("companyId"):
        missing.append("Company (companyId is null/0)")

    # 3. Branch
    if not r.get("branchId"):
        missing.append("Branch (branchId is null/0)")

    # 4. Department
    if not r.get("departmentId"):
        missing.append("Department (departmentId is null/0)")

    # 5. Shift
    if not d.get("shift"):
        missing.append("Shift (shift is null/0)")

    # 6. Business Process
    if not (d.get("business_Process") or "").strip():
        missing.append("Business Process (business_Process is null/empty)")

    # 7. Date of Joining
    if not d.get("date_Of_Joining"):
        missing.append("Date of Joining (date_Of_Joining is null)")

    # 8. Balance Leave
    if not lv.get("balanceLeaves"):
        missing.append("Balance Leave (balanceLeaves is empty)")

    # 9. Salary
    if not (d.get("basic_salary") or 0) > 0:
        missing.append(
            f"Salary (basic_salary={d.get('basic_salary')}, "
            f"gross_Salary_Per_Month={d.get('gross_Salary_Per_Month')})"
        )

    # 10. Bank Details
    account = b.get("account_Number")
    ifsc    = b.get("ifsc_Code")
    if not account or not ifsc:
        parts = []
        if not account: parts.append("account_Number")
        if not ifsc:    parts.append("ifsc_Code")
        missing.append(f"Bank Details ({', '.join(parts)} is null/missing)")

    return missing

try:
    print("==================================================")
    print("SCANNING ALL SYSTEM BRANCHES FOR PENDING PAYROLLS")
    print("==================================================")
    
    branches = get_branches()
    print(f"Total system branches found: {len(branches)}")
    
    pending_branches_count = 0
    total_pending_records = 0
    all_reports = []
    
    # Track branches with pending payrolls
    for idx, b in enumerate(branches, 1):
        branch_id = b["id"]
        branch_name = b.get("branch_Name", f"Branch {branch_id}")
        company_name = b.get("company_Name", "Unknown Company")
        
        # Get payroll status
        try:
            status_list = get_payroll_status(year=YEAR, month=MONTH, branch_id=branch_id)
        except Exception:
            continue
            
        pending_count = next(
            (s["count"] for s in status_list if s.get("status") == "pending"), 0
        )
        
        if pending_count > 0:
            pending_branches_count += 1
            total_pending_records += pending_count
            print(f"\n[{pending_branches_count}] Branch '{branch_name}' ({company_name}) has {pending_count} PENDING records!")
            
            # Fetch pending records
            try:
                response = get_payroll_list(year=YEAR, month=MONTH, branch_id=branch_id, status="pending")
                records = response.get("data", [])
            except Exception as e:
                print(f"  Error fetching payroll list: {e}")
                continue
                
            # Gather details
            pending_data = []
            for emp in records:
                emp_id = emp["employeeId"]
                print(f"  - Gathering details for employee '{emp.get('employeeName')}' (ID: {emp_id})...")
                try:
                    detail = get_employee_detail(emp_id)
                except Exception:
                    detail = {}
                try:
                    bank = get_bank_detail(emp_id)
                except Exception:
                    bank = {}
                try:
                    leave = get_balance_leave(emp_id)
                except Exception:
                    leave = {}
                    
                pending_data.append({
                    "employeeId":   emp_id,
                    "employeeName": emp.get("employeeName", "Unknown").strip(),
                    "employeeCode": emp.get("employeeCode", ""),
                    "record":       emp,
                    "detail":       detail,
                    "bank":         bank,
                    "leave":        leave,
                })
                
            # Run blocker checks
            blocked_by = {}
            all_blocked = []
            
            for e in pending_data:
                missing = _missing_blockers(e)
                name = f"{e['employeeName']} (code: {e['employeeCode']})"
                if missing:
                    all_blocked.append(name)
                    for m in missing:
                        field = m.split(" (")[0]
                        blocked_by.setdefault(field, []).append(name)
                        
            # Build report section
            lines = []
            lines.append("=" * 70)
            lines.append(f"PENDING PAYROLL BLOCKER REPORT — {company_name} | {branch_name} | Month: {MONTH}/{YEAR} — {len(pending_data)} employees")
            lines.append("=" * 70)
            
            if all_blocked:
                lines.append(f"\n{len(all_blocked)}/{len(pending_data)} BLOCKED:")
                for i, name in enumerate(all_blocked, 1):
                    lines.append(f"  {i}. {name}")
                    
            lines.append("\nBLOCKER BREAKDOWN:")
            for field, names in sorted(blocked_by.items(), key=lambda x: -len(x[1])):
                lines.append(f"\n  {len(names)} missing '{field}':")
                for i, name in enumerate(names, 1):
                    lines.append(f"    {i}. {name}")
                    
            lines.append("=" * 70)
            report_section = "\n".join(lines)
            all_reports.append(report_section)
            
    # Compile and write consolidated report
    if all_reports:
        consolidated_report = "\n\n".join(all_reports)
        os.makedirs("reports/payroll data report", exist_ok=True)
        report_path = f"reports/payroll data report/payroll_release_{datetime.today().strftime('%Y-%m-%d')}_all_branches.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(consolidated_report)
            
        print("\n==================================================")
        print(f"CONSOLIDATED REPORT WRITTEN: {report_path}")
        print("==================================================")
    else:
        print("\n==================================================")
        print("NO PENDING RECORD DETECTED FOR ANY SYSTEM BRANCH!")
        print("==================================================")
        
except Exception as e:
    print("Error:", e)
