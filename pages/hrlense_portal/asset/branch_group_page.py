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

    def is_group_in_grid(self, group_name: str, timeout: int = 1500) -> bool:
        """Returns True if the branch group name appears in the grid table."""
        row = self.page.locator("tbody tr").filter(has_text=group_name).first
        try:
            return row.is_visible(timeout=timeout)
        except Exception:
            return False

    def get_group_row_text(self, group_name: str, timeout: int = 5000) -> str:
        """Finds and returns the inner text of a branch group row in the grid."""
        row = self.page.locator("tbody tr").filter(has_text=group_name).first
        row.wait_for(state="visible", timeout=timeout)
        return row.inner_text().strip()

    def navigate_to_branch_group(self):
        logger.info("Navigating to Branch Group page...")
        self.navigate_to_master_menu("Branch Group")
        try:
            self.page.locator(self.NEW_GROUP_BTN).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

    def click_new_group(self):
        self._ensure_modal_closed()
        btn = self.page.locator("button:has-text('New Group'), button:has-text('Add Group'), button:has-text('Add Branch Group')").first
        if not btn.is_visible(timeout=2000):
            btn = self.page.get_by_role("button", name=re.compile(r"New Group|Add Group|Add Branch Group", re.I)).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)

    def get_all_existing_branch_groups(self) -> list[str]:
        """Returns all branch group names currently in the Branch Group table."""
        self.navigate_to_branch_group()
        groups = set()
        try:
            self.page.locator("tbody tr, table tr").first.wait_for(state="visible", timeout=6000)
            while True:
                for r in self.page.locator("tbody tr, table tr").all():
                    for td in r.locator("td").all():
                        t = td.inner_text().strip()
                        if t and not t.startswith("No ") and not t.isdigit() and len(t) > 2:
                            groups.add(t)
                next_btn = self.page.locator("button[aria-label='Next Page'], button:has-text('Next')").first
                if next_btn.is_visible() and next_btn.is_enabled():
                    next_btn.click()
                    self.page.wait_for_timeout(400)
                else:
                    break
        except Exception:
            pass
        return sorted(list(groups))

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

    def fill_group_details(self, group_name: str = None, branch_names: list[str] = None, seating_cost: str = "2500.00", search_query: str = None):
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page

        # 1. Group Name
        if group_name is not None:
            name_input = dialog.get_by_placeholder("e.g. North Zone, Mumbai Cluster", exact=False)
            if not name_input.is_visible(timeout=1000):
                name_input = dialog.get_by_label("Group Name*", exact=False)
            if not name_input.is_visible(timeout=1000):
                name_input = dialog.locator("input[placeholder*='e.g.' i], input").first
            name_input.fill(group_name)

        # 2. Seating Cost (per head)
        if seating_cost is not None:
            cost_input = dialog.get_by_placeholder("e.g. 2500.00", exact=False)
            if not cost_input.is_visible(timeout=1000):
                cost_ctrl = dialog.locator(".chakra-form-control, div").filter(has_text=re.compile(r"Seating Cost", re.I)).first
                cost_input = cost_ctrl.locator("input").first
            if cost_input.is_visible(timeout=1000):
                cost_input.fill(str(seating_cost))

        # 3. Search branches
        target_search = search_query or (branch_names[0] if branch_names else "Varanasi")
        if target_search:
            clean_search = str(target_search).split("(")[0].strip()
            search_input = dialog.locator("input[placeholder*='Search branches'], input[placeholder*='Search']").first
            if search_input.is_visible(timeout=1000):
                search_input.fill(clean_search)
                logger.info(f"[ASSIGN BRANCHES] Searched branches by: '{clean_search}'")

        # 4. Select all checkbox
        select_all_locators = [
            dialog.locator("div.chakra-stack, label.chakra-checkbox").filter(has_text=re.compile(r"Select all", re.I)).locator(".chakra-checkbox__control, input[type='checkbox']").first,
            dialog.locator("label.chakra-checkbox:has-text('Select all')").first,
            dialog.locator("div:has(> p:has-text('Select all')) .chakra-checkbox__control").first,
            dialog.get_by_text("Select all", exact=False).first,
            dialog.locator(".chakra-checkbox__control").first
        ]
        clicked = False
        for loc in select_all_locators:
            try:
                if loc.is_visible(timeout=500):
                    loc.click(force=True)
                    clicked = True
                    logger.info("[ASSIGN BRANCHES] Checked 'Select all' checkbox.")
                    break
            except Exception:
                continue

        if not clicked:
            first_chk = dialog.locator(".chakra-checkbox__control, input[type='checkbox']").first
            if first_chk.is_visible(timeout=1000):
                first_chk.click(force=True)
                logger.info("[ASSIGN BRANCHES] Checked first available branch checkbox.")

    def get_available_branches(self) -> list[str]:
        return self.get_api_company_branches()

    def click_create(self):
        btn = self.page.locator("button:has-text('Create Group'), button:has-text('Create'), button[type='submit']").first
        if not btn.is_visible(timeout=1000):
            btn = self.page.get_by_role("button", name=re.compile(r"Create Group|Create", re.I)).first
        btn.click()

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

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

