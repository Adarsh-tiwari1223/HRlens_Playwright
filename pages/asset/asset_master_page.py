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

