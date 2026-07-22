import random
import time
from dataclasses import dataclass
from faker import Faker

fake = Faker("en_IN")

CATEGORIES = [
    "IT Hardware",
    "Networking",
    "Peripherals",
    "Office Equipment",
    "Furniture",
    "Software Licenses",
    "Mobile Devices",
    "Security Devices",
    "Printing Devices",
    "Storage Devices",
    "Biometric Devices",
    "Electrical Equipment",
    "Audio Video Equipment",
    "Office Supplies",
]

SUB_CATEGORIES = [
    "Laptop",
    "Desktop",
    "Mouse",
    "Keyboard",
    "Monitor",
    "Router",
    "Switch",
    "Printer",
    "Scanner",
    "Projector",
    "UPS",
    "Server",
    "Docking Station",
    "Webcam",
    "Headset",
    "Access Point",
]

VENDOR_COMPANIES = [
    "Tech Solutions Pvt Ltd",
    "ABC Technologies",
    "Prime IT Solutions",
    "Global Infotech",
    "NextGen Systems",
    "OfficeMart",
    "Dell India",
    "HP Enterprise",
    "Lenovo Partner",
    "Canon Solutions",
]

BRANCH_GROUPS = [
    "North Zone",
    "South Zone",
    "East Zone",
    "West Zone",
    "Corporate Offices",
    "Regional Offices",
    "Metro Branches",
]

INDIAN_CITIES = [
    "Noida",
    "Delhi",
    "Agra",
    "Lucknow",
    "Kanpur",
    "Varanasi",
    "Pune",
    "Mumbai",
    "Bangalore",
    "Hyderabad",
]


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


class BusinessTestData:
    """Centralized Enterprise Test Data Factory for HRlens."""

    @staticmethod
    def get_suffix() -> int:
        return random.randint(1000, 9999)

    @classmethod
    def category_name(cls, base_name: str = None) -> str:
        base = base_name if base_name else random.choice(CATEGORIES)
        return f"{base} {cls.get_suffix()}"

    @classmethod
    def sub_category_name(cls, base_name: str = None) -> str:
        base = base_name if base_name else random.choice(SUB_CATEGORIES)
        return f"{base} {cls.get_suffix()}"

    @classmethod
    def code_prefix(cls) -> str:
        return fake.lexify(text="???").upper()

    @classmethod
    def branch_group_name(cls, base_name: str = None) -> str:
        base = base_name if base_name else random.choice(BRANCH_GROUPS)
        return f"{base} {cls.get_suffix()}"

    @classmethod
    def vendor(cls, company_name: str = None) -> VendorData:
        suffix = cls.get_suffix()
        comp = company_name if company_name else random.choice(VENDOR_COMPANIES)
        full_vendor_name = f"{comp} {suffix}"

        first_name = fake.first_name()
        last_name = fake.last_name()
        contact_person = f"{first_name} {last_name}"

        domain = comp.lower().replace(" ", "").replace("pvt", "").replace("ltd", "").replace(".", "")[:12]
        email = f"{first_name.lower()}.{last_name.lower()}{suffix}@{domain}.com"

        phone = fake.numerify(random.choice(["9#########", "8#########", "7#########", "6#########"]))

        state_code = random.choice(["09", "27", "29", "22", "07"])
        pan_letters = fake.lexify(text="?????").upper()
        pan_digits = f"{suffix:0>4}"
        gst = f"{state_code}{pan_letters}{pan_digits}F1Z5"

        city = random.choice(INDIAN_CITIES)
        address = f"Plot {random.randint(10, 999)}, Sector {random.randint(1, 150)}, {city}"

        return VendorData(
            name=full_vendor_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            gst=gst,
            address=address,
            supports_amc=True,
        )


class VendorTestData:
    @staticmethod
    def generate(name_prefix: str = None) -> VendorData:
        return BusinessTestData.vendor(company_name=name_prefix)
