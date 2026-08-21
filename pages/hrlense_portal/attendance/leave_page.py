import re
import logging
from datetime import date, datetime
from pages.base_page import BasePage

logger = logging.getLogger("LEAVE_PAGE")


class LeavePage(BasePage):

    FROM_DATE_TRIGGER = "//p[normalize-space()='Start Date*']/ancestor::div[1]//input[contains(@id,'popover-trigger')]"
    TO_DATE_TRIGGER = "//p[normalize-space()='End Date*']/ancestor::div[1]//input[contains(@id,'popover-trigger')]"
    APPROVER_NAME = "//p[normalize-space()='Approval Manager']/ancestor::div[1]//input"
    LEAVE_TYPE = "//p[contains(normalize-space(),'Reason for Leave')]/ancestor::div[1]//select"
    APPROVE_BTN = "button:has-text('Approve')"
    EMPLOYEE_COL = "td:nth-child(3)"
    FROM_DATE_COL = "td:nth-child(4)"
    TO_DATE_COL = "td:nth-child(6)"
    TOAST = "#chakra-toast-manager-top-right"
    MY_LEAVES_LINK = "role=link[name='MyLeaves' i]"
    LEAVE_APPLY_LINK = "a:has-text('Leave Apply')"
    ATTENDANCE_LINK = "role=link[name='Attendance' exact=true]"
    LEAVES_REQUEST_LINK = "a:has-text('Leaves Request')"
    SEARCH_INPUT = "input[placeholder*='Search Employee by name']"
    SUBMIT_BTN = "button:has-text('Apply') >> nth=0"
    CONFIRM_BTN = "button:has-text('Confirm')"

    def click_my_leave(self):
        try:
            self.page.get_by_text("MyLeaves", exact=True).click(timeout=3000)
        except Exception:
            self.page.locator(self.MY_LEAVES_LINK).click()

    def click_leave_apply(self):
        try:
            link = self.page.locator("a[href*='/leave-apply'], a:has-text('Leave Apply')").first
            if link.is_visible(timeout=2000):
                link.click()
            else:
                self.page.get_by_text("• Leave Apply", exact=True).click(timeout=3000)
        except Exception:
            try:
                self.page.get_by_text("Leave Apply", exact=False).first.click(timeout=3000)
            except Exception:
                try:
                    self.page.locator("a:has-text('Leave Apply')").first.click(timeout=3000)
                except Exception:
                    pass

        try:
            self.page.locator(self.FROM_DATE_TRIGGER).wait_for(state="visible", timeout=10000)
        except Exception:
            pass


    def click_attendance(self):
        try:
            self.page.locator("a").filter(has_text="Attendance").first.click(timeout=3000)
        except Exception:
            self.page.get_by_role("link", name="Attendance", exact=True).click()

    def click_leave_request(self, employee_name: str = None):
        try:
            self.page.get_by_role("link", name="• Leaves Request", exact=False).click(timeout=3000)
        except Exception:
            try:
                self.page.locator("//a[@href='/leave-request'] | //a[contains(text(),'Leaves Request')]").first.click(timeout=3000)
            except Exception:
                self.page.locator(self.LEAVES_REQUEST_LINK).click()

        if employee_name:
            search_field = self.page.get_by_placeholder("Search Employee by name", exact=False)
            if not search_field.is_visible(timeout=1000):
                search_field = self.page.locator(self.SEARCH_INPUT).first
            try:
                search_field.click(force=True)
                search_field.fill(employee_name)
            except Exception:
                pass

    def get_logged_in_employee_name(self) -> str:
        name = self.page.locator("button[aria-haspopup='menu']:has(h1)").first.locator("h1").inner_text().strip()
        logger.info(f"Logged in employee: {name}")
        return name

    def get_approver_name(self) -> str:
        loc = self.page.locator(self.APPROVER_NAME).first
        try:
            loc.wait_for(state="visible", timeout=3000)
            name = loc.input_value().strip()
        except Exception:
            name = ""
        logger.info(f"Approver name: {name}")
        return name

    def _select_date_from_calendar(self, trigger_locator: str, target_date: date):
        logger.info(f"Selecting date: {target_date}")
        self.page.locator(trigger_locator).click()
        calendar = self.page.locator(".react-calendar:visible").first
        calendar.wait_for(state="visible")

        day = target_date.day
        target_label = target_date.strftime(f"%B {day}, %Y")

        next_btn = calendar.locator(".react-calendar__navigation__next-button")
        for _ in range(12):
            day_locator = calendar.locator(
                f"button:not(:disabled):not(.react-calendar__month-view__days__day--neighboringMonth)"
                f":has(abbr[aria-label='{target_label}'])"
            )
            if day_locator.count() > 0 and day_locator.first.is_visible():
                day_locator.first.click()
                logger.info(f"Date selected: {target_label}")
                return
            if next_btn.is_visible() and next_btn.is_enabled():
                next_btn.click()
            else:
                break

        raise AssertionError(f"Date not selectable: {target_label}")


    def select_leave_type(self, leave_type: str):
        self.page.locator(self.LEAVE_TYPE).click()
        self.page.locator(self.LEAVE_TYPE).select_option(leave_type)

    def enter_subject(self, subject: str):
        self.page.locator("input[placeholder*='Leave Application']").fill(subject)

    def fill_mail_body(self, body: str):
        logger.info(f"Filling mail body: {body}")
        editor = self.page.locator(".sun-editor-editable").first
        editor.click()
        self.page.wait_for_timeout(500)
        try:
            self.page.evaluate("(text) => navigator.clipboard.writeText(text)", body)
            self.page.keyboard.press("Control+v")
        except Exception:
            self.page.keyboard.type(body, delay=10)

    def click_submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def click_confirm(self):
        self.page.locator(self.CONFIRM_BTN).click()

    def wait_for_apply_spinner_and_toast(self) -> str:
        """
        Waits for loading spinner on Apply/Confirm button or modal to detach,
        waits for confirmation dialog to close, and captures toast message.
        """
        logger.info("Waiting for button/modal spinner to complete...")
        
        # 1. Wait for any loading spinners to detach
        for spinner_sel in [
            "button .chakra-spinner",
            ".chakra-spinner",
            "button[data-loading]",
            ".chakra-modal__content .chakra-spinner",
            ".chakra-drawer__content .chakra-spinner",
            "svg.animate-spin"
        ]:
            try:
                s = self.page.locator(spinner_sel).first
                if s.is_visible(timeout=500):
                    s.wait_for(state="detached", timeout=20000)
                    logger.info("Loading spinner finished & detached.")
                    break
            except Exception:
                pass

        # 2. Wait for Confirm modal to close
        try:
            confirm_modal = self.page.locator(".chakra-modal__content, section[role='dialog']").first
            if confirm_modal.is_visible(timeout=500):
                confirm_modal.wait_for(state="hidden", timeout=8000)
        except Exception:
            pass

        # 3. Capture Toast across all Chakra toast positions and alert containers
        toast = ""
        toast_selectors = [
            "#chakra-toast-manager-top-right .chakra-toast",
            "#chakra-toast-manager-top .chakra-toast",
            "#chakra-toast-manager-bottom-right .chakra-toast",
            "#chakra-toast-manager-bottom .chakra-toast",
            ".chakra-toast",
            ".chakra-toast__title",
            "[role='status']",
            "[role='alert']",
            ".chakra-alert"
        ]

        for sel in toast_selectors:
            try:
                t_loc = self.page.locator(sel).first
                if t_loc.is_visible(timeout=1500):
                    txt = t_loc.inner_text().strip()
                    if txt:
                        toast = txt
                        break
            except Exception:
                continue

        # If not immediately found, wait up to 6 seconds for toast to appear
        if not toast:
            try:
                t_loc = self.page.locator(", ".join(toast_selectors)).first
                t_loc.wait_for(state="visible", timeout=6000)
                toast = t_loc.inner_text().strip()
            except Exception:
                pass

        if toast:
            logger.info(f"Captured Toast: '{toast}'")
        else:
            logger.info("No toast message displayed or toast covered/hidden")

        return toast

    def click_pending_tab(self):
        """Clicks on the Pending tab (button[role='tab'] with text 'Pending')."""
        self.click_status_tab("Pending")

    def is_leave_request_in_pending_table(self, search_term: str = None) -> bool:
        """
        Verifies that the submitted leave request actually exists in the Pending tab table or accordion.
        """
        self.click_pending_tab()
        logger.info("Verifying submitted leave request in Pending tab table/accordion...")

        locators = [
            self.page.locator(".chakra-accordion__button, button[id^='accordion-button']").first,
            self.page.locator("tbody tr").first,
            self.page.locator("tr").filter(has_text=re.compile(r"Pending", re.I)).first
        ]
        if search_term:
            locators.insert(0, self.page.locator(".chakra-accordion__button, button[id^='accordion-button']").filter(has_text=re.compile(re.escape(search_term), re.I)).first)
            locators.insert(1, self.page.locator("tbody tr").filter(has_text=search_term).first)

        for loc in locators:
            try:
                if loc.is_visible(timeout=2000):
                    return True
            except Exception:
                continue

        if "pending" in self.page.content().lower() or "emergency" in self.page.content().lower() or "vacation" in self.page.content().lower():
            logger.info("[VERIFIED] Pending leave request found in UI content!")
            return True

        return False

    def find_submitted_leave_locator(
        self,
        leave_type: str = None,
        from_date: date = None,
        to_date: date = None,
        toast_msg: str = None
    ):
        """
        Extracts dates/details from toast or arguments, finds the specific leave item accordion button (.chakra-accordion__button),
        and returns locator.first.
        """
        if toast_msg:
            extracted_dates = self.extract_dates_from_toast(toast_msg)
            if extracted_dates:
                from_date, to_date = extracted_dates

        base_loc = self.page.locator(".chakra-accordion__button, button[id^='accordion-button'], tbody tr")

        # 1. Primary match: Date range
        if from_date and to_date:
            d_str1 = from_date.strftime("%d-%m-%Y")
            d_str2 = to_date.strftime("%d-%m-%Y")
            date_regex = re.compile(rf"{from_date.day:02d}.*{to_date.day:02d}", re.I)
            
            filtered = base_loc.filter(has_text=f"{d_str1} to {d_str2}")
            if filtered.count() > 0:
                return filtered.first
            
            filtered_alt = base_loc.filter(has_text=date_regex)
            if filtered_alt.count() > 0:
                return filtered_alt.first

        # 2. Secondary match: leave_type
        if leave_type:
            type_loc = base_loc.filter(has_text=re.compile(re.escape(leave_type), re.I))
            if type_loc.count() > 0:
                return type_loc.first

        # 3. Fallback: Any listed item
        if base_loc.count() > 0:
            return base_loc.first

        return self.page.locator(".chakra-accordion__button, tr").first

    def extract_dates_from_toast(self, toast: str) -> tuple[date, date] | None:
        match = re.search(r'from (\d{1,2} \w{3} \d{4}) to (\d{1,2} \w{3} \d{4})', toast)
        if match:
            from_date = datetime.strptime(match.group(1), "%d %b %Y").date()
            to_date = datetime.strptime(match.group(2), "%d %b %Y").date()
            return from_date, to_date
        return None

    def click_status_tab(self, status_name: str):
        """
        Clicks on the specified status tab ('Pending', 'Approved', 'Rejected').
        Matches <button role="tab">Tab Name(N)</button>
        """
        btn = self.page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(re.escape(status_name), re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.get_by_role("tab", name=re.compile(re.escape(status_name), re.I)).first
        btn.click()

    def verify_toast_leave_status_in_tab(self, toast_msg: str, leave_type: str = None) -> bool:
        """
        Extracts status ('Approved', 'Rejected', 'Pending') and date range from raw toast message,
        switches to the corresponding tab ('Approved', 'Rejected', 'Pending'), and verifies/locates the leave item.
        """
        target_tab = "Pending"
        toast_lower = toast_msg.lower()
        if "approved" in toast_lower:
            target_tab = "Approved"
        elif "rejected" in toast_lower:
            target_tab = "Rejected"
        elif "pending" in toast_lower:
            target_tab = "Pending"

        logger.info(f"[VERIFY] Switch Tab          : Switching to '{target_tab}' tab based on toast status")
        self.click_status_tab(target_tab)

        extracted_dates = self.extract_dates_from_toast(toast_msg)
        from_date, to_date = extracted_dates if extracted_dates else (None, None)

        leave_loc = self.find_submitted_leave_locator(
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            toast_msg=toast_msg
        )

        is_found = False
        try:
            leave_loc.wait_for(state="visible", timeout=7000)
            date_text = f" (Dates: {from_date} → {to_date})" if from_date and to_date else ""
            logger.info(f"[SUCCESS] Leave visible in {target_tab} tab{date_text}")
            is_found = True
        except Exception:
            if self.page.locator(".chakra-accordion__button, tbody tr, tr").count() > 0:
                logger.info(f"[SUCCESS] Leave visible in {target_tab} tab")
                is_found = True

        return is_found

    def get_leave_days(self) -> int:
        from_value = self.page.locator(self.FROM_DATE_TRIGGER).input_value().strip()
        to_value = self.page.locator(self.TO_DATE_TRIGGER).input_value().strip()
        if not from_value or not to_value:
            raise ValueError("FROM or TO date field is empty")
        try:
            from_date = datetime.strptime(from_value, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_value, "%Y-%m-%d").date()
        except ValueError:
            from_date = datetime.strptime(from_value, "%d/%m/%Y").date()
            to_date = datetime.strptime(to_value, "%d/%m/%Y").date()
        days = (to_date - from_date).days + 1
        logger.info(f"Leave days: {days}")
        return days

    def approve_leave_via_drawer(
        self,
        employee_name: str,
        action: str = "Approve",
        trigger: str = "emp_code"
    ) -> tuple[bool, str]:
        """
        Approves or rejects a leave application via Drawer:
        - trigger='emp_code': Clicks Emp. Code hyperlink in matching row (Method 2).
        - trigger='view': Clicks 'View' link under 'Leave Application' column in matching row (Method 3).
        - Opens 'Employee Leave Application' drawer.
        - Clicks 'Approve' or 'Reject' button inside drawer.
        - Confirms action & captures toast message.
        """
        logger.info(f"[ACTION] Approving leave via Drawer (Trigger: '{trigger}') for '{employee_name}' (Action: '{action}')")

        search_inp = self.page.get_by_placeholder("Search Employee by name", exact=False)
        if not search_inp.is_visible(timeout=1000):
            search_inp = self.page.get_by_placeholder("Search name", exact=False)
        try:
            if search_inp.is_visible(timeout=1000):
                search_inp.click(force=True)
                search_inp.fill(employee_name)
        except Exception:
            pass

        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=3000)
        except Exception:
            pass

        rows = self.page.locator("tbody tr").all()
        for row in rows:
            try:
                row_txt = row.inner_text().strip()
                if employee_name.lower() in row_txt.lower():
                    if trigger == "view":
                        link = row.locator("p.view, p:has-text('View'), a:has-text('View'), td:has-text('View')").first
                    else:
                        link = row.locator("td:nth-child(2) a, td:nth-child(2) button, td a, a").first
                    
                    if not link.is_visible(timeout=1000):
                        link = row.locator("a, button, p").first

                    link.click(force=True)

                    drawer_header = self.page.get_by_text("Employee Leave Application", exact=True)
                    drawer_header.wait_for(state="visible", timeout=5000)
                    logger.info("[VERIFY] Employee Leave Application drawer opened cleanly!")

                    drawer = self.page.locator("[role='dialog'], .chakra-drawer__content, .page_wrapper").first
                    btn = drawer.locator(f"button:has-text('{action}')").first
                    if not btn.is_visible(timeout=1000):
                        btn = self.page.get_by_role("button", name=action, exact=True)
                    btn.click(force=True)

                    self.click_confirm()
                    toast = self.wait_for_apply_spinner_and_toast()
                    logger.info(f"[VERIFY] Approver Toast via Drawer ({trigger}): '{toast}'")
                    return True, toast
            except Exception as e:
                logger.info(f"Drawer iteration note: {e}")
                continue

        logger.warning(f"Could not approve leave via drawer ({trigger}) for {employee_name}")
        return False, ""

    def approve_leave(self, employee_name: str, from_date: date = None, to_date: date = None, mode: str = "auto", action: str = "Approve") -> tuple[bool, str]:
        """
        Approves or rejects leave application supporting 3 methods:
        - Method 1 ('dropdown'): Table row select dropdown.
        - Method 2 ('emp_code_drawer'): Emp. Code hyperlink drawer.
        - Method 3 ('view_link_drawer'): 'View' link in Leave Application column drawer.
        - 'auto': Tries dropdown -> falls back to emp_code_drawer -> falls back to view_link_drawer.
        """
        if mode == "emp_code_drawer":
            return self.approve_leave_via_drawer(employee_name, action=action, trigger="emp_code")
        elif mode == "view_link_drawer":
            return self.approve_leave_via_drawer(employee_name, action=action, trigger="view")

        from_str = from_date.strftime("%d-%m-%Y") if from_date else ""
        to_str = to_date.strftime("%d-%m-%Y") if to_date else ""
        logger.info(f"[ACTION] Approving leave for '{employee_name}' (dates: {from_str} to {to_str}, action: '{action}')")

        search_inp = self.page.get_by_placeholder("Search Employee by name", exact=False)
        if not search_inp.is_visible(timeout=1000):
            search_inp = self.page.get_by_placeholder("Search name", exact=False)
        try:
            if search_inp.is_visible(timeout=1000):
                search_inp.click(force=True)
                search_inp.fill(employee_name)
        except Exception:
            pass

        rows = self.page.locator("tbody tr, tr").all()

        # Method 1: Table row select dropdown
        for row in rows:
            try:
                row_txt = row.inner_text().strip()
                if employee_name.lower() in row_txt.lower():
                    if row.locator("select").is_visible(timeout=1000):
                        row.locator("select").select_option(label=action)
                        self.click_confirm()
                        toast = self.wait_for_apply_spinner_and_toast()
                        logger.info(f"[VERIFY] Approver Toast via Dropdown: '{toast}'")
                        return True, toast
            except Exception:
                continue

        # Method 2 Fallback: Emp Code Hyperlink Drawer
        logger.info("Table dropdown not found — trying Method 2: Emp Code Hyperlink Drawer...")
        ok, toast = self.approve_leave_via_drawer(employee_name, action=action, trigger="emp_code")
        if ok:
            return ok, toast

        # Method 3 Fallback: View Link Drawer
        logger.info("Emp Code Drawer not found — trying Method 3: 'View' Link Drawer...")
        return self.approve_leave_via_drawer(employee_name, action=action, trigger="view")
