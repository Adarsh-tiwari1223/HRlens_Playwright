"""
Cross Company Hierarchy Workflow Layer for HR Lens Portal Admin Control.

Encapsulates reusable business workflows for cross-company team lead exclusion,
reporting line reassignment, and hierarchy updates.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.admin_control.cross_company_hierarchy_page import CrossCompanyHierarchyPage

logger = logging.getLogger(__name__)

class CrossCompanyHierarchyWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.hierarchy_page = CrossCompanyHierarchyPage(page)

    def update_cross_company_hierarchy_workflow(self, hierarchy_data: dict):
        """Workflow to update cross-company reporting hierarchy."""
        logger.info("[WORKFLOW] Updating cross company hierarchy")
        self.hierarchy_page.navigate_to_hierarchy()
        self.hierarchy_page.update_hierarchy(hierarchy_data)
        logger.info("[WORKFLOW] Cross company hierarchy updated successfully")
