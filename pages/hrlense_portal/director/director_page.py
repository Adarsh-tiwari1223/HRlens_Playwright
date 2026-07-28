"""
Director Page Object for HR Lens Portal Director Module.
Handles navigation, listing, adding, and updating Director Shareholdings.
"""

import logging
from core.config import settings
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DirectorPage(BasePage):
    # Sidebar navigation
    DIRECTORS_SIDEBAR_LINK = "role=link[name='Directors']"
    
    # Header actions & filters
    ADD_DIRECTOR_BTN = "role=button[name='Add Director']"
    SEARCH_INPUT = "internal:placeholder='Search'"
    
    # Table selectors
    TABLE_ROWS = "tbody tr"
    
    # Form / Modal selectors
    MODAL_DIALOG = "[role='dialog']"
    SAVE_BTN = "role=button[name='Save']"
    SUBMIT_BTN = "role=button[name='Submit']"
    CANCEL_BTN = "role=button[name='Cancel']"
    
    # Toast notification
    TOAST = ".chakra-toast div, [role='status']"

    def navigate_to_directors(self):
        """Navigates to the Directors module page."""
        logger.info("Navigating to Directors page...")
        self.page.goto(f"{settings.BASE_URL}/director")
        self.page.wait_for_load_state("domcontentloaded")
        # Fallback click sidebar link if present
        try:
            link = self.page.get_by_role("link", name="Directors", exact=True)
            if link.is_visible():
                link.click()
        except Exception:
            pass
        try:
            self.page.locator(self.TABLE_ROWS).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

    def click_add_director(self):
        """Clicks the Add Director button to open the creation modal."""
        logger.info("Opening Add Director modal...")
        add_btn = self.page.get_by_role("button", name="Add Director", exact=False)
        add_btn.click()
        self.page.locator(self.MODAL_DIALOG).wait_for(state="visible", timeout=10000)

    def get_available_director_employees(self) -> list[str]:
        """
        Fetches all available employee names from the 'Select Director' dropdown
        who have been assigned the Director role.
        """
        logger.info("Retrieving employees with Director role from dropdown...")
        select_input = self.page.get_by_placeholder("Select Director", exact=False)
        if not select_input.is_visible():
            select_input = self.page.locator("[role='dialog'] select, [role='dialog'] [class*='select']").first
        select_input.click()
        self.page.wait_for_timeout(500)

        options = self.page.locator(".chakra-portal div, .chakra-portal button, .chakra-portal option").all_inner_texts()
        employee_names = []
        for name in options:
            name = name.strip()
            if name and "\n" not in name and not name.startswith("Select") and not name.startswith("Search"):
                if name not in employee_names:
                    employee_names.append(name)
        self.page.keyboard.press("Escape")
        logger.info(f"Available employees with Director role: {employee_names}")
        return employee_names

    def fill_director_details(self, director_name: str, us_company_shares: dict = None, payroll_company_shares: dict = None):
        """
        Fills the Director form:
        - Select Director (Employee with Director role)
        - Assign US Companies & Share Percentages
        - Assign Payroll Companies & Share Percentages
        """
        logger.info(f"Filling details for Director: {director_name}")
        
        # 1. Select Director
        select_input = self.page.get_by_placeholder("Select Director", exact=False)
        if select_input.is_visible():
            select_input.click()
            select_input.fill(director_name)
            self.page.wait_for_timeout(500)
            self.page.locator(".chakra-portal").get_by_text(director_name, exact=False).first.click()
        else:
            select_elem = self.page.locator("[role='dialog'] select").first
            if select_elem.is_visible():
                select_elem.select_option(label=director_name)

        # 2. Fill US Company Shareholdings
        if us_company_shares:
            for comp_name, share_pct in us_company_shares.items():
                logger.debug(f"Assigning US Company '{comp_name}' with {share_pct}%")
                comp_input = self.page.get_by_placeholder("US Companies", exact=False)
                if comp_input.is_visible():
                    comp_input.click()
                    comp_input.fill(comp_name)
                    self.page.wait_for_timeout(500)
                    self.page.locator(".chakra-portal").get_by_text(comp_name, exact=False).first.click()
                
                pct_input = self.page.get_by_placeholder(f"Share % for {comp_name}", exact=False)
                if not pct_input.is_visible():
                    pct_input = self.page.locator(f"input[name*='{comp_name}'], input[id*='{comp_name}']").first
                if pct_input.is_visible():
                    pct_input.fill(str(share_pct))

        # 3. Fill Payroll Company Shareholdings
        if payroll_company_shares:
            for comp_name, share_pct in payroll_company_shares.items():
                logger.debug(f"Assigning Payroll Company '{comp_name}' with {share_pct}%")
                comp_input = self.page.get_by_placeholder("Payroll Companies", exact=False)
                if comp_input.is_visible():
                    comp_input.click()
                    comp_input.fill(comp_name)
                    self.page.wait_for_timeout(500)
                    self.page.locator(".chakra-portal").get_by_text(comp_name, exact=False).first.click()
                
                pct_input = self.page.get_by_placeholder(f"Share % for {comp_name}", exact=False)
                if not pct_input.is_visible():
                    pct_input = self.page.locator(f"input[name*='{comp_name}'], input[id*='{comp_name}']").first
                if pct_input.is_visible():
                    pct_input.fill(str(share_pct))

    def click_save(self):
        """Clicks the Save/Submit button on the modal."""
        logger.info("Submitting Director form...")
        save_btn = self.page.get_by_role("button", name="Save", exact=False)
        if not save_btn.is_visible():
            save_btn = self.page.get_by_role("button", name="Submit", exact=False)
        save_btn.click()

    def click_cancel(self):
        """Clicks the Cancel button on the modal."""
        logger.info("Cancelling modal dialog...")
        cancel_btn = self.page.get_by_role("button", name="Cancel", exact=True)
        if cancel_btn.is_visible():
            cancel_btn.click()

    def edit_director(self, director_name: str):
        """Opens the edit modal for a specific director row."""
        logger.info(f"Editing director record for: {director_name}")
        row = self.page.locator("tbody tr").filter(has_text=director_name).first
        row.get_by_label("Edit").click()
        self.page.locator(self.MODAL_DIALOG).wait_for(state="visible", timeout=10000)

    def open_director_documents(self, director_name: str):
        """Clicks the Document Arrow icon ('>>') for a director to open their documents."""
        logger.info(f"Opening Director Documents for: {director_name}")
        row = self.page.locator("tbody tr").filter(has_text=director_name).first
        doc_btn = row.locator("button:has-text('>>'), a:has-text('>>'), [aria-label*='Document']").first
        doc_btn.click()
        self.page.wait_for_load_state("domcontentloaded")

    def get_first_director_name(self) -> str | None:
        """Retrieves the Director Name from the first row in the grid."""
        try:
            self.page.locator(self.TABLE_ROWS).first.wait_for(state="visible", timeout=6000)
            first_row = self.page.locator(self.TABLE_ROWS).first
            cells = first_row.locator("td").all()
            if len(cells) > 1:
                return cells[1].inner_text().strip()
        except Exception:
            pass
        return None

    def wait_for_toast_message(self) -> str:
        """Waits for and returns toast notification message."""
        return self.wait_for_toast(self.TOAST)
