"""
Employee Test Data Factory.
Generates complete, valid, and realistic Employee entities with all required nested sections.
"""

import random
import time
from faker import Faker

fake = Faker("en_IN")


class EmployeeFactory:
    """Factory for generating unique, realistic Employee test data."""

    @classmethod
    def create(cls, **overrides) -> dict:
        unique_token = f"{int(time.time() * 1000) % 1000000:06d}{random.randint(10, 99)}"
        is_male = random.choice([True, False])
        first_name = fake.first_name_male() if is_male else fake.first_name_female()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        email_prefix = f"{first_name.lower()}.{last_name.lower()}.{unique_token}"
        official_email = f"{email_prefix}@tekinspirations.com"
        personal_email = f"{email_prefix}@gmail.com"
        phone = f"{random.choice(['9', '8', '7'])}{fake.numerify('#########')}"
        emergency_phone = f"{random.choice(['9', '8', '7'])}{fake.numerify('#########')}"

        pan_chars = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=5))
        pan_digits = f"{random.randint(1000, 9999)}"
        pan_last = random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
        pan_number = f"{pan_chars}{pan_digits}{pan_last}"

        aadhar_number = fake.numerify("############")
        account_number = fake.numerify("#############")
        ifsc_code = f"HDFC{fake.numerify('00#####')}"

        data = {
            "basic_details": {
                "full_name": full_name,
                "official_email": official_email,
                "personal_email": personal_email,
                "us_phone": "",
                "phone_number": phone,
                "date_of_birth": "1995-05-15",
                "date_of_joining": "2024-01-10",
                "gender": "Male" if is_male else "Female",
                "branch": "Varanasi",
                "department": "Software Engineering",
                "designation": "Software Engineer",
                "shift": "Day Shift",
                "role": "Employee",
                "blood_group": "O+",
                "current_address": fake.address().replace("\n", ", "),
                "permanent_address": fake.address().replace("\n", ", "),
                "emergency_contact_name": f"{fake.first_name()} {last_name}",
                "emergency_contact_number": emergency_phone,
            },
            "employment_experience": {
                "payroll_company": "TEK INSPIRATIONS",
                "business_process": "Information Technology",
                "reference": "Direct",
                "last_organization": "Tata Consultancy Services",
                "experience": "2",
            },
            "family_detail": [
                {
                    "relation": "Father",
                    "full_name": f"{fake.first_name_male()} {last_name}",
                    "gender": "Male",
                    "dob": "1968-08-20",
                }
            ],
            "salary_compensation": {
                "gross_salary": 650000,
            },
            "identity_bank": {
                "aadhar_number": aadhar_number,
                "pan_number": pan_number,
                "uan_number": fake.numerify("100#########"),
                "account_number": account_number,
                "ifsc_code": ifsc_code,
                "bank_name": "HDFC Bank",
                "branch": "Varanasi Main Branch",
            },
            "document_upload": {
                "document_type_1": "ID Proof",
                "document_name_1": "PAN Card",
                "document_number_1": pan_number,
                "document_file_1": "testdata/static/invoices/invoice_1mb.pdf",
            },
        }

        # Handle top-level overrides or nested merges
        for key, value in overrides.items():
            if key in data and isinstance(data[key], dict) and isinstance(value, dict):
                data[key].update(value)
            else:
                data[key] = value

        return data
