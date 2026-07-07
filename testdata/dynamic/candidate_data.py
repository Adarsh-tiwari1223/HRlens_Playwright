import time
import random
import re
from faker import Faker

# Force Indian localization for authentic Indian names
fake = Faker('en_IN')

# Strict constraint: Only generate locations in Uttar Pradesh
UP_CITIES = [
    "Lucknow", "Kanpur", "Varanasi", "Agra", "Noida", 
    "Prayagraj", "Ghaziabad", "Meerut", "Bareilly", "Aligarh", 
    "Moradabad", "Saharanpur", "Gorakhpur", "Firozabad", "Jhansi", 
    "Muzaffarnagar", "Mathura"
]

def generate_candidate_data(is_experienced: bool = False) -> dict:
    """
    Generates dynamic candidate data using Faker, constrained to Indian names
    and Uttar Pradesh cities. Uses Gmail plus-addressing to avoid duplicate email errors.
    """
    # Randomly decide gender to ensure authentic names match the Gender dropdown
    is_male = random.choice([True, False])
    name = fake.name_male() if is_male else fake.name_female()
    
    # Use the Gmail "Dot Trick" to avoid duplicate validation without breaking URL encoding.
    # Gmail completely ignores dots, so all combinations safely route to qatekinspirations@gmail.com
    base_chars = list("qatekinspirations")
    dot_injected = ""
    for i, char in enumerate(base_chars):
        dot_injected += char
        # Randomly inject a dot between characters (but not after the last character)
        if i < len(base_chars) - 1 and random.choice([True, False]):
            dot_injected += "."
            
    email = f"{dot_injected}@gmail.com"
    
    # Generate a realistic 10-digit Indian phone number
    phone = f"{random.choice(['9', '8', '7'])}{fake.numerify('#########')}"
    
    data = {
        "name": name,
        "gender": "1" if is_male else "2",  # Assuming 1 is Male, 2 is Female
        "email": email,
        "phone": phone,
        "location": random.choice(UP_CITIES),
        # Using the exact select_option values from the user's trace
        "work_mode": "3", 
        "hiring_category": "3",
        "has_experience": is_experienced
    }
    
    if is_experienced:
        data.update({
            "experience_months": str(random.randint(12, 120)), # 1 to 10 years
            "current_salary": str(random.randint(300000, 1500000)),
            "expected_salary": str(random.randint(500000, 2000000)),
            "notice_period": random.choice(["15", "30", "60", "90"])
        })
        
    return data
