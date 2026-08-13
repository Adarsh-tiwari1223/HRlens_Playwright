import logging
import re
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class BranchGroupPage(BasePage):
    ADMIN_BTN = "role=button[name='Admin']"
    MASTER_MENU = "role=menuitem[name='Master']"
    BRANCH_GROUP_LINK = "role=link[name='• Branch Group']"
    
    NEW_GROUP_BTN = "role=button[name='New Group']"
    GROUP_NAME_INPUT = 'internal:placeholder="e.g. North Zone, Mumbai"'
    BRANCH_SEARCH_INPUT = 'internal:placeholder="Search branches…"'
    
    CREATE_BTN = "role=button[name='Create Group']"
    UPDATE_BTN = "role=button[name='Update Group']"
    TOAST = "#chakra-toast-manager-top-right"

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
        try:
            self.page.locator(".chakra-toast").first.wait_for(state="hidden", timeout=4000)
        except Exception:
            pass

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
        err_msgs = {}
        for msg in self.get_active_form_errors():
            logger.info(f"[HIGHLIGHTED FORM ERROR] '{msg}'")
            err_msgs[msg] = msg
        return err_msgs

    def search_branch_group(self, query: str):
        search_input = self.page.get_by_placeholder("Search", exact=False).first
        if search_input.is_visible():
            search_input.fill(query)
            self.page.wait_for_timeout(400)

    def navigate_to_branch_group(self):
        logger.info("Navigating to Branch Group page...")
        self.navigate_to_master_menu("Branch Group")
        try:
            self.page.locator(self.NEW_GROUP_BTN).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

    def click_new_group(self):
        self._ensure_modal_closed()
        self.page.locator(self.NEW_GROUP_BTN).wait_for(state="visible", timeout=10000)
        self.click(self.NEW_GROUP_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)


    def get_api_company_branches(self) -> list[str]:
        """Fetch all stored company branches via API call GET /Hrlense_Branch."""
        try:
            from testdata.dynamic.business_test_data import BusinessTestData
            branch_map = BusinessTestData.get_branch_groups_map_from_api()
            if branch_map:
                all_b = []
                for city, b_list in branch_map.items():
                    all_b.extend(b_list)
                    if city not in all_b:
                        all_b.append(city)
                return all_b
        except Exception as e:
            logger.warning(f"Failed to fetch branches from API: {e}")
        return ["Varanasi", "Agra", "Noida"]

    def fill_group_details(self, group_name: str = None, branch_names: list[str] = None, seating_cost: str = "2500.00"):
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page

        # 1. Group Name
        if group_name is not None:
            name_input = dialog.get_by_placeholder("e.g. North Zone, Mumbai Cluster", exact=False)
            if not name_input.is_visible(timeout=1000):
                name_input = dialog.get_by_label("Group Name*", exact=False)
            if not name_input.is_visible(timeout=1000):
                name_input = dialog.locator("input").first
            name_input.fill(group_name)

        # 2. Seating Cost (per head)
        if seating_cost is not None:
            cost_input = dialog.get_by_placeholder("e.g. 2500.00", exact=False)
            if not cost_input.is_visible(timeout=1000):
                cost_ctrl = dialog.locator(".chakra-form-control, div").filter(has_text=re.compile(r"Seating Cost", re.I)).first
                cost_input = cost_ctrl.locator("input").first
            if cost_input.is_visible(timeout=1000):
                cost_input.fill(str(seating_cost))

        # 3. Assign Branches* (Search stored company branches via API and check)
        if branch_names is not None:
            search_input = dialog.locator("input[placeholder*='Search'], input[placeholder*='branch']").first
            if not search_input.is_visible(timeout=1000):
                search_input = dialog.get_by_placeholder("Search branches", exact=False)

            selected_count = 0
            for b_name in branch_names:
                b_clean = str(b_name).strip()
                if not b_clean or "*" in b_clean or "Group" in b_clean:
                    continue
                logger.info(f"[ASSIGN BRANCHES] Searching stored company branch: '{b_clean}'")
                if search_input.is_visible(timeout=1000):
                    search_input.fill("")
                    search_input.fill(b_clean)
                    self.page.wait_for_timeout(300)

                # Look for matching branch checkbox in body (never header select-all)
                branch_row = dialog.locator("tbody tr, div[role='row'], label.chakra-checkbox").filter(has_text=re.compile(rf"{re.escape(b_clean)}", re.I)).first
                if not branch_row.is_visible(timeout=1000):
                    clean_city = b_clean.split("(")[0].strip() if "(" in b_clean else b_clean
                    branch_row = dialog.locator("tbody tr, div[role='row'], label.chakra-checkbox").filter(has_text=re.compile(rf"{re.escape(clean_city)}", re.I)).first

                if branch_row.is_visible(timeout=1000):
                    chk_elem = branch_row.locator(".chakra-checkbox__control, input[type='checkbox'], span, label").first
                    if chk_elem.is_visible():
                        chk_elem.click(force=True)
                    else:
                        branch_row.click(force=True)
                    self.page.wait_for_timeout(200)
                    selected_count += 1
                    logger.info(f"[ASSIGN BRANCHES] Checked company branch: '{b_clean}'")

            # Clear search filter cleanly after specific selections are made
            if search_input.is_visible(timeout=1000):
                search_input.fill("")
                self.page.wait_for_timeout(200)

            # Fallback: if branch_names was provided but none matched, select first row checkbox in tbody only
            if selected_count == 0 and branch_names:
                first_body_chk = dialog.locator("tbody tr .chakra-checkbox__control, tbody label.chakra-checkbox, tbody input[type='checkbox']").first
                if first_body_chk.is_visible(timeout=1000):
                    first_body_chk.click(force=True)
                    self.page.wait_for_timeout(200)
                    logger.info("[ASSIGN BRANCHES] Checked first body company branch checkbox.")

    def get_available_branches(self) -> list[str]:
        return self.get_api_company_branches()

    def click_create(self):
        self.click(self.CREATE_BTN)

    def click_update(self):
        self.click(self.UPDATE_BTN)

    def edit_branch_group(self, group_name: str):
        logger.debug(f"Editing branch group: {group_name}")
        # 1. Click Edit
        row = self.page.locator("tbody tr").filter(has_text=group_name).first
        row.get_by_label("Edit").click()
        # 2. Wait dialog visible
        dialog = self.page.locator("[role='dialog']")
        dialog.wait_for(state="visible", timeout=10000)
        # 3. Verify dialog title
        header = dialog.locator(".chakra-modal__header, header").first
        if header.is_visible():
            logger.debug(f"Dialog title verified: '{header.inner_text().strip()}'")
        # 4. Verify first field visible
        dialog.locator("input").first.wait_for(state="visible", timeout=5000)
        return

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)

    def get_first_group_name(self) -> str | None:
        first_row = self.page.locator("tbody tr").first
        if first_row.count() > 0:
            cells = first_row.locator("td").all()
            if len(cells) > 1:
                return cells[1].inner_text().strip()
        return None

    def click_cancel(self):
        cancel_btn = self.page.get_by_role("button", name="Cancel", exact=True)
        if cancel_btn.is_visible():
            cancel_btn.click()

    def get_assigned_branch_names(self) -> list[str]:
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=4000)
        except Exception:
            pass
        assigned = []
        rows = self.page.locator("tbody tr").all()
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) > 2:
                branches_text = cells[2].inner_text().strip()
                for b in branches_text.split(","):
                    b = b.strip()
                    if b and "*" not in b and "Group" not in b and b not in assigned:
                        assigned.append(b)
        logger.debug(f"Retrieved assigned branches from grid: {assigned}")
        return assigned

    def get_unassigned_branches(self) -> list[str]:
        assigned = self.get_assigned_branch_names()
        available = self.get_available_branches()
        unassigned = []
        for city in available:
            is_assigned = False
            for assigned_name in assigned:
                if city.lower() in assigned_name.lower() or assigned_name.lower() in city.lower():
                    is_assigned = True
                    break
            if not is_assigned:
                unassigned.append(city)
                
        if not unassigned and available:
            unassigned = [b for b in available if b not in assigned]
            if not unassigned:
                unassigned = [available[0]]
                    
        logger.info(f"Discovered unassigned company branches: {unassigned}")
        return unassigned

    def ensure_at_least_one_free_branch(self):
        logger.info("No unassigned branches found. Freeing up a branch from an existing group...")
        
        # 1. Close the open New Group modal first to clear the pointer events backdrop overlay
        self.click_cancel()
        self.page.wait_for_timeout(1000)
        
        # 2. Free up the branch from an existing group
        first_group = self.get_first_group_name()
        if not first_group:
            logger.warning("No branch groups exist to free a branch from.")
            # Reopen to preserve modal state for the caller
            self.click_new_group()
            return
            
        self.edit_branch_group(first_group)
        self.page.wait_for_timeout(1000)
        
        # Locate the close button on the first selected tag/pill in the edit dialog directly
        tag_close = self.page.locator("[role='dialog'] button.chakra-tag__close-btn, [role='dialog'] .chakra-tag__close-btn, [role='dialog'] button:has-text('x')").first
        
        if tag_close.is_visible():
            tag_close.click()
            self.page.wait_for_timeout(500)
            self.click_update()
            self.wait_for_toast_message()
            self.page.wait_for_timeout(1000)
            logger.info("Successfully freed up one branch.")
        else:
            logger.warning("Could not locate any selected branch pills to deselect.")
            self.click_cancel()
            
        # 3. Re-open the New Group modal to restore page state for the calling test case
        self.click_new_group()

