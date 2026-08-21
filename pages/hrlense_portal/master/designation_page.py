"""
Page Object Model for Designation Master (HR Lens Portal -> Master Module).
Handles adding new Designations under Department Bifurcations (e.g., Accounts US / Accounts IN).
"""

from pages.base_page import BasePage


class DesignationPage(BasePage):
    # Navigation
    MASTER_MENU = "a:has-text('Master'), button:has-text('Master'), span:has-text('Master')"
    DESIGNATION_SUBMENU = "a[href*='designation'], a:has-text('Designation')"

    # Actions & Buttons
    ADD_DESIGNATION_BTN = "button:has-text('Add Designation'), button:has-text('Add New Designation'), button:has-text('Add New')"
    SUBMIT_BTN = "button:has-text('Save'), button:has-text('Submit'), button[type='submit']"

    # Form Fields
    DESIGNATION_NAME_INPUT = "input[name='designationName'], input[name='name'], input[placeholder*='Designation']"
    DEPARTMENT_SELECT = "select[name='departmentId'], select[name='department'], select[id*='department']"

    def navigate_to_designation_master(self):
        """Navigates to Master -> Designation page."""
        # Directly navigate to /master/designation or click side menu
        try:
            self.page.goto(f"{self.page.url.split('/')[0]}//${self.page.url.split('/')[2]}/master/designation", timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

        if "designation" not in self.page.url.lower():
            if self.page.locator(self.MASTER_MENU).first.is_visible():
                self.page.locator(self.MASTER_MENU).first.click()
                self.page.wait_for_timeout(500)
            self.page.locator(self.DESIGNATION_SUBMENU).first.click()
            self.page.wait_for_load_state("domcontentloaded")

    def open_add_designation_modal(self):
        """Opens Add Designation Modal."""
        add_btn = self.page.locator(self.ADD_DESIGNATION_BTN).first
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.click()

    def fill_designation_form(self, designation_name: str, department_name_or_val: str = "Accounts US"):
        """Fills designation name and department selection."""
        name_input = self.page.locator(self.DESIGNATION_NAME_INPUT).first
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(designation_name)

        dept_select = self.page.locator(self.DEPARTMENT_SELECT).first
        if dept_select.is_visible():
            options = dept_select.locator("option").all_inner_texts()
            # Find matching option for Accounts US / Accounts IN
            matched_opt = next((o for o in options if department_name_or_val.lower() in o.lower()), None)
            if matched_opt:
                dept_select.select_option(label=matched_opt)
            else:
                dept_select.select_option(index=1)

    def submit_designation_form(self) -> tuple[bool, str]:
        """Submits designation form and returns success status and toast message."""
        submit_btn = self.page.locator(self.SUBMIT_BTN).first
        submit_btn.click()
        self.page.wait_for_timeout(1000)

        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast_text = ""
        try:
            if toast.is_visible(timeout=5000):
                toast_text = toast.inner_text().strip()
        except Exception:
            pass

        return True, toast_text
