"""
Enterprise Logger Facade Module.
Provides high-level API methods for Test Layer, Workflow Layer, and Page Layer.
"""

import time
import logging
from typing import List, Optional
from utils.log_config import configure_logger
from utils.logger_formatter import LoggerFormatter

_logger = configure_logger()


class LoggerState:
    current_module: str = "Director"
    current_phase: str = "Phase 1"
    current_test: str = ""
    start_time: float = 0.0
    successful_steps: List[str] = []
    current_step: Optional[str] = None


def log_test_start(module: str, phase: str, test: str):
    """Test Layer API: Begins a new test scenario."""
    LoggerState.current_module = module
    LoggerState.current_phase = phase
    LoggerState.current_test = test
    LoggerState.start_time = time.time()
    LoggerState.successful_steps = []
    LoggerState.current_step = None

    header = LoggerFormatter.format_test_header(module, phase, test)
    _logger.info(header)


def log_phase(phase_name: str):
    """Test Layer API: Sets current active test phase."""
    LoggerState.current_phase = phase_name


def log_step(step_name: str, value: Optional[str] = None):
    """Workflow Layer API: Logs high-level business workflow steps (INFO level)."""
    if LoggerState.current_step:
        LoggerState.successful_steps.append(LoggerState.current_step)
    LoggerState.current_step = step_name

    txt = LoggerFormatter.format_step(step_name, value)
    _logger.info(txt)


def log_debug(action: str, target: str = "", value: Optional[str] = None):
    """Page Layer API: Logs detailed UI interaction steps (DEBUG level only)."""
    txt = LoggerFormatter.format_debug(action, target, value)
    _logger.debug(txt)


def log_pass(duration: Optional[float] = None):
    """Test Layer API: Logs PASS result for current test."""
    dur = duration if duration is not None else (time.time() - LoggerState.start_time)
    txt = LoggerFormatter.format_pass(dur)
    _logger.info(txt)


def log_skip(reason: str):
    """Test Layer API: Logs SKIPPED result for current test."""
    txt = LoggerFormatter.format_skip(reason)
    _logger.info(txt)


def log_warning(msg: str):
    """Logs framework warnings (WARNING level)."""
    _logger.warning(f"[WARNING] {msg}")


def log_error(msg: str):
    """Logs framework error messages (ERROR level)."""
    _logger.error(f"[ERROR] {msg}")


def log_fail(exception_msg: str, duration: Optional[float] = None):
    """Test Layer API: Logs detailed failure report upon test exception."""
    dur = duration if duration is not None else (time.time() - LoggerState.start_time)
    txt = LoggerFormatter.format_fail(
        module=LoggerState.current_module,
        phase=LoggerState.current_phase,
        test=LoggerState.current_test,
        successful_steps=LoggerState.successful_steps,
        failed_step=LoggerState.current_step,
        exception_msg=exception_msg,
        duration=dur
    )
    _logger.error(txt)


def log_summary(passed: int, skipped: int, failed: int, duration: float):
    """Framework API: Logs final execution summary."""
    txt = LoggerFormatter.format_summary(passed, skipped, failed, duration)
    _logger.info(txt)


def log_business_validation_summary(validations: dict):
    """Prints a clean, boxed Business Validation Summary table to the framework log stream."""
    _logger.info("============================================================")
    _logger.info("BUSINESS VALIDATION SUMMARY")
    _logger.info("============================================================")
    for key, val in validations.items():
        _logger.info(f"{key:<35}: {val}")
    _logger.info("============================================================")


def log_step_header(step_title: str):
    """Prints step header banner."""
    _logger.info("================================================================================")
    _logger.info(f"{step_title}")
    _logger.info("================================================================================\n")
    _logger.info(f"{'Status':<20}: EXECUTING\n")


def log_step_footer():
    """Prints step footer completion status."""
    _logger.info(f"\n{'Status':<20}: COMPLETED\n")


def log_enterprise_report(
    module: str,
    test_case: str,
    scenario: str,
    role: str,
    exec_id: str,
    env: str,
    user_auth: dict,
    meeting_module: dict,
    meeting_details: dict,
    participant: dict,
    availability: dict,
    submission: dict,
    grid_verification: dict,
    failure_analysis: Optional[dict],
    summary: dict,
    duration: float
):
    """Prints the multi-section Enterprise Execution Report matching exact user template."""
    banner = f"{'=' * 80}\n"
    _logger.info(f"{banner}TEST EXECUTION\n{banner}"
                 f"Module              : {module}\n"
                 f"Test Case           : {test_case}\n"
                 f"Scenario            : {scenario}\n"
                 f"Role                : {role}\n"
                 f"Execution ID        : {exec_id}\n"
                 f"Environment         : {env}\n")

    _logger.info(f"{banner}STEP 01 : USER AUTHENTICATION\n{banner}"
                 f"Role                : {user_auth.get('role', 'HR')}\n"
                 f"Employee Name       : {user_auth.get('name', 'Shiva Kumar')}\n"
                 f"Employee Email      : {user_auth.get('email', '')}\n\n"
                 f"Login Status        : {user_auth.get('login_status', 'PASS')}\n"
                 f"Dashboard Loaded    : {user_auth.get('dashboard_loaded', 'PASS')}\n")

    _logger.info(f"{banner}STEP 02 : MEETING MODULE\n{banner}"
                 f"Navigation          : {meeting_module.get('nav', 'Meetings')}\n"
                 f"Current URL         : {meeting_module.get('url', '')}\n\n"
                 f"Module Access       : {meeting_module.get('access', 'PASS')}\n"
                 f"Create Meeting Btn  : {meeting_module.get('btn', 'Visible')}\n")

    _logger.info(f"{banner}STEP 03 : MEETING DETAILS\n{banner}"
                 f"Meeting Title       : {meeting_details.get('title', '')}\n"
                 f"Meeting Type        : {meeting_details.get('type', 'Online')}\n"
                 f"Meeting Date        : {meeting_details.get('date', '')}\n"
                 f"Start Time          : {meeting_details.get('start', '10:00')}\n"
                 f"End Time            : {meeting_details.get('end', '11:00')}\n\n"
                 f"Description         : {meeting_details.get('desc', '')}\n")

    _logger.info(f"{banner}STEP 04 : PARTICIPANT SELECTION\n{banner}"
                 f"Search Keyword      : {participant.get('keyword', 'sanidhy')}\n\n"
                 f"Participant Found\n\n"
                 f"Employee Name       : {participant.get('name', 'Sanidhy Tiwari')}\n"
                 f"Branch              : {participant.get('branch', 'Job-Varanasi')}\n"
                 f"Employee ID         : {participant.get('id', 'EMP-102')}\n\n"
                 f"Participant Added   : {participant.get('status', 'PASS')}\n")

    _logger.info(f"{banner}STEP 05 : AVAILABILITY\n{banner}"
                 f"Availability Status : {availability.get('status', 'Available')}\n\n"
                 f"Conflict Count      : {availability.get('conflict', '1')}\n\n"
                 f"Availability Check  : {availability.get('check', 'PASS')}\n")

    _logger.info(f"{banner}STEP 06 : MEETING SUBMISSION\n{banner}"
                 f"Create Meeting      : {submission.get('action', 'CLICKED')}\n\n"
                 f"Confirmation Popup  : {submission.get('popup', 'Displayed')}\n\n"
                 f"Confirmation        : {submission.get('confirm', 'Accepted')}\n\n"
                 f"Google OAuth Popup  : {submission.get('oauth', 'Handled')}\n"
                 f"Popup Handling      : {submission.get('oauth_status', 'Bypassed')}\n\n"
                 f"Toast Message       : {submission.get('toast', 'Meeting Created Successfully')}\n\n"
                 f"Submission Status   : {submission.get('status', 'SUCCESS')}\n")

    _logger.info(f"{banner}STEP 07 : GRID VERIFICATION\n{banner}"
                 f"Searching Meeting\n\n"
                 f"Meeting Title       : {grid_verification.get('title', '')}\n\n"
                 f"Grid Refreshed      : {grid_verification.get('refreshed', 'YES')}\n\n"
                 f"Search Applied      : {grid_verification.get('search_applied', 'YES')}\n\n"
                 f"Rows Visible        : {grid_verification.get('rows', '20')}\n\n"
                 f"Meeting Found       : {grid_verification.get('found', 'YES')}\n")

    if grid_verification.get("snapshot"):
        _logger.info(f"{banner}GRID SNAPSHOT\n{banner}"
                     f"{grid_verification.get('snapshot')}\n")

    if failure_analysis:
        _logger.info(f"{banner}FAILURE ANALYSIS\n{banner}"
                     f"Expected Meeting   : {failure_analysis.get('expected')}\n\n"
                     f"Actual Result      : {failure_analysis.get('actual')}\n\n"
                     f"Possible Reason    : {failure_analysis.get('reason')}\n")

    _logger.info(f"{banner}TEST SUMMARY\n{banner}"
                 f"{'Login':<30} {summary.get('login', 'PASS')}\n"
                 f"{'Meeting Module':<30} {summary.get('module', 'PASS')}\n"
                 f"{'Meeting Details':<30} {summary.get('details', 'PASS')}\n"
                 f"{'Participant Selection':<30} {summary.get('participant', 'PASS')}\n"
                 f"{'Availability Check':<30} {summary.get('availability', 'PASS')}\n"
                 f"{'Meeting Submission':<30} {summary.get('submission', 'PASS')}\n"
                 f"{'Grid Verification':<30} {summary.get('grid', 'PASS')}\n\n"
                 f"{'Overall Result':<30} {summary.get('overall', 'PASS')}\n\n"
                 f"{'Execution Time':<30} {duration:.2f} sec\n{banner}")


def log_final_business_summary(validations: dict, duration: float, overall_result: str = "PASS"):
    """Prints the complete, formatted FINAL BUSINESS SUMMARY block."""
    _logger.info("================================================================================")
    _logger.info("FINAL BUSINESS SUMMARY")
    _logger.info("================================================================================\n")
    for key, val in validations.items():
        _logger.info(f"{key:<35} {val}")
    _logger.info(f"\n{'Execution Time':<35} {duration:.2f} sec")
    _logger.info(f"{'Overall Result':<35} {overall_result}\n")
    _logger.info("===========================================================================")
