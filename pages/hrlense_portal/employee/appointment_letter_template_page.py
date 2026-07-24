import re
import pytest
from pages.base_page import BasePage
from testdata.static.appointment_letter_sections import APPOINTMENT_LETTER_SECTIONS
from testdata.static.companies import COMPANIES


class AppointmentLetterTemplatePage(BasePage):
    # ── Selectors ─────────────────────────────────────────────────────────────
    ADMIN_CONTROL       = "a:has-text('Admin Control')"
    OFFER_LETTER_MENU   = "a:has-text('Offer Letter Template')"
    TEMPLATE_SELECT_BTN = ".css-9qrvd0"
    ADD_SECTION_BTN     = "button:has-text('Add Section')"
    SEPARATE_ITEMS_TEXT = "text=Use | to separate items ·"
    TITLE_INPUT         = "[placeholder='e.g. Assignment:-']"
    CONTENT_INPUT       = "[placeholder='Enter content here...']"
    SAVE_BTN            = "button:has-text('Save')"
    UPDATE_BTN          = "button:has-text('Update')"
    ORDER_LABEL         = "label:has-text('Order')"

    # ── Navigation ─────────────────────────────────────────────────────────────
    def navigate_to_appointment_letter_template(self):
        self.page.get_by_role("link", name="Admin Control").click()
        self.page.get_by_role("link", name="• Appointment Letter Template").click()
        self.page.wait_for_load_state("networkidle")

    def select_company(self, company_name: str):
        """
        Select a company from the template dropdown by its visible name.
        Available companies are defined in testdata/static/companies.py.
        Fails immediately if the company name is not in the known list.
        """
        assert company_name in COMPANIES, (
            f"Company '{company_name}' is not in the known company list. "
            f"Available: {COMPANIES}"
        )
        self.page.locator(self.TEMPLATE_SELECT_BTN).click()
        self.page.get_by_role("combobox").select_option(label=company_name)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _fill_field(self, locator_str: str, text: str):
        """Fill an input field with fallback to .type() for rich-text editors."""
        field = self.page.locator(locator_str)
        field.click()
        try:
            field.fill(text)
        except Exception:
            field.type(text)

    # Removed _get_existing_section_keys since we now rely on toast messages.

    def add_section(self, section: dict, start_order: int = 1) -> tuple[bool, int]:
        """
        [CREATE] Add a single section using its key, title, and content.
        Section dict shape: { "key": str, "title": str, "content": str }
        Returns a tuple: (success: bool, final_order_used: int)
        """

        # Open the Add Section dialog
        self.page.get_by_role("button", name="Add Section").click()
        self.page.get_by_text("Use | to separate items ·").click()

        # Select the Section Key dropdown (Bug fixed by Dev)
        try:
            self.page.get_by_label("Section Key").select_option(section["key"], timeout=5000)
        except Exception as e:
            print(f"[WARN] Could not select Section Key '{section['key']}': {e}")

        # Fill title field
        title_field = self.page.get_by_placeholder("e.g. Assignment:-").first
        title_field.click()
        title_field.fill(section["title"])

        # Select Style dynamically from test data
        try:
            style_combo = self.page.get_by_role("combobox", name="Style")
            style_name = section.get("style", "Paragraph")
            style_combo.select_option(label=style_name, timeout=3000)
        except Exception as e:
            print(f"[WARN] Could not dynamically select Style '{section.get('style')}': {e}")

        # Fill content editor
        content_field = self.page.get_by_placeholder("Enter content here...").first
        content_field.click()
        content_field.fill(section["content"])

        # Set strict order from the predefined list
        target_order = section.get("order", start_order)
        order_field = self.page.get_by_label("Order").first
        order_field.click()
        order_field.fill(str(target_order))
            
        # Save
        self.page.get_by_role("button", name="Save").click()
        
        # Capture toast message
        try:
            toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
            toast.wait_for(state="visible", timeout=4000)
            toast_text = toast.inner_text().lower()
            print(f"\n[TOAST NOTIFICATION] {toast.inner_text()}")
            
            # If the backend rejects the strict order, or it already exists, close modal
            if "already exist" in toast_text:
                print(f"[SKIP/FAIL] Section '{section['key']}' or Order {target_order} rejected: {toast_text}")
                try:
                    self.page.get_by_role("button", name="Cancel").nth(1).click(timeout=5000)
                    self.page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"[WARN] Error clicking Cancel: {e}")
                return False, target_order
                
        except Exception:
            print("\n[TOAST NOTIFICATION] No toast message detected.")
            
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

        # Post-save: section title must be visible
        self.read_section(section["key"])
        return True, target_order

    def add_all_sections(self):
        """
        [CREATE ALL] Try to add all 8 sections in defined order.
        If the backend returns an 'already exists' toast, it skips to the next one.
        Tracks the order variable across iterations for speed.
        """
        current_order = 1
        for section in APPOINTMENT_LETTER_SECTIONS:
            success, final_order = self.add_section(section, start_order=current_order)
            if success:
                # Start searching for the next section's order one slot higher
                current_order = final_order + 1

    def verify_duplicate_blocked(self, section: dict):
        """
        [DUPLICATE TEST] Attempt to add a section that already exists.
        Fails if the backend allows it. Asserts that an error toast appears.
        """
        # Open the Add Section dialog
        self.page.get_by_role("button", name="Add Section").click()
        self.page.get_by_text("Use | to separate items ·").click()

        # Select the Section Key dropdown
        try:
            self.page.get_by_label("Section Key").select_option(section["key"], timeout=5000)
        except Exception as e:
            print(f"[WARN] Could not select Section Key '{section['key']}': {e}")

        # Fill title and content
        self.page.locator(self.TITLE_INPUT).fill(section["title"])
        self.page.get_by_placeholder("Enter content here...").fill(section["content"])

        # Save and assert toast error
        self.page.get_by_role("button", name="Save").click()
        
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
        toast.wait_for(state="visible", timeout=5000)
        toast_text = toast.inner_text().lower()
        
        assert "already exists" in toast_text, (
            f"[DUPLICATE PREVENTION FAILED] Expected 'already exists' toast, got: '{toast_text}'"
        )
        print(f"\n[PASS] Duplicate correctly blocked: {toast_text}")
        
        # Close or cancel the modal since save failed
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass

    # ── READ ───────────────────────────────────────────────────────────────────
    def read_section(self, section_key: str) -> bool:
        """[READ] Assert the section title is visible on the page."""
        section = next((s for s in APPOINTMENT_LETTER_SECTIONS if s["key"] == section_key), None)
        assert section, f"Unknown section key: '{section_key}'"
        
        # User provided: page.locator("p").filter(has_text=re.compile(r"^PROBATION$"))
        locator = self.page.locator("p").filter(has_text=re.compile(f"^{section['key']}$")).first
        assert locator.is_visible(), (
            f"[READ FAILED] Section '{section_key}' (title: '{section['title']}') "
            "is not visible on the template page."
        )
        return True

    def read_all_sections(self):
        """[READ ALL] Assert every section title is visible on the page."""
        for section in APPOINTMENT_LETTER_SECTIONS:
            self.read_section(section["key"])

    def get_current_orders(self) -> dict:
        """
        Dynamically calculates the current state by briefly opening each section's Edit modal,
        reading the true Order value, and closing it. Returns a mapping of {section_key: current_order}.
        """
        current_state = {}
        for section in APPOINTMENT_LETTER_SECTIONS:
            section_key = section["key"]
            row = self.page.locator("div").filter(
                has=self.page.locator("p").filter(has_text=re.compile(f"^{section_key}$"))
            ).filter(
                has=self.page.get_by_label("Edit")
            ).last
            
            edit_btn = row.get_by_label("Edit").first
            if edit_btn.count() == 0:
                continue
                
            edit_btn.click()
            self.page.wait_for_timeout(300)
            order_val = self.page.get_by_label("Order").last.input_value()
            current_state[section_key] = int(order_val) if str(order_val).isdigit() else -1
            
            # Robustly close the modal
            try:
                self.page.get_by_role("button", name="Cancel").last.click(timeout=2000)
            except Exception:
                try:
                    self.page.get_by_role("button", name="Cancel").first.click(timeout=2000)
                except Exception:
                    self.page.keyboard.press("Escape")
            
            self.page.wait_for_timeout(300)
            
        return current_state

    # ── UPDATE ─────────────────────────────────────────────────────────────────
    def update_section(self, section_key: str, new_title: str = None, new_content: str = None, enforce_order: int = None, toggle_status: bool = False):
        """
        [UPDATE] Click the Edit label for the target section, update title and/or
        content, click Update, and assert the section is still visible after update.
        """
        section = next((s for s in APPOINTMENT_LETTER_SECTIONS if s["key"] == section_key), None)
        assert section, f"Unknown section key: '{section_key}'"

        # We find a common ancestor <div> that contains both the <p> with our key,
        # and an Edit button. We take the .last match to get the deepest/closest container.
        row = self.page.locator("div").filter(
            has=self.page.locator("p").filter(has_text=re.compile(f"^{section['key']}$"))
        ).filter(
            has=self.page.get_by_label("Edit")
        ).last
        
        edit_btn = row.get_by_label("Edit").first
        
        if edit_btn.count() == 0:
            raise AssertionError(f"Could not find Edit button in row for section '{section_key}'.")
            
        edit_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(500)

        if toggle_status:
            # Click the Active/Inactive text button inside the modal
            try:
                self.page.get_by_text("Active", exact=True).click(timeout=2000)
            except Exception:
                try:
                    self.page.get_by_text("Inactive", exact=True).click(timeout=2000)
                except Exception:
                    print(f"[WARN] Could not find Active/Inactive toggle in modal for {section_key}")

        if new_title:
            title_field = self.page.locator(self.TITLE_INPUT)
            if title_field.count() > 0:
                title_field.click()
                title_field.press("Control+a")
                try:
                    title_field.fill(new_title)
                except Exception:
                    title_field.type(new_title)

        if new_content:
            content_field = self.page.get_by_placeholder("Enter content here...").first
            content_field.click()
            content_field.clear()
            content_field.fill(new_content)

        if enforce_order is not None:
            order_field = self.page.get_by_label("Order").first
            current_order_val = order_field.input_value()
            if current_order_val != str(enforce_order):
                print(f"[REORDER] Fixing '{section_key}' order: {current_order_val} -> {enforce_order}")
                order_field.click()
                order_field.clear()
                order_field.fill(str(enforce_order))

        self.page.get_by_role("button", name="Update").click()
        
        # Check for errors (like 'Sort order already exists' if there's a conflict)
        try:
            toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
            toast.wait_for(state="visible", timeout=3000)
            toast_text = toast.inner_text().lower()
            if "already exist" in toast_text:
                print(f"[WARN] Update failed for '{section_key}': {toast_text}")
                # Close modal safely
                self.page.get_by_role("button", name="Cancel").nth(1).click()
                return False
        except Exception:
            pass

        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

        # Verify section still present after update
        self.read_section(section_key)

    # ── TOGGLE STATUS ─────────────────────────────────────────────────────────
    def toggle_section_status(self, section_key: str):
        """
        [STATUS] Toggle the Active/Inactive Chakra switch for the given section.
        Finds the row by section key text and clicks its switch thumb.

        Locator from codegen:
          page.get_by_text(section_key)
              .locator("xpath=ancestor::tr")
              .locator(".chakra-switch__thumb")
              .click()
        """
        self._toggle_section_switch(section_key)

    def _toggle_section_switch(self, section_key: str):
        """
        Shared helper: click the Chakra switch thumb in the section's row
        to toggle it between active and inactive.
        """
        # Find the deepest common ancestor <div> containing the <p> text and the switch
        row = self.page.locator("div").filter(
            has=self.page.locator("p").filter(has_text=re.compile(f"^{section_key}$"))
        ).filter(
            has=self.page.locator(".chakra-switch__thumb")
        ).last
        
        row.locator(".chakra-switch__thumb").first.click()
        
        # Handle the confirmation modal (the toggle opens a 'Delete Section' modal)
        try:
            # Chakra UI confirmation modals often use role="alertdialog"
            dialog = self.page.locator("[role='alertdialog'], [role='dialog']").first
            # We wait a short time because reactivation might not prompt a modal
            dialog.wait_for(state="visible", timeout=2000)
            
            # Devs changed the confirmation buttons from "Yes" to "Inactive" and "Activate"
            try:
                dialog.get_by_role("button", name="Inactive", exact=True).click(timeout=1500)
            except Exception:
                dialog.get_by_role("button", name="Activate", exact=True).click(timeout=1500)
        except Exception:
            pass # No confirmation modal appeared
        
        # Capture and assert the resulting toast notification
        try:
            toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
            toast.wait_for(state="visible", timeout=5000)
            toast_text = toast.inner_text().lower()
            
            # If the backend throws a conflict error, fail immediately
            if "already exist" in toast_text:
                pytest.fail(f"Row toggle failed for '{section_key}': {toast_text}")
            
            # Assert that a success toast appeared
            assert "updated successfully" in toast_text or "success" in toast_text, f"Expected success toast, but got: {toast_text}"
            print(f"[TOAST] {toast.inner_text()}")
            
        except AssertionError as e:
            raise e # Reraise our own assertion failures
        except Exception as e:
            pytest.fail(f"Failed to capture success toast after toggling '{section_key}'. Error: {e}")
            
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

