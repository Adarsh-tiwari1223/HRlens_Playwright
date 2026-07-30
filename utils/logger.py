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
