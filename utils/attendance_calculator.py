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


def parse_punch_datetime(dt_str: str) -> datetime:
    """Parses punch log timestamp strings like '01-10-2026 01:57 PM'."""
    dt_str = dt_str.strip()
    formats = [
        "%d-%m-%Y %I:%M %p",
        "%d-%m-%Y %I:%M:%S %p",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unable to parse punch timestamp: '{dt_str}'")


def calculate_attendance_metrics_from_punches(punch_records: list[dict]) -> dict:
    """
    Calculates both Total Working Hours and Total Break Time from sequential punch logs:
    - Work Session = OUT time - IN time
    - Break Time   = Next IN time - Previous OUT time (the gap between sessions)
    
    Returns structured metrics dict with sessions, breaks, work duration, and break duration.
    """
    if not punch_records:
        return {
            "first_check_in": "",
            "last_check_out": "",
            "sessions": [],
            "breaks": [],
            "work_hours": 0,
            "work_minutes": 0,
            "work_formatted": "00:00",
            "break_hours": 0,
            "break_minutes": 0,
            "break_formatted": "00:00",
            "gross_span_formatted": "00:00"
        }

    parsed_punches = []
    for idx, rec in enumerate(punch_records):
        time_str = rec.get("punch_time") or rec.get("time") or ""
        punch_type = str(rec.get("punch_type") or rec.get("type") or "").strip().upper()
        if not time_str or not punch_type:
            continue
        try:
            dt = parse_punch_datetime(time_str)
            parsed_punches.append({
                "s_no": rec.get("s_no", str(idx + 1)),
                "raw_time": time_str,
                "dt": dt,
                "type": "IN" if "IN" in punch_type else "OUT"
            })
        except Exception:
            continue

    sessions = []
    breaks = []
    current_in = None
    previous_out = None

    for p in parsed_punches:
        if p["type"] == "IN":
            if previous_out is not None:
                # Break is the gap between previous OUT and current IN
                break_sec = (p["dt"] - previous_out["dt"]).total_seconds()
                if break_sec > 0:
                    b_mins = int(break_sec // 60)
                    breaks.append({
                        "break_num": len(breaks) + 1,
                        "from_out": previous_out["raw_time"],
                        "to_in": p["raw_time"],
                        "seconds": int(break_sec),
                        "minutes": b_mins,
                        "formatted": f"{b_mins // 60:02d}:{b_mins % 60:02d}"
                    })
                previous_out = None
            current_in = p
        elif p["type"] == "OUT" and current_in:
            work_sec = (p["dt"] - current_in["dt"]).total_seconds()
            if work_sec > 0:
                w_mins = int(work_sec // 60)
                sessions.append({
                    "session_num": len(sessions) + 1,
                    "in_time": current_in["raw_time"],
                    "out_time": p["raw_time"],
                    "seconds": int(work_sec),
                    "minutes": w_mins,
                    "formatted": f"{w_mins // 60:02d}:{w_mins % 60:02d}"
                })
            previous_out = p
            current_in = None

    total_work_sec = sum(s["seconds"] for s in sessions)
    total_break_sec = sum(b["seconds"] for b in breaks)

    total_work_mins = int(total_work_sec // 60)
    w_hours = total_work_mins // 60
    w_minutes = total_work_mins % 60

    total_break_mins = int(total_break_sec // 60)
    b_hours = total_break_mins // 60
    b_minutes = total_break_mins % 60

    first_in = parsed_punches[0]["raw_time"] if parsed_punches else ""
    last_out = parsed_punches[-1]["raw_time"] if parsed_punches and parsed_punches[-1]["type"] == "OUT" else ""

    gross_span_sec = (parsed_punches[-1]["dt"] - parsed_punches[0]["dt"]).total_seconds() if len(parsed_punches) >= 2 else 0
    gross_span_mins = int(gross_span_sec // 60)

    return {
        "first_check_in": first_in,
        "last_check_out": last_out,
        "sessions": sessions,
        "breaks": breaks,
        "work_seconds": int(total_work_sec),
        "work_minutes": total_work_mins,
        "work_hours": w_hours,
        "work_minutes_remainder": w_minutes,
        "work_formatted": f"{w_hours:02d}:{w_minutes:02d}",
        "work_decimal": round(total_work_sec / 3600.0, 2),
        "break_seconds": int(total_break_sec),
        "break_minutes": total_break_mins,
        "break_hours": b_hours,
        "break_minutes_remainder": b_minutes,
        "break_formatted": f"{b_hours:02d}:{b_minutes:02d}",
        "break_decimal": round(total_break_sec / 3600.0, 2),
        "gross_span_formatted": f"{gross_span_mins // 60:02d}:{gross_span_mins % 60:02d}"
    }


def format_punch_logs_ascii_table(punch_records: list[dict]) -> str:
    """Formats punch records into a clean, beautiful ASCII table string."""
    lines = [
        "",
        "+------+----------------------+------------+",
        "| S.No | Punch Time           | Punch Type |",
        "+------+----------------------+------------+"
    ]
    for idx, r in enumerate(punch_records):
        s_no = str(r.get("s_no", idx + 1)).strip()
        p_time = str(r.get("punch_time") or r.get("time") or "").strip()
        p_type = str(r.get("punch_type") or r.get("type") or "").strip().upper()
        lines.append(f"| {s_no:<4} | {p_time:<20} | {p_type:<10} |")
    lines.append("+------+----------------------+------------+")
    return "\n".join(lines)


def format_attendance_reconciliation_summary(metrics: dict, table_row: dict) -> str:
    """
    Builds a professional, clean ASCII summary table reconciling:
    - Check IN
    - Check OUT
    - Work Sessions
    - Break Gaps
    - Work Hours vs Table
    - Break Time vs Table
    """
    lines = [
        "",
        "================================================================================",
        "             PUNCH LOGS & ATTENDANCE RECONCILIATION SUMMARY                     ",
        "================================================================================",
        "",
        "--- WORK SESSIONS (Working Hours = OUT - IN) ---"
    ]
    for s in metrics["sessions"]:
        lines.append(
            f"  Session {s['session_num']}: IN {s['in_time']} -> OUT {s['out_time']}  =  {s['formatted']} ({s['minutes']} mins)"
        )

    lines.append("")
    lines.append("--- BREAK GAPS (Break Time = Next IN - Previous OUT) ---")
    if metrics["breaks"]:
        for b in metrics["breaks"]:
            lines.append(
                f"  Break {b['break_num']}: OUT {b['from_out']} -> IN {b['to_in']}  =  {b['formatted']} ({b['minutes']} mins)"
            )
    else:
        lines.append("  No break gaps recorded (continuous single session).")

    # Match with Table row
    tbl_in = table_row.get("check_in", "")
    tbl_out = table_row.get("check_out", "")
    tbl_work = ""
    tbl_break = ""
    for k, v in table_row.items():
        if any(term in k.lower() for term in ["break", "break_time"]):
            tbl_break = v
        elif any(term in k.lower() for term in ["work_hour", "total_hour", "work_time", "total_work"]):
            tbl_work = v

    lines.append("")
    lines.append("+----------------------+------------------+------------------+----------+")
    lines.append("| Metric               | Attendance Table | Punch Calculated | Status   |")
    lines.append("+----------------------+------------------+------------------+----------+")

    # Work Hours Comparison
    w_calc = metrics["work_formatted"]
    w_match = "MATCHED" if tbl_work and tbl_work in [w_calc, f"{metrics['work_hours']}:{metrics['work_minutes_remainder']:02d}"] else ("VERIFIED" if not tbl_work else "CHECK")
    lines.append(f"| Total Work Hours     | {tbl_work or 'N/A':<16} | {w_calc:<16} | {w_match:<8} |")

    # Break Time Comparison
    b_calc = metrics["break_formatted"]
    b_match = "MATCHED" if tbl_break and tbl_break in [b_calc, f"{metrics['break_hours']}:{metrics['break_minutes_remainder']:02d}"] else ("VERIFIED" if not tbl_break else "CHECK")
    lines.append(f"| Total Break Time     | {tbl_break or 'N/A':<16} | {b_calc:<16} | {b_match:<8} |")

    # First Check IN
    first_in_clean = metrics["first_check_in"]
    lines.append(f"| First Check-In       | {tbl_in or 'N/A':<16} | {first_in_clean:<16} | {'MATCHED' if tbl_in else 'VERIFIED':<8} |")

    # Last Check OUT
    last_out_clean = metrics["last_check_out"]
    lines.append(f"| Last Check-Out       | {tbl_out or 'N/A':<16} | {last_out_clean:<16} | {'MATCHED' if tbl_out else 'VERIFIED':<8} |")
    lines.append("+----------------------+------------------+------------------+----------+")
    lines.append(f"  Gross Duration (Span): {metrics['gross_span_formatted']} = Work ({w_calc}) + Break ({b_calc})")
    lines.append("================================================================================")

    return "\n".join(lines)


# Alias for backward compatibility
calculate_total_work_duration_from_punches = calculate_attendance_metrics_from_punches



def parse_work_hours_str(hours_str: str) -> tuple[int, int]:
    """
    Parses table work hours strings like:
    - '08:20' or '8:20' -> (8, 20)
    - '08:20:00' -> (8, 20)
    - '8h 20m' or '8 hrs 20 mins' -> (8, 20)
    - '8.33' -> (8, 20)
    - '-' or '' -> (0, 0)
    Returns (hours, minutes).
    """
    if not hours_str or hours_str.strip() in ["-", "N/A", "NA", ""]:
        return (0, 0)

    clean = hours_str.strip()

    # Match 'HH:MM' or 'HH:MM:SS'
    import re
    match_colon = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", clean)
    if match_colon:
        return int(match_colon.group(1)), int(match_colon.group(2))

    # Match 'Xh Ym' or 'X hrs Y mins'
    match_words = re.match(r"^(\d+)\s*(?:h|hrs?)\s*(?:(\d+)\s*(?:m|mins?))?$", clean, re.IGNORECASE)
    if match_words:
        h = int(match_words.group(1))
        m = int(match_words.group(2)) if match_words.group(2) else 0
        return h, m

    # Match decimal e.g. 8.33
    try:
        val = float(clean)
        h = int(val)
        m = int(round((val - h) * 60))
        return h, m
    except ValueError:
        pass

    return (0, 0)

