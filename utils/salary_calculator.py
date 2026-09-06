"""
Salary Calculator & Offer Logic Engine for HRlens Portal.

Implements rule flow logic:
if minimum_basic_salary < configured_minimum_basic_salary:
    if gross_salary >= configured_minimum_gross_salary:
        show_minimum_salary_alert()
        if confirmed:
            convert_employee_to_paid_intern()
            basic_salary = gross_salary
            hra = 0
            conveyance = 0
            other_allowances = 0
    else:
        salary_not_allowed()
else:
    normal_salary_calculation()
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate_salary_structure(
    gross_salary: float,
    configured_minimum_basic_salary: float = 16000.0,
    configured_minimum_gross_salary: float = 15000.0,
    basic_ratio: float = 0.8435,
    hra_ratio: float = 0.1565
) -> Dict[str, Any]:
    """
    Calculates salary breakdown based on configured basic and gross salary thresholds.

    Args:
        gross_salary: The input monthly gross salary.
        configured_minimum_basic_salary: Configured minimum basic salary limit (from API: min_Basic).
        configured_minimum_gross_salary: Configured minimum gross salary threshold (from API: min_Gross_Salary).
        basic_ratio: Ratio for basic salary calculation (default 84.35%).
        hra_ratio: Ratio for HRA calculation (default 15.65%).

    Returns:
        Dict containing action status, calculated breakdown, or rejection error.
    """
    minimum_basic_salary = gross_salary * basic_ratio

    if minimum_basic_salary < configured_minimum_basic_salary:
        if gross_salary >= configured_minimum_gross_salary:
            logger.info(
                f"[SALARY RULE] Basic salary ({minimum_basic_salary:.2f}) < Configured minimum basic ({configured_minimum_basic_salary}). "
                f"Gross ({gross_salary:.2f}) >= Configured minimum gross ({configured_minimum_gross_salary}). Triggering Paid Intern conversion alert."
            )
            return {
                "action": "SHOW_MINIMUM_SALARY_ALERT",
                "status": "PAID_INTERN_PROMPT",
                "is_allowed": True,
                "requires_confirmation": True,
                "minimum_basic_salary": minimum_basic_salary,
                "configured_minimum_basic_salary": configured_minimum_basic_salary,
                "configured_minimum_gross_salary": configured_minimum_gross_salary,
                "gross_salary": gross_salary,
                "converted_paid_intern_structure": {
                    "employment_type": "INTERN",
                    "intern_payment_type": "PAID",
                    "basic_salary": gross_salary,
                    "hra": 0.0,
                    "conveyance": 0.0,
                    "other_allowances": 0.0,
                    "monthly_ctc": gross_salary,
                    "annual_ctc": gross_salary * 12,
                    "net_salary": gross_salary
                }
            }
        else:
            logger.warning(
                f"[SALARY RULE] Gross salary ({gross_salary:.2f}) < Configured minimum gross salary ({configured_minimum_gross_salary}). Salary not allowed."
            )
            return {
                "action": "SALARY_NOT_ALLOWED",
                "status": "REJECTED",
                "is_allowed": False,
                "error_message": f"Gross salary ₹{gross_salary:,.2f} is below the minimum allowed gross salary threshold of ₹{configured_minimum_gross_salary:,.2f}.",
                "minimum_basic_salary": minimum_basic_salary,
                "configured_minimum_basic_salary": configured_minimum_basic_salary,
                "configured_minimum_gross_salary": configured_minimum_gross_salary,
                "gross_salary": gross_salary
            }
    else:
        # Normal Salary Calculation
        hra = round(gross_salary * hra_ratio, 2)
        basic = round(minimum_basic_salary, 2)
        employee_pf = round(basic * 0.12, 2) if basic <= 15000 else 1800.0
        employer_pf = round(basic * 0.12, 2) if basic <= 15000 else 1800.0
        employee_esic = round(gross_salary * 0.0075, 2) if gross_salary <= 21000 else 0.0
        employer_esic = round(gross_salary * 0.0325, 2) if gross_salary <= 21000 else 0.0

        monthly_ctc = round(gross_salary + employer_pf + employer_esic, 2)
        annual_ctc = round(monthly_ctc * 12, 2)
        net_salary = round(gross_salary - (employee_pf + employee_esic), 2)

        logger.info(f"[SALARY RULE] Normal salary calculation applied for Gross ₹{gross_salary:,.2f}.")
        return {
            "action": "NORMAL_SALARY_CALCULATION",
            "status": "APPROVED",
            "is_allowed": True,
            "requires_confirmation": False,
            "employment_type": "FULL_TIME",
            "gross_salary": gross_salary,
            "basic_salary": basic,
            "hra": hra,
            "employee_pf": employee_pf,
            "employer_pf": employer_pf,
            "employee_esic": employee_esic,
            "employer_esic": employer_esic,
            "monthly_ctc": monthly_ctc,
            "annual_ctc": annual_ctc,
            "net_salary": net_salary
        }
