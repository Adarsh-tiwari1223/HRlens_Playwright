import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetAssignmentPage(BasePage):
    ASSIGN_ASSET_BTN = "role=button[name='Assign Asset']"
    SUBMIT_ASSIGNMENT_BTN = "role=button[name='Assign Asset']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_assignment(self):
        """Navigates to the Asset Assignment page."""
        logger.info("Navigating to Asset Assignment page")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(f"{settings.BASE_URL}/asset-assignment", timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")

    def click_assign_asset(self):
        """Clicks 'Assign Asset' button to open direct assignment modal."""
        btn = self.page.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").first
        if not btn.is_visible(timeout=3000):
            btn = self.page.get_by_role("button", name="Assign Asset").first

        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        modal = self.page.locator(".chakra-modal__content, .chakra-drawer__content, [role='dialog']").first
        modal.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)

    def fill_assignment_details(self, employee_name: str, category: str, sub_category: str, asset_name_or_code: str = None, expected_return_date: str = None, remarks: str = None) -> dict:
        logger.info(f"Filling assignment details: Employee={employee_name}, Category={category}, SubCategory={sub_category}")
        
        # 1. Employee Search input
        emp_search = self.page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = self.page.locator("input[placeholder*='Search employee']").first
        emp_search.fill(employee_name)
        self.page.wait_for_timeout(1000)

        # Select first matching result from suggestion popover/portal
        try:
            opt = self.page.locator(
                ".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list"
            ).get_by_text(employee_name, exact=False).first
            if opt.is_visible(timeout=1500):
                opt.click(force=True)
            else:
                fallback = self.page.locator(".chakra-portal div, [role='option'], p, li").filter(
                    has_text=re.compile(employee_name.split()[0], re.I)
                ).first
                if fallback.is_visible(timeout=1500):
                    fallback.click(force=True)
                else:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
        except Exception as ex:
            logger.warning(f"Note selecting employee '{employee_name}': {ex}")
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")

        
        # Category dropdown
        cat_select = self.page.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = self.page.locator("select").first

        cat_options = [o.strip() for o in cat_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
        target_cat = category if category and any(category.lower() in o.lower() for o in cat_options) else (cat_options[0] if cat_options else None)

        def _select_cat(cat_name):
            if not cat_name:
                return
            try:
                cat_select.select_option(label=cat_name)
            except Exception:
                for idx, opt in enumerate(cat_select.locator("option").all_inner_texts()):
                    if cat_name.lower() in opt.lower():
                        cat_select.select_option(index=idx)
                        break
            self.page.wait_for_timeout(800)

        _select_cat(target_cat)
        
        # Sub Category dropdown
        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        if not modal.is_visible(timeout=1000):
            modal = self.page

        sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.get_by_label("Sub Category*", exact=True).first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.locator("select").nth(1)

        def _try_select_asset(sub_name):
            try:
                sub_select.select_option(label=sub_name, timeout=1500)
            except Exception:
                try:
                    options = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip()]
                    for idx, opt in enumerate(options):
                        if any(part.lower() in opt.lower() for part in sub_name.lower().split() if len(part) > 3) or sub_name.lower() in opt.lower():
                            sub_select.select_option(index=idx, timeout=1500)
                            break
                except Exception as e:
                    logger.warning(f"Subcategory option select note: {e}")
            self.page.wait_for_timeout(800)

            trigger = modal.locator(".chakra-menu__menubutton, button").filter(has_text=re.compile(r"Select asset|Select|Available|ASSET", re.I)).first
            if not trigger.is_visible(timeout=2000):
                trigger = modal.locator(".chakra-menu__menubutton").first

            if trigger.is_visible(timeout=2000):
                trigger.click(force=True)
                self.page.wait_for_timeout(500)

                # Optional search box inside dropdown popover
                if asset_name_or_code:
                    try:
                        search_box = self.page.get_by_placeholder("Search...").first
                        if not search_box.is_visible(timeout=1000):
                            search_box = self.page.locator(".chakra-portal input[placeholder*='Search' i], div.chakra-menu__menu-list input").first
                        if search_box.is_visible(timeout=1000):
                            search_box.fill(asset_name_or_code)
                            self.page.wait_for_timeout(300)
                    except Exception as e:
                        logger.warning(f"Dropdown search box note: {e}")

                menu = self.page.locator(".chakra-portal div[role='menu'], div.chakra-menu__menu-list, [role='menu']").first
                items = menu.locator("[role='menuitem'], [role='menuitemcheckbox'], [role='option'], button").all() if menu.is_visible(timeout=2000) else self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()

                valid_items = [itm for itm in items if "not uploaded" not in itm.inner_text().lower() and len(itm.inner_text().strip()) > 0]
                if valid_items:
                    target_itm = None
                    if asset_name_or_code:
                        for itm in valid_items:
                            if asset_name_or_code.lower() in itm.inner_text().lower():
                                target_itm = itm
                                break
                    if not target_itm:
                        target_itm = valid_items[0]

                    text = target_itm.inner_text().strip()
                    m = re.search(r"ASSET-[A-Z0-9-]+", text)
                    code = m.group(0) if m else text
                    target_itm.click(force=True)
                    logger.info(f"[DROPDOWN ASSET SELECTED SUCCESS] SubCategory: '{sub_name}', Item: '{text}' -> Code: '{code}'")
                    return code
                else:
                    self.page.keyboard.press("Escape")
            return None

        # Try initial subcategory or iterate available subcategories
        selected_code = None
        sub_options = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
        target_sub = sub_category if sub_category and any(sub_category.lower() in o.lower() or o.lower() in sub_category.lower() for o in sub_options) else (sub_options[0] if sub_options else None)

        if target_sub:
            selected_code = _try_select_asset(target_sub)

        # Fast fallback to other available subcategories under target category if asset_name_or_code not strictly required
        if not selected_code and not asset_name_or_code and sub_options:
            for alt_sub in sub_options:
                if alt_sub != target_sub:
                    selected_code = _try_select_asset(alt_sub)
                    if selected_code:
                        break

        # Fast fallback across other categories if not strictly looking for specific asset_name_or_code
        if not selected_code and not asset_name_or_code and cat_options:
            for alt_cat in cat_options:
                if alt_cat != target_cat:
                    _select_cat(alt_cat)
                    alt_subs = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
                    for alt_s in alt_subs:
                        selected_code = _try_select_asset(alt_s)
                        if selected_code:
                            break
                    if selected_code:
                        break

        assert selected_code, f"[ASSIGNMENT FAILED] Could not select an available asset from dropdown for '{employee_name}'! Ensure available stock exists in the branch."

        # Expected Return Date
        if expected_return_date:
            date_input = self.page.locator("[role='dialog'] input[type='date'], input[type='date']").first
            if not date_input.is_visible(timeout=1000):
                date_input = self.page.locator("input[placeholder*='date' i], input[name*='date' i]").first
            if date_input.is_visible(timeout=2000):
                date_input.fill(expected_return_date)
                logger.info(f"Filled Expected Return Date: '{expected_return_date}'")

        # Remarks
        if remarks:
            rem_input = self.page.locator("[role='dialog'] textarea, textarea, input[placeholder*='Assigned' i]").first
            if rem_input.is_visible(timeout=1000):
                rem_input.fill(remarks)
                logger.info(f"Filled Remarks: '{remarks}'")

        return selected_code or asset_name_or_code or "ASSET"

    def click_submit_assignment(self):
        """Submits the Direct Assignment form."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        if modal.is_visible(timeout=2000):
            btn = modal.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").last
        else:
            btn = self.page.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").last
        btn.click(force=True)
        try:
            self.page.locator(".chakra-spinner, span:has-text('Loading')").wait_for(state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def click_cancel(self):
        """Cancels and closes the assignment drawer/modal."""
        btn = self.page.locator("button:has-text('Cancel'), button[aria-label='Close'], .chakra-modal__close-btn").first
        if btn.is_visible(timeout=1000):
            btn.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def select_assignment_duration(self, duration_type: str = "Temporary"):
        """Selects Assignment Type duration: 'Permanent' or 'Temporary'."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        type_select = modal.locator("//div[./label[contains(text(), 'Assignment Type')]]//select").last
        if not type_select.is_visible(timeout=1500):
            type_select = modal.locator("select:has(option:has-text('Permanent'))").first
        if type_select.is_visible(timeout=2000):
            type_select.select_option(label=duration_type)
            logger.info(f"Selected Assignment Duration Type: '{duration_type}'")
            self.page.wait_for_timeout(500)
            return True
        logger.warning(f"Assignment Duration dropdown not found for '{duration_type}'")
        return False

    def get_form_error_messages(self) -> list[str]:
        """Retrieves visible inline error messages inside assignment drawer."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        if not modal.is_visible(timeout=1000):
            modal = self.page
        errors = modal.locator(".chakra-form__error-message, [role='alert'], .text-danger, span[class*='error']").all_inner_texts()
        return [e.strip() for e in errors if e.strip()]

    def verify_gating_restrictions(self) -> dict:
        """
        Audits whether Category, Sub Category, and Assets dropdowns are disabled
        before an Employee is selected (TC-AST-048).
        """
        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        cat_select = modal.locator("//div[./label[contains(text(), 'Category')]]//select").first
        if not cat_select.is_visible(timeout=1000):
            cat_select = modal.locator("select").first
        
        sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.locator("select").nth(1)

        cat_disabled = cat_select.is_disabled() if cat_select.is_visible(timeout=1000) else None
        sub_disabled = sub_select.is_disabled() if sub_select.is_visible(timeout=1000) else None

        return {
            "category_disabled": cat_disabled,
            "subcategory_disabled": sub_disabled,
            "gated": bool(cat_disabled and sub_disabled)
        }

    def open_fulfillment_drawer(self, employee_name: str = None):
        """
        Switches to Requested Assignment tab, optionally searches for employee, and clicks Fulfil to open the assignment drawer.
        Returns the drawer locator or None.
        """
        logger.info(f"Opening fulfillment drawer for employee request: '{employee_name or 'ANY PENDING'}'")
        # 1. Switch to Requested Assignment tab
        req_tab = self.page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not req_tab.is_visible(timeout=2000):
            req_tab = self.page.locator("[role='tab']").nth(1)
        req_tab.click(force=True)
        self.page.wait_for_timeout(1000)

        # 2. Search employee if specified
        if employee_name:
            search_in = self.page.locator("input[placeholder*='Search' i]").first
            if search_in.is_visible(timeout=2000):
                search_in.fill("")
                search_in.fill(employee_name)
                search_in.press("Enter")
                self.page.wait_for_timeout(1000)

        # Wait for table spinner to disappear
        try:
            spinner = self.page.locator(".chakra-spinner, [class*='spinner'], [role='progressbar']").first
            if spinner.is_visible(timeout=1000):
                spinner.wait_for(state="hidden", timeout=10000)
        except Exception:
            pass

        # Wait for table rows to be present
        try:
            self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        # 3. Locate pending row with Fulfil button
        if employee_name:
            emp_first_name = employee_name.split()[0]
            row = self.page.locator("table tbody tr").filter(has_text=re.compile(re.escape(emp_first_name), re.I)).filter(has=self.page.locator("button").filter(has_text=re.compile(r"Fulfil|Assign", re.I))).first
            if not row.is_visible(timeout=2000):
                row = self.page.locator("table tbody tr").filter(has_text=re.compile(re.escape(emp_first_name), re.I)).first
        else:
            row = self.page.locator("table tbody tr").filter(has=self.page.locator("button").filter(has_text=re.compile(r"Fulfil|Assign", re.I))).first

        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").filter(has_text=re.compile(r"PENDING", re.I)).filter(has=self.page.locator("button").filter(has_text=re.compile(r"Fulfil|Assign", re.I))).first

        fulfil_btn = row.locator("button").filter(has_text=re.compile(r"Fulfil|Assign", re.I)).first
        if not fulfil_btn.is_visible(timeout=3000):
            logger.warning(f"No 'Fulfil' button found on row for '{employee_name}'.")
            return None

        fulfil_btn.click()
        drawer = self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        drawer.wait_for(state="visible", timeout=10000)
        return drawer

    def get_fulfillment_available_assets(self, drawer=None) -> list[str]:
        """Extracts all available asset codes listed in the Requested Assignment fulfillment drawer dropdown."""
        form = drawer or self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        trigger = form.locator("button.chakra-menu__menu-button").first
        if not trigger.is_visible(timeout=2000):
            trigger = form.locator(".chakra-menu__menubutton, button").filter(
                has_text=re.compile(r"Select assets to assign|Select asset|Select|Available|ASSET", re.I)
            ).first
        if not trigger.is_visible(timeout=3000):
            logger.warning("Fulfillment asset dropdown trigger button not found.")
            return []

        try:
            trigger.click(force=True)
            self.page.wait_for_timeout(600)
            menu_list = form.locator(".chakra-menu__menu-list, [role='menu']").first
            if not menu_list.is_visible(timeout=1000):
                menu_list = self.page.locator(".chakra-menu__menu-list, [role='menu']").last
            labels = menu_list.locator("span.chakra-checkbox__label, label.chakra-checkbox").all()
            codes = []
            for lbl in labels:
                txt = lbl.inner_text().strip()
                if "not uploaded" in txt.lower() or not txt:
                    continue
                m = re.search(r"ASSET-[A-Z0-9-]+", txt)
                code = m.group(0) if m else txt.split("—")[0].strip()
                if code and code not in codes:
                    codes.append(code)
            # Safely re-click trigger to close dropdown without triggering modal Escape key listener
            try:
                trigger.click(force=True)
            except Exception:
                pass
            self.page.wait_for_timeout(300)
            return codes
        except Exception as ex:
            logger.warning(f"Error extracting fulfillment available assets: {ex}")
            try:
                trigger.click(force=True)
            except Exception:
                pass
            return []

    def get_fulfillment_available_asset_items(self, drawer=None) -> list[dict]:
        """Extracts all available asset items (name, code, full_text) listed in the Requested Assignment fulfillment drawer dropdown."""
        form = drawer or self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        trigger = form.locator(".chakra-menu__menubutton, button").filter(
            has_text=re.compile(r"Select assets to assign|Select asset|Select|Available|ASSET", re.I)
        ).first
        if not trigger.is_visible(timeout=3000):
            logger.warning("Fulfillment asset dropdown trigger button not found.")
            return []

        try:
            trigger.click(force=True)
            self.page.wait_for_timeout(600)
            items = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            assets = []
            for itm in items:
                txt = itm.inner_text().strip()
                if "not uploaded" in txt.lower() or not txt:
                    continue
                m = re.search(r"ASSET-[A-Z0-9-]+", txt)
                code = m.group(0) if m else ""
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                name = lines[0] if lines else txt
                assets.append({"name": name, "code": code, "text": txt})
            # Safely re-click trigger to close dropdown without triggering modal Escape key listener
            try:
                trigger.click(force=True)
            except Exception:
                pass
            self.page.wait_for_timeout(300)
            return assets
        except Exception as ex:
            logger.warning(f"Error extracting fulfillment available asset items: {ex}")
            try:
                trigger.click(force=True)
            except Exception:
                pass
            return []

    def get_direct_assignment_available_assets(self, employee_name: str, category: str = None, sub_category: str = None) -> list[dict]:
        """
        Opens Direct Assignment modal, selects employee, category, subcategory,
        and extracts all asset items from the Asset dropdown without submitting.
        """
        self.click_assign_asset()
        modal = self.page.locator(".chakra-modal__content, .chakra-drawer__content, [role='dialog']").first
        modal.wait_for(state="visible", timeout=10000)

        # 1. Search employee
        emp_search = self.page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = self.page.locator("input[placeholder*='Search employee']").first
        emp_search.fill(employee_name)
        self.page.wait_for_timeout(1000)

        # Select first matching result
        opt = self.page.locator(
            ".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list"
        ).get_by_text(employee_name, exact=False).first
        if opt.is_visible(timeout=1500):
            opt.click(force=True)
        else:
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(800)

        # 2. Category
        cat_select = modal.get_by_label("Category*", exact=True)
        if not cat_select.is_visible(timeout=1000):
            cat_select = modal.locator("select").first
        cat_options = [o.strip() for o in cat_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
        target_cat = category if category and any(category.lower() in o.lower() for o in cat_options) else (cat_options[0] if cat_options else None)
        if target_cat:
            cat_select.select_option(label=target_cat)
            self.page.wait_for_timeout(800)

        # 3. Sub Category
        sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.get_by_label("Sub Category*", exact=True).first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.locator("select").nth(1)
        sub_options = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
        target_sub = sub_category if sub_category and any(sub_category.lower() in o.lower() for o in sub_options) else (sub_options[0] if sub_options else None)
        if target_sub:
            sub_select.select_option(label=target_sub)
            self.page.wait_for_timeout(800)

        # 4. Open Asset Dropdown
        trigger = modal.locator(".chakra-menu__menubutton, button").filter(has_text=re.compile(r"Select asset|Select|Available|ASSET", re.I)).first
        if not trigger.is_visible(timeout=2000):
            trigger = modal.locator(".chakra-menu__menubutton").first
        
        assets = []
        if trigger.is_visible(timeout=2000):
            trigger.click(force=True)
            self.page.wait_for_timeout(600)
            items = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            for itm in items:
                txt = itm.inner_text().strip()
                if "not uploaded" in txt.lower() or not txt:
                    continue
                m = re.search(r"ASSET-[A-Z0-9-]+", txt)
                code = m.group(0) if m else ""
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                name = lines[0] if lines else txt
                assets.append({"name": name, "code": code, "text": txt})
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)

        self.click_cancel()
        return assets

    def submit_open_fulfillment_drawer(self, drawer=None, asset_code: str = None, assignment_type: str = "Permanent", expected_return_date: str = "2026-12-31", remarks: str = None) -> dict:
        """Fulfills the currently open fulfillment drawer directly without re-navigating."""
        form = drawer or self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        
        # 1. Open Asset Dropdown
        asset_select_btn = form.locator("button.chakra-menu__menu-button").first
        if not asset_select_btn.is_visible(timeout=2000):
            asset_select_btn = form.locator(".chakra-menu__menubutton, button").filter(
                has_text=re.compile(r"Select assets to assign|Select asset|Select|Available|ASSET", re.I)
            ).first
        
        selected_code = None
        if asset_select_btn.is_visible(timeout=3000):
            asset_select_btn.click(force=True)
            self.page.wait_for_timeout(600)

            # Wait for menu list to appear
            menu_list = form.locator(".chakra-menu__menu-list, [role='menu']").first
            if not menu_list.is_visible(timeout=1000):
                menu_list = self.page.locator(".chakra-menu__menu-list, [role='menu']").last
            
            try:
                menu_list.wait_for(state="visible", timeout=3000)
            except Exception:
                pass

            # Search or directly locate checkbox
            if asset_code:
                search_box = menu_list.locator("input[placeholder*='Search']").first
                if search_box.is_visible(timeout=1000):
                    search_box.fill(asset_code)
                    self.page.wait_for_timeout(400)

            # Directly locate target checkbox label
            target_chk = None
            item_text = ""
            if asset_code:
                chk_loc = menu_list.locator("span.chakra-checkbox__label, label.chakra-checkbox").filter(
                    has_text=re.compile(re.escape(asset_code), re.I)
                ).first
                if chk_loc.is_visible(timeout=1500):
                    target_chk = chk_loc
                    item_text = chk_loc.inner_text().strip()

            if not target_chk:
                chk_loc = menu_list.locator("span.chakra-checkbox__label, label.chakra-checkbox").first
                if chk_loc.is_visible(timeout=1500):
                    target_chk = chk_loc
                    item_text = chk_loc.inner_text().strip()

            if target_chk:
                m = re.search(r"ASSET-[A-Z0-9-]+", item_text)
                selected_code = m.group(0) if m else item_text
                target_chk.click(force=True)
                self.page.wait_for_timeout(500)
                logger.info(f"[REQUESTED ASSET SELECTED] Item: '{item_text}' -> Code: '{selected_code}'")

                # Close dropdown menu after selection by clicking trigger button again
                try:
                    asset_select_btn.click(force=True)
                    self.page.wait_for_timeout(400)
                except Exception:
                    pass
            else:
                logger.warning("No asset items found in dropdown menu!")
                try:
                    asset_select_btn.click(force=True)
                except Exception:
                    pass

        # 2. Assignment Type ('Permanent' vs 'Temporary')
        type_select = form.locator("select").first
        try:
            if type_select.is_visible(timeout=1000):
                opts = [o.get_attribute("value") for o in type_select.locator("option").all() if o.get_attribute("value")]
                if assignment_type in opts:
                    type_select.select_option(value=assignment_type)
                elif opts:
                    type_select.select_option(value=opts[0])
        except Exception as e:
            logger.warning(f"Type select note: {e}")

        # 3. Date (if Temporary and visible)
        if expected_return_date:
            try:
                date_in = form.locator("input[type='date']").first
                if date_in.is_visible(timeout=1000):
                    date_in.fill(expected_return_date)
            except Exception:
                pass

        # 4. Remarks (if visible)
        if remarks:
            try:
                rem_in = form.locator("textarea, input[placeholder*='remark' i]").first
                if rem_in.is_visible(timeout=1000):
                    rem_in.fill(remarks)
            except Exception:
                pass

        # 5. Submit: Click ' Assign Asset' button in modal footer
        submit_btn = form.locator("footer button, .chakra-modal__footer button").filter(
            has_text=re.compile(r"Assign Asset", re.I)
        ).first
        if not submit_btn.is_visible(timeout=2000):
            submit_btn = form.locator("button").filter(
                has_text=re.compile(r"Assign Asset|Assign|Fulfil|Submit", re.I)
            ).last
        
        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.click(force=True)

        toast = self.wait_for_toast_message() or ""
        logger.info(f"[FULFILLMENT SUBMITTED] Toast: '{toast}'")
        success = any(w in toast.lower() for w in ["success", "assigned", "fulfilled", "saved"]) or not form.is_visible(timeout=3000)
        return {"success": success, "toast": toast, "asset_code": selected_code}

    def assign_requested_asset(self, employee_name: str, asset_code: str = None, assignment_type: str = "Permanent", expected_return_date: str = "2026-12-31", remarks: str = "Asset issued against request") -> dict:
        """
        Fulfills an employee requested asset from the Requested Assignment tab:
        1. Switches to Requested Assignment tab.
        2. Filters table by employee name.
        3. Clicks 'Fulfil' button on matching row.
        4. Selects available asset & assignment type.
        5. Submits form and captures toast response.
        """
        logger.info(f"Fulfilling requested asset for employee: {employee_name}")

        # 1. Switch to Requested Assignment tab
        req_tab = self.page.get_by_role("tab", name=re.compile(r"Requested Assignment|Employee Requests", re.I)).first
        if not req_tab.is_visible(timeout=2000):
            req_tab = self.page.locator("[role='tab']").nth(1)
        req_tab.click(force=True)
        self.page.wait_for_timeout(1000)

        # 2. Search employee
        search_in = self.page.locator("input[placeholder*='Search' i]").first
        if search_in.is_visible(timeout=2000):
            search_in.fill("")
            search_in.fill(employee_name)
            search_in.press("Enter")
            self.page.wait_for_timeout(1000)

        # 3. Locate row & click Fulfil
        emp_first_name = employee_name.split()[0]
        row = self.page.locator("table tbody tr").filter(has_text=re.compile(re.escape(emp_first_name), re.I)).first
        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").first

        fulfil_btn = row.locator("button").filter(has_text=re.compile(r"Fulfil|Assign|Action", re.I)).first
        if not fulfil_btn.is_visible(timeout=2000):
            logger.warning(f"No 'Fulfil' button found on row for '{employee_name}'.")
            return {"success": False, "reason": "Fulfil button not visible", "asset_code": None, "toast": ""}

        fulfil_btn.click()
        self.page.wait_for_timeout(1000)

        # 4. In Drawer: Select asset
        form = self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        asset_select_btn = form.locator(".chakra-menu__menubutton, button").filter(has_text=re.compile(r"Select assets to assign|Select asset|Select|Available|ASSET", re.I)).first
        
        selected_code = None
        if asset_select_btn.is_visible(timeout=3000):
            asset_select_btn.click(force=True)
            self.page.wait_for_timeout(600)

            items_loc = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            if items_loc:
                target_item = items_loc[0]
                if asset_code:
                    for it in items_loc:
                        if asset_code.lower() in it.inner_text().lower():
                            target_item = it
                            break
                item_text = target_item.inner_text().strip()
                m = re.search(r"ASSET-[A-Z0-9-]+", item_text)
                selected_code = m.group(0) if m else item_text
                target_item.click(force=True)
                logger.info(f"[REQUESTED ASSET SELECTED] Item: '{item_text}' -> Code: '{selected_code}'")
            else:
                self.page.keyboard.press("Escape")

        # 5. Assignment Type ('Permanent' vs 'Temporary')
        type_select = form.locator("select").first
        if type_select.is_visible(timeout=1000):
            try:
                type_select.select_option(label=assignment_type)
            except Exception:
                type_select.select_option(value=assignment_type)

        if assignment_type.lower() == "temporary" and expected_return_date:
            date_in = form.locator("input[type='date']").first
            if date_in.is_visible(timeout=1000):
                date_in.fill(expected_return_date)

        # 6. Submit
        submit_btn = form.locator("button").filter(has_text=re.compile(r"^Assign Asset$|Assign|Submit", re.I)).last
        submit_btn.click(force=True)
        self.page.wait_for_timeout(500)
        toast = self.wait_for_toast_message()

        return {
            "success": True,
            "asset_code": selected_code,
            "toast": toast
        }

    def wait_for_toast_message(self) -> str:
        """Waits for and returns the text of any top-right Chakra toast."""
        return self.wait_for_toast(self.TOAST)
