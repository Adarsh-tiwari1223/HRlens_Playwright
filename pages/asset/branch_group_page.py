import logging
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
        logger.info("Navigating to Branch Group page")
        self.page.goto(f"{settings.BASE_URL}/master/branch-group")
        self.page.wait_for_load_state("networkidle")

    def click_new_group(self):
        self.click(self.NEW_GROUP_BTN)

    def fill_group_details(self, group_name: str = None, branch_names: list[str] = None):
        if group_name is not None:
            self.page.get_by_placeholder("e.g. North Zone, Mumbai").fill(group_name)
        
        if branch_names:
            self.page.get_by_placeholder("Search branches…").click()
            for b_name in branch_names:
                logger.info(f"Selecting branch: {b_name}")
                self.page.get_by_placeholder("Search branches…").fill(b_name)
                self.page.wait_for_timeout(500)
                self.page.locator(".chakra-portal").get_by_text(b_name).first.click()
                self.page.get_by_placeholder("Search branches…").fill("")
                self.page.wait_for_timeout(500)

    def click_create(self):
        self.click(self.CREATE_BTN)

    def click_update(self):
        self.click(self.UPDATE_BTN)

    def edit_branch_group(self, group_name: str):
        logger.info(f"Editing branch group: {group_name}")
        row_locator = f"role=row[name*='{group_name}']"
        self.page.locator(row_locator).get_by_label("Edit").click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
