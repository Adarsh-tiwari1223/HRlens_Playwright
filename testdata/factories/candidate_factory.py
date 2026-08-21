"""
Candidate Test Data Factory.
Generates unique, valid, and realistic Candidate entities for recruitment tests.
"""

import random
import time
from faker import Faker

fake = Faker("en_IN")

UP_CITIES = [
    "Lucknow", "Kanpur", "Varanasi", "Agra", "Noida",
    "Prayagraj", "Ghaziabad", "Meerut", "Bareilly", "Aligarh",
    "Moradabad", "Saharanpur", "Gorakhpur", "Firozabad", "Jhansi",
]


class CandidateFactory:
    """Factory for generating unique, realistic Candidate test data."""

    @classmethod
    def create(cls, is_experienced: bool = False, **overrides) -> dict:
        unique_token = f"{int(time.time() * 1000) % 1000000:06d}{random.randint(10, 99)}"
        is_male = random.choice([True, False])
        first_name = fake.first_name_male() if is_male else fake.first_name_female()
        last_name = fake.last_name()
        name = f"{first_name} {last_name}"

        # Unique email via token to avoid backend duplicate constraint failures
        email = f"{first_name.lower()}.{last_name.lower()}.{unique_token}@jobvrittatest.com"
        phone = f"{random.choice(['9', '8', '7'])}{fake.numerify('#########')}"

        data = {
            "name": name,
            "gender": "1" if is_male else "2",
            "email": email,
            "phone": phone,
            "location": random.choice(UP_CITIES),
            "work_mode": "3",
            "hiring_category": "3",
            "has_experience": is_experienced,
        }

        if is_experienced:
            data.update({
                "experience_months": str(random.randint(12, 120)),
                "current_salary": str(random.randint(300000, 1500000)),
                "expected_salary": str(random.randint(500000, 2000000)),
                "notice_period": random.choice(["15", "30", "60", "90"]),
            })

        data.update(overrides)
        return data
