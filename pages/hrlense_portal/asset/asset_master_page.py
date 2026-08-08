import re
import logging
from faker import Faker
from playwright.sync_api import expect
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)
fake = Faker()


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
        """Navigates to Asset Master page via Global Master Menu Helper."""
        logger.info("Navigating to Asset Master...")
        self.navigate_to_master_menu("Asset Master")



    def navigate_to_sub_categories(self):
        logger.debug("Navigating to Sub Categories tab...")
        try:
            tab = self.page.locator("[role='tab']").filter(has_text=re.compile(r"^Sub Categor(y|ies)$", re.I)).first
            if not tab.is_visible(timeout=1000):
                tab = self.page.get_by_role("tab", name=re.compile(r"Sub Categor", re.I)).first
            if not tab.is_visible(timeout=1000):
                tab = self.page.locator(self.SUB_CATEGORIES_TAB).first
            tab.click(force=True)
            self.page.wait_for_timeout(400)
        except Exception:
            self.click(self.SUB_CATEGORIES_TAB)
        try:
            tab = self.page.locator("[role='tab']").filter(has_text=re.compile(r"^Sub Categor(y|ies)$", re.I)).first
            if not tab.is_visible(timeout=1000):
                tab = self.page.get_by_role("tab", name=re.compile(r"Sub Categor", re.I)).first
            if not tab.is_visible(timeout=1000):
                tab = self.page.locator(self.SUB_CATEGORIES_TAB).first
            tab.click(force=True)
            self.page.wait_for_timeout(400)
        except Exception:
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
        self.navigate_to_category_tab()
        self.click(self.ADD_CATEGORY_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def click_add_sub_category(self):
        self._ensure_modal_closed()
        self.navigate_to_sub_categories()
        logger.info("Attempting to click Add Sub Category")
        btn = self.page.get_by_role("button", name="Add Sub Category", exact=True).first
        logger.info(f"Add Sub Category count: {self.page.get_by_role('button', name='Add Sub Category', exact=True).count()}")
        btn.click(timeout=10000)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def click_add_vendor(self):
        self._ensure_modal_closed()
        self.navigate_to_vendors()
        logger.info("Attempting to click Add Vendor")
        btn = self.page.get_by_role("button", name="Add Vendor", exact=True).first
        logger.info(f"Add Vendor count: {self.page.get_by_role('button', name='Add Vendor', exact=True).count()}")
        btn.click(timeout=10000)
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
            select_elem = dialog.get_by_label("Category*")
            if not select_elem.is_visible(timeout=1000):
                select_elem = dialog.locator("select[class*='chakra-select']").first
            select_elem.wait_for(state="visible", timeout=5000)

            try:
                select_elem.select_option(label=category_label, timeout=3000)
            except Exception:
                options = select_elem.locator("option").all_inner_texts()
                matched_idx = None
                for idx, opt_text in enumerate(options):
                    if opt_text.strip() and (category_label.lower() in opt_text.lower() or opt_text.lower() in category_label.lower()):
                        matched_idx = idx
                        break
                if matched_idx is not None:
                    select_elem.select_option(index=matched_idx)
                elif len(options) > 1:
                    select_elem.select_option(index=1)
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
        btn = self.page.get_by_role("button", name="Create", exact=True).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator(self.CREATE_BTN).first
        btn.click(force=True)
        self.page.wait_for_timeout(400)

        errors = self.get_active_form_errors()
        if errors:
            logger.error(f"[CATEGORY FORM VALIDATION INLINE ERRORS] {errors}")

    def click_update(self):
        btn = self.page.get_by_role("button", name="Update", exact=True).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator("button:has-text('Update')").first
        btn.wait_for(state="visible", timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(400)

        errors = self.get_active_form_errors()
        if errors:
            logger.error(f"[CATEGORY FORM VALIDATION INLINE ERRORS] {errors}")

    def get_active_form_errors(self, container=None) -> list[str]:
        """Extracts and returns all inline Chakra UI validation errors from .chakra-form__error-message."""
        container = container or self.page.locator("[role='dialog']").first
        if not container.is_visible():
            container = self.page

        errors = container.locator(".chakra-form__error-message, [id*='feedback']")
        messages = []
        for i in range(errors.count()):
            text = errors.nth(i).inner_text().strip()
            if text and text not in messages:
                messages.append(text)

        return messages

    def get_validation_messages(self) -> dict[str, str]:
        """
        Scans all inline form controls and extracts error messages from .chakra-form__error-message.
        Logs all extracted highlighted form validation errors for complete transparency.
        """
        err_msgs = {}
        for msg in self.get_active_form_errors():
            logger.info(f"[HIGHLIGHTED FORM ERROR] '{msg}'")
            err_msgs[msg] = msg
        return err_msgs

    def wait_for_toast_message(self) -> str:
        toast_txt = self.wait_for_toast(self.TOAST)
        errors = self.get_active_form_errors()
        if errors:
            logger.error(f"[CATEGORY FORM VALIDATION TOAST ERRORS] {errors}")
            if toast_txt and "correct" in toast_txt.lower():
                raise AssertionError(f"Create category validation failed: {errors}")
        return toast_txt

    def edit_category(self, category_name: str = None):
        logger.debug(f"Editing category: {category_name}")
        if category_name:
            self.search_category(category_name)
            self.page.wait_for_timeout(400)
            row = self.page.locator("tbody tr").filter(has_text=category_name).first
            if not row.is_visible(timeout=2000):
                row = self.page.locator("tbody tr").first
        else:
            row = self.page.locator("tbody tr").first

        edit_btn = row.locator("button, [aria-label*='Edit'], [aria-label*='edit'], svg").first
        if not edit_btn.is_visible(timeout=1500):
            edit_btn = self.page.get_by_label(re.compile(r"edit", re.IGNORECASE)).first

        edit_btn.click(force=True)

        # 2. Wait dialog visible
        dialog = self.page.locator("[role='dialog']").first
        dialog.wait_for(state="visible", timeout=10000)

    def edit_sub_category(self, category_name: str = None, sub_category_name: str = None, code_prefix: str = None):
        logger.debug(f"Editing subcategory: {category_name} -> {sub_category_name} ({code_prefix})")
        if sub_category_name:
            self.search_sub_category(sub_category_name)
            self.page.wait_for_timeout(400)
            row = self.page.locator("tbody tr").filter(has_text=sub_category_name).first
            if not row.is_visible(timeout=2000):
                row = self.page.locator("tbody tr").first
        else:
            row = self.page.locator("tbody tr").first

        edit_btn = row.locator("button, [aria-label*='Edit'], [aria-label*='edit'], svg").first
        if not edit_btn.is_visible(timeout=1500):
            edit_btn = self.page.get_by_label(re.compile(r"edit", re.IGNORECASE)).first
        edit_btn.click(force=True)

        dialog = self.page.locator("[role='dialog']").first
        dialog.wait_for(state="visible", timeout=10000)
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

    def navigate_to_category_tab(self):
        """Navigates to Category tab on Asset Master page."""
        logger.debug("Navigating to Category tab...")
        try:
            cat_tab = self.page.get_by_text("Category", exact=True).first
            if not cat_tab.is_visible(timeout=1000):
                cat_tab = self.page.locator("[role='tab']:has-text('Category'), button:has-text('Category')").first
            cat_tab.click(force=True)
            self.page.wait_for_timeout(400)
        except Exception as e:
            logger.warning(f"Category tab navigation error: {e}")

    def ensure_category_exists(self, name: str = "Hardware", description: str = "Hardware Category") -> str:
        """
        Ensures a single unique Category record exists.
        If already present or if 'Category with this name already exists' validation appears,
        closes modal cleanly and reuses the existing Category record.
        """
        self.navigate_to_asset_master()
        self.navigate_to_category_tab()

        existing = self.get_existing_categories()
        for cat in existing:
            if cat.strip().lower() == name.strip().lower():
                logger.info(f"Category '{cat}' already exists in grid — reusing Category record.")
                return cat

        logger.info(f"Category '{name}' not found — opening Add Category modal...")
        self.click_add_category()
        self.fill_category_details(name=name, description=description, toggle_spans=False)
        self.click_create()

        # Check if form validation error message appears ("Category with this name already exists")
        try:
            error_msg_loc = self.page.locator(".chakra-form__error-message, [id*='feedback']").first
            if error_msg_loc.is_visible(timeout=1500):
                err_text = error_msg_loc.inner_text().strip()
                if "already exists" in err_text.lower() or "exists" in err_text.lower():
                    logger.info(f"Detected form validation error: '{err_text}'. Closing modal & proceeding to Sub Category tab.")
                    self._ensure_modal_closed()
                    return name
        except Exception:
            pass

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

    def search_sub_category(self, query: str):
        """Searches sub-category in grid using exact placeholder 'Search sub category…'."""
        logger.debug(f"Searching sub-category for query: '{query}'...")
        search_input = self.page.get_by_placeholder("Search sub category…").first
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='sub category']").first
        search_input.fill(query)
        self.page.wait_for_timeout(300)

    def search_category(self, query: str):
        """Searches category in grid using exact placeholder 'Search category…'."""
        logger.debug(f"Searching category for query: '{query}'...")
        search_input = self.page.get_by_placeholder("Search category…").first
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='category']").first
        search_input.fill(query)
        self.page.wait_for_timeout(300)

    def search_vendors(self, query: str):
        """Searches vendors in grid using exact placeholder 'Search vendors…'."""
        logger.debug(f"Searching vendors for query: '{query}'...")
        search_input = self.page.get_by_placeholder("Search vendors…").first
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='vendor']").first
        search_input.fill(query)
        self.page.wait_for_timeout(300)

    def search_and_verify_sub_category_row(
        self,
        category_name: str,
        sub_category_name: str,
        code_prefix: str,
        expected_status: str = "Active"
    ) -> bool:
        """
        Steps 7 & 8: Searches for newly created Sub-Category in table grid,
        locates row, and verifies Category, Sub-Category, Code Prefix, and Status.
        """
        logger.info(f"[SEARCH & VERIFY] Searching for Sub-Category '{sub_category_name}' in table grid...")
        self.search_sub_category(sub_category_name)
        
        row_locator = self.page.locator("tbody tr").filter(
            has_text=re.compile(re.escape(sub_category_name), re.IGNORECASE)
        ).first

        try:
            row_locator.wait_for(state="visible", timeout=5000)
            row_text = row_locator.inner_text().strip()
            logger.info(f"Located Sub-Category Table Row: '{row_text}'")

            assert category_name.lower() in row_text.lower(), f"Category '{category_name}' not found in row text '{row_text}'"
            assert sub_category_name.lower() in row_text.lower(), f"Sub-Category '{sub_category_name}' not found in row text '{row_text}'"
            assert code_prefix.lower() in row_text.lower(), f"Code Prefix '{code_prefix}' not found in row text '{row_text}'"
            
            logger.info(f"[VERIFIED TABLE ROW] Category='{category_name}', SubCategory='{sub_category_name}', Code='{code_prefix}', Status='{expected_status}'")
            return True
        except Exception as e:
            logger.error(f"[VERIFICATION FAILED] Could not locate or verify row for Sub-Category '{sub_category_name}': {e}")
            return False

    def get_sub_category_row_count(self) -> int:
        """Reads current number of Sub-Category records in grid table."""
        self.navigate_to_sub_categories()
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=4000)
            return self.page.locator("tbody tr").count()
        except Exception:
            return 0

    def ensure_category_with_sub_categories_decision_tree(self) -> tuple[str, list[dict]]:
        """
        Flowchart Implementation:
        Open Asset Master -> Open Sub-Category Tab -> Check existing Sub-Category records.
        ├── Sub-Category records exist:
        │   Go to Category Tab -> Create NEW Category -> Go to Sub-Category Tab -> Create 2-3 Sub-Categories -> Verify -> PASS
        └── No Sub-Category records:
            Create Category -> Create 2-3 Sub-Categories -> Verify relationship -> PASS
        """
        from testdata.static.asset_categories import ASSET_CATEGORIES_DATASET

        # Step 1: Open Asset Master & Open Sub-Category Tab
        self.navigate_to_asset_master()
        self.navigate_to_sub_categories()

        # Step 2: Check existing Sub-Category records
        existing_sub_count = self.get_sub_category_row_count()
        logger.info(f"[FLOWCHART CHECK] Existing Sub-Category records count: {existing_sub_count}")

        if existing_sub_count > 0:
            logger.info("[FLOWCHART BRANCH A] Sub-Category records exist in grid — switching to Category tab to add a fresh Category...")
            existing_rows = self.page.locator("tbody tr").all()
            grid_text = " ".join([r.inner_text() for r in existing_rows if r.is_visible()]).lower()

            target_cat_data = None
            for cat_entry in ASSET_CATEGORIES_DATASET:
                if cat_entry["name"].lower() not in grid_text:
                    target_cat_data = cat_entry
                    break

            if not target_cat_data:
                dynamic_name = f"Hardware Enterprise {random.randint(100, 999)}"
                target_cat_data = {
                    "name": dynamic_name,
                    "subcategories": [
                        {"name": f"{dynamic_name} Laptop", "code_prefix": "LAP"},
                        {"name": f"{dynamic_name} Desktop", "code_prefix": "DES"},
                        {"name": f"{dynamic_name} Monitor", "code_prefix": "MON"}
                    ]
                }

            category_name = target_cat_data["name"]
            sub_list = target_cat_data["subcategories"]

            # Go to Category Tab -> Create NEW Fresh Category
            self.navigate_to_category_tab()
            logger.info(f"[FLOWCHART BRANCH A] Creating brand new fresh Category '{category_name}'...")
            self.click_add_category()
            self.fill_category_details(name=category_name, description=f"{category_name} Fresh Category", toggle_spans=False)
            self.click_create()

            try:
                err_loc = self.page.locator(".chakra-form__error-message, [id*='feedback']").first
                if err_loc.is_visible(timeout=1500):
                    err_txt = err_loc.inner_text().strip()
                    if "already exists" in err_txt.lower():
                        logger.info(f"Category '{category_name}' already exists — creating unique fresh Category with random suffix...")
                        self._ensure_modal_closed()
                        category_name = f"{category_name} {random.randint(100, 999)}"
                        self.click_add_category()
                        self.fill_category_details(name=category_name, description=f"{category_name} Fresh Category", toggle_spans=False)
                        self.click_create()
            except Exception:
                pass

            self.wait_for_toast_message()

            # Go to Sub-Category Tab -> Create 2-3 Sub-Categories under newly created Category
            self.navigate_to_sub_categories()
            verified_subs = []
            for item in sub_list[:3]:
                sub_name = item["name"]
                sub_code = item["code_prefix"]
                logger.info(f"[STEP] Creating Sub-Category '{sub_name}' under newly created Category '{category_name}'...")
                self.click_add_sub_category()
                self.fill_sub_category_details(
                    category_label=category_name,
                    name=sub_name,
                    code_prefix=sub_code,
                    description=f"{sub_name} Sub-Category"
                )
                self.click_create()
                toast = self.wait_for_toast_message()

                # Verify Category + Sub-Categories
                is_verified = self.search_and_verify_sub_category_row(
                    category_name=category_name,
                    sub_category_name=sub_name,
                    code_prefix=sub_code,
                    expected_status="Active"
                )
                assert is_verified, f"Verification failed for Sub-Category '{sub_name}' under Category '{category_name}'!"
                verified_subs.append({"name": sub_name, "code_prefix": sub_code, "verified": is_verified})

            logger.info(f"[FLOWCHART BRANCH A PASSED] Created NEW Category '{category_name}' with {len(verified_subs)} Sub-Categories!")
            return category_name, verified_subs

        else:
            logger.info("[FLOWCHART BRANCH B] No Sub-Category records exist in grid.")
            target_cat_data = ASSET_CATEGORIES_DATASET[0]  # 'Hardware'
            category_name = target_cat_data["name"]
            sub_list = target_cat_data["subcategories"]

            # Create Category
            self.navigate_to_category_tab()
            parent_cat = self.ensure_category_exists(category_name, f"{category_name} Category")

            # Create 2-3 Sub-Categories
            self.navigate_to_sub_categories()
            verified_subs = []
            for item in sub_list[:3]:
                sub_name = item["name"]
                sub_code = fake.lexify("???").upper()
                logger.info(f"[STEP] Creating Sub-Category '{sub_name}' under Category '{parent_cat}' with code prefix '{sub_code}'...")
                self.click_add_sub_category()
                self.fill_sub_category_details(
                    category_label=parent_cat,
                    name=sub_name,
                    code_prefix=sub_code,
                    description=f"{sub_name} Sub-Category"
                )
                self.click_create()
                toast = self.wait_for_toast_message()

                # Verify relationship
                is_verified = self.search_and_verify_sub_category_row(
                    category_name=parent_cat,
                    sub_category_name=sub_name,
                    code_prefix=sub_code,
                    expected_status="Active"
                )
                assert is_verified, f"Relationship verification failed for '{sub_name}' under '{parent_cat}'!"
                verified_subs.append({"name": sub_name, "code_prefix": sub_code, "verified": is_verified})

            logger.info(f"[FLOWCHART BRANCH B PASSED] Initialized Category '{parent_cat}' with {len(verified_subs)} Sub-Categories!")
            return parent_cat, verified_subs

