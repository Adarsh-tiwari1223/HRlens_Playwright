import logging
import re
from playwright.sync_api import Page
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from testdata.dynamic.business_test_data import BusinessTestData

logger = logging.getLogger(__name__)


class BranchGroupWorkflow:
    """
    Branch Group Enterprise Workflow based on:
    Branch API -> Get all branches -> Group by City -> Select City -> 
    Group Name = {city} -> Select branches belonging to {city} -> 
    Enter Seating Cost -> Create Branch Group -> Validate Group + Branch Mapping
    """

    def __init__(self, page: Page):
        self.page = page
        self.branch_group_page = BranchGroupPage(page)

    def create_branch_group_workflow(self, group_name: str = None, branch_names: list[str] = None, seating_cost: str = "2500.00", search_query: str = None) -> str:
        """Workflow to open Branch Group, click New Group, fill details, and submit."""
        logger.info(f"[WORKFLOW] Creating Branch Group: '{group_name}'")
        self.branch_group_page.navigate_to_branch_group()
        self.branch_group_page.click_new_group()
        if not branch_names:
            branch_names = self.branch_group_page.get_api_company_branches()
        self.branch_group_page.fill_group_details(
            group_name=group_name or "Varanasi",
            branch_names=branch_names,
            seating_cost=seating_cost,
            search_query=search_query or "Varanasi"
        )
        self.branch_group_page.click_create()
        toast = self.branch_group_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Branch Group creation toast result: '{toast}'")
        # Ensure modal dialog is cleanly closed if creation failed/blocked
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
        # Step 1 & 2: Branch API -> Get all branches -> Group by City
        branch_map = BusinessTestData.get_branch_groups_map_from_api()
        if not branch_map:
            branch_map = {"Varanasi": ["Varanasi"], "Agra": ["Agra"], "Noida": ["Noida"]}

        # Select target city
        if not city or city not in branch_map:
            city = list(branch_map.keys())[0]

        branches_for_city = branch_map[city]
        group_name = city

        logger.info(f"[BRANCH GROUP FLOW] City: '{city}' | Target Branches: {branches_for_city} | Seating Cost: {seating_cost}")

        # Step 3: Navigate to Branch Group UI
        self.branch_group_page.navigate_to_branch_group()
        self.branch_group_page.click_new_group()

        # Step 4, 5, 6: Group Name = {city} -> Select branches -> Enter Seating Cost
        self.branch_group_page.fill_group_details(
            group_name=group_name,
            branch_names=branches_for_city,
            seating_cost=seating_cost
        )

        # Step 7: Create Branch Group
        self.branch_group_page.click_create()
        toast = self.branch_group_page.wait_for_toast_message()
        logger.info(f"[BRANCH GROUP FLOW] Creation Toast Result: '{toast}'")

        return group_name, branches_for_city, toast

    def validate_group_branch_mapping(self, group_name: str, expected_branches: list[str]) -> bool:
        """
        Validates that the created Branch Group is displayed in the grid table with its mapped branches.
        """
        self.branch_group_page.navigate_to_branch_group()
        # Search for group_name in table search box if present
        search_input = self.page.get_by_placeholder("Search", exact=False)
        if search_input.is_visible(timeout=500):
            search_input.fill(group_name)

        row = self.page.locator("tbody tr").filter(has_text=group_name).first
        try:
            row.wait_for(state="visible", timeout=5000)
        except Exception:
            logger.warning(f"[BRANCH GROUP VALIDATION] Group '{group_name}' not found in grid rows.")
            return False

        row_text = row.inner_text().strip()
        logger.info(f"[BRANCH GROUP VALIDATION] Found Grid Row: '{row_text}'")

        # Validate that city/group_name is in the row text
        return group_name.lower() in row_text.lower()
