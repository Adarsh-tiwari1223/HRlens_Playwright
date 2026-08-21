"""
Vendor Test Data Factory.
Generates complete, unique, and realistic Vendor entities.
"""

import random
import time
from faker import Faker

fake = Faker("en_IN")


class VendorFactory:
    """Factory for generating unique, realistic Vendor test data."""

    @staticmethod
    def _generate_gst() -> str:
        # Standard Indian GSTIN format: 2-digit state code + 10-char PAN + 1-digit entity + Z + 1 check digit
        state_code = f"{random.randint(1, 37):02d}"
        pan_chars = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=5))
        pan_digits = f"{random.randint(1000, 9999)}"
        pan_last = random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
        entity_num = random.choice("123456789")
        check_digit = random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        return f"{state_code}{pan_chars}{pan_digits}{pan_last}{entity_num}Z{check_digit}"

    @classmethod
    def create(cls, **overrides) -> dict:
        unique_token = f"{int(time.time() * 1000) % 1000000:06d}{random.randint(10, 99)}"
        company_suffix = random.choice(["Enterprises", "Solutions", "Technologies", "Infotech", "Systems", "Logistics", "Services"])
        vendor_name = f"{fake.last_name()} {company_suffix} {unique_token}"
        contact_person = f"{fake.first_name()} {fake.last_name()}"
        email_clean = contact_person.lower().replace(" ", ".")
        email = f"{email_clean}.{unique_token}@vendorinfratest.com"
        phone = f"{random.choice(['9', '8', '7'])}{fake.numerify('#########')}"
        gst = cls._generate_gst()

        data = {
            "vendor_name": vendor_name,
            "contact_person": contact_person,
            "email": email,
            "phone": phone,
            "gst": gst,
            "pan": gst[2:12],
            "address": fake.street_address(),
            "city": fake.city(),
            "state": "Uttar Pradesh",
            "pincode": "221005",
            "country": "India",
        }
        data.update(overrides)
        return data
