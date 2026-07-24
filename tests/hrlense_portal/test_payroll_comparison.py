import os
import re
import pytest
import pandas as pd
from utils.api.payroll_api import get_released_payroll, find_payroll_company_id
from utils.payroll_reconciliation import PayrollReconciliationAgent, StructuralValidationError

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
YEAR         = 2026
MONTH        = 4
REPORTS_DIR  = "reports"
PAYROLL_DATA = "testdata/static/PayrollData"

def find_all_payroll_sheets():
    """Discover all non-empty sheets in Excel files dynamically from the test folder."""
    params = []
    if not os.path.exists(PAYROLL_DATA):
        return params
    for filename in sorted(os.listdir(PAYROLL_DATA)):
        if filename.endswith(".xlsx") or filename.endswith(".XLSX"):
            if filename.startswith("~$"):
                continue
            path = os.path.join(PAYROLL_DATA, filename)
            try:
                xl = pd.ExcelFile(path)
                for sheet in xl.sheet_names:
                    params.append((filename, sheet))
            except Exception:
                pass
    return params

# Generate IDs for test parametrization
PARAMS = find_all_payroll_sheets()
TEST_IDS = [f"{filename}::{sheet}" for filename, sheet in PARAMS]

# ---------------------------------------------------------------------------
# DYNAMIC PAYROLL TEST
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    "excel_filename,sheet_name",
    PARAMS,
    ids=TEST_IDS
)
def test_payroll_excel_vs_api(excel_filename, sheet_name):
    excel_file = os.path.join(PAYROLL_DATA, excel_filename)
    if not os.path.exists(excel_file):
        pytest.skip(f"Excel file not found: {excel_file}")

    # Instantiate our dynamic validation and reconciliation agent
    agent = PayrollReconciliationAgent(excel_file, sheet_name)

    # STEP 1 & 2: SCAN & MAP
    try:
        scan_results = agent.scan_file()
    except StructuralValidationError as sve:
        # Check if this is a minor decorative/blank sheet to skip
        # Sheet1 in some workbooks might not have enough data to be valid
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            non_empty_count = df.notna().sum().sum()
        except Exception:
            non_empty_count = 0
            
        if non_empty_count < 10:
            pytest.skip(f"Skipping decorative/blank sheet '{sheet_name}': {sve}")
            
        # Emit a structural validation failure report as required
        err_report_path = agent.generate_json_report({
            "matched": [], "mismatches": [], "missing_in_api": [], "missing_in_payroll": [], "confidence_score": 0.0
        })
        pytest.fail(f"Structural validation failure on '{excel_filename}' sheet '{sheet_name}': {sve}. Report generated: {err_report_path}")

    # Fetch company ID from API dynamically
    display_company = scan_results["display_company"]
    company_fragment = scan_results["company_fragment"]
    
    try:
        payroll_company_id = find_payroll_company_id(company_fragment)
    except ValueError as exc:
        pytest.fail(f"Company ID lookup failed for '{display_company}' (fragment: '{company_fragment}'): {exc}")

    # Fetch API records
    try:
        api_response = get_released_payroll(YEAR, MONTH, payroll_company_id)
    except Exception as exc:
        pytest.fail(f"API call failed for '{display_company}': {exc}")

    api_records = api_response.get("data", [])
    assert api_records, f"API returned empty data for company '{display_company}'"

    # STEP 3: VALIDATE DATA (row count, blanks, duplicates, totals)
    excel_records = agent.parse_data()
    assert excel_records, f"No employee rows parsed from Excel sheet '{sheet_name}'"

    # STEP 4: API COMPARISON
    comparison_results = agent.compare_against_api(excel_records, api_records)

    # STEP 5: REPORTING
    json_path = agent.generate_json_report(comparison_results)
    excel_path = agent.generate_excel_report(excel_records, api_records, comparison_results)

    # Log summary info to console
    print(f"\n{'='*60}")
    print(f"  {display_company}  |  Sheet: {sheet_name}  |  Branch: {agent.display_branch}  |  {YEAR}-{MONTH:02d}")
    print(f"{'='*60}")
    print(f"  Status          : {agent.status}")
    print(f"  Excel Records   : {len(excel_records)}")
    print(f"  API Records     : {len(api_records)}")
    print(f"  Matched Records : {len(comparison_results['matched'])}")
    print(f"  Mismatched      : {len(comparison_results['mismatches'])}")
    print(f"  Missing in API  : {len(comparison_results['missing_in_api'])}")
    print(f"  Missing in Excel: {len(comparison_results['missing_in_payroll'])}")
    print(f"  Confidence Score: {comparison_results['confidence_score']}%")
    print(f"{'='*60}")
    print(f"  JSON Report : {json_path}")
    print(f"  Excel Report: {excel_path}")

    # Fail fast if structural validation failed
    assert agent.status != "FAIL", f"Payroll reconciliation failed on data comparison or numeric consistency. See report: {excel_path}"
    
    # Assert there are no critical financial mismatches
    mismatches = comparison_results["mismatches"]
    if mismatches:
        print(f"\nMismatches (first 30 of {len(mismatches)}):")
        for r in mismatches[:30]:
            print(f"  [{r['employee_code']}] {r['employee_name']:<30} "
                  f"| Field: {r['field']} | Expected={r['expected_value']}  Actual={r['actual_value']}  | Col: {r['source_column']}")

    assert not mismatches, (
        f"{display_company} - Sheet '{sheet_name}': {len(mismatches)} field mismatch(es) detected. "
        f"See report sheet 'T2 Differences' for details."
    )
