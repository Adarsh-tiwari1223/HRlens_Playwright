"""
HR Lens Attendance Calculator Utility.
Encapsulates attendance status calculation rules:
- Duration < 4 hrs -> Early Out / Absent
- 4.5 hrs <= Duration < 8 hrs (04:30:00 to 07:59:59) -> Half Day
- Duration >= 8 hrs -> Present
- Check-In > shift_start + 1 min -> Late
- Overwritten Punch: Latest Check-In without Check-Out overwrites previous Check-In.
"""

from datetime import datetime, timedelta


def parse_time_str(time_str: str) -> datetime:
    """Parses time strings like '09:30', '18:30', '2:00 PM', '14:00' into datetime objects."""
    time_str = time_str.strip()
    formats = ["%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unable to parse time string: '{time_str}'")


def resolve_latest_check_in(punches: list[str]) -> str:
    """
    Overwritten Check-In Rule:
    If employee checks in multiple times without checkout (e.g. 2:00 PM and 6:00 PM),
    the latest check-in time is considered the recent active check-in.
    """
    if not punches:
        return ""
    # Returns the last check-in punch
    return punches[-1]


def calculate_attendance_status(in_time_str: str, out_time_str: str, shift_start_str: str = "09:00") -> dict:
    """
    Calculates rendered attendance status based on HR Lens business rules:
    - worked < 4 hrs -> Early Out
    - 4.5 hrs <= worked < 8 hrs -> Half Day
    - worked >= 8 hrs -> Present
    - in_time > shift_start + 1 min -> Late
    """
    t_in = parse_time_str(in_time_str)
    t_out = parse_time_str(out_time_str)
    t_shift = parse_time_str(shift_start_str)

    # Handle cross-midnight shift
    if t_out < t_in:
        t_out += timedelta(days=1)

    worked_seconds = (t_out - t_in).total_seconds()
    worked_hours = worked_seconds / 3600.0

    # 1. Determine base status by worked hours
    if worked_hours < 4.0:
        base_status = "Early Out"
    elif 4.5 <= worked_hours < 8.0:
        base_status = "Half Day"
    else:  # worked_hours >= 8.0
        base_status = "Present"

    # 2. Check Late condition (in_time > shift_start + 1 min)
    is_late = (t_in - t_shift).total_seconds() > 60

    return {
        "status": base_status,
        "is_late": is_late,
        "worked_hours": round(worked_hours, 2),
        "display_status": f"Late ({base_status})" if is_late else base_status
    }
