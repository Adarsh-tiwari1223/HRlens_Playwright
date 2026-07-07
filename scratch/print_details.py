import sys
sys.path.append(r"c:\Users\User\Desktop\Tekinspirations\HRlens_Playwright")
from utils.api.payroll_api import get_employee_detail, get_released_payroll
import json

# 1. Fetch profile details
print("--- PROFILE (EMPLOYEE DETAIL) ---")
profile = get_employee_detail(3672)
print(json.dumps(profile, indent=2))

# 2. Fetch released payroll
print("\n--- RELEASED PAYROLL ---")
payroll_resp = get_released_payroll(2026, 4, 7)
records = payroll_resp.get("data", [])
abhishek_rec = None
for r in records:
    if r.get("employeeId") == 3672 or "Abhishek" in r.get("employeeName", ""):
        abhishek_rec = r
        break

if abhishek_rec:
    print(json.dumps(abhishek_rec, indent=2))
else:
    print("Abhishek not found in released payroll. First record:")
    if records:
        print(json.dumps(records[0], indent=2))
