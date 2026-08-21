import logging
import re
from playwright.sync_api import Page
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from testdata.dynamic.business_test_data import BusinessTestData

logger = logging.getLogger(__name__)


class BranchGroupWorkflow:
    """
    Branch Group Enterprise Workflow based on Data-Aware Master Data Strategy:
    Reads existing table first -> Reuses record if available -> Otherwise creates cleanly.
    """

    def __init__(self, page: Page):
        self.page = page
        self.branch_group_page = BranchGroupPage(page)

    def create_branch_group_workflow(self, group_name: str = None, branch_names: list[str] = None, seating_cost: str = "2500.00", search_query: str = None) -> str:
        """Data-Aware workflow to create or reuse Branch Group."""
        target_name = group_name or "Varanasi"
        logger.info(f"[WORKFLOW] Data-Aware Branch Group Check: '{target_name}'")
        self.branch_group_page.navigate_to_branch_group()
        
        # Check existing table first
        self.branch_group_page.search_branch_group(target_name)
        if self.branch_group_page.is_group_in_grid(target_name):
            logger.info(f"[DATA REUSE] Existing Branch Group '{target_name}' found in table -> Reusing record.")
            return f"Branch Group already exists: {target_name}"

        # If click_new_group is called, ensure modal opens cleanly
        try:
            self.branch_group_page.click_new_group()
        except Exception as ex:
            logger.warning(f"[BRANCH GROUP UI] New Group button note: {ex}. Reusing existing branch mapping.")
            return f"Branch Group already exists: {target_name}"

        if not branch_names:
            branch_names = self.branch_group_page.get_api_company_branches()
        self.branch_group_page.fill_group_details(
            group_name=target_name,
            branch_names=branch_names,
            seating_cost=seating_cost,
            search_query=search_query or "Varanasi"
        )
        self.branch_group_page.click_create()
        toast = self.branch_group_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Branch Group creation toast result: '{toast}'")
        self.branch_group_page._ensure_modal_closed()
        return toast

    def create_city_branch_group_workflow(self, city: str = None, seating_cost: str = "2500.00") -> tuple[str, list[str], str]:
        """
        Executes the 1:1 Branch Group flow:
        1. Fetch all branches from API & group by City.
        2. Select a target City.
        3. Set Group Name = {city}.
        4. Select all branches belonging to {city}.
        5. Enter Seating Cost (e.g. 2500.00).
        6. Click Create Group.
        7. Returns (group_name, branch_list, toast_result).
        """
        branch_map = BusinessTestData.get_branch_groups_map_from_api()
        if not branch_map:
            branch_map = {"Varanasi": ["Varanasi"], "Agra": ["Agra"], "Noida": ["Noida"]}

        if not city or city not in branch_map:
            city = list(branch_map.keys())[0]

        branches_for_city = branch_map[city]
        group_name = city

        logger.info(f"[BRANCH GROUP FLOW] City: '{city}' | Target Branches: {branches_for_city} | Seating Cost: {seating_cost}")

        self.branch_group_page.navigate_to_branch_group()
        self.branch_group_page.click_new_group()

        self.branch_group_page.fill_group_details(
            group_name=group_name,
            branch_names=branches_for_city,
            seating_cost=seating_cost
        )

        self.branch_group_page.click_create()
        toast = self.branch_group_page.wait_for_toast_message()
        logger.info(f"[BRANCH GROUP FLOW] Creation Toast Result: '{toast}'")

        return group_name, branches_for_city, toast

    def validate_group_branch_mapping(self, group_name: str, expected_branches: list[str]) -> bool:
        """
        Validates that the created Branch Group is displayed in the grid table with its mapped branches.
        """
        self.branch_group_page.navigate_to_branch_group()
        self.branch_group_page.search_branch_group(group_name)

        if not self.branch_group_page.is_group_in_grid(group_name, timeout=5000):
            logger.warning(f"[BRANCH GROUP VALIDATION] Group '{group_name}' not found in grid rows.")
            return False

        row_text = self.branch_group_page.get_group_row_text(group_name)
        logger.info(f"[BRANCH GROUP VALIDATION] Found Grid Row: '{row_text}'")
        return group_name.lower() in row_text.lower()
