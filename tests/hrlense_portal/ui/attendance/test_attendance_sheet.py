import pytest
from datetime import datetime
from pages.hrlense_portal.attendance.attendance_sheet_page import AttendanceSheetPage
from pages.base_page import TestStoryLogger
from utils.attendance_logic import calculate_attendance_status

def parse_ui_time(date_str: str, time_str: str) -> datetime | None:
    if not time_str or time_str in ("—", "-", "", "00:00"):
        return None
    clean_time = time_str.replace(" ", "")
    # Try parsing common formats
    for fmt in ("%d-%m-%Y %I:%M%p", "%d-%m-%Y %H:%M", "%d-%m-%Y %I:%M %p", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M:%S"):
        try:
            return datetime.strptime(f"{date_str} {clean_time}", fmt)
        except ValueError:
            pass
    return None

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

    # Step 5: Compare retrieved UI status with calculated business logic status
    check_ins = []
    check_outs = []
    
    in_time = parse_ui_time(record["date"], record["check_in"])
    out_time = parse_ui_time(record["date"], record["check_out"])
    
    if in_time:
        check_ins.append(in_time)
    if out_time:
        check_outs.append(out_time)
        
    shift_start = datetime.strptime(f"{record['date']} 09:00 AM", "%d-%m-%Y %I:%M %p") if record["date"] else datetime.now()
    
    calculated = calculate_attendance_status(check_ins, check_outs, shift_start)
    
    # If check-in and check-out are empty, status must match "Absent"
    expected_status = calculated["status"]
    if not check_ins and not check_outs:
        expected_status = "Absent"
        
    ui_status = record["status"]
    is_matched = ui_status.lower() == expected_status.lower()
    
    story.log_step(
        "Compare UI Status with Business Logic Calculation",
        record=f"UI Status: {ui_status} | Calculated Status: {expected_status}",
        expected=f"UI status should match calculated status: '{expected_status}'",
        actual=f"UI status '{ui_status}' matches calculated status" if is_matched else f"Mismatch: UI shows '{ui_status}', logic calculated '{expected_status}'",
        status="PASS" if is_matched else "FAIL"
    )
    assert is_matched, f"UI status '{ui_status}' does not match computed business logic status '{expected_status}'"

    story.finish(status="PASS")
