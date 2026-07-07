import sys
sys.path.append(r"c:\Users\User\Desktop\Tekinspirations\HRlens_Playwright")
from utils.api.payroll_api import get_payroll_companies
import json

companies = get_payroll_companies()
print(json.dumps(companies, indent=2))
