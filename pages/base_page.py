import logging
import re
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class TestStoryLogger:
    """Enterprise Storyteller Logger for Playwright Test Execution."""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.step_count = 0
        self.start_time = None

    def start(self):
        import time
        self.start_time = time.time()
        logger.info("=========================================================")
        logger.info(f"TEST : {self.test_name}")
        logger.info("=========================================================")
        logger.info("")

    def log_step(self, action: str, record: str = None, details: dict = None, expected: str = None, actual: str = None, status: str = "PASS"):
        self.step_count += 1
        if self.step_count > 1:
            logger.info("---------------------------------------------------------")
            logger.info("")

        logger.info(f"Step {self.step_count} : {action}")
        if record:
            logger.info(f"Record : {record}")
        if details:
            for k, v in details.items():
                logger.info(f"{k} : {v}")
        if expected:
            logger.info(f"Expected : {expected}")
        if actual:
            logger.info(f"Actual   : {actual}")
        if status:
            logger.info(f"Status : {status}")
        logger.info("")

    def finish(self, status: str = "PASS"):
        import time
        exec_time = time.time() - self.start_time if self.start_time else 0
        logger.info("=========================================================")
        logger.info("SUMMARY")
        logger.info("=========================================================")
        logger.info("")
        logger.info(f"Result : {status}")
        logger.info(f"Execution Time : {exec_time:.2f} sec")
        logger.info("=========================================================")
        logger.info("")


class ValidationFailure(AssertionError):
    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected: '{expected}', Actual: '{actual}'")



class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def run_validations(self, module_name: str, validations: list):
        import time
        from datetime import datetime
        import os

        start_total = time.time()
        results = []
        failures = []
        total_count = len(validations)

        for idx, (name, func) in enumerate(validations, 1):
            start_time = time.time()
            try:
                func()
                duration = time.time() - start_time
                results.append((idx, name, "PASS", None, None, None, None, duration))
            except ValidationFailure as e:
                duration = time.time() - start_time
                failure_type = "Application Defect"

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
                filename = f"{safe_name}_{timestamp}.png"
                os.makedirs("screenshots", exist_ok=True)
                screenshot_path = os.path.join("screenshots", filename).replace("\\", "/")
                try:
                    self.page.screenshot(path=screenshot_path)
                except Exception as ex:
                    logger.error(f"Screenshot capture failed: {ex}")
                    screenshot_path = f"Failed to capture: {ex}"

                results.append((idx, name, "FAIL", failure_type, e.expected, e.actual, screenshot_path, duration))
                failures.append((name, failure_type))
            except Exception as e:
                duration = time.time() - start_time
                failure_type = "Automation Issue"

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
                filename = f"{safe_name}_{timestamp}.png"
                os.makedirs("screenshots", exist_ok=True)
                screenshot_path = os.path.join("screenshots", filename).replace("\\", "/")
                try:
                    self.page.screenshot(path=screenshot_path)
                except Exception as ex:
                    logger.error(f"Screenshot capture failed: {ex}")
                    screenshot_path = f"Failed to capture: {ex}"

                err_line = str(e).split('\n')[0] if str(e) else e.__class__.__name__

                results.append((idx, name, "FAIL", failure_type, "Successful operation/expected validation", err_line, screenshot_path, duration))
                failures.append((name, failure_type))

        total_duration = time.time() - start_total
        passed_count = sum(1 for r in results if r[2] == "PASS")
        failed_count = len(failures)

        report_lines = []
        report_lines.append("=========================================================")
        report_lines.append(f"TEST : {module_name}")
        report_lines.append("=========================================================")
        report_lines.append("")

        for r in results:
            idx, name, status, failure_type, expected, actual, screenshot, duration = r
            report_lines.append(f"[{idx}/{total_count}] {name}")
            report_lines.append("")
            report_lines.append(f"Status : {status}")
            report_lines.append("")
            if status == "FAIL":
                report_lines.append(f"Classification : {failure_type}")
                report_lines.append("")
                report_lines.append("Expected")
                report_lines.append(expected)
                report_lines.append("")
                report_lines.append("Actual")
                report_lines.append(actual)
                report_lines.append("")
                report_lines.append("Screenshot")
                report_lines.append(screenshot)
                report_lines.append("")
            report_lines.append(f"Duration : {duration:.1f} sec")
            report_lines.append("")
            report_lines.append("---------------------------------------------------------")
            report_lines.append("")

        report_lines.append("=========================================================")
        report_lines.append("SUMMARY")
        report_lines.append("=========================================================")
        report_lines.append("")
        report_lines.append(f"Total Validations : {total_count}")
        report_lines.append("")
        report_lines.append(f"Passed : {passed_count}")
        report_lines.append("")
        report_lines.append(f"Failed : {failed_count}")
        report_lines.append("")
        report_lines.append(f"Execution Time : {total_duration:.0f} sec")
        report_lines.append("")
        report_lines.append("=========================================================")

        logger.info("\n" + "\n".join(report_lines))

        if failed_count > 0:
            raise AssertionError(f"{module_name} failed with {failed_count} errors. Check logger output.")

    # ══════════════════════════════════════════════════════════════════════════════
    # REUSABLE SYNCHRONIZATION HELPERS (DEBUG LEVEL)
    # ══════════════════════════════════════════════════════════════════════════════

    def wait_for_dropdown_options(self, locator: str, min_options: int = 2, timeout: int = 5000):
        logger.debug(f"wait_for_dropdown_options → {locator}")
        select_el = self.page.locator(locator)
        select_el.wait_for(state="visible", timeout=timeout)
        try:
            select_el.locator("option").nth(min_options - 1).wait_for(state="attached", timeout=timeout)
        except Exception as e:
            logger.warning(f"Dropdown options count failed to reach {min_options}: {e}")

    def get_dropdown_options(self, locator: str, min_options: int = 1, timeout: int = 5000) -> list[str]:
        self.wait_for_dropdown_options(locator, min_options=min_options, timeout=timeout)
        options = self.page.locator(locator).locator("option").all_inner_texts()
        logger.debug(f"get_dropdown_options → {locator} = {options}")
        return options

    def wait_for_modal_ready(self, modal_selector: str, control_selector: str, timeout: int = 5000):
        logger.debug(f"wait_for_modal_ready → modal: '{modal_selector}', control: '{control_selector}'")
        self.page.locator(modal_selector).wait_for(state="visible", timeout=timeout)
        self.page.locator(control_selector).wait_for(state="visible", timeout=timeout)

    def wait_for_table_loaded(self, table_selector: str, timeout: int = 5000):
        logger.debug(f"wait_for_table_loaded → {table_selector}")
        self.page.locator(table_selector).wait_for(state="visible", timeout=timeout)
        self.page.locator(f"{table_selector} tbody tr, {table_selector} tr").first.wait_for(state="visible", timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════════
    # CORE INTERACTION ACTIONS (DEBUG LEVEL)
    # ══════════════════════════════════════════════════════════════════════════════

    def navigate(self, url: str):
        logger.debug(f"navigate → {url}")
        self.page.goto(url, wait_until="domcontentloaded")

    def click(self, locator: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).click()
        logger.debug(f"click → {locator}")

    # ══════════════════════════════════════════════════════════════════════════════
    # FIELD-LEVEL FORM VALIDATION HELPERS (FRAMEWORK-WIDE)
    # ══════════════════════════════════════════════════════════════════════════════

    def get_field_validation(self, field_label_or_locator: str) -> str:
        """Returns validation text below a specific form field or label."""
        try:
            control = self.page.locator(f".chakra-form-control:has(label:has-text('{field_label_or_locator}'))").first
            if control.is_visible():
                err = control.locator(".chakra-form__error-message, [id$='-feedback'], [role='alert']").first
                if err.is_visible():
                    return err.inner_text().strip()
            err_direct = self.page.locator(field_label_or_locator).locator(".chakra-form__error-message, [id$='-feedback'], [role='alert']").first
            if err_direct.is_visible():
                return err_direct.inner_text().strip()
        except Exception as e:
            logger.debug(f"get_field_validation for '{field_label_or_locator}' error: {e}")
        return ""

    def get_all_validation_messages(self, container_selector: str = "[role='dialog'], form") -> dict[str, str]:
        """Dynamically discovers all visible field-level error messages in form or modal.
        Returns a dictionary mapping field labels to their respective error text,
        e.g. {'Category Name': 'Category name is required'}
        """
        validations = {}
        try:
            container = self.page.locator(container_selector).first
            if not container.is_visible():
                container = self.page

            controls = container.locator(".chakra-form-control").all()
            for ctrl in controls:
                if ctrl.is_visible():
                    err_elem = ctrl.locator(".chakra-form__error-message, [id$='-feedback'], [role='alert']").first
                    if err_elem.is_visible():
                        err_text = err_elem.inner_text().strip()
                        label_elem = ctrl.locator(".chakra-form__label, label").first
                        if label_elem.is_visible():
                            label_text = label_elem.inner_text().strip().rstrip("*").strip()
                        else:
                            label_text = "Field"
                        validations[label_text] = err_text

            if not validations:
                err_elements = container.locator(".chakra-form__error-message, [id$='-feedback']").all()
                for idx, err in enumerate(err_elements, 1):
                    if err.is_visible():
                        validations[f"Field_{idx}"] = err.inner_text().strip()
        except Exception as e:
            logger.debug(f"get_all_validation_messages error: {e}")

        logger.debug(f"Discovered field validations: {validations}")
        return validations

    def assert_validation_message(self, expected_messages: dict[str, str], container_selector: str = "[role='dialog'], form") -> bool:
        """Asserts expected field-level validation messages and logs field-by-field details.
        expected_messages: e.g. {'Category Name': 'Category name is required'}
        """
        actual_messages = self.get_all_validation_messages(container_selector)
        all_passed = True
        
        logger.info("=========================================================")
        logger.info("Validation Summary")
        logger.info("=========================================================")

        for field_name, exp_text in expected_messages.items():
            act_text = actual_messages.get(field_name, "")
            is_match = exp_text.lower() in act_text.lower() if act_text else False
            if not is_match:
                all_passed = False
            status = "PASS" if is_match else "FAIL"

            logger.info(f"Field      : {field_name}")
            logger.info(f"Expected   : {exp_text}")
            logger.info(f"Actual     : {act_text if act_text else '<No field error displayed>'}")
            logger.info(f"Status     : {status}")
            logger.info("---------------------------------------------------------")

        return all_passed


    def fill(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).fill(value)
        logger.debug(f"fill → {locator} = '{value}'")

    def get_text(self, locator: str) -> str:
        self.page.locator(locator).wait_for(state="visible")
        text = self.page.locator(locator).inner_text()
        logger.debug(f"get_text → {locator} = '{text}'")
        return text

    def get_all_texts(self, locator: str) -> list[str]:
        texts = self.page.locator(locator).all_inner_texts()
        logger.debug(f"get_all_texts → {locator} = {texts}")
        return texts

    def is_visible(self, locator: str) -> bool:
        result = self.page.locator(locator).is_visible()
        logger.debug(f"is_visible → {locator} = {result}")
        return result

    def is_enabled(self, locator: str) -> bool:
        result = self.page.locator(locator).is_enabled()
        logger.debug(f"is_enabled → {locator} = {result}")
        return result

    def select_option(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).select_option(value)
        logger.debug(f"select_option → {locator} = '{value}'")

    def wait_for_url(self, partial: str):
        self.page.wait_for_url(f"**{partial}**")
        logger.debug(f"wait_for_url → '{partial}'")

    def wait_for_toast(self, locator: str, timeout: int = 6000) -> str:
        toast_loc = self.page.locator(f"{locator} .chakra-toast, {locator} [role='status'], {locator}").first
        try:
            toast_loc.wait_for(state="visible", timeout=timeout)
            text = toast_loc.inner_text().strip()
        except Exception as e:
            logger.warning(f"Timeout waiting for toast element: {e}")
            text = ""
        logger.debug(f"toast → '{text}'")

        return text






    def get_all_toasts(self, locator: str) -> list[str]:
        self.page.locator(locator).wait_for(state="visible")
        toasts = self.page.locator(f"{locator} [id*='toast'][id*='title']").all_inner_texts()
        logger.debug(f"toasts → {toasts}")
        return toasts

    def wait_for_hidden(self, locator: str):
        self.page.locator(locator).wait_for(state="hidden")
        logger.debug(f"wait_for_hidden → {locator}")

    def get_count(self, locator: str) -> int:
        count = self.page.locator(locator).count()
        logger.debug(f"get_count → {locator} = {count}")
        return count

    def upload_file(self, locator: str, file_path: str):
        self.page.locator(locator).set_input_files(file_path)
        logger.debug(f"upload_file → {locator} = '{file_path}'")

    def scroll_into_view(self, locator: str):
        self.page.locator(locator).scroll_into_view_if_needed()
        logger.debug(f"scroll_into_view → {locator}")

    def reload(self):
        self.page.reload()
        logger.debug("reload")
