"""
Master Data Provider Utility enforcing User Rules:
1. Master Categories: Hardware, Software, Furniture, Peripherals, Mobile Phones
2. Master Sub-Categories: NO NUMBERS in sub-category names (Laptop, Desktop, Monitor, Headset, Smartphone, Office Desk)
3. Master Vendors: NO NUMBERS in vendor names (Dell Technologies, Apple India, Lenovo Enterprise, HP Solutions, Samsung Electronics)
4. Branch Groups: Varanasi, Agra, Noida, Greater Noida
5. Duplicate Testing Helper: Picks existing record data to test duplicate validation without adding artificial prefixes like 'dup{name}'.
6. Edit Testing Helper: Picks existing record row, clicks edit, and updates in-place without creating redundant records.
"""

import random
import logging

logger = logging.getLogger(__name__)

MASTER_CATEGORIES = ["Hardware", "Software", "Furniture", "Peripherals", "Mobile Phones"]

# Clean Sub-Categories — ZERO NUMBERS
CLEAN_SUB_CATEGORIES = [
    "Laptop",
    "Desktop",
    "Monitor",
    "Headset",
    "Smartphone",
    "Tablet",
    "Office Desk",
    "Ergonomic Chair",
    "Wireless Mouse",
    "Mechanical Keyboard"
]

# Clean Corporate Vendor Names — ZERO NUMBERS
CLEAN_VENDORS = [
    {"name": "Dell Technologies", "contact": "Rajesh Sharma", "phone": "9876543210", "email": "sales@dellindia.com", "address": "Tech Park, Bangalore"},
    {"name": "Apple India", "contact": "Anita Verma", "phone": "9876543211", "email": "enterprise@apple.com", "address": "BKC, Mumbai"},
    {"name": "Lenovo Enterprise", "contact": "Suresh Gupta", "phone": "9876543212", "email": "commercial@lenovo.com", "address": "Cyber City, Gurgaon"},
    {"name": "HP Solutions", "contact": "Vikram Malhotra", "phone": "9876543213", "email": "support@hpindia.com", "address": "Nehru Place, Delhi"},
    {"name": "Samsung Electronics", "contact": "Pooja Patel", "phone": "9876543214", "email": "b2b@samsung.com", "address": "Electronic City, Noida"},
    {"name": "Logitech Tech", "contact": "Amitabh Sen", "phone": "9876543215", "email": "orders@logitech.com", "address": "Viman Nagar, Pune"}
]

# Supported Branches
BRANCHES = ["Varanasi", "Agra", "Noida", "Greater Noida"]

def get_clean_sub_category_name() -> str:
    """Returns a clean sub-category name containing ZERO numbers."""
    return random.choice(CLEAN_SUB_CATEGORIES)

def get_clean_vendor_details() -> dict:
    """Returns clean corporate vendor details containing ZERO numbers in vendor name."""
    return random.choice(CLEAN_VENDORS)
