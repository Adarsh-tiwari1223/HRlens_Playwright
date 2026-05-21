import os
import pytest
import pandas as pd
from datetime import datetime
import openpyxl
import difflib

from utils.api.payroll_api import map_payroll_to_excel

def safe_float(val):
    """Safe float conversion for numerical comparison."""
    if pd.isna(val) or val is None or val == "":
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

@pytest.mark.regression
def test_payroll_excel_vs_api():
    """
    Validates the payroll data by comparing the provided Excel sheet
    with the API response, generates a detailed TXT report, and exports it to Excel.
    """
    year = 2026
    month = 4
    payroll_company_id = 7
    excel_file = "testdata/static/Originator-Salary-April'2026.xlsx"
    sheet_name = "APR'26"

    try:
        comparison_data = map_payroll_to_excel(
            year=year,
            month=month,
            payroll_company_id=payroll_company_id,
            excel_file=excel_file,
            sheet_name=sheet_name
        )
    except FileNotFoundError:
        pytest.skip(f"Test data file not found: {excel_file}")

    exact_matches = []
    fuzzy_matches = []
    exact_diff = []
    exact_equal = []
    unmatched_salary = []

    # 1. Categorize matches into Exact, Fuzzy, and Differences
    for emp in comparison_data.get("comparison_results", []):
        parent_name = str(emp.get("employeeName_excel", "Unknown")).strip()
        gen_name = str(emp.get("employeeName_api", "Unknown")).strip()

        parent_net_pay = 0.0
        gen_amount = 0.0
        
        for field, data in emp["fields"].items():
            if data["api_field"] == "netSalary":
                parent_net_pay = safe_float(data["excel_value"])
                gen_amount = safe_float(data["api_value"])
                break
                
        # Determine match type
        if parent_name.upper() == gen_name.upper():
            match_type = "EXACT"
        else:
            ratio = difflib.SequenceMatcher(None, parent_name.upper(), gen_name.upper()).ratio()
            match_type = "FUZZY_85" if ratio > 0.8 else "CONTAINS"
            
        m_data = {
            "parent_name": parent_name,
            "gen_name": gen_name,
            "parent_net_pay": parent_net_pay,
            "gen_amount": gen_amount,
            "match_type": match_type,
            "diff": parent_net_pay - gen_amount
        }

        if match_type == "EXACT":
            exact_matches.append(m_data)
            if abs(m_data["diff"]) > 0.01:
                exact_diff.append(m_data)
            else:
                exact_equal.append(m_data)
        else:
            fuzzy_matches.append(m_data)

    # Handle Missing
    for code_or_name in comparison_data.get("unmatched_from_excel", []):
        unmatched_salary.append({
            "parent_name": code_or_name,
            "parent_net_pay": 0.0
        })
        
    total_payroll = len(exact_matches) + len(fuzzy_matches)

    # 2. GENERATE TXT REPORT
    report_txt = []
    report_txt.append("=" * 70)
    report_txt.append(f"           PAYROLL MAPPING REPORT - {datetime.now().strftime('%B %Y').upper()}")
    report_txt.append("=" * 70)

    report_txt.append("\nTABLE 1: SUMMARY")
    report_txt.append("=" * 70)
    report_txt.append(f"{'Result':<28} | {'Count':>10}")
    report_txt.append(f"{'-' * 28} | {'-' * 10}")
    report_txt.append("-" * 45)
    report_txt.append(f"{'Match (Exact)':<28} | {len(exact_matches):>10}")
    report_txt.append(f"{'Match (Spelling)':<28} | {len(fuzzy_matches):>10}")
    report_txt.append(f"{'Unmatch':<28} | {len(unmatched_salary):>10}")
    report_txt.append(f"{'---':<28} | {'---':>10}")
    report_txt.append(f"{'Total BNF_NAME':<28} | {total_payroll:>10}")

    report_txt.append("\nTABLE 2: DIFFERENCE TABLE")
    report_txt.append("=" * 70)
    report_txt.append(f"{'Status':<28} | {'Count':>10}")
    report_txt.append(f"{'-' * 28} | {'-' * 10}")
    report_txt.append("-" * 45)
    report_txt.append(f"{'Matched (Exact = Paid)':<28} | {len(exact_equal):>10}")
    report_txt.append(f"{'Matched (Exact != Paid)':<28} | {len(exact_diff):>10}")
    report_txt.append(f"{'Matched (Spelling)':<28} | {len(fuzzy_matches):>10}")
    report_txt.append(f"{'---':<28} | {'---':>10}")
    report_txt.append(f"{'Total Matched':<28} | {total_payroll:>10}")

    report_txt.append("\nTABLE 3: SPELLING MISMATCH (Fuzzy Matched)")
    report_txt.append("=" * 70)
    report_txt.append(f"{'#':<3} | {'PARENT COLUMN':<26} | {'PAYROLL COLUMN':<26} | {'TYPE':<10}")
    report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 26} | {'-' * 10}")
    report_txt.append("-" * 75)
    for idx, m in enumerate(fuzzy_matches):
        s_name = m['parent_name'][:24] if len(m['parent_name']) > 24 else m['parent_name']
        g_name = m['gen_name'][:24] if len(m['gen_name']) > 24 else m['gen_name']
        report_txt.append(f"{idx+1:<3} | {s_name:<26} | {g_name:<26} | {m['match_type']:<10}")
    if fuzzy_matches:
        report_txt.append(f"\nWARNING: These {len(fuzzy_matches)} entries may be WRONG matches!")

    report_txt.append("\nTABLE 4: MATCHED (Exact)")
    report_txt.append("=" * 70)
    report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
    report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 14} | {'-' * 14}")
    for idx, m in enumerate(exact_matches):
        name = m['parent_name'][:26] if len(m['parent_name']) > 26 else m['parent_name']
        report_txt.append(f"{idx+1:<3} | {name:<26} | {m['parent_net_pay']:>14,.0f} | {m['gen_amount']:>14,.0f}")
    report_txt.append(f"\nTotal: {len(exact_matches)}")

    report_txt.append("\nTABLE 5: DIFFERENCE (Parent Salary != Payroll Salary)")
    report_txt.append("=" * 70)
    report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14} | {'DIFFERENCE':>12}")
    report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 14} | {'-' * 14} | {'-' * 12}")
    for idx, m in enumerate(exact_diff):
        diff = m['diff']
        name = m['parent_name'][:26] if len(m['parent_name']) > 26 else m['parent_name']
        diff_str = f"+{diff:,.0f}" if diff > 0 else f"{diff:,.0f}"
        report_txt.append(f"{idx+1:<3} | {name:<26} | {m['parent_net_pay']:>14,.0f} | {m['gen_amount']:>14,.0f} | {diff_str:>12}")
    report_txt.append(f"\nTotal: {len(exact_diff)}")

    report_txt.append("\nTABLE 5A: MATCHED (EXACT = PAID)")
    report_txt.append("=" * 70)
    report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<30} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
    report_txt.append(f"{'-' * 3} | {'-' * 30} | {'-' * 14} | {'-' * 14}")
    for idx, m in enumerate(exact_equal):
        name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
        report_txt.append(f"{idx+1:<3} | {name:<30} | {m['parent_net_pay']:>14,.0f} | {m['gen_amount']:>14,.0f}")
    report_txt.append(f"\nTotal: {len(exact_equal)}")

    report_txt.append("\nTABLE 6: NOT IN PAYROLL")
    report_txt.append("=" * 70)
    report_txt.append(f"{'#':<3} | {'Employee Name':<30} | {'PARENT SALARY':>14}")
    report_txt.append(f"{'-' * 3} | {'-' * 30} | {'-' * 14}")
    for idx, m in enumerate(unmatched_salary):
        name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
        report_txt.append(f"{idx+1:<3} | {name:<30} | {m['parent_net_pay']:>14,.0f}")
    report_txt.append(f"\nTotal: {len(unmatched_salary)}")

    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    txt_path = f"reports/payroll_mapping_report_{timestamp}.txt"
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_txt))
        
    print(f"\nTXT Report saved to: {txt_path}")

    # 3. CONVERT TXT REPORT TO MULTI-SHEET EXCEL
    excel_path = f"reports/payroll_mapping_excel_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        pd.DataFrame([
            {"Metric": "Match (Exact)", "Count": len(exact_matches)},
            {"Metric": "Match (Spelling)", "Count": len(fuzzy_matches)},
            {"Metric": "Unmatch", "Count": len(unmatched_salary)},
            {"Metric": "Total BNF_NAME", "Count": total_payroll}
        ]).to_excel(writer, sheet_name="Summary", index=False)
        
        if exact_diff:
            pd.DataFrame(exact_diff).rename(columns={
                "parent_name": "EMPLOYEE NAME", "parent_net_pay": "PARENT SALARY", 
                "gen_amount": "PAYROLL SALARY", "diff": "DIFFERENCE"
            }).drop(columns=["gen_name", "match_type"]).to_excel(writer, sheet_name="Difference", index=False)
            
        if exact_equal:
            pd.DataFrame(exact_equal).rename(columns={
                "parent_name": "EMPLOYEE NAME", "parent_net_pay": "PARENT SALARY", 
                "gen_amount": "PAYROLL SALARY"
            }).drop(columns=["gen_name", "match_type", "diff"]).to_excel(writer, sheet_name="Exact Match (Equal)", index=False)
            
        if fuzzy_matches:
            pd.DataFrame(fuzzy_matches).rename(columns={
                "parent_name": "PARENT COLUMN", "gen_name": "PAYROLL COLUMN", "match_type": "TYPE"
            }).drop(columns=["parent_net_pay", "gen_amount", "diff"]).to_excel(writer, sheet_name="Spelling Mismatch", index=False)
            
        if unmatched_salary:
            pd.DataFrame(unmatched_salary).rename(columns={
                "parent_name": "Employee Name", "parent_net_pay": "PARENT SALARY"
            }).to_excel(writer, sheet_name="Not In Payroll", index=False)
            
    print(f"Excel Report saved to: {excel_path}")

    # 4. Pytest Assertions
    mismatches = len(exact_diff) + len(fuzzy_matches) + len(unmatched_salary)
    assert mismatches == 0, f"Found {mismatches} mismatches between API and Excel data. Check reports for details."