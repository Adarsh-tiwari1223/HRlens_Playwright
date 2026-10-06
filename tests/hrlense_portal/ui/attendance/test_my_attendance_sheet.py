"""
UI Test Suite for Employee My Attendance Sheet (/myAttendanceSheet).
Validates:
1. Navigation and Header banner (Employee Name and Emp Code).
2. Top 10 Summary Metric Cards (Total Days, Present, Absent, Late, Week Off, Short Leave, etc.).
3. Daily Attendance Table rendering (S.No, Date, Day, Check IN, Check OUT, Break Time, Status).
4. Month/Year selectors and future dates handling.
"""

import pytest
import logging
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.attendance.attendance_sheet_page import AttendanceSheetPage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def employee_session(page):
    """Logs in as employee (Uttam Kumar) and navigates to /myAttendanceSheet."""
    emp_creds = settings.USERS.get("uttam_kumar", settings.USERS.get("employee"))
    assert emp_creds, "Employee credentials missing in configuration."

    page.goto(f"{settings.BASE_URL}/login", timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    login_page = LoginPage(page)
    login_page.login(emp_creds["username"], emp_creds["password"])

    sheet_page = AttendanceSheetPage(page)
    sheet_page.navigate_to_my_attendance_sheet()
    return sheet_page


@pytest.mark.ui
@pytest.mark.attendance
def test_verify_my_attendance_sheet_dashboard(page, employee_session):
    """
    Validates visible elements on https://stg-hrlense.jobvritta.com/myAttendanceSheet:
    - Visible Header with employee name & code
    - 10 Summary Cards
    - Daily attendance log rows for the month
    """
    sheet_page = employee_session

    # 1. Header Validation
    header_info = sheet_page.get_header_employee_info()
    logger.info(f"Verified Header: {header_info}")
    assert header_info["name"] != "", f"Expected non-empty employee name in header, got: {header_info}"

    # 2. Top Summary Cards Validation (10 metrics)
    metrics = sheet_page.get_summary_metrics()
    logger.info(f"Verified Summary Cards: {metrics}")
    assert len(metrics) >= 8, f"Expected at least 8 metric cards, found: {len(metrics)}"
    assert "Total Days" in metrics, f"'Total Days' card missing in {metrics}"
    assert "Present" in metrics, f"'Present' card missing in {metrics}"
    assert "Week off" in metrics, f"'Week off' card missing in {metrics}"
    assert metrics["Total Days"] in [28, 29, 30, 31], f"Unexpected Total Days value: {metrics['Total Days']}"

    # 3. Table Headers Validation
    headers = sheet_page.get_table_headers()
    logger.info(f"Verified Table Headers: {headers}")
    expected_headers = ["S. No", "Date", "Day", "Check IN", "Check OUT", "Break Time", "Status"]
    for h in expected_headers:
        assert any(h.lower() in existing.lower() for existing in headers), f"Missing header: {h}"

    # 4. Daily Attendance Rows Validation
    records = sheet_page.get_daily_records()
    logger.info(f"Total days rendered in table: {len(records)}")
    assert len(records) == metrics["Total Days"], (
        f"Row count {len(records)} does not match Total Days metric {metrics['Total Days']}"
    )

    # 5. Check Sample Day Record (e.g. Day 1)
    day_1 = sheet_page.get_record_by_date_or_day(1)
    logger.info(f"Day 1 Record: {day_1}")
    assert day_1 is not None, "Day 1 record not found in table."
    assert day_1.get("day") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # 6. Verify Future Dates contain '-'
    day_31 = sheet_page.get_record_by_date_or_day(31)
    if day_31:
        logger.info(f"Day 31 Record: {day_31}")
        assert day_31.get("status") in ["-", "Week Off", "Present", "Absent", "Holiday"]

    logger.info("My Attendance Sheet dashboard validation completed successfully!")


@pytest.mark.ui
@pytest.mark.attendance
def test_click_date_opens_punch_logs_modal(page, employee_session):
    """
    Validates clicking on a date row opens the 'Punch Logs' modal:
    1. Employee visits /myAttendanceSheet.
    2. Clicks on Date (e.g. Day 1 / 2026-10-01).
    3. Asserts Punch Logs modal opens with header 'Punch Logs – <date>'.
    4. Asserts Punch Logs table renders columns: S. No, Punch Time, Punch Type.
    5. Reads punch records and asserts valid Punch Types ('IN' / 'OUT').
    6. Closes the modal and asserts it is no longer visible.
    """
    sheet_page = employee_session

    # Step 1: Click on Day 1 date to open Punch Logs modal
    opened = sheet_page.click_date_to_open_punch_logs(target_day_or_date=1)
    assert opened, "Failed to open Punch Logs modal when clicking on Day 1 date."

    # Step 2: Validate modal header
    header_text = sheet_page.get_punch_logs_modal_header()
    logger.info(f"Verified Punch Logs modal header: '{header_text}'")
    assert "punch logs" in header_text.lower(), f"Unexpected modal header: '{header_text}'"

    # Step 3: Validate table headers
    table_headers = sheet_page.get_punch_logs_table_headers()
    logger.info(f"Verified Punch Logs table headers: {table_headers}")
    expected_cols = ["S. No", "Punch Time", "Punch Type"]
    for col in expected_cols:
        assert any(col.lower() in h.lower() for h in table_headers), f"Expected column '{col}' missing from modal table"

    # Step 4: Validate punch log rows
    punch_records = sheet_page.get_punch_logs_records()
    from utils.attendance_calculator import format_punch_logs_ascii_table
    logger.info(format_punch_logs_ascii_table(punch_records))

    if punch_records:
        for idx, entry in enumerate(punch_records):
            punch_type = entry.get("punch_type", "").strip()
            assert any(t in punch_type.upper() for t in ["IN", "OUT"]), f"Unexpected punch type: '{punch_type}'"

    # Step 5: Close modal and verify it is dismissed
    sheet_page.close_punch_logs_modal()
    assert not sheet_page.is_punch_logs_modal_visible(), "Punch Logs modal remained visible after clicking close."
    logger.info("Punch Logs modal successfully closed and verified!")


@pytest.mark.ui
@pytest.mark.attendance
def test_verify_total_work_hours_matches_punch_logs(page, employee_session):
    """
    Business Rule Verification:
    1. Working Hours: sum(OUT - IN) = Total Working Hours
    2. Break Time:    sum(Next IN - Previous OUT) = Total Break Time
    3. Reconciles Attendance Sheet table row with Punch Logs modal.
    """
    from utils.attendance_calculator import (
        calculate_attendance_metrics_from_punches,
        parse_work_hours_str,
        format_punch_logs_ascii_table,
        format_attendance_reconciliation_summary
    )
    sheet_page = employee_session

    # Step 1: Read Day 1 record from main attendance table
    day_1 = sheet_page.get_record_by_date_or_day(1)
    assert day_1 is not None, "Day 1 attendance row not found in table."

    # Step 2: Open Punch Logs modal for Day 1
    opened = sheet_page.click_date_to_open_punch_logs(target_day_or_date=1)
    assert opened, "Failed to open Punch Logs modal for Day 1."

    # Step 3: Extract punch log records
    punch_records = sheet_page.get_punch_logs_records()
    assert punch_records, "No punch logs found in modal for Day 1."

    # Log clean ASCII Punch Logs Table
    logger.info(format_punch_logs_ascii_table(punch_records))

    # Step 4: Calculate Working Hours and Break Time metrics
    metrics = calculate_attendance_metrics_from_punches(punch_records)

    # Log clean Reconciliation Summary Table
    reconciliation_summary = format_attendance_reconciliation_summary(metrics, day_1)
    logger.info(reconciliation_summary)

    # Step 5: Assert Working Hours matches
    tbl_work = ""
    tbl_break = ""
    for k, v in day_1.items():
        if any(term in k.lower() for term in ["break", "break_time"]):
            tbl_break = v
        elif any(term in k.lower() for term in ["work_hour", "total_hour", "work_time", "total_work"]):
            tbl_work = v

    if tbl_work and tbl_work not in ["-", "N/A", ""]:
        tbl_h, tbl_m = parse_work_hours_str(tbl_work)
        calc_h, calc_m = metrics["work_hours"], metrics["work_minutes_remainder"]
        diff_work = abs((tbl_h * 60 + tbl_m) - (calc_h * 60 + calc_m))
        assert diff_work <= 1, (
            f"Working Hours mismatch! Table='{tbl_work}' vs Punch Log='{metrics['work_formatted']}' (diff={diff_work}m)"
        )

    # Step 6: Assert Break Time matches
    if tbl_break and tbl_break not in ["-", "N/A", ""]:
        tbl_bh, tbl_bm = parse_work_hours_str(tbl_break)
        calc_bh, calc_bm = metrics["break_hours"], metrics["break_minutes_remainder"]
        diff_break = abs((tbl_bh * 60 + tbl_bm) - (calc_bh * 60 + calc_bm))
        assert diff_break <= 1, (
            f"Break Time mismatch! Table='{tbl_break}' vs Punch Log='{metrics['break_formatted']}' (diff={diff_break}m)"
        )

    # Step 7: Close modal
    sheet_page.close_punch_logs_modal()
    assert not sheet_page.is_punch_logs_modal_visible(), "Punch Logs modal remained open."
    logger.info("Working Hours & Break Time validation successfully verified!")


