import sys
sys.path.append(r"c:\Users\User\Desktop\Tekinspirations\HRlens_Playwright")
from utils.api.payroll_api import get_balance_leave
import json

print("Checking Mansi Singh (ID: 3660)...")
res1 = get_balance_leave(3660)
print(json.dumps(res1, indent=2))

print("\nChecking Roshani kumari (ID: 3670)...")
res2 = get_balance_leave(3670)
print(json.dumps(res2, indent=2))
