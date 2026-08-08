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

    def navigate_to_branch_group(self):
        logger.info("Navigating to Branch Group page...")
        self.navigate_to_master_menu("Branch Group")
        try:
            self.page.locator(self.NEW_GROUP_BTN).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

    def click_new_group(self):
        self.page.locator(self.NEW_GROUP_BTN).wait_for(state="visible", timeout=10000)
        self.click(self.NEW_GROUP_BTN)
        self.page.locator("[role='dialog']").wait_for(state="visible", timeout=10000)


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

        # 3. Assign Branches
        if branch_names:
            search_input = dialog.get_by_placeholder("Search branches...", exact=False)
            if not search_input.is_visible(timeout=1000):
                search_input = dialog.get_by_placeholder("Search branches", exact=False)

            for b_name in branch_names:
                logger.debug(f"Selecting branch: {b_name}")
                if search_input.is_visible(timeout=1000):
                    search_input.fill(b_name)
                    self.page.wait_for_timeout(400)

                # Look for matching branch checkbox / label
                branch_row = dialog.locator("label, .chakra-checkbox, div").filter(has_text=re.compile(rf"^\s*{re.escape(b_name)}", re.I)).first
                if not branch_row.is_visible(timeout=1000):
                    branch_row = dialog.get_by_text(b_name, exact=False).first

                if branch_row.is_visible(timeout=1000):
                    branch_row.click(force=True)
                    self.page.wait_for_timeout(200)

                if search_input.is_visible(timeout=1000):
                    search_input.fill("")
                    self.page.wait_for_timeout(200)

    def get_available_branches(self) -> list[str]:
        self.page.get_by_placeholder("Search branches", exact=False).click()
        self.page.wait_for_timeout(500)
        options = self.page.locator(".chakra-portal div, .chakra-portal button, .chakra-portal span").all_inner_texts()
        branch_names = []
        for name in options:
            name = name.strip()
            # Must not contain newlines to ensure it is a leaf option, not a wrapper container
            if name and "\n" not in name and not name.startswith("Search") and "(" in name:
                city = name.split("(")[0].strip()
                if city not in branch_names:
                    branch_names.append(city)
        logger.debug(f"Retrieved available branch cities from dropdown: {branch_names}")
        return branch_names

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
        # 5. Return
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
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
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
                    if b and b not in assigned:
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
                if city.lower() in assigned_name.lower():
                    is_assigned = True
                    break
            if not is_assigned:
                unassigned.append(city)
                
        if not unassigned:
            self.ensure_at_least_one_free_branch()
            assigned = self.get_assigned_branch_names()
            available = self.get_available_branches()
            unassigned = []
            for city in available:
                is_assigned = False
                for assigned_name in assigned:
                    if city.lower() in assigned_name.lower():
                        is_assigned = True
                        break
                if not is_assigned:
                    unassigned.append(city)
                    
        logger.debug(f"Discovered unassigned branch cities: {unassigned}")
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

