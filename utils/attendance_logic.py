from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def calculate_attendance_status(check_ins: list[datetime], check_outs: list[datetime], shift_start: datetime) -> dict:
    """
    Calculates attendance status and lateness based on HR Lens Attendance Logic:
    
    1. if less than 4.5 hr = early Out (specifically less than 4 hr is early out, and half day starts at 4.5 hr)
    2. if equal or greater than 4.5 hr and less than 8 hr = half day (4.5 - 7:59:59)
    3. if equal or greater than 8 hrs = present
    4. if check in time is 1 min greater than shift start time = late
    5. if Check in at 2:00 pm and again check in At 6:00 pm without checkout then the new check in time considered the recent one
    """
    if not check_ins:
        return {
            "status": "Absent",
            "is_late": False,
            "total_duration_hours": 0.0
        }

    # Sort inputs chronologically
    sorted_ins = sorted(check_ins)
    sorted_outs = sorted(check_outs)

    # 1. Normalize check-ins and check-outs to handle consecutive check-ins without check-outs
    # If a check-in occurs after another check-in without an intervening check-out,
    # the later check-in replaces the earlier one (it is considered the recent one).
    normalized_ins = []
    
    # We pair check-ins and check-outs chronologically
    in_idx = 0
    out_idx = 0
    last_in = None
    
    while in_idx < len(sorted_ins):
        current_in = sorted_ins[in_idx]
        
        # Check if there is a next check-in before the next check-out
        next_in = sorted_ins[in_idx + 1] if in_idx + 1 < len(sorted_ins) else None
        next_out = sorted_outs[out_idx] if out_idx < len(sorted_outs) else None
        
        # If there's another check-in before the next check-out, skip current check-in (overwritten by the more recent one)
        if next_in and (not next_out or next_in < next_out):
            logger.info(f"Discarding check-in at {current_in} because a more recent check-in exists at {next_in} before checkout.")
            in_idx += 1
            continue
            
        # Otherwise, this is a valid check-in
        normalized_ins.append(current_in)
        in_idx += 1
        
        # Move out index past any check-outs that happened before this check-in
        while out_idx < len(sorted_outs) and sorted_outs[out_idx] < current_in:
            out_idx += 1

    # Filter out check-outs that occur after the normalized check-ins
    normalized_outs = []
    for out in sorted_outs:
        # Find if this check-out corresponds to a check-in
        # For simplicity, we pair each normalized check-in with the first check-out that happens after it
        pass

    # Re-pair chronologically
    pairs = []
    out_idx = 0
    for chk_in in normalized_ins:
        # Find the first check-out that is after this check-in
        while out_idx < len(sorted_outs) and sorted_outs[out_idx] <= chk_in:
            out_idx += 1
        if out_idx < len(sorted_outs):
            pairs.append((chk_in, sorted_outs[out_idx]))
            out_idx += 1 # Consume this check-out
        else:
            # Unpaired check-in (no check-out)
            pass

    # 2. Calculate total worked duration
    total_duration = timedelta()
    for chk_in, chk_out in pairs:
        total_duration += (chk_out - chk_in)
        
    duration_hours = total_duration.total_seconds() / 3600.0

    # 3. Determine status
    if duration_hours >= 8.0:
        status = "Present"
    elif duration_hours >= 4.5:
        status = "Half Day"
    else:
        status = "Early Out"

    # 4. Determine lateness
    # If the first valid check-in is > shift_start + 1 minute, it is late
    is_late = False
    if normalized_ins:
        first_in = normalized_ins[0]
        # Compare time component of first_in with time component of shift_start
        first_in_time = first_in.time()
        shift_start_time = shift_start.time()
        
        # Convert times to minutes from midnight for direct comparison
        first_in_minutes = first_in_time.hour * 60 + first_in_time.minute
        shift_start_minutes = shift_start_time.hour * 60 + shift_start_time.minute
        
        if first_in_minutes > (shift_start_minutes + 1):
            is_late = True

    return {
        "status": status,
        "is_late": is_late,
        "total_duration_hours": round(duration_hours, 2)
    }
