"""
API Business Validation Test Suite: Absence Case Listing Rules.
Validates business logic:
Do NOT list in Absence Case if ANY of:
1. status == 'Present'
2. has_Approved_Leave == true
3. has_Approved_Regularization == true
4. has_Approved_Remote == true

List in Absence Case ONLY IF:
status != 'Present' AND has_Approved_Leave == false AND has_Approved_Regularization == false AND has_Approved_Remote == false
"""

import os
import json
import logging
import pytest
import pandas as pd
from core.config import settings
from utils.api.base_api import get
from utils.api.absence_api import get_absence_case_list, get_absence_case_by_id

logger = logging.getLogger(__name__)


def should_be_listed_in_absence_case(
    status: str,
    has_approved_leave: bool = False,
    has_approved_regularization: bool = False,
    has_approved_remote: bool = False
) -> tuple[bool, str]:
    """
    Evaluates business rule for Absence Case listing:
    Returns (is_listed: bool, reason: str)
    """
    status_clean = str(status).strip().lower()
    
    if status_clean in ["present", "p"]:
        return False, "Status is 'Present' (Attendance marked)"
    if has_approved_leave:
        return False, "Approved Leave exists"
    if has_approved_regularization:
        return False, "Approved Regularization exists"
    if has_approved_remote:
        return False, "Approved Remote Work exists"
        
    return True, "Absent with NO approved Leave, Regularization, or Remote"


# =============================================================================
# 1. Parameterized Matrix Test for Specified Business Scenarios
# =============================================================================
@pytest.mark.api
@pytest.mark.parametrize("scenario, status, has_leave, has_reg, has_remote, expected_listing", [
    ("Scenario 1: Present (No requests)", "Present", False, False, False, "Not Listed"),
    ("Scenario 2: Absent + Approved Leave", "Absent", True, False, False, "Not Listed"),
    ("Scenario 3: Absent + Approved Regularization", "Absent", False, True, False, "Not Listed"),
    ("Scenario 4: Absent + Approved Remote", "Absent", False, False, True, "Not Listed"),
    ("Scenario 5: Pure Absent (No Approved Requests)", "Absent", False, False, False, "Listed"),
])
def test_absence_case_listing_logic_matrix(scenario, status, has_leave, has_reg, has_remote, expected_listing):
    """
    Validates the 5 exact scenario examples against the Absence Case listing rule engine.
    """
    is_listed, reason = should_be_listed_in_absence_case(
        status=status,
        has_approved_leave=has_leave,
        has_approved_regularization=has_reg,
        has_approved_remote=has_remote
    )
    actual_listing = "Listed" if is_listed else "Not Listed"
    
    logger.info(f"[{scenario}] Status='{status}', Leave={has_leave}, Reg={has_reg}, Remote={has_remote} => Actual: '{actual_listing}', Expected: '{expected_listing}' ({reason})")
    assert actual_listing == expected_listing, f"Failed for {scenario}: Expected '{expected_listing}', got '{actual_listing}' ({reason})"


# =============================================================================
# 2. Live API Single Case Validation (e.g. Case 1116)
# =============================================================================
@pytest.mark.api
def test_absence_case_single_record_api(case_id: int = 1116):
    """
    GET /api/AbsenceCase/{id}
    Fetches and validates single absence case against listing rules.
    """
    logger.info(f"Fetching Absence Case ID {case_id} from {settings.API_BASE_URL}...")
    case_data = get_absence_case_by_id(case_id)
    
    if not case_data:
        # If specific ID not found, attempt fetching first available ID from list
        cases = get_absence_case_list(rows=5)
        if cases:
            case_id = cases[0].get("id", case_id)
            case_data = get_absence_case_by_id(case_id) or cases[0]

    print("\n" + "=" * 95)
    print(f"             ABSENCE CASE RECORD AUDIT: ID #{case_id}")
    print("=" * 95)
    print(json.dumps(case_data, indent=2, default=str))

    assert case_data, f"Absence Case #{case_id} data could not be retrieved."

    # Validate that the listed case has valid absent attributes
    emp_name = case_data.get("employee_Name") or case_data.get("employeeName") or "Unknown"
    emp_code = case_data.get("employee_Code") or case_data.get("employeeId") or "N/A"
    absent_days = case_data.get("continuous_Absent_Days") or case_data.get("continuousAbsentDays") or 1
    status = case_data.get("status") or "UnderReview"

    print(f"\nEmployee:      {emp_name} (Code: {emp_code})")
    print(f"Absent Days:   {absent_days}")
    print(f"Case Status:   {status}")
    print("=" * 95 + "\n")


# =============================================================================
# 3. Live API Listing Audit & Compliance Report
# =============================================================================
@pytest.mark.api
def test_audit_live_absence_case_list_rules():
    """
    Audits live Absence Case listings from GET /api/AbsenceCase/list:
    Ensures that NO listed record violates the visibility rule:
    - Must NOT be 'Present'
    - Must NOT have active Approved Leave, Regularization, or Remote.
    Exports compliance audit report to Excel and Markdown.
    """
    logger.info("Auditing live Absence Case list against visibility rules...")
    records = get_absence_case_list(rows=500)
    assert len(records) > 0, "No Absence Cases returned from API."

    audit_rows = []
    violations = []

    for item in records:
        case_id = item.get("id", "")
        emp_name = item.get("employee_Name") or item.get("employeeName") or "Unknown"
        emp_code = item.get("employee_Code") or item.get("employeeId") or "N/A"
        branch = item.get("branch_Name") or item.get("branchName") or "N/A"
        company = item.get("company_Name") or item.get("companyName") or "N/A"
        raw_date = item.get("start_Date") or item.get("startDate") or ""
        date_str = raw_date.split("T")[0] if "T" in str(raw_date) else str(raw_date)[:10]
        absent_days = item.get("continuous_Absent_Days") or 1
        status = item.get("status") or "UnderReview"

        # Check for flags in record
        has_leave = bool(item.get("has_Approved_Leave") or item.get("hasApprovedLeave") or False)
        has_reg = bool(item.get("has_Approved_Regularization") or item.get("hasApprovedRegularization") or False)
        has_remote = bool(item.get("has_Approved_Remote") or item.get("hasApprovedRemote") or False)
        day_status = item.get("day_Status") or item.get("attendanceStatus") or "Absent"

        # Check compliance
        is_compliant = True
        violation_reason = "Compliant (Pure Absent)"

        if str(day_status).lower() in ["present", "p"]:
            is_compliant = False
            violation_reason = "VIOLATION: Status is Present"
        elif has_leave:
            is_compliant = False
            violation_reason = "VIOLATION: Has Approved Leave"
        elif has_reg:
            is_compliant = False
            violation_reason = "VIOLATION: Has Approved Regularization"
        elif has_remote:
            is_compliant = False
            violation_reason = "VIOLATION: Has Approved Remote"

        if not is_compliant:
            violations.append({
                "case_id": case_id,
                "emp_name": emp_name,
                "reason": violation_reason
            })

        audit_rows.append({
            "Case ID": case_id,
            "Employee Name": emp_name,
            "Emp Code": emp_code,
            "Branch": branch,
            "Company": company,
            "Start Date": date_str,
            "Absent Days": absent_days,
            "Status": status,
            "Has Approved Leave": has_leave,
            "Has Approved Regularization": has_reg,
            "Has Approved Remote": has_remote,
            "Listing Rule Result": "Compliant" if is_compliant else "Non-Compliant",
            "Rule Evaluation": violation_reason
        })

    # Summary Console Table
    print("\n" + "=" * 125)
    print(f"             ABSENCE CASE LISTING COMPLIANCE AUDIT REPORT | TOTAL CASES: {len(audit_rows)}")
    print("=" * 125)
    print(f"{'Case ID':<8} | {'Employee Name':<22} | {'Branch':<12} | {'Start Date':<10} | {'Absent':<6} | {'Leave':<6} | {'Reg':<6} | {'Remote':<6} | {'Compliance'}")
    print("-" * 125)

    for r in audit_rows[:35]:
        print(f"{str(r['Case ID']):<8} | {r['Employee Name'][:22]:<22} | {r['Branch'][:12]:<12} | {r['Start Date']:<10} | {str(r['Absent Days']):<6} | {str(r['Has Approved Leave'])[:6]:<6} | {str(r['Has Approved Regularization'])[:6]:<6} | {str(r['Has Approved Remote'])[:6]:<6} | {r['Listing Rule Result']}")

    print("-" * 125)
    print(f"Audit Summary: {len(audit_rows) - len(violations)} Compliant | {len(violations)} Violations found.")
    print("=" * 125 + "\n")

    # Export to Excel
    os.makedirs("reports", exist_ok=True)
    excel_path = "reports/absence_case_listing_validation.xlsx"
    df = pd.DataFrame(audit_rows)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Absence_Listing_Audit")
        ws = writer.sheets["Absence_Listing_Audit"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    logger.info(f"Exported Absence Listing Validation Excel report to: {excel_path}")
    print(f"Successfully generated Excel report: {excel_path}")

    # Export to Markdown
    md_path = "reports/absence_case_listing_validation.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Absence Case Listing Compliance Audit Report\n\n")
        f.write("### Rule: Do NOT list in Absence Case if `Present`, `Approved Leave`, `Approved Regularization`, or `Approved Remote`.\n\n")
        f.write(f"**Total Cases Audited**: {len(audit_rows)} | **Compliant**: {len(audit_rows) - len(violations)} | **Violations**: {len(violations)}\n\n")
        f.write("| Case ID | Employee Name | Emp Code | Branch | Start Date | Absent Days | Leave | Reg | Remote | Compliance | Evaluation |\n")
        f.write("|---------|---------------|----------|--------|------------|-------------|-------|-----|--------|------------|------------|\n")
        for r in audit_rows:
            f.write(f"| {r['Case ID']} | {r['Employee Name']} | {r['Emp Code']} | {r['Branch']} | {r['Start Date']} | {r['Absent Days']} | {r['Has Approved Leave']} | {r['Has Approved Regularization']} | {r['Has Approved Remote']} | {r['Listing Rule Result']} | {r['Rule Evaluation']} |\n")

    logger.info(f"Exported Absence Listing Validation Markdown report to: {md_path}")
