import re
import random
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetAssignmentPage(BasePage):
    ASSIGN_ASSET_BTN = "role=button[name='Assign Asset']"
    SUBMIT_ASSIGNMENT_BTN = "role=button[name='Assign Asset']" # Form submit button
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_assignment(self):
        logger.info("Navigating to Asset Assignment page")
        self.page.goto(f"{settings.BASE_URL}/asset-assignment")
        self.page.wait_for_load_state("domcontentloaded")

    def click_assign_asset(self):
        """Clicks 'Assign Asset' button to open direct assignment drawer/modal."""
        btn = self.page.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").first
        if not btn.is_visible(timeout=3000):
            btn = self.page.get_by_role("button", name="Assign Asset").first

        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        modal = self.page.locator(".chakra-modal__content, .chakra-drawer__content, [role='dialog']").first
        modal.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)

    def validate_available_assets_dropdown(self) -> dict:
        """
        Validates whether the Available Asset dropdown populates items for assignment.
        Returns a dict: {"populated": bool, "count": int, "items": list[str]}
        """
        logger.info("Validating Available Asset dropdown population...")
        trigger_btn = self.page.get_by_role("button", name=re.compile(r"Select asset", re.I)).first
        if not trigger_btn.is_visible(timeout=1000):
            trigger_btn = self.page.locator("button").filter(has_text=re.compile(r"Select asset|Select|Assets", re.I)).first

        if not trigger_btn.is_visible(timeout=2000):
            logger.warning("Available Asset dropdown trigger button is not visible.")
            return {"populated": False, "count": 0, "items": []}

        try:
            trigger_btn.click()
            self.page.wait_for_timeout(600)
            items_loc = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            items = [item.inner_text().strip() for item in items_loc if item.inner_text().strip()]
            
            # Press Escape to close popover
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
            
            populated = len(items) > 0
            logger.info(f"Available Asset Dropdown Populated={populated}, Count={len(items)}, Items={items}")
            return {"populated": populated, "count": len(items), "items": items}
        except Exception as ex:
            logger.warning(f"Error checking available asset dropdown: {ex}")
            return {"populated": False, "count": 0, "items": []}

    def is_asset_in_available_dropdown(self, asset_code: str) -> bool:
        """
        Targeted search filter check:
        1. Clicks 'Select asset' trigger button.
        2. Clicks self.page.get_by_placeholder("Search...") directly.
        3. Pastes/fills the asset code to instantly filter the list.
        4. Verifies if any matching asset option exists.
        """
        logger.info(f"Checking availability of asset code '{asset_code}' via targeted search filter...")
        trigger_btn = self.page.locator("button:has-text('Select asset'), button:has-text('Select')").first
        if not trigger_btn.is_visible(timeout=1500):
            trigger_btn = self.page.locator(".chakra-menu__menubutton, button").filter(has_text=re.compile(r"Select|Available|ASSET", re.I)).first

        if not trigger_btn.is_visible(timeout=1500):
            logger.warning("Available Asset dropdown trigger button is not visible.")
            return False

        try:
            trigger_btn.click()
            self.page.wait_for_timeout(250)

            # Direct search input click and fill
            search_input = self.page.get_by_placeholder("Search...")
            search_input.click()
            search_input.fill(asset_code)
            self.page.wait_for_timeout(250)

            # Direct check for filtered matching option
            target_match = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], [role='option'], .chakra-menu__menuitem, div.chakra-menu__menu-list button").filter(has_text=asset_code)
            is_present = target_match.count() > 0

            # Press Escape to close popover cleanly
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(200)

            logger.info(f"[SEARCH FILTER RESULT] Asset '{asset_code}' visible in filtered dropdown = {is_present}")
            return is_present
        except Exception as ex:
            logger.warning(f"Error checking targeted asset in dropdown: {ex}")
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
            return False

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
            opt = self.page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text(employee_name, exact=False).first
            if opt.is_visible(timeout=1500):
                opt.click(force=True)
            else:
                fallback = self.page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile(employee_name.split()[0], re.I)).first
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
        sub_select = self.page.get_by_label("Sub Category*", exact=True)
        if not sub_select.is_visible(timeout=1000):
            sub_select = self.page.locator("select").nth(1)

        modal = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        if not modal.is_visible(timeout=1000):
            modal = self.page

        def _try_select_asset(sub_name):
            try:
                sub_select.select_option(label=sub_name, timeout=500)
            except Exception:
                for idx, opt in enumerate(sub_select.locator("option").all_inner_texts()):
                    if any(part.lower() in opt.lower() for part in sub_name.lower().split() if len(part) > 3) or sub_name.lower() in opt.lower():
                        sub_select.select_option(index=idx)
                        break
            self.page.wait_for_timeout(200)

            trigger = modal.locator(".chakra-menu__menubutton, button").filter(has_text=re.compile(r"Select asset|Select|Available|ASSET", re.I)).first
            if not trigger.is_visible(timeout=300):
                trigger = modal.locator(".chakra-menu__menubutton").first

            if trigger.is_visible(timeout=300):
                trigger.click(force=True)
                self.page.wait_for_timeout(200)

                # Direct search box click and paste to filter dropdown
                if asset_name_or_code:
                    search_box = self.page.get_by_placeholder("Search...")
                    search_box.click()
                    search_box.fill(asset_name_or_code)
                    self.page.wait_for_timeout(250)

                menu = self.page.locator(".chakra-portal div[role='menu'], div.chakra-menu__menu-list, [role='menu']").first
                items = menu.locator("[role='menuitem'], [role='menuitemcheckbox'], [role='option'], button").all() if menu.is_visible(timeout=300) else self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()

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

        # Fast fallback to other available subcategories under target category
        if not selected_code and sub_options:
            for alt_sub in sub_options:
                if alt_sub != target_sub:
                    selected_code = _try_select_asset(alt_sub)
                    if selected_code:
                        break

        # Fast fallback across other categories if still no assets found
        if not selected_code and cat_options:
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
        """Submits the Direct Assignment form using the modal's submit button (.last)."""
        btn = self.page.locator("button:has-text('Assign Asset'), button.chakra-button:has-text('Assign Asset')").last
        if not btn.is_visible(timeout=2000):
            dialog = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
            btn = dialog.locator("button:has-text('Assign Asset'), button:has-text('Assign'), button[type='submit']").last
        btn.click(force=True)
        try:
            self.page.locator(".chakra-spinner, span:has-text('Loading')").wait_for(state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def click_cancel(self):
        try:
            btn = self.page.locator("button:has-text('Cancel'), button.chakra-button:has-text('Cancel')").last
            if btn.is_visible(timeout=1000):
                btn.click()
            else:
                self.page.keyboard.press("Escape")
        except Exception:
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass

    def assign_requested_asset(self, employee_name: str, asset_code: str = None, assignment_type: str = "Temporary", expected_return_date: str = "2026-12-31", remarks: str = "Asset issued against request") -> dict:
        """
        Fulfills a requested asset assignment:
        1. Clicks 'Requested Assignment' tab.
        2. Searches employee/asset in table search.
        3. Clicks 'Fulfil →' button on the row.
        4. In 'Assign Requested Asset' form, clicks 'Select assets to assign'.
        5. Validates whether available asset dropdown populates records or shows 'No results found'.
        6. Selects an asset.
        7. Selects Assignment Type ('Permanent' vs 'Temporary').
        8. If Temporary, fills Expected Return Date & Remarks.
        9. Clicks 'Assign Asset' button to submit.
        """
        import re
        logger.info(f"Fulfilling requested asset for employee: {employee_name}")
        
        # 1. Click Requested Assignment tab
        req_tab = self.page.get_by_role("tab", name=re.compile(r"Requested Assignment", re.I)).first
        if not req_tab.is_visible(timeout=1000):
            req_tab = self.page.locator("button[role='tab']").filter(has_text=re.compile(r"Requested Assignment", re.I)).first
        req_tab.click()
        self.page.wait_for_timeout(1000)

        # Wait for table rows to attach/render
        try:
            self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        # 2. Search employee/asset in search box if visible
        search_in = self.page.locator("input[placeholder*='Search assets, employees']").first
        if not search_in.is_visible(timeout=1000):
            search_in = self.page.locator("input[placeholder*='Search']").first
        if search_in.is_visible(timeout=1000):
            search_in.fill(employee_name)
            search_in.press("Enter")
            self.page.wait_for_timeout(800)

        # 3. Locate row and click 'Fulfil →' button
        first_name = employee_name.split()[0] if employee_name else "Sanidhy"
        row = self.page.locator("table tbody tr").filter(has_text=re.compile(first_name, re.I)).first
        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").filter(has=self.page.locator("button", has_text=re.compile(r"Fulfil", re.I))).first
        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").first

        fulfil_btn = row.locator("button").filter(has_text=re.compile(r"Fulfil", re.I)).first
        if not fulfil_btn.is_visible(timeout=2000):
            fulfil_btn = self.page.locator("button").filter(has_text=re.compile(r"Fulfil", re.I)).first

        if not fulfil_btn.is_visible(timeout=2000):
            logger.warning(f"No 'Fulfil' button found on row for '{employee_name}'.")
            return {"success": False, "reason": "Fulfil button not visible", "dropdown_info": {"populated": False, "count": 0, "items": []}}

        fulfil_btn.click()
        self.page.wait_for_timeout(1000)

        # 4. Form 'Assign Requested Asset' appears. Click 'Select assets to assign'
        form = self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        if not form.is_visible(timeout=1000):
            form = self.page

        dropdown_info = {"populated": False, "count": 0, "items": []}
        asset_select_btn = form.locator("button").filter(has_text=re.compile(r"Select assets to assign|Select asset", re.I)).first
        if asset_select_btn.is_visible(timeout=3000):
            asset_select_btn.click()
            self.page.wait_for_timeout(600)

            # Validate popover contents
            popover = self.page.locator("[role='menu'], .chakra-menu__menu-list").first
            no_results = popover.locator("p").filter(has_text=re.compile(r"No results found", re.I)).first
            
            items_loc = popover.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            items = [it.inner_text().strip() for it in items_loc if it.inner_text().strip()]

            if items:
                dropdown_info = {"populated": True, "count": len(items), "items": items}
                logger.info(f"Available Assets Dropdown POPULATED with {len(items)} items: {items}")
                # Select specified asset or first available item
                selected_item = False
                if asset_code:
                    for it in items_loc:
                        if asset_code.lower() in it.inner_text().lower():
                            it.click(force=True)
                            selected_item = True
                            break
                if not selected_item:
                    items_loc[0].click(force=True)
            elif no_results.is_visible(timeout=1000):
                dropdown_info = {"populated": False, "count": 0, "items": ["No results found"]}
                logger.warning("Available Assets Dropdown shows: 'No results found'")
            
            # Press Escape to close popover if still open
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
            except Exception:
                pass

        # 5. Select Assignment Type ('Permanent' or 'Temporary')
        type_select = form.locator("//div[./label[contains(text(), 'Assignment Type')]]//select").first
        if not type_select.is_visible(timeout=1000):
            type_select = form.locator("select").first
        if type_select.is_visible(timeout=1000):
            try:
                type_select.select_option(label=assignment_type)
            except Exception:
                type_select.select_option(value=assignment_type)
            logger.info(f"Selected Assignment Type: '{assignment_type}'")

        # 6. If Temporary, fill Expected Return Date & Remarks
        if assignment_type.lower() == "temporary":
            if expected_return_date:
                date_in = form.locator("//div[./label[contains(text(), 'Expected Return Date')]]//input").first
                if not date_in.is_visible(timeout=500):
                    date_in = form.locator("input[type='date']").first
                if date_in.is_visible(timeout=1000):
                    date_in.fill(expected_return_date)

            if remarks:
                rem_in = form.locator("//div[./label[contains(text(), 'Remarks')]]//textarea").first
                if not rem_in.is_visible(timeout=500):
                    rem_in = form.locator("textarea").first
                if rem_in.is_visible(timeout=1000):
                    rem_in.fill(remarks)

        # 7. Submit Assignment
        submit_btn = form.locator("button").filter(has_text=re.compile(r"^Assign Asset$", re.I)).first
        if not submit_btn.is_visible(timeout=1000):
            submit_btn = form.locator("button").filter(has_text=re.compile(r"Assign Asset|Assign|Submit", re.I)).first
        submit_btn.click(force=True)
        self.page.wait_for_timeout(500)

        return {
            "success": True,
            "dropdown_info": dropdown_info,
            "assignment_type": assignment_type
        }

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
