import pandas as pd
from difflib import SequenceMatcher
import re

# Read both Excel files
parent_file = "testdata/static/Originator-Salary-April'2026.xlsx"
generated_file = "testdata/static/Payroll(4-2026)-Originator informatics Pvt. Ltd.-Varanasi (TEK)-2026_05_16_11_48_16.xlsx"

# Read parent file
df_parent = pd.read_excel(parent_file, sheet_name="APR'26", header=5, skiprows=[0])
parent_names = df_parent.iloc[:, 4].dropna().tolist()
parent_net_pay = df_parent.iloc[:, 25].dropna().tolist()

# Read generated file
df_gen = pd.read_excel(generated_file, sheet_name="Payroll(4-2026)")
gen_names = df_gen['BNF_NAME'].tolist()
gen_acc = df_gen['BENE_ACC_NO'].tolist()
gen_amount = df_gen['AMOUNT'].tolist()

total_salary = len(parent_names)
total_payroll = len(gen_names)

# Dynamic header widths
header1 = f"{'Result':<28} | {'Count':>10}"
sep1 = len(header1)

print("=" * sep1)
print("               SUMMARY - PAYROLL ANALYSIS")
print("=" * sep1)
print(f"Total Employees in Salary Sheet:  {total_salary}")
print(f"Total BNF_NAME in Payroll:   {total_payroll}")

# Name cleaning
def clean_name(name):
    name = str(name).strip().upper()
    name = re.sub(r'\s+', ' ', name)
    return name

def names_match(name1, name2):
    n1 = clean_name(name1)
    n2 = clean_name(name2)
    if n1 == n2:
        return True, "EXACT"
    if n1 in n2 or n2 in n1:
        return True, "CONTAINS"
    if len(n1) < 5 or len(n2) < 5:
        return False, "TOO_SHORT"
    ratio = SequenceMatcher(None, n1, n2).ratio()
    if ratio > 0.85:
        return True, "FUZZY_85"
    if ratio > 0.80:
        return True, "FUZZY_80"
    return False, "NO_MATCH"

# Match payroll to salary
all_matches = []
unmatched_payroll = []

for j, gname in enumerate(gen_names):
    best_match = None
    best_ratio = 0
    match_type = "NO_MATCH"
    
    for i, pname in enumerate(parent_names):
        is_match, mtype = names_match(pname, gname)
        if is_match:
            ratio = SequenceMatcher(None, clean_name(pname), clean_name(gname)).ratio()
            if ratio > best_ratio or (best_match is None):
                best_match = i
                best_ratio = ratio
                match_type = mtype
    
    if best_match is not None:
        all_matches.append({
            'payroll_idx': j,
            'salary_idx': best_match,
            'gen_name': gname,
            'parent_name': parent_names[best_match],
            'bene_acc': gen_acc[j],
            'gen_amount': gen_amount[j],
            'parent_net_pay': parent_net_pay[best_match],
            'match_type': match_type,
            'match_ratio': best_ratio
        })
    else:
        unmatched_payroll.append({
            'name': gname,
            'bene_acc': gen_acc[j],
            'gen_amount': gen_amount[j]
        })

# Separate exact vs fuzzy matches
exact_matches = [m for m in all_matches if m['match_type'] == "EXACT"]
fuzzy_matches = [m for m in all_matches if m['match_type'] != "EXACT"]

# Difference from exact matches
exact_diff = [m for m in exact_matches if m['parent_net_pay'] != m['gen_amount']]

# Exact match with equal salary (no difference)
exact_equal = [m for m in exact_matches if m['parent_net_pay'] == m['gen_amount']]

print(f"\n--- MATCHING RESULTS ---")
print(f"Total Payroll Entries:    {total_payroll}")
print(f"Matched (Exact):        {len(exact_matches)}")
print(f"Matched (Fuzzy/Spelling): {len(fuzzy_matches)}")
print(f"Unmatched:              {len(unmatched_payroll)}")

# Print tables
# TABLE 1: SUMMARY
header1 = f"{'Result':<28} | {'Count':>10}"
sep1 = len(header1)
print("\n" + "=" * sep1)
print(f"{'Unmatch':<28} | {len(unmatched_payroll):>10}")
print(f"{'---':<28} | {'---':>10}")
print(f"{'Total BNF_NAME':<28} | {total_payroll:>10}")

print("\n" + "=" * 70)
print("TABLE 2: DIFFERENCE TABLE")
print("=" * 70)
print(f"{'Status':<28} | {'Count':>10}")
print("-" * 45)
print(f"{'Matched (Exact = Paid)':<28} | {len(exact_matches) - len(exact_diff):>10}")
print(f"{'Matched (Exact != Paid)':<28} | {len(exact_diff):>10}")
print(f"{'Matched (Spelling)':<28} | {len(fuzzy_matches):>10}")
print(f"{'---':<28} | {'---':>10}")
print(f"{'Total Matched':<28} | {len(all_matches):>10}")

# TABLE 3: SPELLING MISMATCH
print("\n" + "=" * 70)
print("TABLE 3: SPELLING MISMATCH (Fuzzy Matched - May be Wrong!)")
print("=" * 70)
print(f"{'#':<3} | {'PARENT COLUMN':<26} | {'PAYROLL COLUMN':<26} | {'TYPE':<10}")
print("-" * 75)
for idx, m in enumerate(fuzzy_matches):
    s_name = m['parent_name'][:24] if len(m['parent_name']) > 24 else m['parent_name']
    g_name = m['gen_name'][:24] if len(m['gen_name']) > 24 else m['gen_name']
    print(f"{idx+1:<3} | {s_name:<26} | {g_name:<26} | {m['match_type']:<10}")

print(f"\nWARNING: These {len(fuzzy_matches)} entries matched via fuzzy logic.")
print("They may be WRONG matches due to spelling differences!")
print("Check them manually!")

# TABLE 4: MATCHED (Exact)
print("\n" + "=" * 70)
print("TABLE 4: MATCHED EMPLOYEES (Exact Match)")
print("=" * 70)
print(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
print("-" * 58)
for idx, m in enumerate(exact_matches[:30]):
    name = m['parent_name'][:26] if len(m['parent_name']) > 26 else m['parent_name']
    print(f"{idx+1:<3} | {name:<28} | {m['parent_net_pay']:>8,} | {m['gen_amount']:>8,}")
print(f"\nTotal Exact Match: {len(exact_matches)}")

# TABLE 5: DIFFERENCE
print("\n" + "=" * 70)
print("TABLE 5: DIFFERENCE (Parent Salary != Payroll Salary)")
print("=" * 70)
print(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14} | {'DIFFERENCE':>12}")
print("-" * 70)
for idx, m in enumerate(exact_diff[:20]):
    net_pay = m.get('parent_net_pay', 0) or 0
    diff = net_pay - m['gen_amount']
    name = m['parent_name'][:26] if len(m['parent_name']) > 26 else m['parent_name']
    diff_str = f"+{diff:,}" if diff > 0 else str(diff)
    print(f"{idx+1:<3} | {name:<28} | {net_pay:>8,} | {m['gen_amount']:>8,} | {diff_str:>8}")
print(f"\nTotal with Difference: {len(exact_diff)}")

# TABLE 5A: EXACT = PAID
print("\n" + "=" * 70)
print("TABLE 5A: MATCHED (EXACT = PAID)")
print("=" * 70)
print(f"{'#':<3} | {'EMPLOYEE NAME':<30} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
print("-" * 70)
for idx, m in enumerate(exact_equal[:30]):
    name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
    print(f"{idx+1:<3} | {name:<30} | {m['parent_net_pay']:>10,} | {m['gen_amount']:>10,}")
print(f"\nTotal with Equal Salary: {len(exact_equal)}")

# TABLE 6: NOT IN PAYROLL
unmatched_salary = [i for i in range(len(parent_names)) if not any(m['salary_idx'] == i for m in all_matches)]
print("\n" + "=" * 70)
print("TABLE 6: NOT IN PAYROLL")
print("=" * 70)
print(f"{'#':<3} | {'Employee Name':<30} | {'PARENT SALARY':>14}")
print("-" * 58)
for idx, i in enumerate(unmatched_salary):
    name = parent_names[i][:28] if len(parent_names[i]) > 28 else parent_names[i]
    print(f"{idx+1:<3} | {name:<30} | {parent_net_pay[i]:>10,}")
print(f"\nTotal Not in Payroll: {len(unmatched_salary)}")

# ========== SAVE REPORT ==========
report_txt = []
report_txt.append("=" * 70)
report_txt.append("           PAYROLL MAPPING REPORT - APRIL 2026")
report_txt.append("=" * 70)

report_txt.append("")
report_txt.append("TABLE 1: SUMMARY")
report_txt.append("=" * 70)
report_txt.append(f"{'Result':<28} | {'Count':>10}")
report_txt.append(f"{'-' * 28} | {'-' * 10}")
report_txt.append("-" * 45)
report_txt.append(f"{'Match (Exact)':<28} | {len(exact_matches):>10}")
report_txt.append(f"{'Match (Spelling)':<28} | {len(fuzzy_matches):>10}")
report_txt.append(f"{'Unmatch':<28} | {len(unmatched_payroll):>10}")
report_txt.append(f"{'---':<28} | {'---':>10}")
report_txt.append(f"{'Total BNF_NAME':<28} | {total_payroll:>10}")

report_txt.append("")
report_txt.append("TABLE 2: DIFFERENCE TABLE")
report_txt.append("=" * 70)
report_txt.append(f"{'Status':<28} | {'Count':>10}")
report_txt.append(f"{'-' * 28} | {'-' * 10}")
report_txt.append("-" * 45)
report_txt.append(f"{'Matched (Exact = Paid)':<28} | {len(exact_matches) - len(exact_diff):>10}")
report_txt.append(f"{'Matched (Exact != Paid)':<28} | {len(exact_diff):>10}")
report_txt.append(f"{'Matched (Spelling)':<28} | {len(fuzzy_matches):>10}")
report_txt.append(f"{'---':<28} | {'---':>10}")
report_txt.append(f"{'Total Matched':<28} | {len(all_matches):>10}")

report_txt.append("")
report_txt.append("TABLE 3: SPELLING MISMATCH (Fuzzy Matched)")
report_txt.append("=" * 70)
report_txt.append(f"{'#':<3} | {'PARENT COLUMN':<26} | {'PAYROLL COLUMN':<26} | {'TYPE':<10}")
report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 26} | {'-' * 10}")
report_txt.append("-" * 75)
for idx, m in enumerate(fuzzy_matches):
    s_name = m['parent_name'][:24] if len(m['parent_name']) > 24 else m['parent_name']
    g_name = m['gen_name'][:24] if len(m['gen_name']) > 24 else m['gen_name']
    report_txt.append(f"{idx+1:<3} | {s_name:<26} | {g_name:<26} | {m['match_type']:<10}")
report_txt.append(f"\nWARNING: These {len(fuzzy_matches)} entries may be WRONG matches!")

report_txt.append("")
report_txt.append("TABLE 4: MATCHED (Exact)")
report_txt.append("=" * 70)
report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 14} | {'-' * 14}")
for idx, m in enumerate(exact_matches):
    name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
    report_txt.append(f"{idx+1:<3} | {name:<30} | {m['parent_net_pay']:>10,} | {m['gen_amount']:>10,}")
report_txt.append(f"\nTotal: {len(exact_matches)}")

report_txt.append("")
report_txt.append("TABLE 5: DIFFERENCE (Parent Salary != Payroll Salary)")
report_txt.append("=" * 70)
report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<26} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14} | {'DIFFERENCE':>12}")
report_txt.append(f"{'-' * 3} | {'-' * 26} | {'-' * 14} | {'-' * 14} | {'-' * 12}")
for idx, m in enumerate(exact_diff):
    net_pay = m.get('parent_net_pay', 0) or 0
    diff = net_pay - m['gen_amount']
    name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
    diff_str = f"+{diff:,}" if diff > 0 else str(diff)
    report_txt.append(f"{idx+1:<3} | {name:<30} | {net_pay:>10,} | {m['gen_amount']:>10,} | {diff_str:>10}")
report_txt.append(f"\nTotal: {len(exact_diff)}")

report_txt.append("")
report_txt.append("TABLE 5A: MATCHED (EXACT = PAID)")
report_txt.append("=" * 70)
report_txt.append(f"{'#':<3} | {'EMPLOYEE NAME':<30} | {'PARENT SALARY':>14} | {'PAYROLL SALARY':>14}")
report_txt.append(f"{'-' * 3} | {'-' * 30} | {'-' * 14} | {'-' * 14}")
for idx, m in enumerate(exact_equal):
    name = m['parent_name'][:30] if len(m['parent_name']) > 30 else m['parent_name']
    report_txt.append(f"{idx+1:<3} | {name:<30} | {m['parent_net_pay']:>10,} | {m['gen_amount']:>10,}")
report_txt.append(f"\nTotal: {len(exact_equal)}")

report_txt.append("")
report_txt.append("TABLE 6: NOT IN PAYROLL")
report_txt.append("=" * 70)
report_txt.append(f"{'#':<3} | {'Employee Name':<30} | {'PARENT SALARY':>14}")
report_txt.append(f"{'-' * 3} | {'-' * 30} | {'-' * 14}")
for idx, i in enumerate(unmatched_salary):
    name = parent_names[i][:30] if len(parent_names[i]) > 30 else parent_names[i]
    report_txt.append(f"{idx+1:<3} | {name:<30} | {parent_net_pay[i]:>10,}")
report_txt.append(f"\nTotal: {len(unmatched_salary)}")

# Write with UTF-8 encoding
with open("reports/payroll_mapping_report.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(report_txt))

print(f"\n\nReport saved to: reports/payroll_mapping_report.txt")
