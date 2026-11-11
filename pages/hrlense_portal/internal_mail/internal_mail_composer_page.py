"""
HRlens Portal — Internal Mail Composer Page Object.
Route: /internal-mail-composer

Covers:
1. Composer Drawer Open & Discard.
2. Recipient Mode Selection:
   - Mode 1: Individual
     * Cascading Filters: Company -> Branch -> Department
     * Dynamic Employee Search (Global fallback when unselected, Scoped when selected)
     * Employee chip selection and management
   - Mode 2: Group / Branch
     * Group Type & Native Select Target Group dropdown
3. Subject & SunEditor Rich-Text Body Handling.
4. Send Message Execution & Toast/Validation Validation.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class InternalMailComposerPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_composer(self) -> None:
        """Navigates to Internal Mail Composer page."""
        url = f"{settings.BASE_URL}/internal-mail-composer"
        logger.info(f"Navigating to Internal Mail Composer: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)

    # ──────────────────────────────────────────────────────────────────────────
    # COMPOSER DRAWER & ACTIONS
    # ──────────────────────────────────────────────────────────────────────────

    def click_compose(self) -> None:
        """Clicks 'Compose' or 'Send your first message' button to open composer drawer."""
        logger.info("Clicking 'Compose' button...")
        btn = self.page.locator("button:has-text('Compose'), button:has-text('Send your first message')").first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        # Wait for drawer header 'New Message'
        self.page.locator("p:has-text('New Message'), h2:has-text('New Message')").first.wait_for(
            state="visible", timeout=10000
        )
        self.page.wait_for_timeout(600)

    def click_discard(self) -> None:
        """Clicks 'Discard' button or discard close icon to close composer."""
        logger.info("Clicking 'Discard' button...")
        btn = self.page.locator("button:has-text('Discard'), button[aria-label='Discard']").first
        if btn.is_visible(timeout=3000):
            btn.click()
            self.page.wait_for_timeout(500)

    def click_send_message(self) -> str:
        """
        Clicks 'Send Message' button and waits for confirmation toast.
        Returns the captured toast message string.
        """
        logger.info("Clicking 'Send Message' button...")
        btn = self.page.locator("button:has-text('Send Message')").last
        btn.wait_for(state="visible", timeout=5000)
        btn.click()

        # Capture response toast
        toast_msg = ""
        try:
            toast_loc = self.page.locator(".chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            toast_loc.wait_for(state="visible", timeout=8000)
            toast_msg = toast_loc.inner_text().strip()
            logger.info(f"[COMPOSE TOAST] Captured: '{toast_msg}'")
        except Exception as e:
            logger.warning(f"Toast capture note: {e}")

        return toast_msg

    # ──────────────────────────────────────────────────────────────────────────
    # RECIPIENT MODE SELECTION
    # ──────────────────────────────────────────────────────────────────────────

    def select_recipient_mode(self, mode: str = "individual") -> None:
        """Selects recipient mode radio: 'individual' or 'group'."""
        logger.info(f"Selecting recipient mode: '{mode}'")
        if mode.lower() in ["group", "branch", "group / branch"]:
            radio = self.page.locator("label:has-text('Group / Branch'), input[value='group']").first
        else:
            radio = self.page.locator("label:has-text('Individual'), input[value='individual']").first

        radio.wait_for(state="visible", timeout=5000)
        radio.click()
        self.page.wait_for_timeout(600)

    def is_recipient_mode_checked(self, mode: str = "individual") -> bool:
        """Checks if the specified recipient mode radio is currently active."""
        if mode.lower() in ["group", "branch", "group / branch"]:
            radio_input = self.page.locator("input[value='group']").first
        else:
            radio_input = self.page.locator("input[value='individual']").first

        return radio_input.is_checked()

    # ──────────────────────────────────────────────────────────────────────────
    # CASCADING FILTERS (Company -> Branch -> Department)
    # ──────────────────────────────────────────────────────────────────────────

    def _get_filter_button(self, label_text: str) -> Locator:
        """Returns the dropdown trigger button under the specified form control label."""
        return self.page.locator(
            f"//div[contains(@class, 'chakra-form-control') and .//label[contains(text(), '{label_text}')]]//button"
        ).first

    def get_company_filter_button_text(self) -> str:
        """Returns the current text displayed on the Company filter button."""
        btn = self._get_filter_button("Company")
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Select Company'), button:has-text('Company')").first
        return btn.inner_text().strip()

    def get_branch_filter_button_text(self) -> str:
        """Returns the current text displayed on the Branch filter button."""
        btn = self._get_filter_button("Branch")
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Select Branch'), button:has-text('Select Company First')").first
        return btn.inner_text().strip()

    def get_department_filter_button_text(self) -> str:
        """Returns the current text displayed on the Department filter button."""
        btn = self._get_filter_button("Department")
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Select Department'), button:has-text('Select Branch First')").first
        return btn.inner_text().strip()

    def is_branch_filter_enabled(self) -> bool:
        """Checks whether the Branch filter button is enabled."""
        btn = self._get_filter_button("Branch")
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Select Branch'), button:has-text('Select Company First')").first
        return btn.is_enabled()

    def is_department_filter_enabled(self) -> bool:
        """Checks whether the Department filter button is enabled."""
        btn = self._get_filter_button("Department")
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Select Department'), button:has-text('Select Branch First')").first
        return btn.is_enabled()

    def select_company_filter(self, company_name: str) -> bool:
        """Opens Company dropdown, searches for company_name, and selects it."""
        logger.info(f"Selecting Company filter: '{company_name}'")
        btn = self._get_filter_button("Company")
        btn.click()
        self.page.wait_for_timeout(400)

        menu = self.page.locator(".chakra-menu__menu-list:visible").first
        menu.wait_for(state="visible", timeout=5000)

        # Search inside menu
        search_input = menu.locator("input[placeholder*='Search']").first
        if search_input.is_visible(timeout=1000):
            search_input.fill(company_name)
            self.page.wait_for_timeout(400)

        # Click checkbox item
        item = menu.locator(
            f"label.chakra-checkbox:has-text('{company_name}'), "
            f"span.chakra-checkbox__label:has-text('{company_name}'), "
            f"button:has-text('{company_name}')"
        ).first

        if item.is_visible(timeout=3000):
            item.click()
            self.page.wait_for_timeout(400)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(600)
            logger.info(f"Selected Company: '{company_name}'")
            return True

        logger.warning(f"Company '{company_name}' not found in dropdown.")
        self.page.keyboard.press("Escape")
        return False

    def select_branch_filter(self, branch_name: str) -> bool:
        """Opens Branch dropdown (enabled after Company is selected) and selects branch_name."""
        logger.info(f"Selecting Branch filter: '{branch_name}'")
        btn = self._get_filter_button("Branch")
        if not btn.is_enabled(timeout=4000):
            logger.warning("Branch filter button is disabled!")
            return False

        btn.click()
        self.page.wait_for_timeout(500)

        menu = self.page.locator(".chakra-menu__menu-list:visible").first
        menu.wait_for(state="visible", timeout=5000)

        # Check if option is directly visible without search
        item = menu.locator(
            f"button:has-text('{branch_name}'), "
            f"label:has-text('{branch_name}'), "
            f"span:has-text('{branch_name}'), "
            f"[role='menuitem']:has-text('{branch_name}')"
        ).first

        if not item.is_visible(timeout=1500):
            search_input = menu.locator("input[placeholder*='Search']").first
            if search_input.is_visible(timeout=1000):
                search_input.fill(branch_name)
                self.page.wait_for_timeout(400)
                item = menu.locator(
                    f"button:has-text('{branch_name}'), "
                    f"label:has-text('{branch_name}'), "
                    f"span:has-text('{branch_name}')"
                ).first

        if item.is_visible(timeout=3000):
            item.click()
            self.page.wait_for_timeout(500)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            logger.info(f"Selected Branch: '{branch_name}'")
            return True

        # Fallback: click first visible branch option
        first_opt = menu.locator("button, [role='menuitem']").first
        if first_opt.is_visible(timeout=2000):
            first_opt.click()
            self.page.wait_for_timeout(500)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            return True

        self.page.keyboard.press("Escape")
        return False

    def select_department_filter(self, dept_name: str) -> bool:
        """Opens Department dropdown (enabled after Branch is selected) and selects dept_name."""
        logger.info(f"Selecting Department filter: '{dept_name}'")
        btn = self._get_filter_button("Department")
        if not btn.is_enabled(timeout=4000):
            logger.warning("Department filter button is disabled!")
            return False

        btn.click()
        self.page.wait_for_timeout(400)

        menu = self.page.locator(".chakra-menu__menu-list:visible").first
        menu.wait_for(state="visible", timeout=5000)

        search_input = menu.locator("input[placeholder*='Search']").first
        if search_input.is_visible(timeout=1000):
            search_input.fill(dept_name)
            self.page.wait_for_timeout(400)

        item = menu.locator(
            f"label.chakra-checkbox:has-text('{dept_name}'), "
            f"span.chakra-checkbox__label:has-text('{dept_name}'), "
            f"button:has-text('{dept_name}')"
        ).first

        if item.is_visible(timeout=3000):
            item.click()
            self.page.wait_for_timeout(400)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            logger.info(f"Selected Department: '{dept_name}'")
            return True

        self.page.keyboard.press("Escape")
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # EMPLOYEE SEARCH & SELECTION (Universal input locator)
    # ──────────────────────────────────────────────────────────────────────────

    def _get_employee_search_input(self) -> Locator:
        """Returns the search input locator matching both unfiltered and filtered placeholders."""
        return self.page.locator(
            "input[placeholder*='Search employee'], "
            "input[placeholder*='Employees load'], "
            "input[placeholder*='type to narrow']"
        ).first

    def search_employees(self, query: str) -> List[Dict[str, str]]:
        """
        Fills query into employee search input and extracts visible suggestion cards.
        Returns list of dicts with employee details.
        """
        logger.info(f"Searching employee with query: '{query}'")
        emp_input = self._get_employee_search_input()
        emp_input.wait_for(state="visible", timeout=5000)
        emp_input.click()
        emp_input.fill("")
        emp_input.press_sequentially(query, delay=100)
        self.page.wait_for_timeout(1500)

        results = []
        cards = self.page.locator(
            "//div[contains(@class, 'chakra-stack') or contains(@class, 'css-')]//p[contains(@class, 'chakra-text')]"
        ).all()

        for c in cards:
            txt = c.inner_text().strip()
            if txt and not txt.startswith("Search") and not txt.startswith("Select"):
                results.append({"name": txt})

        logger.info(f"Found {len(results)} suggestion elements for query '{query}'")
        return results

    def select_employee_by_name(self, employee_name: str) -> bool:
        """
        Types employee_name and clicks the exact employee suggestion card.
        """
        logger.info(f"Selecting employee: '{employee_name}'")
        emp_input = self._get_employee_search_input()
        emp_input.wait_for(state="visible", timeout=5000)
        emp_input.click()
        emp_input.fill("")
        emp_input.press_sequentially(employee_name, delay=100)
        self.page.wait_for_timeout(1500)

        # Click exact paragraph matching employee name in suggestion popover
        card = self.page.locator(
            f"//p[normalize-space(text())='{employee_name}'] | "
            f"//span[normalize-space(text())='{employee_name}']"
        ).first

        if card.is_visible(timeout=5000):
            card.click()
            logger.info(f"Clicked employee suggestion card: '{employee_name}'")
            self.page.wait_for_timeout(800)
            return True

        # Fallback: click first visible result
        fallback = self.page.locator("p:has-text('" + employee_name.split()[0] + "')").first
        if fallback.is_visible(timeout=3000):
            fallback.click()
            logger.info(f"Clicked fallback employee suggestion card for: '{employee_name}'")
            self.page.wait_for_timeout(800)
            return True

        logger.warning(f"Employee suggestion for '{employee_name}' not visible.")
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 2: GROUP / BRANCH TARGET SELECTION (Native HTML <select>)
    # ──────────────────────────────────────────────────────────────────────────

    def select_group_target(self, target_name: str = "Varanasi") -> bool:
        """
        Selects a group recipient target using either the native <select> dropdown
        or legacy chip buttons.
        """
        logger.info(f"Selecting group recipient target: '{target_name}'")
        select_loc = self.page.locator("select.chakra-select").last

        if select_loc.is_visible(timeout=3000):
            options = select_loc.locator("option").all()
            target_val = None
            first_val = None
            for opt in options:
                val = opt.get_attribute("value")
                txt = opt.inner_text().strip()
                if val and val != "":
                    if not first_val:
                        first_val = val
                    if target_name.lower() in txt.lower():
                        target_val = val
                        break
            chosen = target_val or first_val
            if chosen:
                select_loc.select_option(value=chosen)
                self.page.wait_for_timeout(600)
                logger.info(f"Selected group target option value: '{chosen}'")
                return True

        # Fallback to chips if legacy UI
        chip = self.page.locator(f"button:has-text('{target_name}')").first
        if chip.is_visible(timeout=2000):
            chip.click()
            self.page.wait_for_timeout(400)
            return True

        return False

    # ──────────────────────────────────────────────────────────────────────────
    # SUBJECT & MESSAGE BODY
    # ──────────────────────────────────────────────────────────────────────────

    def fill_subject(self, subject: str) -> None:
        """Fills the Subject input field."""
        logger.info(f"Filling subject: '{subject}'")
        subj_input = self.page.locator("input[placeholder*='about' i], input[placeholder*='Subject' i]").first
        if not subj_input.is_visible(timeout=1000):
            subj_input = self.page.locator("//div[./label[contains(text(), 'Subject')]]//input").first

        subj_input.wait_for(state="visible", timeout=5000)
        subj_input.fill("")
        subj_input.fill(subject)

    def fill_message_body(self, body_text: str) -> None:
        """Fills rich text SunEditor contenteditable area with message body."""
        logger.info("Filling message body in rich text editor...")
        editor = self.page.locator(".sun-editor-editable, div[contenteditable='true']").first
        editor.wait_for(state="visible", timeout=5000)
        editor.click()
        editor.fill(body_text)
        self.page.wait_for_timeout(300)
