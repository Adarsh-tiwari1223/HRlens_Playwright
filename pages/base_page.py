"""
HRlens Portal — Base Page Object.

Provides core page-level utilities for all Page Objects:
- Page initialization with Playwright's Page instance.
- Portal navigation (e.g. Master menu navigation).
- Chakra UI Toast detection and retrieval.
- Chakra UI / React-Select searchable dropdown interactions.
- Field-level form error discovery and validation.

NOTE: Does NOT wrap native Playwright actions (click, fill, goto, etc.).
Page objects should interact directly with self.page / self.page.locator().
"""

import logging
import re
from playwright.sync_api import Page
from core.config import settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED LOGGING & ASSERTION EXPORTS (Backward Compatibility)
# ══════════════════════════════════════════════════════════════════════════════

def format_ascii_table(title: str, data: dict | list[dict] | None) -> str:
    """Formats dict or list of dicts into an ASCII grid table."""
    header_block = (
        "=========================================================\n"
        f"{title.upper()}\n"
        "========================================================="
    )
    if not data:
        return header_block + "\n\nNo records found."

    if isinstance(data, dict):
        data_list = [data]
    elif isinstance(data, list):
        data_list = [item for item in data if isinstance(item, dict)]
        if not data_list:
            return header_block + "\n\nNo records found."
    else:
        return header_block + "\n\nNo records found."

    headers = list(data_list[0].keys())
    display_headers = [" ".join(w.capitalize() for w in h.replace("_", " ").split()) for h in headers]

    rows = []
    for item in data_list:
        row = []
        for h in headers:
            val = item.get(h)
            row.append("—" if val is None or val == "" or val == "-" else str(val))
        rows.append(row)

    try:
        from tabulate import tabulate
        return header_block + "\n\n" + tabulate(rows, headers=display_headers, tablefmt="grid")
    except ImportError:
        pass

    col_widths = [max(len(display_headers[i]), max((len(r[i]) for r in rows), default=0)) for i in range(len(headers))]
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    lines = [separator]
    lines.append("|" + "|".join(f" {display_headers[i].ljust(w)} " for i, w in enumerate(col_widths)) + "|")
    lines.append(separator)
    for row in rows:
        lines.append("|" + "|".join(f" {row[i].ljust(w)} " for i, w in enumerate(col_widths)) + "|")
    lines.append(separator)

    return header_block + "\n\n" + "\n".join(lines)


class TestStoryLogger:
    """Enterprise Storyteller Logger for Playwright Test Execution."""
    __test__ = False

    def __init__(self, test_name: str, module: str = "Asset Management", phase: str = "Asset Lifecycle"):
        self.test_name = test_name
        self.module = module
        self.phase = phase
        self.step_count = 0
        self.start_time = None

    def start(self):
        import time
        from utils.logger import log_test_start
        self.start_time = time.time()
        log_test_start(module=self.module, phase=self.phase, test=self.test_name)

    def log_step(self, action: str, record: str = None, details: dict = None, expected: str = None, actual: str = None, status: str = "PASS"):
        from utils.logger import log_step
        self.step_count += 1
        log_step(action, value=record)

    def finish(self, status: str = "PASS"):
        from utils.logger import log_pass, log_fail, log_skip
        if status.upper() == "PASS":
            log_pass()
        elif status.upper() == "SKIP":
            log_skip(f"Status: {status}")
        else:
            log_fail(f"Status: {status}")


class ValidationFailure(AssertionError):
    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected: '{expected}', Actual: '{actual}'")


# ══════════════════════════════════════════════════════════════════════════════
# BASE PAGE CLASS
# ══════════════════════════════════════════════════════════════════════════════

class BasePage:
    """
    Base class for all Page Objects in HRlens Portal.
    Exposes `self.page` (Playwright Page) and application-level utilities.
    """

    def __init__(self, page: Page):
        self.page = page

    # ──────────────────────────────────────────────────────────────────────────
    # PORTAL-WIDE NAVIGATION HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def navigate_to_master_menu(self, target_link_name: str = None, **kwargs):
        """
        Global Master Navigation Helper (3-Step Menu Navigation):
        1. Checks if target link is already visible.
        2. Dismisses top-right toast overlay if present.
        3. Clicks profile button to open dropdown.
        4. Clicks 'Master' menuitem.
        5. Clicks target sub-link if provided (e.g. 'Asset Master', 'Company Document').
        """
        if target_link_name:
            link = self.page.locator(f"a[href*='{target_link_name.lower().replace(' ', '-')}'], a:has-text('{target_link_name}')").first
            if link.is_visible(timeout=300):
                link.click(force=True)
                return

        logger.info(f"Navigating to Master menu{' -> ' + target_link_name if target_link_name else ''}...")

        # Close any open dialog or overlay
        try:
            dialog = self.page.locator("[role='dialog'], .chakra-modal__content").first
            if dialog.is_visible(timeout=300):
                close_btn = dialog.locator(".chakra-modal__close-btn, button[aria-label*='Close' i], button:has-text('Cancel'), button:has-text('Close')").first
                if close_btn.is_visible(timeout=300):
                    close_btn.click(force=True)
                else:
                    self.page.keyboard.press("Escape")
                try:
                    dialog.wait_for(state="hidden", timeout=1500)
                except Exception:
                    pass
            overlay = self.page.locator(".chakra-modal__overlay").first
            if overlay.is_visible(timeout=300):
                self.page.keyboard.press("Escape")
                try:
                    overlay.wait_for(state="hidden", timeout=1500)
                except Exception:
                    pass
        except Exception:
            pass

        # Close active toast overlay
        try:
            toast_close_btn = self.page.locator(".chakra-toast__close-button, #chakra-toast-manager-top-right button[aria-label*='Close']").first
            if toast_close_btn.is_visible(timeout=500):
                toast_close_btn.click(force=True)
                try:
                    toast_close_btn.wait_for(state="hidden", timeout=1000)
                except Exception:
                    pass
        except Exception:
            pass

        # Click user profile menu button or fallback to direct route
        try:
            profile_btn = self.page.locator("button[id^='menu-button']:has(.chakra-avatar), button.chakra-menu__menu-button:has(.chakra-avatar), button:has(.chakra-avatar)").first
            if not profile_btn.is_visible(timeout=1500):
                profile_btn = self.page.get_by_role("button").filter(has=self.page.locator(".chakra-avatar, h1")).first

            profile_btn.click(timeout=3000)

            master_item = self.page.locator("[role='menuitem']:has-text('Master'), a:has-text('Master')").first
            if not master_item.is_visible(timeout=1000):
                profile_btn.click(force=True)

            master_item.wait_for(state="visible", timeout=3000)
            master_item.click()

            if target_link_name:
                sub_link = self.page.locator(f"a[href*='{target_link_name.lower().replace(' ', '-')}'], a:has-text('{target_link_name}')").first
                sub_link.wait_for(state="visible", timeout=3000)
                sub_link.click(force=True)
        except Exception as nav_err:
            logger.debug(f"Menu click navigation encountered: {nav_err}. Falling back to direct URL route...")
            if target_link_name:
                slug = target_link_name.lower().replace(' ', '-')
                self.page.goto(f"{settings.BASE_URL}/{slug}", timeout=30000)
            else:
                self.page.goto(f"{settings.BASE_URL}/asset-master", timeout=30000)

    # ──────────────────────────────────────────────────────────────────────────
    # TOAST & NOTIFICATION HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def dismiss_toasts(self):
        """Dismisses all visible Chakra toasts by clicking their close 'X' button or SVG."""
        try:
            close_locators = [
                ".chakra-toast button[aria-label='Close']",
                ".chakra-toast .chakra-toast__close-button",
                ".chakra-toast button:has(svg)",
                ".chakra-toast svg.chakra-icon",
                "#chakra-toast-manager-top-right button",
                "#chakra-toast-manager-top-right svg"
            ]
            for sel in close_locators:
                elements = self.page.locator(sel).all()
                for el in elements:
                    if el.is_visible():
                        el.click(force=True)
            self.page.wait_for_timeout(200)
        except Exception:
            pass

    def wait_for_toast(self, locator: str = "#chakra-toast-manager-top-right", timeout: int = 10000, **kwargs) -> str:
        """Waits for a toast message to appear, captures text, and dismisses the toast 'X' button."""
        toast_loc = self.page.locator(
            f"{locator} .chakra-toast, {locator} [role='status'], {locator} [role='alert'], "
            f".chakra-toast, [role='status'], [role='alert'], .chakra-alert"
        ).first
        try:
            toast_loc.wait_for(state="visible", timeout=timeout)
            text = toast_loc.inner_text().strip()
            # Click 'X' close button / SVG icon on toast
            close_btn = toast_loc.locator("button[aria-label='Close'], .chakra-toast__close-button, button:has(svg), svg.chakra-icon").first
            if close_btn.is_visible(timeout=500):
                close_btn.click(force=True)
        except Exception as e:
            logger.warning(f"Timeout waiting for toast element: {e}")
            text = ""
        logger.debug(f"toast → '{text}'")
        return text

    def wait_for_toast_message(self, locator: str = "#chakra-toast-manager-top-right", timeout: int = 10000, **kwargs) -> str:
        """Alias for wait_for_toast."""
        return self.wait_for_toast(locator=locator, timeout=timeout, **kwargs)

    def get_all_toasts(self, locator: str = "#chakra-toast-manager-top-right", timeout: int = 6000) -> list[str]:
        """Returns all visible toast messages."""
        toast_container = self.page.locator(locator)
        try:
            toast_container.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass
        toasts = self.page.locator(f"{locator} .chakra-toast, {locator} [role='status'], {locator} [id*='toast']").all_inner_texts()
        cleaned_toasts = [t.strip() for t in toasts if t.strip()]
        logger.debug(f"get_all_toasts → {cleaned_toasts}")
        return cleaned_toasts

    # ──────────────────────────────────────────────────────────────────────────
    # SEARCHABLE DROPDOWNS (CHAKRA UI / REACT-SELECT)
    # ──────────────────────────────────────────────────────────────────────────

    def select_react_dropdown(self, placeholder_text: str, option_text: str, container=None) -> str:
        """
        Interacts with searchable dropdowns (Chakra UI / React-Select).
        Clicks input, types search query, waits for options, and clicks the matching item.
        """
        target = container if container else self.page
        try:
            inp = target.get_by_placeholder(placeholder_text, exact=True).first
            if not inp.is_visible(timeout=1000):
                inp = target.get_by_placeholder(f"Search {placeholder_text}", exact=True).first
            if not inp.is_visible(timeout=1000):
                inp = target.get_by_placeholder(f"Select {placeholder_text}", exact=True).first
            if not inp.is_visible(timeout=1000):
                inp = target.locator(f"input[placeholder*='{placeholder_text}' i]").first
            if not inp.is_visible(timeout=1000):
                inp = target.locator(f"text='{placeholder_text}'").locator("xpath=ancestor::div[contains(@class, 'control') or contains(@class, 'select')]//input").first
            if not inp.is_visible(timeout=1000):
                inp = target.locator("input[id*='react-select']").first

            inp.click(force=True, timeout=2000)
            inp.fill("")
            inp.press_sequentially(option_text, delay=20)

            selected_text = option_text
            menu_options = self.page.locator("div[id*='option'], [role='option'], div[class*='option'], li[class*='option']").filter(has_text=re.compile(f"{re.escape(option_text)}", re.I))
            try:
                menu_options.first.wait_for(state="visible", timeout=1500)
                txt = menu_options.first.inner_text().strip()
                if txt:
                    selected_text = txt
                menu_options.first.click(force=True)
            except Exception:
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")

            try:
                container_tag = inp.locator("xpath=ancestor::div[contains(@class, 'form') or contains(@class, 'control') or contains(@class, 'group')]//span[contains(@class, 'css-1ny2kle') or contains(@class, 'tag') or contains(@class, 'singleValue')]").first
                if not container_tag.is_visible(timeout=300):
                    container_tag = target.locator("span.css-1ny2kle, .chakra-tag, div[class*='singleValue']").last

                if container_tag.is_visible(timeout=1000):
                    txt = container_tag.inner_text().strip().split("\n")[0].replace("×", "").strip()
                    if txt and txt != option_text:
                        selected_text = txt
            except Exception:
                pass

            logger.debug(f"select_react_dropdown → '{placeholder_text}' = '{selected_text}'")
            return selected_text
        except Exception as e:
            logger.warning(f"Failed to select '{option_text}' in dropdown '{placeholder_text}': {e}")
            return option_text

    # ──────────────────────────────────────────────────────────────────────────
    # FORM FIELD VALIDATION HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def get_field_validation(self, field_label_or_locator: str) -> str:
        """Returns validation error text below a specific form field or label."""
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
        """
        Dynamically discovers all visible field-level error messages in a form or modal.
        Returns a dictionary mapping field labels to their respective error text.
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
                        label_text = label_elem.inner_text().strip().rstrip("*").strip() if label_elem.is_visible() else "Field"
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
        """Asserts expected field-level validation messages and logs field-by-field details."""
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

    # ──────────────────────────────────────────────────────────────────────────
    # CUSTOM TABLE COLUMN FILTERING HELPERS (CHAKRA UI CUSTOM TABLE)
    # ──────────────────────────────────────────────────────────────────────────

    def filter_custom_table_column(
        self,
        header_name: str,
        query: str,
        condition: str = "Contains",
        table_selector: str = "table"
    ) -> None:
        """
        Generic 5-Step Custom Table Column Header Filter Helper (Chakra UI Custom Table):
        1. Locates <th> matching header_name (case-insensitive) and clicks its Filter button.
        2. Targets the open popover container (via aria-controls or visible popover section).
        3. Selects the condition option (e.g. 'Contains', 'Equals', 'Starts with').
        4. Fills the search query value input and presses Enter.
        5. Dismisses popover overlay with Escape and waits for filtered rows to render.
        """
        header_upper = header_name.upper()
        header_lower = header_name.lower()
        logger.info(f"Filtering table column '{header_name}' with query: '{query}' (Condition: '{condition}')")

        try:
            # Step 1: Locate Column Header & Filter Icon
            th_xpath = f"//th[contains(translate(., '{header_lower}', '{header_upper}'), '{header_upper}')]"
            th = self.page.locator(th_xpath).first
            if not th.is_visible(timeout=3000):
                th = self.page.locator(f"{table_selector} th").filter(has_text=re.compile(f"{re.escape(header_name)}", re.I)).first

            th.wait_for(state="visible", timeout=6000)
            th.scroll_into_view_if_needed()

            filter_btn = th.locator("button[aria-label='Filter']").first
            if not filter_btn.is_visible(timeout=1000):
                filter_btn = th.locator("button:has(svg), .chakra-button").first

            filter_btn.wait_for(state="visible", timeout=5000)
            filter_btn.scroll_into_view_if_needed()

            aria_controls = filter_btn.get_attribute("aria-controls")
            filter_btn.click()
            self.page.wait_for_timeout(600)

            # Step 2: Target Popover Container
            if aria_controls:
                popover = self.page.locator(f"#{aria_controls}")
                if not popover.is_visible():
                    popover = self.page.locator("section.chakra-popover__content:visible, [role='dialog']:visible, .chakra-popover__body:visible").first
            else:
                popover = self.page.locator("section.chakra-popover__content:visible, [role='dialog']:visible, .chakra-popover__body:visible").first

            popover.wait_for(state="visible", timeout=5000)

            # Step 3: Select Condition (e.g. 'Contains')
            select_el = popover.locator("select").first
            if select_el.count() > 0 and select_el.is_visible():
                try:
                    select_el.select_option(label=condition)
                except Exception:
                    try:
                        select_el.select_option(value=condition.lower())
                    except Exception:
                        pass
            else:
                cond_trigger = popover.locator("button, [role='button'], div.css-1tsdjac, div[class*='select']").first
                if cond_trigger.is_visible() and condition.lower() not in cond_trigger.inner_text().lower():
                    cond_trigger.click()
                    self.page.wait_for_timeout(300)
                    self.page.locator(f"//div[normalize-space()='{condition}'] | //button[normalize-space()='{condition}'] | [role='option']:has-text('{condition}')").first.click()
                    self.page.wait_for_timeout(300)

            # Step 4: Fill Value Input & Submit
            val_input = popover.locator("input[placeholder='Value'], input[placeholder*='Value'], input[type='text'], input").first
            val_input.wait_for(state="visible", timeout=5000)
            val_input.click()
            val_input.fill(query)
            self.page.wait_for_timeout(300)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(500)

            # Step 5: Close Popover Overlay & Wait for Table Refresh
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            self.page.wait_for_load_state("domcontentloaded")
            return

        except Exception as e:
            logger.warning(f"Custom table header filter for '{header_name}' encountered: {e}. Attempting global search input fallback...")

        # Fallback to search input if column header filter popover is not present
        try:
            search_input = self.page.locator("input[placeholder*='Search' i], input[type='search']").first
            if search_input.is_visible(timeout=2000):
                search_input.click()
                search_input.fill(query)
                search_input.press("Enter")
                self.page.wait_for_timeout(1000)
        except Exception:
            pass

