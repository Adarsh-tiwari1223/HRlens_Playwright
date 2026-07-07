import os
import glob
import pandas as pd

VALIDATION_FIELDS_KEYS = ["Basic", "HRA", "Conveyance", "Incentive", "Employee PF", "Employer PF", "TDS", "Net Salary", "Balance Leave"]

def detect_excel_columns(df):
    header_row_idx = -1
    for idx in range(min(15, len(df))):
        row = df.iloc[idx]
        row_vals = [str(val).strip().lower() for val in row if pd.notna(val)]
        has_name = any("name" in val for val in row_vals)
        has_code = any(any(x in val for x in ["code", "id", "emp.", "emp"]) for val in row_vals)
        if has_name and has_code:
            header_row_idx = idx
            break
            
    if header_row_idx == -1:
        header_row_idx = 5

    headers = [str(x).strip().lower() if pd.notna(x) else "" for x in df.iloc[header_row_idx]]
    
    col_name = -1
    col_code = -1
    
    for idx, h in enumerate(headers):
        if "name" in h and not any(x in h for x in ["father", "company", "bank", "branch"]):
            col_name = idx
            break
            
    for idx, h in enumerate(headers):
        if any(x in h for x in ["code", "emp id", "employee id", "hrlenseid"]) and not "company" in h:
            col_code = idx
            break
    if col_code == -1:
        for idx, h in enumerate(headers):
            if h == "emp" or h == "emp.":
                col_code = idx
                break
                
    if col_name == -1:
        col_name = 4
    if col_code == -1:
        col_code = 7

    field_keywords = {
        "Basic": ["basic salary", "basic + da", "basic+da", "stipend", "basic"],
        "HRA": ["h.r.a. amt.", "hra amt.", "h.r.a.", "hra"],
        "Conveyance": ["conv. amt.", "conveyance", "conv.", "conveyance allowance"],
        "Incentive": ["incentive", "spcl. alw.", "special allowance", "special alw"],
        "Employee PF": ["deductions p.f.", "pf deduction", "pf", "p.f.", "esic & pf"],
        "Employer PF": ["employer pf", "employer p.f.", "employer_pf"],
        "TDS": ["deductions t.d.s.", "tds", "t.d.s."],
        "Net Salary": ["net payable", "net salary", "net amount", "total net", "net payable salary"],
        "Balance Leave": ["earned leave", "casual leave", "reserve leave", "balance leave", "cl", "el"]
    }
    
    mapped_indices = {}
    for label, keywords in field_keywords.items():
        best_idx = -1
        for idx, h in enumerate(headers):
            if not h:
                continue
            for kw in keywords:
                if kw == h or kw in h:
                    best_idx = idx
                    break
        mapped_indices[label] = best_idx if best_idx != -1 else None

    return header_row_idx, col_name, col_code, mapped_indices, headers

def test_run():
    search_paths = [
        "testdata/static/PayrollData/*.xlsx",
        "testdata/static/PayrollData/*.XLSX",
        "testdata/static/*.xlsx"
    ]
    files = []
    for path in search_paths:
        files.extend(glob.glob(path))
    files = sorted(list(set(os.path.abspath(f) for f in files)))
    
    for f in files:
        print(f"\nFile: {os.path.basename(f)}")
        try:
            wb_sheets = pd.ExcelFile(f).sheet_names
            for sh in wb_sheets[:3]:
                df = pd.read_excel(f, sheet_name=sh, header=None)
                header_idx, col_name, col_code, mapped, headers = detect_excel_columns(df)
                print(f"  Sheet: '{sh}' | Header Row: {header_idx}")
                print(f"    Name Col: {col_name} ('{headers[col_name]}') | Code Col: {col_code} ('{headers[col_code]}')")
                for k, idx in mapped.items():
                    val = f"{idx} ('{headers[idx]}')" if idx is not None else "None"
                    print(f"    {k:<15}: {val}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_run()
