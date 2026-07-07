import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.api.payroll_api import flag_payroll_generated

class TestFlagPayrollGenerated(unittest.TestCase):
    def setUp(self):
        # Set up variables
        self.year = 2026
        self.month = 4
        self.branch_id = 4
        self.branch_name = "Varanasi"
        self.company_name = "Jobvritta Inc"
        self.flag_file_path = os.path.join("logs", "payroll_generated_flag.txt")
        # Ensure cleanup before start
        if os.path.exists(self.flag_file_path):
            os.remove(self.flag_file_path)

    def tearDown(self):
        # Clean up any created flag file
        if os.path.exists(self.flag_file_path):
            os.remove(self.flag_file_path)

    @patch("utils.api.payroll_api.get_payroll_status")
    def test_when_employees_pending_then_no_flag_file(self, mock_get_status):
        # Mock status where pending count is > 0
        mock_get_status.return_value = [
            {"status": "generated", "count": 10},
            {"status": "pending", "count": 2}
        ]
        
        result = flag_payroll_generated(
            year=self.year,
            month=self.month,
            branch_id=self.branch_id,
            branch_name=self.branch_name,
            company_name=self.company_name
        )
        
        # Verify result is None and no file was created
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(self.flag_file_path))

    @patch("utils.api.payroll_api.get_payroll_status")
    def test_when_no_employees_pending_then_creates_flag_file(self, mock_get_status):
        # Mock status where pending count is 0
        mock_get_status.return_value = [
            {"status": "generated", "count": 12},
            {"status": "pending", "count": 0}
        ]
        
        result = flag_payroll_generated(
            year=self.year,
            month=self.month,
            branch_id=self.branch_id,
            branch_name=self.branch_name,
            company_name=self.company_name
        )
        
        # Verify flag file is created and returns the path
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.flag_file_path))
        self.assertEqual(os.path.abspath(result), os.path.abspath(self.flag_file_path))
        
        # Verify content format
        with open(self.flag_file_path, "r") as f:
            content = f.read()
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        expected_msg = f"Payroll fully generated on {current_date}"
        self.assertIn(expected_msg, content)
        self.assertIn(f"Year: {self.year}", content)
        self.assertIn(f"Month: {self.month}", content)
        self.assertIn(f"Branch ID: {self.branch_id}", content)
        self.assertIn(f"Branch Name: {self.branch_name}", content)
        self.assertIn(f"Company Name: {self.company_name}", content)

if __name__ == "__main__":
    unittest.main()
