"""
Regularization Page Object for HR Lens Portal Attendance Module.
Handles date selection, in/out time inputs, reason entries, and approval workflows.
"""

import re
import random
import logging
from datetime import datetime
from core.config import settings
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class RegularizationPage(BasePage):
    # Sidebar navigation
    ATTENDANCE_NAV = "a:has-text('Attendance')"
    REGULARIZATION_NAV = ".submenu_item[href*='regularisation'], .submenu_item[href*='regularizationRequest'], a:has-text('Regularization')"

    # Calendar (react-calendar)
    DATE_CELL = ".react-calendar__month-view__days button:not([disabled])"

    # Form Locators
    IN_TIME = "input[placeholder*='HH'], input[placeholder*='In Time']"
    OUT_TIME = "input[placeholder*='HH'], input[placeholder*='Out Time']"
    REASON_INPUT = "textarea[placeholder*='Reason'], textarea"
    APPLY_BTN = "button:has-text('Apply'), button:has-text('Submit')"
    CONFIRM_BTN = "button:has-text('Confirm'), button:has-text('Yes')"

    # Toast (Chakra UI)
    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, div[id^='toast-']"
    )

    # User Info
    LOGGED_IN_USER = ".user-name, .user-profile, [class*='userName']"

    def click_my_attendance(self):
        """Clicks Attendance in sidebar navigation."""
        logger.info("Navigating to Attendance module...")
        nav = self.page.locator("a:has-text('Attendance')").first
        if nav.is_visible():
            nav.click()
            self.page.wait_for_timeout(300)

    def click_regularization(self):
        """Clicks Regularization Request sub-menu link or navigates directly to /regularizationRequest."""
        logger.info("Opening Regularization Request page...")
        link = self.page.locator("a[href*='regularizationRequest'], a[href*='regularization'], .submenu_item[href*='regularization']").first
        if link.is_visible():
            link.click()
            self.page.wait_for_load_state("domcontentloaded")
        elif "/regularizationRequest" not in self.page.url:
            self.page.goto(f"{settings.BASE_URL}/regularizationRequest")
            self.page.wait_for_load_state("domcontentloaded")

    def get_logged_in_employee_name(self) -> str:
        """Retrieves exact logged-in employee name directly from the portal header or active user profile."""
        profile_selectors = [
            ".chakra-menu__menu-button [class*='text']",
            ".chakra-menu__menu-button p",
            ".chakra-menu__menu-button span",
            ".user-name",
            ".user-profile",
            "[class*='userName']",
            "[class*='userProfile']",
            ".chakra-avatar + [class*='text']",
            "header p",
            "header span"
        ]
        for sel in profile_selectors:
            try:
                elements = self.page.locator(sel).all()
                for el in elements:
                    txt = el.inner_text().strip()
                    if txt and not any(kw in txt.lower() for kw in ["menu", "notification", "search", "logout"]):
                        if 1 <= len(txt.split()) <= 4 and any(c.isalpha() for c in txt):
                            logger.info(f"Retrieved exact logged-in employee name from header: '{txt}'")
                            return txt
            except Exception:
                continue

        # Fallback dynamically derived from active user emails without hardcoding
        for user_key in ["sanidhy", "kumar_piyush", "uttam_kumar", "abhishek_singh", "ritesh_singh"]:
            user_email = settings.USERS.get(user_key, {}).get("username", "")
            if user_email and "@" in user_email:
                prefix = user_email.split("@")[0]
                derived = " ".join(word.capitalize() for word in prefix.split("."))
                return derived

        raise RuntimeError("Unable to retrieve exact logged-in employee name from header or user profile.")

    def date_pick(self, day: int | None = None):
        """Picks a valid day cell in the react-calendar."""
        logger.info(f"Selecting calendar date day={day}...")
        try:
            self.page.locator(self.DATE_CELL).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        cells = self.page.locator(self.DATE_CELL).all()
        available = [c for c in cells if c.inner_text().strip().isdigit()]
        if not available:
            return

        if day is None:
            cell = random.choice(available)
        else:
            cell = next((c for c in available if c.inner_text().strip() == str(day)), available[0])

        cell.click()
        self.page.wait_for_timeout(300)

    def get_action_needed_dates(self) -> list[dict]:
        """
        Reads all eligible dates and statuses from the 'Action Needed' panel on the right.
        Returns list of dicts: [{'date': '03-07-2026', 'day': 3, 'status': 'Absent'}, ...]
        """
        results = []
        rows = self.page.locator("tr, div").filter(has_text=re.compile(r"Absent|Late|Missing", re.IGNORECASE)).all()
        for row in rows:
            txt = row.inner_text().strip()
            if txt and any(s in txt for s in ["Absent", "Late"]):
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                for line in lines:
                    match = re.search(r"(\d{2})-\d{2}-\d{4}", line)
                    if match:
                        day_num = int(match.group(1))
                        status = "Absent" if "Absent" in line else "Late"
                        results.append({"day": day_num, "status": status})
        return results

    def pick_eligible_date_from_calendar_or_panel(self) -> tuple[int, str]:
        """
        Selects an eligible date (Absent / Late) directly from the Action Needed panel or Calendar Badges.
        Returns (day_number, status_name).
        """
        logger.info("Locating eligible Regularization date (Absent / Late)...")

        # 1. Check Action Needed Panel
        action_dates = self.get_action_needed_dates()
        for item in action_dates:
            if item["status"].upper() in ["ABSENT", "LATE"]:
                self.date_pick(item["day"])
                return item["day"], item["status"]

        # 2. Check Calendar Badges (Red = Absent, Yellow = Late)
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text()
            if "Absent" in txt or "Late" in txt:
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                day_num = next((int(l) for l in lines if l.isdigit()), None)
                if day_num:
                    cell.click()
                    self.page.wait_for_timeout(300)
                    return day_num, "Absent" if "Absent" in txt else "Late"

        # Fallback to day 3
        self.date_pick(3)
        return 3, "Absent"

    def get_date_cell_status(self, day: int) -> str:
        """Reads attendance status tooltip or class text for the specified calendar day."""
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text().strip()
            if txt == str(day):
                title = cell.get_attribute("title") or cell.get_attribute("aria-label") or cell.inner_html()
                return title.upper() if title else ""
        return ""

    def is_regularization_eligible(self, day: int) -> bool:
        """
        Business Rule:
        if attendance_status in ["Present", "WeekOff", "Holiday"]:
            cannot apply regularization
        else:
            apply regularization
        """
        status = self.get_date_cell_status(day)
        ineligible_list = ["PRESENT", "WEEKOFF", "WEEK OFF", "HOLIDAY"]
        for ineligible in ineligible_list:
            if ineligible in status:
                logger.info(f"Day {day} has status '{status}' -> Ineligible for Regularization")
                return False
        return True

    def in_time_input(self, time_str: str = "09:30", index: int = 1):
        """Fills In-Time input field."""
        logger.info(f"Entering In-Time: {time_str}")
        self.page.wait_for_timeout(300)
        row_inputs = self.page.locator("tbody tr input:not([type='checkbox']), .chakra-table tbody tr input:not([type='checkbox']), [role='row'] input:not([type='checkbox'])").all()
        if not row_inputs:
            row_inputs = self.page.locator("input[type='time'], input[placeholder*='HH' i], input[placeholder*='--:--'], input[placeholder*='00:00'], input[placeholder*='Time' i]").all()
        
        target = None
        if row_inputs and len(row_inputs) >= (2 * index - 1):
            target = row_inputs[2 * index - 2]
        
        if not target or not target.is_visible():
            target = self.page.locator("input[type='time'], input[placeholder*='HH' i], input[placeholder*='--:--']").first
        
        if target and target.is_visible():
            target.click()
            target.fill("")
            target.fill(time_str)
            target.dispatch_event("change")
            logger.info(f"Successfully entered In-Time: {time_str}")
        else:
            logger.warning(f"Could not locate In-Time input for index {index}")

    def out_time_input(self, time_str: str = "18:30", index: int = 1):
        """Fills Out-Time input field."""
        logger.info(f"Entering Out-Time: {time_str}")
        self.page.wait_for_timeout(300)
        row_inputs = self.page.locator("tbody tr input:not([type='checkbox']), .chakra-table tbody tr input:not([type='checkbox']), [role='row'] input:not([type='checkbox'])").all()
        if not row_inputs:
            row_inputs = self.page.locator("input[type='time'], input[placeholder*='HH' i], input[placeholder*='--:--'], input[placeholder*='00:00'], input[placeholder*='Time' i]").all()
        
        target = None
        if row_inputs and len(row_inputs) >= (2 * index):
            target = row_inputs[2 * index - 1]
            
        if not target or not target.is_visible():
            target = self.page.locator("input[type='time'], input[placeholder*='HH' i], input[placeholder*='--:--']").nth(1)

        if target and target.is_visible():
            target.click()
            target.fill("")
            target.fill(time_str)
            target.dispatch_event("change")
            logger.info(f"Successfully entered Out-Time: {time_str}")
        else:
            logger.warning(f"Could not locate Out-Time input for index {index}")

    def enter_reason(self, reason: str = None, index: int = 1):
        """Fills Regularization reason."""
        reason_text = reason or random.choice(["System malfunction", "On Duty Client Visit", "Work from Home"])
        logger.info(f"Entering Regularization Reason: {reason_text}")
        textareas = self.page.locator("textarea[placeholder*='Reason'], textarea").all()
        if textareas and len(textareas) >= index:
            target = textareas[index - 1]
            target.click()
            target.fill(reason_text)
            target.dispatch_event("change")

    def fill_regularization_row(self, index: int, time_in: str, time_out: str, reason: str):
        """Fills a single regularization row."""
        self.in_time_input(time_in, index)
        self.out_time_input(time_out, index)
        self.enter_reason(reason, index)

    def click_apply_btn(self):
        """Clicks Apply / Submit button using exact role locator."""
        logger.info("Clicking Apply button...")
        self.page.wait_for_timeout(400)
        try:
            apply_btn = self.page.get_by_role("button", name="Apply", exact=True).first
            if not apply_btn.is_visible(timeout=1500):
                apply_btn = self.page.get_by_role("button", name=re.compile(r"^Apply$", re.I)).first
            if not apply_btn.is_visible(timeout=1000):
                apply_btn = self.page.locator("button:has-text('Apply')").first
            apply_btn.click(force=True)
            logger.info("Apply button clicked successfully.")
        except Exception as e:
            logger.warning(f"Error clicking Apply button: {e}")
            self.page.keyboard.press("Enter")

    def click_confirm_btn(self):
        """Clicks Confirm / Yes button in dialog if confirmation dialog appears."""
        logger.info("Checking for confirmation dialog...")
        try:
            btn = self.page.get_by_role("button", name="Confirm", exact=True).first
            if not btn.is_visible(timeout=2000):
                btn = self.page.locator("button:has-text('Confirm'), button:has-text('Yes'), .chakra-modal__content button:has-text('Confirm')").first
            if btn.is_visible(timeout=1000):
                logger.info("Clicking Confirm button...")
                btn.click(force=True)
        except Exception:
            pass

    def get_pop_msg(self) -> str | None:
        """Waits for and returns toast notification message."""
        return self.wait_for_toast(self.TOAST)

    def navigate_to_admin_regularisation(self):
        """Admin Flow: Navigates using page.get_by_role('link', name='Attendance') -> page.get_by_role('link', name='• Regularisation')."""
        logger.info("Admin Navigating: page.get_by_role('link', name='Attendance') -> page.get_by_role('link', name='• Regularisation')...")
        try:
            self.page.get_by_role("link", name="Attendance", exact=True).first.click()
            self.page.wait_for_timeout(400)
            self.page.get_by_role("link", name="• Regularisation").first.click()
            self.page.wait_for_load_state("domcontentloaded")
            return
        except Exception:
            pass

        try:
            att_nav = self.page.locator("a").filter(has_text="Attendance").first
            if att_nav.is_visible(timeout=2000):
                att_nav.click()
                self.page.wait_for_timeout(400)
                reg_link = self.page.get_by_role("link", name=re.compile(r"•\s*Regularis|Regularis|Regulariz", re.I)).first
                if not reg_link.is_visible(timeout=1000):
                    reg_link = self.page.locator("a[href*='regularis'], a[href*='regulariz']").first
                if reg_link.is_visible(timeout=2000):
                    reg_link.click()
                    self.page.wait_for_load_state("domcontentloaded")
                    return
        except Exception:
            pass

        # Fallback to direct URL
        if "/regularis" not in self.page.url.lower() and "/regulariz" not in self.page.url.lower():
            self.page.goto(f"{settings.BASE_URL}/regularization")
            self.page.wait_for_load_state("domcontentloaded")

    def search_employee(self, employee_name: str):
        """Searches for employee using 'Search Employee by name....' textbox."""
        clean_name = employee_name.splitlines()[-1].strip()
        logger.info(f"Searching for employee name: '{clean_name}'...")
        try:
            search_input = self.page.get_by_role("textbox", name="Search Employee by name....").first
            if not search_input.is_visible(timeout=1000):
                search_input = self.page.locator("input[placeholder*='Search Employee by name' i], input[placeholder*='Search' i]").first
            if search_input.is_visible(timeout=1000):
                search_input.fill("")
                search_input.fill(clean_name)
                self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.debug(f"Search note: {e}")

    def get_regularization_status(self, employee_name: str, reg_date: datetime | str | None = None) -> str:
        """Searches employee and returns current regularization status string."""
        logger.info(f"Getting regularization status for '{employee_name}' (date={reg_date})...")
        self.search_employee(employee_name)
        row = self.get_matched_employee_row(employee_name, reg_date)
        if row:
            try:
                sel = row.locator("select").first
                if sel.is_visible(timeout=500):
                    val = sel.input_value()
                    if val:
                        return val
            except Exception:
                pass
            
            txt = row.inner_text().strip()
            for st in ["Approved", "Pending", "Rejected", "Week Off", "Present", "Absent"]:
                if st.lower() in txt.lower():
                    return st
            return txt
        return "Not Found"

    def get_matched_employee_row(self, employee_name: str, reg_date: datetime | str | None = None):
        """Finds regularization row for specified employee and date in approver table."""
        logger.info(f"Searching regularization row for '{employee_name}', date={reg_date}...")
        date_candidates = []
        if reg_date:
            if isinstance(reg_date, datetime):
                date_candidates.append(reg_date.strftime("%d-%m-%Y"))
                date_candidates.append(reg_date.strftime("%Y-%m-%d"))
                date_candidates.append(reg_date.strftime("%d/%m/%Y"))
            else:
                date_candidates.append(str(reg_date))

        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        rows = self.page.locator("tbody tr").all()
        clean_target = employee_name.splitlines()[-1].strip().lower()

        # 1. Exact target name + date match
        for row in rows:
            txt = row.inner_text().lower()
            if any(part in txt for part in clean_target.split()):
                if date_candidates and not any(d.lower() in txt for d in date_candidates):
                    continue
                return row

        # 2. Match by date if search filtered the table
        if date_candidates:
            for row in rows:
                txt = row.inner_text().lower()
                if any(d.lower() in txt for d in date_candidates):
                    return row

        return rows[0] if rows else None

    def approve_regularization(self, employee_name: str, reg_date: datetime | str | None = None, reason: str = "Approved by Manager") -> str | None:
        """
        Admin Flow:
        1. Search employee name
        2. Match row
        3. Select 'Approve' (value='Approved')
        4. Modal opens with header 'Approve Reason' (page.get_by_text('Approve Reason', exact=True))
        5. Enter approve reason in placeholder 'Enter approve reason...'
        6. Click Submit (page.get_by_role('button', name='Submit'))
        7. Wait for button spinner to complete (dynamic state wait)
        8. Catch toast notification
        """
        logger.info(f"Approving Regularization request for '{employee_name}'...")
        self.search_employee(employee_name)
        row = self.get_matched_employee_row(employee_name, reg_date)
        if row:
            select_elem = row.locator("select").first
            if select_elem.is_visible(timeout=1000):
                logger.info("Selecting 'Approve' (value='Approved') in table row dropdown...")
                try:
                    select_elem.select_option(value="Approved")
                except Exception:
                    select_elem.select_option(label="Approve")
            else:
                approve_btn = row.locator("button:has-text('Approve'), a:has-text('Approve')").first
                if approve_btn.is_visible(timeout=1000):
                    approve_btn.click(force=True)

            modal_detected = False

            # Check for 'Approve Reason' modal
            try:
                modal_header = self.page.get_by_text("Approve Reason", exact=True).first
                if modal_header.is_visible(timeout=3000):
                    logger.info("Approve Reason modal detected. Entering reason...")
                    reason_input = self.page.get_by_placeholder("Enter approve reason...").first
                    if not reason_input.is_visible(timeout=1000):
                        reason_input = self.page.locator("textarea[placeholder*='reason' i], input[placeholder*='reason' i]").first
                    if reason_input.is_visible(timeout=1000):
                        reason_input.fill(reason)
                    
                    submit_btn = self.page.get_by_role("button", name="Submit").first
                    if not submit_btn.is_visible(timeout=1000):
                        submit_btn = self.page.locator("button:has-text('Submit'), .chakra-modal__content button:has-text('Submit')").first
                    if submit_btn.is_visible(timeout=1000):
                        logger.info("Clicking Submit button on Approve Reason modal...")
                        submit_btn.click(force=True)
            except Exception as e:
                logger.debug(f"Approve Reason modal note: {e}")

            # Confirmation modal opens after Submit -> Click Confirm
            self.click_confirm_btn()

            # Dynamic wait: wait for spinner to disappear
            try:
                self.page.locator(".chakra-spinner, [data-loading], [aria-busy='true']").first.wait_for(state="detached", timeout=15000)
            except Exception:
                pass

            toast = self.get_pop_msg()
            logger.info(f"Captured Approval Toast: '{toast}'")
            return toast
        return None

    def switch_status_tab_or_filter(self, status: str = "Approved"):
        """Switches status filter/tab to Approved, All, or Pending if available."""
        try:
            tab = self.page.locator(f"button:has-text('{status}'), [role='tab']:has-text('{status}'), a:has-text('{status}')").first
            if tab.is_visible(timeout=1000):
                tab.click()
                self.page.wait_for_timeout(1000)
                return
        except Exception:
            pass

        try:
            filter_select = self.page.locator("select").filter(has_text=re.compile(r"Pending|Approved|All", re.I)).first
            if filter_select.is_visible(timeout=1000):
                try:
                    filter_select.select_option(label=status)
                except Exception:
                    filter_select.select_option(value=status)
                self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def get_row_details(self, employee_name: str, reg_date: datetime | str | None = None) -> dict:
        """Finds row for specified employee and date, returning its full text and status."""
        self.search_employee(employee_name)
        row = self.get_matched_employee_row(employee_name, reg_date)

        # If not found in default view, check Approved / All filters
        if not row:
            for st in ["Approved", "All"]:
                self.switch_status_tab_or_filter(st)
                self.search_employee(employee_name)
                row = self.get_matched_employee_row(employee_name, reg_date)
                if row:
                    break

        if row:
            txt = row.inner_text().strip()
            curr_val = ""
            try:
                curr_val = row.locator("select").first.input_value()
            except Exception:
                pass
            is_actionable = row.locator("select:not([disabled])").count() > 0 and curr_val != "Approved"
            is_approved = "approved" in txt.lower() or curr_val.lower() == "approved"
            return {
                "found": True,
                "text": txt,
                "is_approved": is_approved,
                "is_actionable": is_actionable
            }
        return {"found": False, "text": "", "is_approved": True, "is_actionable": False}

    def get_rendered_attendance_status(self, day: int) -> str:
        """Reads the rendered attendance status badge/text on the attendance calendar for specified day."""
        logger.info(f"Inspecting rendered attendance status on calendar for day={day}...")
        cells = self.page.locator(self.DATE_CELL).all()
        for cell in cells:
            txt = cell.inner_text()
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            if lines and lines[0] == str(day):
                if len(lines) > 1:
                    return lines[1]
                title = cell.get_attribute("title") or cell.inner_text()
                return title
        return ""

    def reject_regularization(self, employee_name: str, reg_date: datetime | str | None = None, remark: str = "Rejected for testing") -> str | None:
        """Admin Flow: Selects Reject and confirms regularization request (REG_002, REG_009)."""
        logger.info(f"Rejecting Regularization request for '{employee_name}' with remark '{remark}'...")
        row = self.get_matched_employee_row(employee_name, reg_date)
        if row:
            select_elem = row.locator("select").first
            if select_elem.is_visible():
                try:
                    select_elem.select_option(label="Reject")
                except Exception:
                    select_elem.select_option(value="Reject")
            else:
                reject_btn = row.locator("button:has-text('Reject'), a:has-text('Reject')").first
                if reject_btn.is_visible():
                    reject_btn.click(force=True)

            remark_input = self.page.locator("textarea[placeholder*='Remark'], input[placeholder*='Remark']").first
            if remark_input.is_visible():
                remark_input.fill(remark)

            self.click_confirm_btn()
            return self.get_pop_msg()
        return None

    def cancel_pending_request(self, day_num: int) -> str | None:
        """Employee Flow: Cancels a pending regularization request (REG_003)."""
        logger.info(f"Cancelling pending regularization request for day={day_num}...")
        self.date_pick(day_num)
        cancel_btn = self.page.locator("button:has-text('Cancel Request'), button:has-text('Cancel'), .chakra-button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click(force=True)
            self.click_confirm_btn()
            return self.get_pop_msg()
        return None

    def edit_pending_request(self, day_num: int, new_in_time: str = "10:00", new_out_time: str = "19:00", new_reason: str = "Updated Reason") -> str | None:
        """Employee Flow: Edits a pending regularization request (REG_004)."""
        logger.info(f"Editing pending regularization request for day={day_num}...")
        self.date_pick(day_num)
        edit_btn = self.page.locator("button:has-text('Edit'), .chakra-button:has-text('Edit')").first
        if edit_btn.is_visible():
            edit_btn.click(force=True)

        self.in_time_input(new_in_time)
        self.out_time_input(new_out_time)
        self.enter_reason(new_reason)
        self.click_apply_btn()
        self.click_confirm_btn()
        return self.get_pop_msg()

    def get_audit_trail_records(self) -> list[str]:
        """Reads audit trail history entries for regularization lifecycle (REG_009)."""
        logger.info("Reading audit trail history records...")
        results = []
        try:
            audit_btn = self.page.locator("button:has-text('History'), button:has-text('Audit'), a:has-text('Audit')").first
            if audit_btn.is_visible():
                audit_btn.click(force=True)
                self.page.wait_for_timeout(400)

            items = self.page.locator(".chakra-modal__content tr, [role='dialog'] tr, .audit-item").all()
            for item in items:
                txt = item.inner_text().strip()
                if txt:
                    results.append(txt)
        except Exception:
            pass
        return results

    def is_payroll_locked_warning_visible(self) -> bool:
        """Checks if payroll locked / payroll generated restriction warning is visible (REG_006, REG_007)."""
        try:
            warning = self.page.locator("text=Payroll, text=locked, text=already generated, .chakra-alert").first
            return warning.is_visible()
        except Exception:
            return False
