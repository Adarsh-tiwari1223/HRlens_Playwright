"""
Asset Test Data Factory.
Generates unique, realistic, and complete Asset entity definitions for inventory and procurement.
"""

import random
import time
from faker import Faker

fake = Faker("en_IN")


class AssetFactory:
    """Factory for generating unique, realistic Asset test data."""

    PRESETS = [
        {"brand": "Dell", "model": "Latitude 7440", "sub_category": "Laptop", "prefix": "LAP", "cost": "85000.00"},
        {"brand": "Lenovo", "model": "ThinkPad T14 Gen 4", "sub_category": "Laptop", "prefix": "LAP", "cost": "92000.00"},
        {"brand": "Apple", "model": "MacBook Pro 14\"", "sub_category": "Laptop", "prefix": "MAC", "cost": "165000.00"},
        {"brand": "HP", "model": "ProDesk 600 G9", "sub_category": "Desktop", "prefix": "DSK", "cost": "65000.00"},
        {"brand": "Dell", "model": "OptiPlex 7010 Micro", "sub_category": "Desktop", "prefix": "DSK", "cost": "58000.00"},
        {"brand": "Dell", "model": "UltraSharp 27 4K", "sub_category": "Monitor", "prefix": "MON", "cost": "32000.00"},
    ]

    @classmethod
    def create(cls, **overrides) -> dict:
        preset = random.choice(cls.PRESETS)
        unique_token = f"{int(time.time() * 1000) % 1000000:06d}{random.randint(100, 999)}"
        serial_number = f"SN-{preset['prefix']}-{unique_token}"
        asset_code = f"ASSET-{preset['prefix']}-2026-{unique_token}"
        asset_name = f"{preset['brand']} {preset['model']}"

        data = {
            "asset_name": asset_name,
            "asset_code": asset_code,
            "serial_number": serial_number,
            "category": "Hardware",
            "sub_category": preset["sub_category"],
            "brand": preset["brand"],
            "model": preset["model"],
            "vendor": "Dell India Enterprises",
            "branch": "Varanasi",
            "cost": preset["cost"],
            "purchase_date": "2026-01-15",
            "warranty_expiry": "2029-01-15",
            "condition": "New",
            "status": "Available",
            "specifications": {
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "processor": "Intel Core i7-1365U",
            }
        }
        data.update(overrides)
        return data
