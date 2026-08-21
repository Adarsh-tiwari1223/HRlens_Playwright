"""
Test Data Factories for HRlens Portal Automation Framework.
Provides single-responsibility, unique, and realistic test entity generation.
"""

from testdata.factories.vendor_factory import VendorFactory
from testdata.factories.employee_factory import EmployeeFactory
from testdata.factories.asset_factory import AssetFactory
from testdata.factories.job_opening_factory import JobOpeningFactory
from testdata.factories.candidate_factory import CandidateFactory

__all__ = [
    "VendorFactory",
    "EmployeeFactory",
    "AssetFactory",
    "JobOpeningFactory",
    "CandidateFactory",
]
