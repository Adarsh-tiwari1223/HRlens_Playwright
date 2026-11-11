"""
HRlens Portal — Attendance Master Page Object Model.
Target URL: /master/attendance_master

Encapsulates page locators, grid inspection, search, column configuration,
and modal operations for Attendance Setting master data.
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Locator
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AttendanceMasterPage(BasePage):
    """Page Object for Attendance Setting Master (/master/attendance_master)."""

    PAGE_ROUTE = "/master/attendance_master"

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN GRID & PAGE LOCATORS
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def heading(self) -> Locator:
        """Returns the main page title element or primary CTA."""
        return self.page.locator("button:has-text('Add Attendance Setting')").or_(
            self.page.locator("h1, h2, h3").filter(has_text="Attendance")
        ).first

    @property
    def add_attendance_setting_button(self) -> Locator:
        """Returns the 'Add Attendance Setting' button."""
        btn = self.page.locator("button:has-text('Add Attendance Setting')").first
        if not btn.is_visible(timeout=1000):
            return self.page.get_by_role("button", name="Add Attendance Setting").first
        return btn

    @property
    def search_input(self) -> Locator:
        """Returns the primary search input field."""
        return self.page.locator("input[placeholder*='Search by company, branch or department' i]").first

    @property
    def columns_menu_button(self) -> Locator:
        """Returns the columns visibility toggle button."""
        return self.page.locator("button[aria-label='Columns']").first

    @property
    def table(self) -> Locator:
        """Returns the main table locator."""
        return self.page.locator("table.chakra-table").first

    @property
    def table_headers(self) -> Locator:
        """Returns all header cells in the grid."""
        return self.page.locator("table.chakra-table thead th")

    @property
    def table_rows(self) -> Locator:
        """Returns all data rows in table body."""
        return self.page.locator("table.chakra-table tbody tr")

    @property
    def empty_state_message(self) -> Locator:
        """Returns empty data / no records indicator text."""
        return self.page.locator("p:has-text('No data available'), p:has-text('No records found')").first

    @property
    def page_size_select(self) -> Locator:
        """Returns the page size dropdown element (20, 50, 100, 200)."""
        return self.page.locator("select.chakra-select").first

    # ──────────────────────────────────────────────────────────────────────────
    # MODAL LOCATOR PROPERTIES
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def modal(self) -> Locator:
        """Returns the active Attendance Setting modal / slide container."""
        return self.page.locator(".chakra-modal__content").filter(
            has=self.page.locator(".chakra-modal__header, header")
        ).last

    @property
    def modal_header(self) -> Locator:
        """Returns modal header element."""
        return self.modal.locator(".chakra-modal__header, header").first

    @property
    def modal_close_button(self) -> Locator:
        """Returns modal close 'X' button."""
        return self.modal.locator("button.chakra-modal__close-btn, button[aria-label='Close']").first

    @property
    def company_dropdown_button(self) -> Locator:
        """Returns the Company select menu button inside the modal."""
        return self.modal.locator("div.chakra-form-control:has(> label:has-text('Company')), div:has(> label:has-text('Company'))").locator("button.chakra-menu__menu-button").first

    @property
    def branch_dropdown_button(self) -> Locator:
        """Returns the Branch select menu button inside the modal."""
        return self.modal.locator("div.chakra-form-control:has(> label:has-text('Branch')), div:has(> label:has-text('Branch'))").locator("button.chakra-menu__menu-button").first

    @property
    def department_dropdown_button(self) -> Locator:
        """Returns the Department select menu button inside the modal."""
        return self.modal.locator("div.chakra-form-control:has(> label:has-text('Department')), div:has(> label:has-text('Department'))").locator("button.chakra-menu__menu-button").first

    @property
    def late_minute_input(self) -> Locator:
        """Returns Late Grace (Minutes) input."""
        return self.modal.locator("input[name='lateGraceMinutes'], input[name='lateMinute'], input[placeholder*='15']").first

    @property
    def grace_hour_input(self) -> Locator:
        """Returns Grace Hour (After Shift End) input."""
        return self.modal.locator("input[name='graceHourAfterShiftEnd'], input[name='graceHour'], input[placeholder*='0.5']").first

    @property
    def total_working_hour_input(self) -> Locator:
        """Returns Total Working Hour input."""
        return self.modal.locator("input[name='totalWorkingHours'], input[name='totalWorkingHour'], input[placeholder*='8']").first

    @property
    def half_day_time_input(self) -> Locator:
        """Returns Half Day Time (Hours) input."""
        return self.modal.locator("input[name='halfDayTimeHours'], input[name='halfDayTime'], input[placeholder*='4']").first

    @property
    def short_leave_from_input(self) -> Locator:
        """Returns Short Leave Duration From input."""
        return self.modal.locator("input[name='shortLeaveFromHours'], input[name='shortLeaveFrom'], input[placeholder*='From' i]").first

    @property
    def short_leave_to_input(self) -> Locator:
        """Returns Short Leave Duration To input."""
        return self.modal.locator("input[name='shortLeaveToHours'], input[name='shortLeaveTo'], input[placeholder*='To' i]").first

    @property
    def short_leave_count_for_half_day_input(self) -> Locator:
        """Returns Short Leaves Count For Half Day input."""
        return self.modal.locator("input[name='shortLeaveCountForHalfDay'], input[placeholder*='2']").first

    @property
    def modal_save_button(self) -> Locator:
        """Returns modal Save or Update button."""
        return self.modal.locator(
            "footer button[type='submit'], footer button:has-text('Save'), footer button:has-text('Update')"
        ).first

    @property
    def modal_cancel_button(self) -> Locator:
        """Returns modal Cancel button."""
        return self.modal.locator("footer button:has-text('Cancel')").first

    # ──────────────────────────────────────────────────────────────────────────
    # UI ACTIONS
    # ──────────────────────────────────────────────────────────────────────────

    def navigate_to_attendance_master(self):
        """Navigates directly to the Attendance Setting master page and waits for DOM load."""
        target_url = f"{settings.BASE_URL}{self.PAGE_ROUTE}"
        logger.info(f"Navigating to Attendance Master: {target_url}")
        try:
            self.page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(target_url, timeout=45000, wait_until="commit")
        self.heading.wait_for(state="visible", timeout=25000)

    def click_add_attendance_setting(self) -> Locator:
        """Clicks 'Add Attendance Setting' button and waits for modal to appear."""
        logger.info("Opening 'Add Attendance Setting' modal...")
        btn = self.add_attendance_setting_button
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.modal.wait_for(state="visible", timeout=10000)
        logger.info("Add Attendance Setting modal opened successfully.")
        return self.modal

    def close_add_modal(self):
        """Closes Add Attendance Setting modal safely."""
        logger.info("Closing Add Attendance Setting modal...")
        close_btn = self.modal_close_button
        if close_btn.is_visible(timeout=1000):
            close_btn.click(force=True)
        elif self.modal_cancel_button.is_visible(timeout=1000):
            self.modal_cancel_button.click(force=True)
        else:
            self.page.keyboard.press("Escape")
        self.modal.wait_for(state="hidden", timeout=5000)

    def select_chakra_menu_options(self, trigger_btn: Locator, options: Any):
        """
        Interacts with Chakra multiselect dropdown:
        - Options can be a single string or list of strings.
        - Uses aria-controls attribute to precisely target the dropdown menu.
        - Clicks trigger button to expand menu list.
        - Checks matching items without closing prematurely.
        - Unfocuses menu safely without dismissing the modal.
        """
        if isinstance(options, str):
            options = [options]

        logger.info(f"Selecting multiselect option(s) {options} from dropdown...")
        trigger_btn.wait_for(state="visible", timeout=10000)
        try:
            self.page.wait_for_function(
                "btn => !btn.hasAttribute('disabled') && !btn.disabled",
                arg=trigger_btn.element_handle(),
                timeout=8000
            )
        except Exception:
            pass
        self.page.wait_for_timeout(300)

        controls_id = trigger_btn.get_attribute("aria-controls")
        if controls_id:
            menu_list = self.page.locator(f'[id="{controls_id}"]')
        else:
            menu_list = self.page.locator("div.chakra-menu__menu-list[role='menu']").last

        if trigger_btn.get_attribute("aria-expanded") != "true":
            trigger_btn.click()
            self.page.wait_for_timeout(400)

        if not menu_list.is_visible(timeout=1000):
            trigger_btn.click(force=True)
            self.page.wait_for_timeout(400)

        if not menu_list.is_visible(timeout=1000):
            menu_list = self.page.locator("div.chakra-menu__menu-list[role='menu']:visible, [role='menu']:visible").last

        menu_list.wait_for(state="visible", timeout=5000)

        for opt in options:
            search_box = menu_list.locator("input[placeholder*='Search' i]").first
            if search_box.is_visible(timeout=500):
                search_box.fill(str(opt))
                self.page.wait_for_timeout(300)

            item = menu_list.locator(
                f"button[role='menuitem']:has-text('{opt}'), label.chakra-checkbox:has-text('{opt}')"
            ).first
            item.wait_for(state="visible", timeout=5000)

            is_checked = (
                item.locator("label.chakra-checkbox[data-checked]").count() > 0 or
                item.locator("input[type='checkbox']:checked").count() > 0 or
                item.locator("[aria-checked='true']").count() > 0
            )

            if not is_checked:
                item.click()
                self.page.wait_for_timeout(200)

        # Unfocus/close menu safely by clicking modal header
        try:
            if menu_list.is_visible(timeout=300):
                self.modal_header.click(force=True)
                self.page.wait_for_timeout(300)
        except Exception:
            pass

    def select_company(self, company_names: Any):
        """Selects one or more Companies and ensures Branch dropdown transitions out of disabled state."""
        self.select_chakra_menu_options(self.company_dropdown_button, company_names)
        # Wait for Branch dropdown to become enabled
        try:
            self.page.wait_for_function(
                "btn => !btn.hasAttribute('disabled') && !btn.disabled",
                arg=self.branch_dropdown_button.element_handle(),
                timeout=5000
            )
        except Exception:
            pass

    def select_branch(self, branch_names: Any):
        """Selects one or more Branches after Company has been selected."""
        self.select_chakra_menu_options(self.branch_dropdown_button, branch_names)
        # Wait for Department dropdown to become enabled
        try:
            self.page.wait_for_function(
                "btn => !btn.hasAttribute('disabled') && !btn.disabled",
                arg=self.department_dropdown_button.element_handle(),
                timeout=5000
            )
        except Exception:
            pass

    def select_department(self, department_names: Any):
        """Selects one or more Departments."""
        self.select_chakra_menu_options(self.department_dropdown_button, department_names)

    def configure_attendance_rules(
        self,
        late_minute: Optional[Any] = None,
        grace_hour: Optional[Any] = None,
        total_working_hour: Optional[Any] = None,
        half_day_time: Optional[Any] = None,
        short_leave_from: Optional[Any] = None,
        short_leave_to: Optional[Any] = None,
        short_leave_count_for_half_day: Optional[Any] = None,
    ):
        """Configures all numeric attendance rules."""
        if late_minute is not None:
            self.late_minute_input.fill(str(late_minute))
        if grace_hour is not None:
            self.grace_hour_input.fill(str(grace_hour))
        if total_working_hour is not None:
            self.total_working_hour_input.fill(str(total_working_hour))
        if half_day_time is not None:
            self.half_day_time_input.fill(str(half_day_time))
        if short_leave_from is not None:
            self.short_leave_from_input.fill(str(short_leave_from))
        if short_leave_to is not None:
            self.short_leave_to_input.fill(str(short_leave_to))
        if short_leave_count_for_half_day is not None:
            self.short_leave_count_for_half_day_input.fill(str(short_leave_count_for_half_day))

    def fill_attendance_setting_form(self, data: Dict[str, Any]):
        """Fills complete Attendance Setting form with provided configuration dictionary."""
        logger.info(f"Filling Attendance Setting form with data: {data}")

        if "company" in data:
            self.select_company(data["company"])

        if "branch" in data:
            self.select_branch(data["branch"])

        if "department" in data:
            self.select_department(data["department"])

        self.configure_attendance_rules(
            late_minute=data.get("late_minute") or data.get("lateMinute"),
            grace_hour=data.get("grace_hour") or data.get("graceHour"),
            total_working_hour=data.get("total_working_hour") or data.get("totalWorkingHour"),
            half_day_time=data.get("half_day_time") or data.get("halfDayTime"),
            short_leave_from=data.get("short_leave_from") or data.get("shortLeaveFrom"),
            short_leave_to=data.get("short_leave_to") or data.get("shortLeaveTo"),
            short_leave_count_for_half_day=data.get("short_leave_count_for_half_day") or data.get("shortLeaveCountForHalfDay"),
        )

    def submit_attendance_setting_form(self) -> Optional[str]:
        """Clicks Save and waits for toast message or modal closure."""
        logger.info("Submitting Attendance Setting form...")
        self.modal_save_button.click()
        return self.wait_for_toast_message(timeout=5000)

    def get_validation_errors(self) -> List[str]:
        """Extracts field validation error messages or indicators inside the modal."""
        errors = []
        error_nodes = self.modal.locator(".chakra-form__error-message, [aria-invalid='true'], p[id*='error']").all()
        for node in error_nodes:
            txt = node.inner_text().strip()
            if txt and txt not in errors:
                errors.append(txt)
        return errors

    def get_form_field_label_sequence(self) -> List[str]:
        """
        Extracts visible form labels inside the active modal in their exact DOM sequence.
        Filters to rule labels or all form labels.
        """
        labels = self.modal.locator(".chakra-form__label, label").all()
        sequence = []
        for lbl in labels:
            txt = lbl.inner_text().strip()
            if txt and txt not in sequence:
                sequence.append(txt)
        return sequence

    def search(self, query: str):
        """Fills search query into the search input and waits for table refresh."""
        logger.info(f"Filtering attendance settings by: '{query}'")
        search_box = self.search_input
        search_box.wait_for(state="visible", timeout=10000)
        search_box.fill(query)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("domcontentloaded")

    def get_column_header_titles(self) -> List[str]:
        """Extracts visible text titles from all table columns."""
        headers = self.table_headers
        count = headers.count()
        titles = []
        for i in range(count):
            txt = headers.nth(i).inner_text().strip()
            clean_title = txt.split("\n")[0].strip()
            if clean_title:
                titles.append(clean_title)
        return titles

    def set_page_size(self, size: str = "50"):
        """Selects page size (20, 50, 100, 200) from the footer selector."""
        select = self.page_size_select
        select.wait_for(state="visible", timeout=10000)
        select.select_option(value=size)

    def get_form_values(self) -> Dict[str, Any]:
        """Reads current values of all fields inside the active modal."""
        return {
            "lateMinute": self.late_minute_input.input_value(),
            "graceHour": self.grace_hour_input.input_value(),
            "totalWorkingHour": self.total_working_hour_input.input_value(),
            "halfDayTime": self.half_day_time_input.input_value(),
            "shortLeaveFrom": self.short_leave_from_input.input_value(),
            "shortLeaveTo": self.short_leave_to_input.input_value(),
            "shortLeaveCountForHalfDay": self.short_leave_count_for_half_day_input.input_value(),
        }

    def click_edit_setting_by_index(self, row_index: int = 0) -> Locator:
        """Clicks edit action on a specific table row index and waits for update modal."""
        logger.info(f"Clicking edit on attendance setting at row index {row_index}...")
        row = self.table_rows.nth(row_index)
        row.wait_for(state="visible", timeout=10000)
        edit_btn = row.locator("button[aria-label*='edit' i], button:has(svg), td:last-child button").first
        edit_btn.wait_for(state="visible", timeout=5000)
        edit_btn.click()
        self.modal.wait_for(state="visible", timeout=10000)
        return self.modal

    def click_edit_setting_by_company(self, company_name: str) -> Locator:
        """Clicks edit action on a table row matching company name."""
        logger.info(f"Clicking edit on attendance setting for company '{company_name}'...")
        row = self.table.locator(f"tbody tr:has-text('{company_name}')").first
        row.wait_for(state="visible", timeout=10000)
        edit_btn = row.locator("button[aria-label*='edit' i], button:has(svg), td:last-child button").first
        edit_btn.wait_for(state="visible", timeout=5000)
        edit_btn.click()
        self.modal.wait_for(state="visible", timeout=10000)
        return self.modal

    def check_input_validity(self, input_locator: Locator) -> bool:
        """Checks HTML5 input validity for a given form element."""
        return input_locator.evaluate("el => el.checkValidity()")

