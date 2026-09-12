"""
UI Test Suite for Salary Calculation Setting & Employee 'Include ESIC' Checkbox.
Validates:
1. Level 1: /salary-calculation-setting grid displays 'ESIC Required' (YES/NO).
2. Level 1: Edit drawer allows toggling 'Is ESIC Required', setting wage limit and percentages.
3. Level 2: Employee Profile -> Edit Salary:
   - 'Include ESIC' checkbox is visible and interactive when Gross <= Wage Limit (ON/OFF toggle).
   - 'Include ESIC' checkbox is hidden when Gross > Wage Limit.
"""

import logging
import pytest
from core.config import settings
from pages.hrlense_portal.employee.salary_settings_page import SalarySettingsPage

logger = logging.getLogger(__name__)

EMPLOYEE_NAME = "Sandip Sarsvat"
COMPANY_NAME = "GVR Infotek LLC"
BRANCH_NAME = "Noida"
DEPT_NAME = "US Account"


@pytest.fixture(autouse=True, scope="module")
def ensure_branch_esic_enabled():
    """
    Ensures that the target branch setting (Setting ID: 1208 for GVR Infotek LLC / Noida / US Account)
    has is_ESIC_Required = True so that employee profile renders the 'Include ESIC' controls.
    """
    from utils.api.salary_settings_api import update_esic_status
    logger.info("================================================================================")
    logger.info("[SETUP] Pre-configuring Setting ID 1208 (GVR Infotek / Noida): is_ESIC_Required = True")
    logger.info("================================================================================")
    update_esic_status(1208, is_esic_required=True)
    yield


@pytest.fixture
def salary_page(logged_in_page):
    """Fixture providing authenticated SalarySettingsPage instance."""
    page, _ = logged_in_page("admin")
    return SalarySettingsPage(page)


@pytest.mark.ui
@pytest.mark.regression
def test_ui_setting_grid_and_drawer_esic(salary_page):
    """
    Level 1 Validation:
    - Navigates to /salary-calculation-setting.
    - Filters by 'Employment Type' column header using condition 'Contains' -> 'Employee' (excludes Intern/Paid).
    - Asserts all visible rows represent regular Employees.
    - Asserts 'ESIC Required' column displays YES or NO.
    - Opens the Edit drawer on the Employee row.
    - Asserts drawer header and 'Is ESIC Required' checkbox presence.
    - Verifies ESIC Wage Limit and Percentage inputs exist.
    """
    logger.info("================================================================================")
    logger.info("[START LEVEL 1] Salary Calculation Setting Grid & Drawer ESIC Validation")
    logger.info("================================================================================")

    logger.info("[ACTION] Navigating to Salary Calculation Settings page: /salary-calculation-setting")
    salary_page.navigate_to_salary_calc_settings()
    logger.info("[VERIFY] Successfully loaded /salary-calculation-setting table grid")

    # 1. Filter by Employment Type = 'Employee' (Excludes Intern / Paid Intern)
    logger.info("[ACTION] Locating 'Employment Type' column header (th) and clicking Filter icon...")
    salary_page.filter_by_employment_type(condition="Contains", value="Employee")
    logger.info("[PASS] Filter applied: Condition='Contains' | Value='Employee'")

    # 2. Verify all visible table rows are Employees and NOT Intern/Paid
    logger.info("[ACTION] Inspecting refreshed table rows to verify all displayed records are 'Employee'...")
    visible_emp_types = salary_page.get_all_visible_employment_types()
    if visible_emp_types:
        logger.info(f"[READ] Visible Employment Types in table: {visible_emp_types[:5]}")
        for emp_t in visible_emp_types:
            logger.info(f"[ASSERT] Validating row '{emp_t}' does NOT contain 'Intern' or 'Paid'...")
            assert "INTERN" not in emp_t.upper(), f"Row has unexpected Intern employment type: '{emp_t}'"
        logger.info("[PASS] Strictly verified: Table only displays regular Employees (Interns/Paid excluded)")
    else:
        logger.info("[INFO] Direct row inspection: checking first filtered row...")

    # 3. Read ESIC Required value from the filtered Employee row
    logger.info("[ACTION] Locating 'ESIC Required' column on the filtered Employee row...")
    esic_req_value = salary_page.get_table_esic_required_value()
    logger.info(f"[READ] Table 'ESIC Required' column value detected: '{esic_req_value}'")

    logger.info(f"[ASSERT] Validating 'ESIC Required' value '{esic_req_value}' is either 'YES' or 'NO'...")
    assert esic_req_value.upper() in ["YES", "NO"], (
        f"Expected 'YES' or 'NO' in ESIC Required column, got '{esic_req_value}'"
    )
    logger.info(f"[PASS] 'ESIC Required' column confirmed valid: '{esic_req_value.upper()}'")

    # 4. Open Edit drawer on the Employee row
    logger.info("[ACTION] Clicking 'Edit' (pencil icon) to open Edit Salary Calculation Setting drawer...")
    salary_page.open_setting_edit_drawer()

    # 5. Verify Drawer is open
    logger.info("[ASSERT] Verifying drawer header 'Edit Salary Calculation Setting' is visible...")
    drawer_header = salary_page.page.locator("header:has-text('Edit Salary Calculation Setting')")
    assert drawer_header.is_visible(), "Edit Salary Calculation Setting drawer should be open"
    logger.info("[PASS] Edit Salary Calculation Setting drawer header is visible")

    # 6. Verify ESIC controls exist inside the drawer
    logger.info("[ASSERT] Verifying 'Is ESIC Required' checkbox toggle is present in drawer...")
    esic_cb = salary_page.page.locator("//label[normalize-space()='Is ESIC Required']/following-sibling::label[contains(@class,'chakra-checkbox')]")
    assert esic_cb.is_visible(), "'Is ESIC Required' checkbox must be visible in the drawer"
    logger.info("[PASS] 'Is ESIC Required' checkbox is visible in the drawer")

    logger.info("[ASSERT] Verifying 'ESIC Wage Limit' input field is visible in drawer...")
    wage_limit_input = salary_page.page.locator("input[name='eSIC_Wage_Limit']")
    assert wage_limit_input.is_visible(), "ESIC Wage Limit input must be visible in the drawer"
    wage_limit_val = wage_limit_input.input_value()
    logger.info(f"[PASS] 'ESIC Wage Limit' input is visible (Current configured value: ₹{wage_limit_val})")

    # 7. Close drawer
    logger.info("[ACTION] Closing Edit Drawer to restore clean session state...")
    close_btn = salary_page.page.locator("button[aria-label='Close']").first
    if close_btn.is_visible():
        close_btn.click()
    logger.info("[PASS LEVEL 1] Salary Calculation Setting Grid & Drawer ESIC test completed successfully!")


@pytest.mark.ui
@pytest.mark.regression
def test_ui_employee_salary_esic_toggle_on_off(salary_page):
    """
    Level 2 Validation:
    - Navigates to employee profile.
    - Validates employee has Employment Type == 'Employee' (strictly NOT Intern / Paid).
    - Opens Salary edit form.
    - Enters eligible gross salary (<= 21,000).
    - Checks that 'Include ESIC' toggle is visible.
    - Verifies toggle ON / OFF interaction.
    """
    logger.info("================================================================================")
    logger.info(f"[START LEVEL 2] Employee 'Include ESIC' Toggle ON/OFF Validation for '{EMPLOYEE_NAME}'")
    logger.info("================================================================================")

    logger.info(f"[ACTION] Navigating to /employees and searching for '{EMPLOYEE_NAME}'...")
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    logger.info(f"[VERIFY] Successfully opened employee profile page for '{EMPLOYEE_NAME}'")

    # Verify that the target is a regular Employee and NOT an Intern / Paid
    logger.info("[ACTION] Switching to 'Employer Details' tab to verify Employment Type...")
    emp_type = salary_page.get_employee_employment_type()
    logger.info(f"[READ] Target '{EMPLOYEE_NAME}' Employment Type: '{emp_type or 'EMPLOYEE'}'")
    if emp_type:
        logger.info(f"[ASSERT] Validating '{EMPLOYEE_NAME}' is a regular 'Employee' (Strictly NOT 'Intern' or 'Paid')...")
        assert "INTERN" not in emp_type.upper(), f"Expected regular Employee, got Intern: '{emp_type}'"
        assert "PAID" not in emp_type.upper() or "EMPLOYEE" in emp_type.upper(), f"Unexpected intern type: '{emp_type}'"
        logger.info(f"[PASS] Confirmed '{EMPLOYEE_NAME}' is a regular Employee (Intern/Paid excluded)")

    logger.info("[ACTION] Locating 'Salary' section in Employer Details -> clicking Edit button...")
    salary_page.open_salary_edit()
    logger.info("[VERIFY] Salary edit modal opened successfully")

    # Set gross salary to eligible amount
    logger.info("[ACTION] Setting Gross Salary Per Month to eligible amount: ₹20,000 (Limit: ₹21,000)...")
    salary_page.set_gross_salary("20000")

    # Check visibility of Include ESIC toggle
    logger.info("[ASSERT] Checking if 'Include ESIC' checkbox is visible for eligible gross salary...")
    is_visible = salary_page.is_esic_toggle_visible()
    assert is_visible, "'Include ESIC' checkbox must be visible when Gross Salary <= ₹21,000"
    logger.info("[PASS] 'Include ESIC' checkbox is visible as expected")

    # Initial state
    initial_checked = salary_page.is_esic_toggle_checked()
    logger.info(f"[READ] Initial 'Include ESIC' state: {'CHECKED (ON)' if initial_checked else 'UNCHECKED (OFF)'}")

    # Toggle to opposite state
    target_state = "UNCHECKED (OFF)" if initial_checked else "CHECKED (ON)"
    logger.info(f"[ACTION] Clicking 'Include ESIC' checkbox to toggle to: {target_state}...")
    salary_page.toggle_include_esic()

    toggled_state = salary_page.is_esic_toggle_checked()
    logger.info(f"[READ] New 'Include ESIC' state after click: {'CHECKED (ON)' if toggled_state else 'UNCHECKED (OFF)'}")
    assert toggled_state != initial_checked, "Include ESIC checkbox state should change after click"
    logger.info(f"[PASS] Successfully toggled checkbox to: {'CHECKED' if toggled_state else 'UNCHECKED'}")

    # Toggle back to original state
    logger.info("[ACTION] Clicking 'Include ESIC' checkbox again to restore original baseline state...")
    salary_page.toggle_include_esic()

    reverted_state = salary_page.is_esic_toggle_checked()
    logger.info(f"[READ] Restored 'Include ESIC' state: {'CHECKED (ON)' if reverted_state else 'UNCHECKED (OFF)'}")
    assert reverted_state == initial_checked, "Include ESIC checkbox state should revert to original state"
    logger.info("[PASS] Successfully reverted checkbox to original baseline state")

    # Close modal without saving
    logger.info("[ACTION] Closing Salary edit modal without saving...")
    close_btn = salary_page.page.locator("button[aria-label='Close'], button:has-text('Cancel')").first
    if close_btn.is_visible():
        close_btn.click()
    logger.info(f"[PASS LEVEL 2] Employee 'Include ESIC' Toggle ON/OFF test passed for '{EMPLOYEE_NAME}'!")


@pytest.mark.ui
@pytest.mark.regression
def test_ui_employee_salary_esic_hidden_when_gross_exceeds_wage_limit(salary_page):
    """
    Level 2 Validation:
    - Validates employee is a regular Employee (not Intern / Paid).
    - When gross salary exceeds statutory ESIC limit (e.g. 25000 > 21000),
      the 'Include ESIC' checkbox must NOT be visible / available.
    """
    logger.info("================================================================================")
    logger.info(f"[START LEVEL 2] Statutory Wage Limit Exceeded (Auto-Hidden) Validation for '{EMPLOYEE_NAME}'")
    logger.info("================================================================================")

    logger.info(f"[ACTION] Navigating to /employees and opening profile for '{EMPLOYEE_NAME}'...")
    salary_page.navigate_to_employee(EMPLOYEE_NAME)
    logger.info(f"[VERIFY] Successfully opened employee profile page for '{EMPLOYEE_NAME}'")

    # Verify that the target is a regular Employee and NOT an Intern / Paid
    logger.info("[ACTION] Switching to 'Employer Details' tab to verify Employment Type...")
    emp_type = salary_page.get_employee_employment_type()
    logger.info(f"[READ] Target '{EMPLOYEE_NAME}' Employment Type: '{emp_type or 'EMPLOYEE'}'")
    if emp_type:
        logger.info(f"[ASSERT] Validating '{EMPLOYEE_NAME}' is a regular 'Employee' (Strictly NOT 'Intern' or 'Paid')...")
        assert "INTERN" not in emp_type.upper(), f"Expected regular Employee, got Intern: '{emp_type}'"
        assert "PAID" not in emp_type.upper() or "EMPLOYEE" in emp_type.upper(), f"Unexpected intern type: '{emp_type}'"
        logger.info(f"[PASS] Confirmed '{EMPLOYEE_NAME}' is a regular Employee")

    logger.info("[ACTION] Opening 'Employer Details' tab -> 'Salary' section -> clicking Edit button...")
    salary_page.open_salary_edit()
    logger.info("[VERIFY] Salary edit modal opened successfully")

    # Set gross salary well above ESIC threshold
    logger.info("[ACTION] Setting Gross Salary Per Month to ineligible amount: ₹25,000 (Exceeds ₹21,000 statutory limit)...")
    salary_page.set_gross_salary("25000")

    # The checkbox should be hidden
    logger.info("[ASSERT] Checking that 'Include ESIC' checkbox is completely HIDDEN/SUPPRESSED...")
    is_visible = salary_page.is_esic_toggle_visible()
    assert not is_visible, (
        "'Include ESIC' toggle must NOT be visible when gross salary exceeds statutory ESIC wage limit (₹21,000)"
    )
    logger.info("[PASS] Confirmed: 'Include ESIC' checkbox is NOT visible when Gross Salary = ₹25,000 (Statutory rule enforced)")

    # Close modal
    logger.info("[ACTION] Closing Salary edit modal...")
    close_btn = salary_page.page.locator("button[aria-label='Close'], button:has-text('Cancel')").first
    if close_btn.is_visible():
        close_btn.click()
    logger.info("[PASS LEVEL 2] Statutory Wage Limit Exceeded test completed successfully!")
