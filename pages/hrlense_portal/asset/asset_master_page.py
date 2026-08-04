import re
import logging
from playwright.sync_api import expect
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetMasterPage(BasePage):
    ADMIN_BTN = "role=button[name='Admin']"
    MASTER_MENU = "role=menuitem[name='Master']"
    ASSET_MASTER_LINK = "role=link[name='• Asset Master']"
    
    # Categories tab elements
    ADD_CATEGORY_BTN = "role=button[name='Add Category']"
    CATEGORY_NAME_INPUT = "input[placeholder*='e.g. Hardware']"
    DESCRIPTION_INPUT = "textarea"
    CREATE_BTN = "role=button[name='Create']"
    UPDATE_BTN = "role=button[name='Update']"
    TOAST = "#chakra-toast-manager-top-right"

    # Sub Categories tab elements
    SUB_CATEGORIES_TAB = "role=tab[name='Sub Category']"
    ADD_SUB_CATEGORY_BTN = "role=button[name='Add Sub Category']"

    CATEGORY_SELECT = 'internal:label="Category*"'
    SUB_CATEGORY_NAME_INPUT = 'internal:label="Sub Category Name*"'
    CODE_PREFIX_INPUT = 'internal:placeholder="LAP"'

    # Vendors tab elements
    VENDORS_TAB = "role=tab[name='Vendors']"
    ADD_VENDOR_BTN = "role=button[name='Add Vendor']"
    VENDOR_NAME_INPUT = 'internal:label="Vendor Name*"'
    CONTACT_PERSON_INPUT = 'internal:label="Contact Person"'
    PHONE_INPUT = 'internal:label="Phone"'
    EMAIL_INPUT = 'internal:label="Email"'
    ADDRESS_INPUT = 'internal:label="Address"'
    GST_INPUT = 'internal:label="GST Number"'
    SUPPORTS_AMC_TEXT = "text=Supports AMC"


    def navigate_to_asset_master(self):
        logger.debug("Navigating to Asset Master page")

        self.page.goto(f"{settings.BASE_URL}/master/asset-master")

        self.page.wait_for_load_state("domcontentloaded")
        if "/login" in self.page.url:
            logger.warning("Redirected to login page. Performing authentication...")
            try:
                self.page.get_by_label("Email").wait_for(state="visible", timeout=10000)
                from pages.login_page import LoginPage
                LoginPage(self.page).login(settings.USERS["admin"]["username"], settings.USERS["admin"]["password"])
                self.page.goto(f"{settings.BASE_URL}/master/asset-master")

                self.page.wait_for_load_state("domcontentloaded")
            except Exception as e:
                logger.error(f"Auto-authentication failed: {e}")



    def navigate_to_sub_categories(self):
        logger.debug("Navigating to Sub Categories tab")
        self.click(self.SUB_CATEGORIES_TAB)

    def navigate_to_vendors(self):
        logger.debug("Navigating to Vendors tab")
        self.click(self.VENDORS_TAB)

    def _ensure_modal_closed(self):
        dialog = self.page.locator("[role='dialog']").first
        if dialog.is_visible():
            close_btn = dialog.locator(".chakra-modal__close-btn, button:has-text('Cancel')").first
            if close_btn.is_visible():
                try:
                    close_btn.click()
                    dialog.wait_for(state="hidden", timeout=3000)
                except Exception:
                    pass
        try:
            self.page.locator(".chakra-modal__overlay").first.wait_for(state="hidden", timeout=3000)
        except Exception:
            pass
        # Wait for toasts to disappear so they do not overlap top-right action buttons
        try:
            self.page.locator(".chakra-toast").first.wait_for(state="hidden", timeout=4000)
        except Exception:
            pass


    def click_add_category(self):
        self._ensure_modal_closed()
        self.click(self.ADD_CATEGORY_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def click_add_sub_category(self):
        self._ensure_modal_closed()
        self.click(self.ADD_SUB_CATEGORY_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def click_add_vendor(self):
        self._ensure_modal_closed()
        self.click(self.ADD_VENDOR_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def fill_category_details(self, name: str, description: str = None, toggle_spans: bool = False):
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page
        if name is not None:
            dialog.locator(self.CATEGORY_NAME_INPUT).fill(name)
        if description is not None:
            dialog.locator(self.DESCRIPTION_INPUT).fill(description)
        if toggle_spans:
            logger.debug("Toggling extra category status/options")
            dialog.locator("span").nth(2).click()
            dialog.locator("span").nth(1).click()

    def fill_sub_category_details(self, category_label: str = None, name: str = None, code_prefix: str = None, description: str = None):
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page
        if category_label is not None:
            logger.debug(f"Selecting category label: {category_label}")
            dialog.get_by_label("Category*").wait_for(state="visible")
            dialog.get_by_label("Category*").select_option(label=category_label)
        if name is not None:
            dialog.get_by_label("Sub Category Name*").fill(name)
        if code_prefix is not None:
            dialog.get_by_placeholder("LAP").fill(code_prefix)
        if description is not None:
            dialog.locator(self.DESCRIPTION_INPUT).fill(description)

    def fill_vendor_details(self, name: str = None, contact_person: str = None, phone: str = None, email: str = None, address: str = None, gst: str = None, supports_amc: bool = False, toggle_spans: list[int] = None):
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page

        if name is not None:
            dialog.get_by_label("Vendor Name*").fill(name)
        if contact_person is not None:
            dialog.get_by_label("Contact Person").fill(contact_person)
        if phone is not None:
            dialog.get_by_label("Phone").fill(phone)
        if email is not None:
            dialog.get_by_label("Email").fill(email)
        if address is not None:
            dialog.get_by_label("Address").fill(address)
        if gst is not None:
            dialog.get_by_label("GST Number").fill(gst)
        if supports_amc:
            logger.debug("Checking 'Supports AMC' option")
            dialog.get_by_text("Supports AMC").click()
        if toggle_spans:
            logger.debug(f"Toggling vendor option spans: {toggle_spans}")
            for idx in toggle_spans:
                dialog.locator("span").nth(idx).click()


    def click_create(self):
        self.click(self.CREATE_BTN)

    def click_update(self):
        self.click(self.UPDATE_BTN)

    def edit_category(self, category_name: str):
        logger.debug(f"Editing category: {category_name}")
        search_input = self.page.get_by_placeholder("Search", exact=False)
        if search_input.is_visible():
            search_input.fill(category_name)
            self.page.wait_for_timeout(500)
        # 1. Click Edit
        row_locator = f"role=row[name*='{category_name}']"
        self.page.locator(row_locator).first.get_by_label(re.compile(r"edit", re.IGNORECASE)).click()
        # 2. Wait dialog visible
        dialog = self.page.locator("[role='dialog']")
        dialog.wait_for(state="visible", timeout=10000)
        # 3. Verify dialog title
        header = dialog.locator(".chakra-modal__header, header").first
        if header.is_visible():
            logger.debug(f"Dialog title verified: '{header.inner_text().strip()}'")
        # 4. Verify first field visible
        dialog.locator("input[placeholder*='e.g. Hardware'], input[type='text']").first.wait_for(state="visible", timeout=5000)
        # 5. Return
        return

    def edit_sub_category(self, category_name: str, sub_category_name: str, code_prefix: str):
        logger.debug(f"Editing subcategory: {category_name} -> {sub_category_name} ({code_prefix})")
        search_input = self.page.get_by_placeholder("Search", exact=False)
        if search_input.is_visible():
            search_input.fill(sub_category_name)
            self.page.wait_for_timeout(500)
        # 1. Click Edit
        row_locator = f"role=row[name*='{category_name}'][name*='{sub_category_name}'][name*='{code_prefix}']"
        self.page.locator(row_locator).first.get_by_label(re.compile(r"edit", re.IGNORECASE)).click()
        # 2. Wait dialog visible
        dialog = self.page.locator("[role='dialog']")
        dialog.wait_for(state="visible", timeout=10000)
        # 3. Verify dialog title
        header = dialog.locator(".chakra-modal__header, header").first
        if header.is_visible():
            logger.debug(f"Dialog title verified: '{header.inner_text().strip()}'")
        # 4. Verify first field visible
        dialog.locator("select, input").first.wait_for(state="visible", timeout=5000)
        # 5. Return
        return

    def edit_vendor(self, vendor_name: str):
        logger.debug(f"Editing vendor: {vendor_name}")
        search_input = self.page.get_by_placeholder("Search", exact=False)
        if search_input.is_visible():
            search_input.fill(vendor_name)
            self.page.wait_for_timeout(500)
        # 1. Click Edit
        row_locator = f"role=row[name*='{vendor_name}']"
        self.page.locator(row_locator).first.get_by_label(re.compile(r"edit", re.IGNORECASE)).click()
        # 2. Wait dialog visible
        dialog = self.page.locator("[role='dialog']")
        dialog.wait_for(state="visible", timeout=10000)
        # 3. Verify dialog title
        header = dialog.locator(".chakra-modal__header, header").first
        if header.is_visible():
            logger.debug(f"Dialog title verified: '{header.inner_text().strip()}'")
        # 4. Verify first field visible
        dialog.locator("input").first.wait_for(state="visible", timeout=5000)
        # 5. Return
        return




    def get_validation_messages(self) -> dict[str, str]:
        """Discovers and returns all field-level validation error messages displayed in the current form/dialog."""
        return self.get_all_validation_messages()

    def get_field_validation_message(self, field_label_or_locator: str) -> str:
        """Returns the specific field-level validation error text displayed below a form control."""
        return self.get_field_validation(field_label_or_locator)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)

    def set_category_inactive(self, category_name: str):
        """Edit a category and toggle its Active status to Inactive."""
        logger.debug(f"Setting category inactive: {category_name}")
        self.edit_category(category_name)
        dialog = self.page.locator("[role='dialog']").first
        dialog.wait_for(state="visible")
        active_toggle = dialog.locator("span").nth(1)
        active_toggle.wait_for(state="visible")
        active_toggle.click()

    def verify_category_not_in_dropdown(self, category_name: str):
        """Assert that category_name does NOT appear in the Category select dropdown in Add Sub Category dialog."""
        logger.debug(f"Verifying '{category_name}' is absent from Sub Category dropdown")
        dialog = self.page.locator("[role='dialog']").first
        dropdown = dialog.get_by_label("Category*")
        dropdown.wait_for(state="visible")
        options = dropdown.locator("option").all_inner_texts()
        logger.debug(f"Dropdown options: {options}")
        assert category_name not in options, f"Inactive category '{category_name}' is still selectable in Sub Category form!"

    def close_modal(self):
        """Close the currently open dialog modal."""
        logger.debug("Closing open modal")
        self._ensure_modal_closed()

    def get_existing_categories(self) -> list[str]:
        """Reads and returns all Category names currently displayed in the Categories grid table."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=4000)
        except Exception:
            pass
        rows = self.page.locator("tbody tr").all()
        categories = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) > 1:
                cat_name = cells[1].inner_text().strip()
                if cat_name and cat_name not in categories:
                    categories.append(cat_name)
        logger.debug(f"Retrieved existing categories from grid: {categories}")
        return categories

    def get_existing_sub_categories(self) -> list[str]:
        """Reads and returns all Sub-Category names currently displayed in the Sub Categories grid table."""
        self.navigate_to_sub_categories()
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=4000)
        except Exception:
            pass
        rows = self.page.locator("tbody tr").all()
        sub_categories = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) > 2:
                sub_name = cells[2].inner_text().strip()
                if sub_name and sub_name not in sub_categories:
                    sub_categories.append(sub_name)
        logger.debug(f"Retrieved existing sub-categories from grid: {sub_categories}")
        return sub_categories

    def ensure_category_exists(self, name: str = "Hardware", description: str = "Hardware Category") -> str:
        """
        Ensures a single unique Category record exists.
        If already present in Asset Master, reuses the single existing Category record instead of creating duplicates.
        """
        self.navigate_to_asset_master()
        existing = self.get_existing_categories()
        for cat in existing:
            if cat.lower() == name.lower() or name.lower() in cat.lower():
                logger.info(f"Category '{cat}' already exists — reusing single Category record.")
                return cat

        logger.info(f"Category '{name}' not found — creating single Category record.")
        self.click_add_category()
        self.fill_category_details(name=name, description=description, toggle_spans=False)
        self.click_create()
        self.wait_for_toast_message()
        return name

    def ensure_sub_category_exists(self, category_name: str = "Hardware", sub_category_name: str = "Laptop", code_prefix: str = "LAP", description: str = "Sub-Category") -> str:
        """
        Ensures a Sub-Category record exists under a single parent Category record.
        Prevents duplicate category and sub-category entries.
        """
        parent_cat = self.ensure_category_exists(category_name)
        existing_sub = self.get_existing_sub_categories()
        for sub in existing_sub:
            if sub.lower() == sub_category_name.lower():
                logger.info(f"Sub-Category '{sub}' already exists under parent Category '{parent_cat}' — reusing single record.")
                return sub

        logger.info(f"Creating Sub-Category '{sub_category_name}' under single parent Category '{parent_cat}'.")
        self.click_add_sub_category()
        self.fill_sub_category_details(
            category_label=parent_cat,
            name=sub_category_name,
            code_prefix=code_prefix,
            description=description
        )
        self.click_create()
        self.wait_for_toast_message()
        return sub_category_name

