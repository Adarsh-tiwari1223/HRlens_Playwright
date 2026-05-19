# TODO - Payroll Generation Flag Feature

## Task
When payroll status shows "SKIPPED (No pending employees — payroll fully generated.)", create a txt file that flags the date when generation was completed.

## Steps

- [x] 1. Add `flag_payroll_generated()` function in utils/api/payroll_api.py
- [x] 2. The function checks if pending == 0 and creates a flag file with date
- [ ] 3. Test the implementation

## Details
- Flag file location: logs/payroll_generated_flag.txt
- Format: Date in YYYY-MM-DD format
- Content example: "Payroll fully generated on 2026-05-16"

## Usage
```python
from utils.api.payroll_api import flag_payroll_generated, find_branch_id

# Get branch ID
branch_id = find_branch_id("Varanasi", "Infoserv LLC")

# Create flag file when payroll is fully generated
flag_file = flag_payroll_generated(
    year=2026,
    month=4,
    branch_id=branch_id,
    branch_name="Varanasi",
    company_name="Infoserv LLC"
)
```
