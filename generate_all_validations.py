import os
import sys
import glob
import pandas as pd
from datetime import datetime

# Append workspace path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.api.payroll_api import get_payroll_companies, get_released_payroll
from tests.api.test_payroll_validation import (
    read_excel,
    build_api_lookup,
    run_comparison,
    build_wide_rows,
    build_tables,
    save_workbook
)

YEAR = 2026
MONTH = 4
OUTPUT_DIR = "reports/payroll validation report"

def get_excel_for_company(company_name: str) -> str:
    c_name = company_name.lower().strip()
    # Search in both PayrollData folder and static folder
    search_paths = [
        "testdata/static/PayrollData/*.xlsx",
        "testdata/static/PayrollData/*.XLSX",
        "testdata/static/*.xlsx"
    ]
    files = []
    for path in search_paths:
        files.extend(glob.glob(path))
        
    for f in files:
        base = os.path.basename(f).lower()
        # Specific overrides and substring matchers
        if "originator" in c_name and "originator" in base:
            return f
        if "adventa tech" in c_name and "adventa" in base and "software" not in c_name and "software" not in base:
            if "bbsr" not in base:
                return f
        if "adventa tech software" in c_name and "bbsr" in base:
            return f
        if "vyze" in c_name and "bbsr" in base:
            return f
        if "infusive" in c_name and "infusive" in base:
            return f
        if "jobvritta" in c_name and "jobvritta" in base:
            return f
        if "tek inspirations" in c_name and "tek" in base:
            return f
        if "legit guru" in c_name and "legit" in base:
            return f
        if "infoserv" in c_name and "infoserv" in base:
            return f
        if "init talent" in c_name and "init" in base:
            return f
        if "code crewzs" in c_name and "code crewzs" in base:
            return f
            
    return None

def main():
    print("==================================================")
    print(f"RUNNING PAYROLL RECONCILIATION FOR ALL COMPANIES")
    print(f"Target Month: {MONTH}/{YEAR}")
    print("==================================================")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        companies = get_payroll_companies()
    except Exception as e:
        print(f"Failed to fetch payroll companies: {e}")
        sys.exit(1)
        
    print(f"Found {len(companies)} payroll companies in system.\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, c in enumerate(companies, 1):
        c_id = c["id"]
        c_name = c["payrollCompanyName"]
        c_code = c.get("companyCode", f"CMP{c_id}")
        
        print(f"[{idx}/{len(companies)}] Processing company: {c_name} (ID: {c_id}, Code: {c_code})...")
        
        # 1. Identify Excel File
        excel_path = get_excel_for_company(c_name)
        if excel_path:
            print(f"  - Matching Excel found: {excel_path}")
        else:
            print("  - No matching Excel file found. Excel columns will be filled with 'NA'.")
            
        # 2. Fetch Released Payroll Records
        try:
            api_resp = get_released_payroll(YEAR, MONTH, c_id)
            api_records = api_resp.get("data", [])
        except Exception as e:
            print(f"  - ERROR fetching payroll list: {e}")
            fail_count += 1
            print("-" * 50)
            continue
            
        if not api_records:
            print("  - WARNING: No released payroll records found for this company.")
            print("-" * 50)
            continue
            
        print(f"  - Fetched {len(api_records)} records from API.")
        
        # 3. Read Excel if present
        df = None
        if excel_path:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(excel_path, read_only=True)
                sheet_names = wb.sheetnames
                wb.close()
                
                c_name_lower = c_name.lower()
                
                if "infusive" in c_name_lower:
                    # Concatenate all branch sheets for Infusive
                    dfs = []
                    for sh in sheet_names:
                        if any(b in sh.lower() for b in ["agra", "jaipur", "noida"]):
                            try:
                                dfs.append(read_excel(excel_path, sh))
                            except Exception as e:
                                print(f"    - Warning reading sheet '{sh}': {e}")
                    if dfs:
                        df = pd.concat(dfs, ignore_index=True)
                elif "vyze" in c_name_lower:
                    sheet_to_use = next((s for s in sheet_names if "vyze" in s.lower()), None)
                    if sheet_to_use:
                        df = read_excel(excel_path, sheet_to_use)
                elif "adventa tech software" in c_name_lower:
                    sheet_to_use = next((s for s in sheet_names if "adventa" in s.lower()), None)
                    if sheet_to_use:
                        df = read_excel(excel_path, sheet_to_use)
                else:
                    # Standard logic: find APR'26 or APR-26 or first sheet
                    sheet_to_use = None
                    for name in ["APR'26", "Apr-26", "APR-26", "Sheet1"]:
                        if name in sheet_names:
                            sheet_to_use = name
                            break
                    if not sheet_to_use and sheet_names:
                        sheet_to_use = sheet_names[0]
                    if sheet_to_use:
                        df = read_excel(excel_path, sheet_to_use)
            except Exception as e:
                print(f"  - WARNING reading Excel sheet: {e}. Proceeding with Excel columns as 'NA'.")
                df = None
                
        # 4. Perform comparison
        try:
            composite_lookup, name_lookup = build_api_lookup(api_records)
            detail_rows = run_comparison(df, composite_lookup, name_lookup)
            
            wide_rows, field_labels = build_wide_rows(detail_rows)
            t1, t2, t3, t4, t5, t6, t7 = build_tables(detail_rows, api_total=len(api_records))
            
            # Save spreadsheet
            clean_company_name = "".join(x for x in c_name if x.isalnum() or x in " _-").strip()
            clean_company_name = clean_company_name.replace(" ", "_")
            report_filename = f"payroll_validation_{clean_company_name}.xlsx"
            report_path = os.path.join(OUTPUT_DIR, report_filename)
            
            save_path = save_workbook(
                wide_rows, field_labels, t1, t2, t3, t4, t5, t6, t7,
                custom_path=report_path, company_name=c_name
            )
            
            print(f"  - SUCCESS: Validation report saved to: {save_path}")
            print(f"    Summary: {t1[4]['Count']} Matched | {t1[8]['Count']} Salary Mismatches")
            success_count += 1
        except Exception as e:
            import traceback
            print(f"  - ERROR running comparison/saving workbook: {e}")
            traceback.print_exc()
            fail_count += 1
            
        print("-" * 50)
        
    print("\n==================================================")
    print(f"ALL PAYROLL VALIDATION RUN COMPLETE!")
    print(f"Processed: {len(companies)} | Success: {success_count} | Fail/Skip: {fail_count}")
    print(f"Reports saved in folder: {OUTPUT_DIR}")
    print("==================================================")

if __name__ == "__main__":
    main()
