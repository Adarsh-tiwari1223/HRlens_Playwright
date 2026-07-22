import time
from dataclasses import dataclass
from faker import Faker

fake = Faker()


@dataclass
class VendorData:
    name: str
    contact_person: str
    email: str
    phone: str
    gst: str
    address: str
    supports_amc: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "contact_person": self.contact_person,
            "email": self.email,
            "phone": self.phone,
            "gst": self.gst,
            "address": self.address,
            "supports_amc": self.supports_amc,
        }


class VendorTestData:
    @staticmethod
    def generate(name_prefix: str = "Vendor") -> VendorData:
        """Generates a fresh, unique Vendor dataset for test isolation."""
        unique_id = int(time.time() * 1000) % 1000000
        rand_digits = fake.random_number(digits=5, fix_len=True)
        
        phone = fake.numerify("9#########")
        email = f"vendor_{unique_id}_{rand_digits}@testdata.com"
        
        letters = fake.lexify(text="?????").upper()
        digits = f"{unique_id:0>4}"[:4]
        gst = f"22{letters}{digits}A1Z5"
        
        vendor_name = f"{name_prefix} {fake.company().replace(',', '').replace('.', '')[:12]} {rand_digits}"
        contact_person = f"{fake.first_name()} {fake.last_name()}"
        address = f"Suite {rand_digits} {fake.city()}"

        return VendorData(
            name=vendor_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            gst=gst,
            address=address,
            supports_amc=True,
        )

