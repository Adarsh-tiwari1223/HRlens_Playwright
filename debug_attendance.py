from utils.api.payroll_api import get_payroll_list, find_branch_id
from utils.api.attendance_api import get_attendance_summary

YEAR, MONTH = 2026, 4
BID = find_branch_id("Varanasi", "TEK Inspirations LLC")

records = get_payroll_list(year=YEAR, month=MONTH, branch_id=BID).get("data", [])
generated = [r for r in records if r.get("status") == "generated"]

att_map = {r["employeeId"]: r for r in get_attendance_summary(
    f"{YEAR}-{MONTH:02d}-01", f"{YEAR}-{MONTH:02d}-30"
)}

for p in generated:
    a = att_map.get(p["employeeId"])
    if a is None:
        continue

    absent        = a["absent"]
    half_day      = a["halfDay"]
    balance_leave = float(p["balance_Leave"]) if p["balance_Leave"] not in (None, "--", "") else 0.0
    gross         = float(p["grossSalary"]) if p["grossSalary"] else 0.0
    total_days    = p["totalDaysInMonth"]

    leave_required = absent + (half_day / 2)
    leave_used     = min(balance_leave, leave_required)
    lop            = leave_required - leave_used
    paid_days      = total_days - lop
    per_day        = gross / total_days if total_days else 0
    earned         = paid_days * per_day
    allowances     = p["conveyance_Allowance"] + p["health_Insurance_Amount"] + p["transport_Allowance_Amount"] + p["meal_Allowance_Amount"]
    total_earnings = earned + p["incentive"] + p["otherEarning"] + allowances
    total_deductions = p["employee_PF"] + p["esic_Employee"] + p["tds"] + p["otherDeduction"]
    computed_net   = total_earnings - total_deductions

    if abs(computed_net - p["netSalary"]) >= 0.01:
        print(f"\nMISMATCH: {p['employeeName']}")
        print(f"  absent={absent} halfDay={half_day} balance_Leave={balance_leave}")
        print(f"  leaveRequired={leave_required} leaveUsed={leave_used} lop={lop}")
        print(f"  paidDays={paid_days} perDay={per_day:.4f} earned={earned:.2f}")
        print(f"  allowances={allowances} incentive={p['incentive']} otherEarning={p['otherEarning']}")
        print(f"  totalEarnings={total_earnings:.2f} totalDeductions={total_deductions:.2f}")
        print(f"  computed_net={computed_net:.2f} payroll_net={p['netSalary']}")
        print(f"  payroll_totalEarnings={p['totalEarnings']} payroll_lop={p['lop']} payroll_paidDays={p['paidDays']}")
