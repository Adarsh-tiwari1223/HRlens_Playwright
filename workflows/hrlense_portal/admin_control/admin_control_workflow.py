"""
Admin Control Aggregator Workflow Layer for HR Lens Portal.

Exposes workflows for absence settings, cross-company hierarchy, and management interaction.
"""

from workflows.hrlense_portal.admin_control.absence_setting_workflow import AbsenceSettingWorkflow
from workflows.hrlense_portal.admin_control.cross_company_hierarchy_workflow import CrossCompanyHierarchyWorkflow
from workflows.hrlense_portal.admin_control.management_interaction_workflow import ManagementInteractionWorkflow

class AdminControlWorkflow:
    def __init__(self, page):
        self.page = page
        self.absence_setting_workflow = AbsenceSettingWorkflow(page)
        self.cross_company_hierarchy_workflow = CrossCompanyHierarchyWorkflow(page)
        self.management_interaction_workflow = ManagementInteractionWorkflow(page)
