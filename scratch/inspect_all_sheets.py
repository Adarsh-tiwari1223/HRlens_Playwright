import os
import glob
import openpyxl
import pandas as pd

def inspect_all():
    search_paths = [
        "testdata/static/PayrollData/*.xlsx",
        "testdata/static/PayrollData/*.XLSX",
        "testdata/static/*.xlsx"
    ]
    files = []
    for path in search_paths:
        files.extend(glob.glob(path))
    
    # remove duplicate paths if any
    files = sorted(list(set(os.path.abspath(f) for f in files)))
    
    print(f"Found {len(files)} Excel files:")
    for f in files:
        print(f"\nFile: {os.path.basename(f)}")
        try:
            wb = openpyxl.load_workbook(f, read_only=True)
            sheets = wb.sheetnames
            wb.close()
            print(f"  Sheets: {sheets}")
            for sh in sheets[:3]:  # print first 3 sheets
                try:
                    df = pd.read_excel(f, sheet_name=sh, header=None)
                    print(f"    Sheet: '{sh}' | Shape: {df.shape}")
                    # Find a row that looks like it has headers (e.g. contains 'Name' or 'Code')
                    header_row_idx = -1
                    for idx, row in df.iterrows():
                        row_vals = [str(val).strip().lower() for val in row if pd.notna(val)]
                        if any("name" in val for val in row_vals) and any(any(x in val for x in ["code", "id", "emp"]) for val in row_vals):
                            header_row_idx = idx
                            break
                    if header_row_idx != -1:
                        print(f"      Detected Header at Row {header_row_idx}:")
                        headers = [str(x).strip() for x in df.iloc[header_row_idx]]
                        print(f"      Cols: {headers[:15]} ...")
                    else:
                        print(f"      No standard header row detected in first 20 rows.")
                        for idx in range(min(5, len(df))):
                            print(f"      Row {idx}: {list(df.iloc[idx][:10])}")
                except Exception as e:
                    print(f"      Error reading sheet {sh}: {e}")
        except Exception as e:
            print(f"  Error reading workbook: {e}")

if __name__ == "__main__":
    inspect_all()
