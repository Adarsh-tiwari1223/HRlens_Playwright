"""
Director Page Object for HR Lens Portal Director Module.
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Encapsulates all Playwright UI locators recorded via Codegen.
"""

import re
from core.config import settings
from pages.base_page import BasePage
from utils.logger import log_debug


class DirectorPage(BasePage):
    # Sidebar & Navigation
    DIRECTORS_SIDEBAR_LINK = "role=link[name='Directors']"
    
    # Header actions & search
    ADD_DIRECTOR_BTN = "role=button[name='Add Director']"
    SEARCH_INPUT = "internal:placeholder='Search'"
    
    # Table Grid
    TABLE_ROWS = "tbody tr"
    
    # Modal Form Locators (Codegen exact)
    MODAL_DIALOG = ".chakra-modal__content, section.chakra-modal__content"
    DIRECTOR_SELECT_LABEL = "Director *"
    US_COMPANY_MENU_BTN = "role=button[name='Select US Company']"
    PAYROLL_COMPANY_MENU_BTN = "role=button[name='Select Payroll Company']"
    ADD_BTN = "role=button[name='Add']"
    UPDATE_BTN = "role=button[name='Update']"
    CANCEL_BTN = "role=button[name='Cancel']"
    
    # Toast notification
    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, [role='status']"
    )

    def navigate_to_directors(self):
        """Navigates to the Directors module page."""
        log_debug("Navigate", "Directors")
        if "/directors" not in self.page.url:
            self.page.get_by_role("link", name="Directors").click()
            self.page.wait_for_load_state("domcontentloaded")
            
        try:
            self.page.locator(self.TABLE_ROWS).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

    def click_add_director(self):
        """Clicks the Add Director button to open creation modal."""
        log_debug("Click", "Add Director")
        if self.is_modal_open():
            return

        add_btn = self.page.locator("button, a, [role='button']").filter(has_text=re.compile(r"Add Director", re.IGNORECASE)).first
        if not add_btn.is_visible():
            add_btn = self.page.get_by_text("Add Director", exact=False).first

        add_btn.click(force=True)
        self.page.wait_for_timeout(300)
        try:
            self.page.locator(self.MODAL_DIALOG).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

    def click_select_existing_tab(self):
        """Clicks 'Select Existing' tab in Add Director modal (Codegen exact)."""
        log_debug("Click", "Tab: Select Existing")
        self.page.get_by_role("tab", name="Select Existing").click()
        self.page.wait_for_timeout(200)

    def click_add_new_director_tab(self):
        """Clicks 'Add New Director' tab in Add Director modal (Codegen exact)."""
        log_debug("Click", "Tab: Add New Director")
        self.page.get_by_role("tab", name="Add New Director").click()
        self.page.wait_for_timeout(200)

    def fill_new_director_info(self, name: str, email: str, phone: str):
        """Fills Name, Email, and Phone Number in the 'Add New Director' tab (Codegen exact)."""
        log_debug("Fill", "New Director Info", value=f"{name} | {email} | {phone}")
        name_box = self.page.locator("div").filter(has_text=re.compile(r"^Director Name$")).get_by_role("textbox")
        if not name_box.is_visible():
            name_box = self.page.get_by_placeholder("Director Name")
        if not name_box.is_visible():
            name_box = self.page.locator(".chakra-modal__content input").first
        name_box.click()
        name_box.fill(name)

        email_box = self.page.locator("div").filter(has_text=re.compile(r"^Email$")).get_by_role("textbox")
        if not email_box.is_visible():
            email_box = self.page.get_by_placeholder("Email")
        if not email_box.is_visible():
            email_box = self.page.locator(".chakra-modal__content input[type='email'], .chakra-modal__content input").nth(1)
        email_box.click()
        email_box.fill(email)

        phone_box = self.page.locator("div").filter(has_text=re.compile(r"^Phone Number$")).get_by_role("textbox")
        if not phone_box.is_visible():
            phone_box = self.page.get_by_placeholder("Phone Number")
        if not phone_box.is_visible():
            phone_box = self.page.locator(".chakra-modal__content input[type='tel'], .chakra-modal__content input").nth(2)
        phone_box.click()
        phone_box.fill(phone)

    def select_director_candidate(self, director_name: str):
        """Selects a candidate from the 'Director *' select dropdown."""
        log_debug("Select", "Director", value=director_name)
        select_elem = self.page.get_by_label(self.DIRECTOR_SELECT_LABEL)
        if not select_elem.is_visible():
            select_elem = self.page.locator(".chakra-modal__content select").first

        if select_elem.is_visible():
            try:
                select_elem.select_option(label=director_name)
            except Exception:
                opt_match = select_elem.locator("option").filter(has_text=director_name).first
                if opt_match.is_visible():
                    val = opt_match.get_attribute("value")
                    if val:
                        select_elem.select_option(value=val)
                    else:
                        select_elem.select_option(index=1)
                else:
                    select_elem.select_option(index=1)

    def select_us_companies_and_shares(self, us_company_shares: dict):
        """Selects multiple US Companies and enters their share percentages."""
        if not us_company_shares:
            return

        btn = self.page.locator(".chakra-modal__content button, button[id^='menu-button-'], [role='button']").filter(has_text=re.compile(r"Select US Company|US Companies", re.IGNORECASE)).first
        if not btn.is_visible():
            btn = self.page.get_by_role("button", name="Select US Company")
        if not btn.is_visible():
            btn = self.page.get_by_label("US Companies")

        if btn.is_visible():
            log_debug("Open US Companies Dropdown")
            btn.click(force=True)
            self.page.wait_for_timeout(300)

            for comp_name in us_company_shares.keys():
                log_debug("Select", "US Company", value=comp_name)
                item = self.page.get_by_role("menuitem", name=re.compile(re.escape(comp_name[:10]), re.IGNORECASE)).first
                if not item.is_visible():
                    item = self.page.locator(".chakra-menu__menuitem, [role='menuitem']").filter(has_text=comp_name[:10]).first
                if item.is_visible():
                    item.click(force=True)
                self.page.wait_for_timeout(200)

            # Click on blank space in form to close the dropdown menu (Codegen flow)
            try:
                self.page.locator(".chakra-modal__header, .chakra-modal__content").first.click(position={"x": 20, "y": 20}, force=True)
            except Exception:
                self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(400)

            # Fill share percentage spinbuttons for each US company at distinct index
            all_spins = self.page.get_by_role("spinbutton").all()
            if not all_spins:
                all_spins = self.page.locator(".chakra-modal__content input[type='number'], input[type='number']").all()

            for idx, (comp_name, share_pct) in enumerate(us_company_shares.items()):
                log_debug("Fill", "US Share Percentage", value=f"{comp_name} -> {share_pct}%")
                if idx < len(all_spins):
                    spin = all_spins[idx]
                    spin.click()
                    spin.fill(str(share_pct))
                    self.page.wait_for_timeout(100)

    def select_payroll_companies_and_shares(self, payroll_company_shares: dict, us_count: int = 0):
        """Selects multiple Payroll Companies and enters their share percentages."""
        if not payroll_company_shares:
            return

        btn = self.page.locator(".chakra-modal__content button, button[id^='menu-button-'], [role='button']").filter(has_text=re.compile(r"Select Payroll Company|Payroll Companies", re.IGNORECASE)).first
        if not btn.is_visible():
            btn = self.page.get_by_role("button", name="Select Payroll Company")
        if not btn.is_visible():
            btn = self.page.get_by_label("Payroll Companies")

        if btn.is_visible():
            log_debug("Open Payroll Companies Dropdown")
            btn.click(force=True)
            self.page.wait_for_timeout(300)

            for comp_name in payroll_company_shares.keys():
                log_debug("Select", "Payroll Company", value=comp_name)
                item = self.page.get_by_role("menuitem", name=re.compile(re.escape(comp_name[:10]), re.IGNORECASE)).first
                if not item.is_visible():
                    item = self.page.locator(".chakra-menu__menuitem, [role='menuitem']").filter(has_text=comp_name[:10]).first
                if item.is_visible():
                    item.click(force=True)
                self.page.wait_for_timeout(200)

            # Click on blank space in form to close the dropdown menu (Codegen flow)
            try:
                self.page.locator(".chakra-modal__header, .chakra-modal__content").first.click(position={"x": 20, "y": 20}, force=True)
            except Exception:
                self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(400)

            # Fill share percentage spinbuttons for each Payroll company at distinct index (after us_count)
            all_spins = self.page.get_by_role("spinbutton").all()
            if not all_spins:
                all_spins = self.page.locator(".chakra-modal__content input[type='number'], input[type='number']").all()

            payroll_spins = all_spins[us_count:]
            for idx, (comp_name, share_pct) in enumerate(payroll_company_shares.items()):
                log_debug("Fill", "Payroll Share Percentage", value=f"{comp_name} -> {share_pct}%")
                if idx < len(payroll_spins):
                    spin = payroll_spins[idx]
                    spin.click()
                    spin.fill(str(share_pct))
                    self.page.wait_for_timeout(100)

    def fill_director_details(self, director_name: str, us_company_shares: dict = None, payroll_company_shares: dict = None):
        """Fills complete Director form using exact Codegen locators."""
        self.select_director_candidate(director_name)
        us_count = len(us_company_shares) if us_company_shares else 0
        self.select_us_companies_and_shares(us_company_shares or {})
        self.select_payroll_companies_and_shares(payroll_company_shares or {}, us_count=us_count)

    def click_save(self):
        """Clicks the 'Add' or 'Update' button on the modal."""
        log_debug("Click", "Save")
        btn = self.page.get_by_role("button", name="Add", exact=True)
        if btn.is_visible():
            btn.click(force=True)
            self.page.wait_for_timeout(500)
            return

        update_btn = self.page.get_by_role("button", name="Update", exact=True)
        if update_btn.is_visible():
            update_btn.click(force=True)
            self.page.wait_for_timeout(500)
            return

        save_btn = self.page.locator(".chakra-modal__content button").filter(has_text=re.compile(r"Add|Save|Update|Submit", re.IGNORECASE)).first
        if save_btn.is_visible():
            save_btn.click(force=True)
            self.page.wait_for_timeout(500)

    def click_cancel(self):
        """Clicks Cancel button on modal."""
        log_debug("Click", "Cancel")
        cancel_btn = self.page.get_by_role("button", name="Cancel", exact=True)
        if not cancel_btn.is_visible():
            cancel_btn = self.page.locator(".chakra-modal__content button").filter(has_text=re.compile(r"Cancel|Close", re.IGNORECASE)).first
        if cancel_btn.is_visible():
            cancel_btn.click(force=True)
            self.page.wait_for_timeout(500)

    def edit_director(self, director_name: str):
        """Clicks Edit icon on the grid row for target Director (Codegen exact)."""
        log_debug("Click", "Edit Director", value=director_name)
        row = self.page.locator("tbody tr").filter(has_text=director_name).first
        edit_btn = row.get_by_label("Edit")
        if not edit_btn.is_visible():
            edit_btn = row.locator("button, a, [aria-label='Edit']").first
        edit_btn.click(force=True)
        self.page.wait_for_timeout(500)

    def search_director(self, query: str):
        """Types query into the grid search input."""
        log_debug("Fill", "Search", value=query)
        search_box = self.page.get_by_placeholder("Search")
        if not search_box.is_visible():
            search_box = self.page.locator("input[placeholder*='Search']").first
        search_box.click()
        search_box.fill(query)
        self.page.wait_for_timeout(400)

    def get_first_director_name(self) -> str | None:
        """Returns name of first director row in grid."""
        rows = self.page.locator(self.TABLE_ROWS).all()
        if rows:
            txt = rows[0].inner_text().strip()
            tokens = [t.strip() for t in txt.replace("\t", "\n").split("\n") if t.strip()]
            for token in tokens:
                if len(token) > 3 and not token.isdigit() and "%" not in token and "showing" not in token.lower() and "prev" not in token.lower():
                    return token
        return None

    def get_existing_director_names(self) -> list[str]:
        """Returns list of all director names currently in grid (case normalized)."""
        names = []
        cells = self.page.locator("tbody tr td a, tbody tr td:nth-child(2)").all()
        for cell in cells:
            txt = cell.inner_text().strip()
            if txt and len(txt) > 2 and not txt.isdigit() and "showing" not in txt.lower():
                clean_name = txt.splitlines()[-1].strip()
                if clean_name and clean_name not in names:
                    names.append(clean_name)
        return names

    def click_shareholding_details(self, director_name: str):
        """Clicks shareholding cell to open popover details."""
        log_debug(f"Clicking shareholding cell for: {director_name}")
        row = self.page.locator(self.TABLE_ROWS).filter(has_text=director_name).first
        if row.is_visible():
            cell = row.locator("td").filter(has_text="%").first
            if cell.is_visible():
                cell.click()

    def is_modal_open(self) -> bool:
        """Returns True if Add/Edit Director modal is visible."""
        try:
            return self.page.locator(self.MODAL_DIALOG).first.is_visible()
        except Exception:
            return False

    def get_form_error_or_toast(self) -> str:
        """Captures toast notification text or form field error message."""
        try:
            toast = self.page.locator(self.TOAST).first
            if toast.is_visible():
                return toast.inner_text().strip()
        except Exception:
            pass
            
        try:
            err = self.page.locator(".chakra-form__error-message, [role='alert']").first
            if err.is_visible():
                return err.inner_text().strip()
        except Exception:
            pass
        return ""
