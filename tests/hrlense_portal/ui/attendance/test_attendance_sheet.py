import pytest
from pages.hrlense_portal.attendance.attendance_sheet_page import AttendanceSheetPage
from pages.base_page import TestStoryLogger

@pytest.mark.ui
@pytest.mark.attendance
def test_admin_view_attendance_sheet(logged_in_page):
    story = TestStoryLogger("Admin Attendance Sheet Verification")
    story.start()

    # Step 1: Login as Admin
    admin_page, admin_context = logged_in_page("admin")

    # Step 2: Navigate to Attendance Sheet
    sheet_page = AttendanceSheetPage(admin_page)
    sheet_page.navigate_to_attendance_sheet()

    # Step 3: Search for an employee (Sanidhy Tiwari)
    employee_name = "Sanidhy"
    sheet_page.search_employee(employee_name)

    # Step 4: Verify attendance record details in table
    record = sheet_page.get_employee_attendance_record(employee_name)
    
    # Log the structured ASCII table
    story.log_table("Attendance Record", record)
    
    is_verified = record is not None
    story.log_step(
        "Verify Attendance Row Data",
        record=f"Employee: {employee_name}",
        expected="Attendance record should exist in the sheet",
        actual="Attendance record successfully retrieved" if is_verified else "No matching record in table",
        status="PASS" if is_verified else "FAIL"
    )
    assert is_verified, f"Attendance record for '{employee_name}' not found in the grid"
    assert record["name"], "Employee name cell is empty"
    assert record["date"], "Date cell is empty"

    story.finish(status="PASS")
