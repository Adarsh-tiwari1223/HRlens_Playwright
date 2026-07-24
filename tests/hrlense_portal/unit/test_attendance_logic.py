import pytest
from datetime import datetime
from utils.attendance_logic import calculate_attendance_status

def test_attendance_present():
    # 8 hours shift: check-in at 09:00, check-out at 17:00
    check_ins = [datetime(2026, 7, 24, 9, 0)]
    check_outs = [datetime(2026, 7, 24, 17, 0)]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    assert result["status"] == "Present"
    assert result["total_duration_hours"] == 8.0
    assert result["is_late"] is False

def test_attendance_half_day():
    # 5 hours worked: 4.5h to 8h is Half Day
    check_ins = [datetime(2026, 7, 24, 9, 0)]
    check_outs = [datetime(2026, 7, 24, 14, 0)]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    assert result["status"] == "Half Day"
    assert result["total_duration_hours"] == 5.0
    assert result["is_late"] is False

def test_attendance_early_out():
    # 3.5 hours worked: < 4.5h is Early Out
    check_ins = [datetime(2026, 7, 24, 9, 0)]
    check_outs = [datetime(2026, 7, 24, 12, 30)]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    assert result["status"] == "Early Out"
    assert result["total_duration_hours"] == 3.5
    assert result["is_late"] is False

def test_attendance_late():
    # Shift starts at 09:00. Check-in is 09:02 (> 1 min late)
    check_ins = [datetime(2026, 7, 24, 9, 2)]
    check_outs = [datetime(2026, 7, 24, 17, 2)]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    assert result["is_late"] is True

def test_attendance_not_late_on_boundary():
    # Shift starts at 09:00. Check-in is 09:01 (1 min late is acceptable, not > 1 min)
    check_ins = [datetime(2026, 7, 24, 9, 1)]
    check_outs = [datetime(2026, 7, 24, 17, 1)]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    assert result["is_late"] is False

def test_consecutive_checkins_without_checkout():
    # Check-in at 2:00 PM (14:00) and again at 6:00 PM (18:00) without checkout
    # The 6:00 PM check-in is considered the recent one.
    # Check-out happens at 10:00 PM (22:00). Total worked duration should be 4 hours.
    check_ins = [
        datetime(2026, 7, 24, 14, 0),
        datetime(2026, 7, 24, 18, 0)
    ]
    check_outs = [
        datetime(2026, 7, 24, 22, 0)
    ]
    shift_start = datetime(2026, 7, 24, 9, 0)
    
    result = calculate_attendance_status(check_ins, check_outs, shift_start)
    # 18:00 to 22:00 is 4 hours, which is less than 4.5 hours -> Early Out
    assert result["status"] == "Early Out"
    assert result["total_duration_hours"] == 4.0
    assert result["is_late"] is True # 18:00 is late compared to 09:00
