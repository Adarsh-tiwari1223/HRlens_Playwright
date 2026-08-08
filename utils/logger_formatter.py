"""
Enterprise Logger Formatter Module.
Provides exact text formatting templates for test lifecycle, debug steps, failure reports, and summaries.
"""

from typing import List, Optional


class LoggerFormatter:

    @staticmethod
    def format_test_header(module: str, phase: str, test: str) -> str:
        """Formats clean concise test header."""
        return f"[TEST START] {module} | {phase} | {test}"

    @staticmethod
    def format_pass(duration: float) -> str:
        """Formats PASS result block."""
        return f"[TEST RESULT: PASS] (Duration: {duration:.2f}s)"

    @staticmethod
    def format_skip(reason: str) -> str:
        """Formats SKIPPED result block."""
        return f"[TEST RESULT: SKIPPED] Reason: {reason}"

    @staticmethod
    def format_fail(
        module: str,
        phase: str,
        test: str,
        successful_steps: List[str],
        failed_step: Optional[str],
        exception_msg: str,
        duration: float
    ) -> str:
        """Formats detailed FAILED status report."""
        success_block = ""
        if successful_steps:
            steps_txt = "\n".join([f"✓ {s}" for s in successful_steps])
            success_block = (
                f"Last Successful Step\n"
                f"--------------------\n"
                f"{steps_txt}\n\n"
            )

        failed_block = ""
        if failed_step:
            failed_block = (
                f"Failed Step\n"
                f"-----------\n"
                f"✗ {failed_step}\n\n"
            )

        return (
            f"\n{'=' * 80}\n"
            f"TEST\n"
            f"{'=' * 80}\n"
            f"Module : {module}\n"
            f"Phase  : {phase}\n"
            f"Test   : {test}\n\n"
            f"STATUS : FAILED\n\n"
            f"{success_block}"
            f"{failed_block}"
            f"Exception\n"
            f"---------\n"
            f"{exception_msg}\n\n"
            f"Execution Time : {duration:.2f} sec\n"
            f"{'=' * 80}\n"
        )

    @staticmethod
    def format_step(step_name: str, value: Optional[str] = None) -> str:
        """Formats Workflow Layer [STEP] logging."""
        if value:
            return f"[STEP] {step_name} : {value}"
        return f"[STEP] {step_name}"

    @staticmethod
    def format_debug(action: str, target: str = "", value: Optional[str] = None) -> str:
        """Formats Page Layer [DEBUG] interaction logging."""
        if target:
            res = f"[DEBUG] {action} → {target}"
        else:
            res = f"[DEBUG] {action}"
        if value:
            res += f"\n        Value : {value}"
        return res

    @staticmethod
    def format_summary(passed: int, skipped: int, failed: int, duration_sec: float) -> str:
        """Formats final test execution summary block."""
        mins = int(duration_sec // 60)
        secs = int(duration_sec % 60)
        dur_str = f"{mins:02d}m {secs:02d}s"

        return (
            f"\n{'=' * 80}\n"
            f"SUMMARY\n"
            f"{'=' * 80}\n\n"
            f"Passed  : {passed}\n\n"
            f"Skipped : {skipped}\n\n"
            f"Failed  : {failed}\n\n"
            f"Duration: {dur_str}\n"
            f"{'=' * 80}\n"
        )
