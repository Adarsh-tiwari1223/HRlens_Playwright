import random
from dataclasses import dataclass, asdict
from datetime import timedelta
from faker import Faker

fake = Faker("en_IN")

# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE ASSET SPECIFICATION TEMPLATES (VALID MAPPINGS ONLY)
# ══════════════════════════════════════════════════════════════════════════════

ASSET_TEMPLATES = {
    "IT Hardware": {
        "Laptop": [
            {
                "brand": "Dell",
                "model": "Latitude 7440",
                "os": "Windows 11 Pro",
                "processor": "Intel Core i7-1365U",
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "screen_size": "14\" FHD+",
                "color": "Titan Gray",
                "prefix": "LAP"
            },
            {
                "brand": "Lenovo",
                "model": "ThinkPad T14 Gen 4",
                "os": "Windows 11 Pro",
                "processor": "AMD Ryzen 7 PRO 7840U",
                "ram": "32 GB",
                "storage": "1 TB SSD",
                "screen_size": "14\" WUXGA",
                "color": "Thunder Black",
                "prefix": "LAP"
            },
            {
                "brand": "Apple",
                "model": "MacBook Pro 14\"",
                "os": "macOS Sonoma",
                "processor": "Apple M3 Pro",
                "ram": "18 GB",
                "storage": "512 GB SSD",
                "screen_size": "14.2\" Liquid Retina XDR",
                "color": "Space Black",
                "prefix": "MAC"
            }
        ],
        "Desktop": [
            {
                "brand": "HP",
                "model": "ProDesk 600 G9",
                "os": "Windows 11 Pro",
                "processor": "Intel Core i5-13500",
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "screen_size": "N/A",
                "color": "Jack Black",
                "prefix": "DT"
            },
            {
                "brand": "Dell",
                "model": "OptiPlex 7010 Micro",
                "os": "Windows 11 Pro",
                "processor": "Intel Core i7-13700T",
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "screen_size": "N/A",
                "color": "Carbon Black",
                "prefix": "DT"
            }
        ],
        "Server": [
            {
                "brand": "Dell EMC",
                "model": "PowerEdge R760",
                "os": "Red Hat Enterprise Linux 9",
                "processor": "Dual Intel Xeon Silver 4410Y",
                "ram": "128 GB",
                "storage": "4x 2.4TB SAS HDD RAID 5",
                "screen_size": "N/A",
                "color": "Metallic Silver",
                "prefix": "SRV"
            },
            {
                "brand": "HPE",
                "model": "ProLiant DL360 Gen11",
                "os": "VMware ESXi 8.0",
                "processor": "Intel Xeon Gold 5415+",
                "ram": "64 GB",
                "storage": "2x 960GB SATA SSD RAID 1",
                "screen_size": "N/A",
                "color": "Metallic Silver",
                "prefix": "SRV"
            }
        ]
    },
    "Peripherals": {
        "Monitor": [
            {
                "brand": "LG",
                "model": "27UP850-W",
                "os": "N/A",
                "processor": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "screen_size": "27\"",
                "color": "White/Silver",
                "prefix": "MON"
            },
            {
                "brand": "Dell",
                "model": "UltraSharp U2424H",
                "os": "N/A",
                "processor": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "screen_size": "24\"",
                "color": "Platinum Silver",
                "prefix": "MON"
            }
        ],
        "Mouse": [
            {
                "brand": "Logitech",
                "model": "MX Master 3S",
                "os": "N/A",
                "processor": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "screen_size": "N/A",
                "color": "Graphite",
                "prefix": "MSE"
            }
        ],
        "Keyboard": [
            {
                "brand": "Logitech",
                "model": "MX Keys S",
                "os": "N/A",
                "processor": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "screen_size": "N/A",
                "color": "Pale Gray",
                "prefix": "KBD"
            }
        ]
    },
    "Networking": {
        "Router": [
            {
                "brand": "Cisco",
                "model": "ISR 4331",
                "os": "Cisco IOS XE",
                "processor": "Multi-Core CPU",
                "ram": "4 GB",
                "storage": "4 GB Flash",
                "screen_size": "N/A",
                "color": "Dark Gray",
                "prefix": "RTR"
            }
        ],
        "Switch": [
            {
                "brand": "Cisco",
                "model": "Catalyst 9200",
                "os": "Cisco IOS XE",
                "processor": "UADP 2.0 Sec",
                "ram": "4 GB",
                "storage": "4 GB Flash",
                "screen_size": "N/A",
                "color": "Silver/Gray",
                "prefix": "SW"
            }
        ],
        "Access Point": [
            {
                "brand": "Aruba",
                "model": "AP-515",
                "os": "ArubaOS",
                "processor": "IPQ8074",
                "ram": "1 GB",
                "storage": "512 MB Flash",
                "screen_size": "N/A",
                "color": "Polar White",
                "prefix": "AP"
            }
        ]
    },
    "Printing Devices": {
        "Printer": [
            {
                "brand": "Brother",
                "model": "HL-L8360CDW",
                "os": "Brother Firmware",
                "processor": "800MHz",
                "ram": "512 MB",
                "storage": "N/A",
                "screen_size": "N/A",
                "color": "Off-White",
                "prefix": "PRN"
            }
        ],
        "Scanner": [
            {
                "brand": "Fujitsu",
                "model": "ScanSnap iX1600",
                "os": "ScanSnap Firmware",
                "processor": "Dual-Core",
                "ram": "N/A",
                "storage": "N/A",
                "screen_size": "4.3\"",
                "color": "Soft White",
                "prefix": "SCN"
            }
        ]
    },
    "Mobile Devices": {
        "Mobile": [
            {
                "brand": "Samsung",
                "model": "Galaxy S24",
                "os": "Android 14",
                "processor": "Exynos 2400",
                "ram": "8 GB",
                "storage": "256 GB",
                "screen_size": "6.2\"",
                "color": "Onyx Black",
                "prefix": "MOB"
            },
            {
                "brand": "Apple",
                "model": "iPhone 15 Pro",
                "os": "iOS 17",
                "processor": "A17 Pro",
                "ram": "8 GB",
                "storage": "128 GB",
                "screen_size": "6.1\"",
                "color": "Natural Titanium",
                "prefix": "MOB"
            }
        ]
    }
}

BRANCHES = ["Noida HQ", "Bangalore Tech Park", "Pune Development Center", "Mumbai Corporate", "Hyderabad R&D"]
DEPARTMENTS = ["Engineering", "Information Technology", "Finance & Accounts", "Human Resources", "Sales & Marketing"]
CURRENCIES = ["INR", "USD", "EUR", "GBP"]
STATUSES = ["Available", "Assigned", "In Repair", "Under Maintenance", "Retired", "Lost", "Scrapped"]
CONDITIONS = ["New", "Excellent", "Good", "Fair", "Poor"]
OWNERSHIPS = ["Owned", "Leased", "Rented"]
DEPRECIATION_METHODS = ["Straight Line", "Double Declining Balance", "Sum of the Years Digits", "Units of Production"]


# ══════════════════════════════════════════════════════════════════════════════
# DATACLASS DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

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
        return asdict(self)


@dataclass
class AssetData:
    company: str
    branch: str
    department: str
    category: str
    sub_category: str
    asset_name: str
    asset_code: str
    asset_tag: str
    brand: str
    model: str
    serial_number: str
    manufacturer: str
    vendor_name: str
    vendor_email: str
    vendor_phone: str
    vendor_gstin: str
    po_number: str
    invoice_number: str
    purchase_date: str
    installation_date: str
    warranty_start: str
    warranty_end: str
    cost: float
    currency: str
    location: str
    floor: int
    room_number: str
    rack_number: str
    assigned_employee: str
    employee_id: str
    condition: str
    status: str
    ownership: str
    useful_life_years: int
    depreciation_method: str
    mac_address: str
    imei: str
    ip_address: str
    os: str
    processor: str
    ram: str
    storage: str
    screen_size: str
    color: str
    description: str
    remarks: str

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# DATA GENERATION FACTORY
# ══════════════════════════════════════════════════════════════════════════════

class BusinessTestData:
    """Enterprise-Quality, valid, non-robotic dynamic test data generator."""

    @staticmethod
    def get_unique_suffix() -> int:
        return random.randint(10000, 99999)

    @classmethod
    def state_branch_pair(cls, state: str = None, branch: str = None) -> tuple[str, str]:
        """Returns a consistent State and Branch combination."""
        pairs = [
            ("UttarPradesh", "Varanasi"),
            ("Maharashtra", "Mumbai"),
            ("Karnataka", "Bengaluru"),
            ("Delhi", "NewDelhi"),
            ("Telangana", "Hyderabad"),
            ("TamilNadu", "Chennai"),
            ("Gujarat", "Ahmedabad"),
            ("WestBengal", "Kolkata")
        ]
        if state and branch:
            return state, branch
        return random.choice(pairs)

    @classmethod
    def geo_category_name(cls, prefix: str = "Hardware", state: str = None, branch: str = None) -> str:
        """
        Generates Category Name following pattern:
        Hardware-{State}-{Branch} (e.g. Hardware-UttarPradesh-Varanasi)
        """
        s, b = cls.state_branch_pair(state, branch)
        return f"{prefix}-{s}-{b}"

    @classmethod
    def geo_sub_category_names(cls, state: str = None, branch: str = None) -> list[str]:
        """
        Generates Sub-Categories following pattern with consistent State + Branch:
        [
            Laptop-{State}-{Branch},
            Desktop-{State}-{Branch},
            Monitor-{State}-{Branch}
        ]
        """
        s, b = cls.state_branch_pair(state, branch)
        return [
            f"Laptop-{s}-{b}",
            f"Desktop-{s}-{b}",
            f"Monitor-{s}-{b}"
        ]

    @classmethod
    def category_name(cls, base_name: str = None) -> str:
        """Generates a clean single enterprise asset category name (e.g. 'Hardware', 'Software')."""
        if base_name:
            return base_name
        return random.choice(["Hardware", "Software", "Peripherals", "Office Equipment"])

    @classmethod
    def sub_category_name(cls, base_name: str = None) -> str:
        """Generates a clean single enterprise asset sub-category name (e.g. 'Laptop', 'Desktop')."""
        if base_name:
            return base_name
        return random.choice(["Laptop", "Desktop", "Monitor", "Printer", "Scanner"])

    @classmethod
    def branch_group_name(cls, base_name: str = None) -> str:
        """Generates a realistic corporate branch group division."""
        base = base_name if base_name else "Regional Cluster"
        return f"{base} - {fake.city()} Area"

    @classmethod
    def vendor(cls, company_name: str = None) -> VendorData:
        """Generates realistic Indian enterprise vendor information."""
        suffix = cls.get_unique_suffix()
        
        # Indian corporate name structure
        if not company_name:
            org_name = fake.company()
            if not org_name.endswith("Ltd") and not org_name.endswith("Pvt Ltd"):
                org_name = f"{org_name} Technologies Pvt Ltd"
        else:
            org_name = company_name
            if not org_name.endswith("Ltd") and not org_name.endswith("Pvt Ltd"):
                org_name = f"{org_name} {suffix} Solutions Pvt Ltd"
            else:
                org_name = f"{org_name} {suffix}"

        first_name = fake.first_name()
        last_name = fake.last_name()
        contact_person = f"{first_name} {last_name}"

        # Production-grade domain name mapping
        clean_org = org_name.lower().replace("pvt", "").replace("ltd", "").replace("solutions", "").replace("tech", "").replace("india", "").replace(" ", "").replace(".", "").replace(",", "")[:15]
        domain = f"{clean_org}{suffix % 100}"
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}.co.in"

        # Indian phone number starting with valid prefix
        phone = fake.numerify(random.choice(["9#########", "8#########", "7#########", "6#########"]))

        # Indian GSTIN format: State Code (2d) + PAN (10 chars) + Entity (1d) + Z (1d) + Check (1d)
        state_code = random.choice(["09", "27", "29", "22", "07", "33", "19", "24"])
        pan_letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        pan_digits = f"{random.randint(1000, 9999)}"
        pan_char = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        gstin = f"{state_code}{pan_letters}{pan_digits}{pan_char}1Z{random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"

        address = f"{fake.street_address()}, Sector {random.randint(1, 120)}, {fake.city()}, {fake.state()}"

        return VendorData(
            name=org_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            gst=gstin,
            address=address,
            supports_amc=random.choice([True, False])
        )

    @classmethod
    def generate_asset(cls, category: str = None, sub_category: str = None) -> AssetData:
        """Generates realistic asset inventory records with fully consistent parameters."""
        suffix = cls.get_unique_suffix()

        # Resolve category
        if not category:
            category = random.choice(list(ASSET_TEMPLATES.keys()))
        
        # Resolve sub-category
        if category not in ASSET_TEMPLATES:
            # Fallback to random template entry
            category = random.choice(list(ASSET_TEMPLATES.keys()))
        
        sub_categories_dict = ASSET_TEMPLATES[category]
        if not sub_category or sub_category not in sub_categories_dict:
            sub_category = random.choice(list(sub_categories_dict.keys()))

        # Resolve spec details from mock data
        spec = random.choice(sub_categories_dict[sub_category])
        brand = spec["brand"]
        model = spec["model"]
        prefix = spec["prefix"]

        # Date consistency
        purchase_date = fake.date_between(start_date='-4y', end_date='-10d')
        installation_date = purchase_date + timedelta(days=random.randint(2, 8))
        warranty_start = installation_date
        warranty_end = warranty_start + timedelta(days=365 * random.choice([1, 3, 5]))

        # Unique tags
        asset_name = f"{brand} {model}"
        asset_code = f"AST-{prefix}-{suffix}"
        asset_tag = f"TAG-{prefix}-{random.randint(100000, 999999)}"
        serial_number = f"SN{brand[:3].upper()}{random.randint(10000, 99999)}{random.choice('XYZ')}"

        # Indian corporate environment setup
        company = fake.company()
        branch = random.choice(BRANCHES)
        department = random.choice(DEPARTMENTS)
        location = f"{branch} - Wing {random.choice(['A', 'B', 'C', 'D'])}"
        floor = random.randint(1, 5)
        room_number = f"Office Room {floor}0{random.randint(1, 9)}"
        rack_number = f"RACK-{prefix[:2]}-{random.randint(10, 99)}" if prefix in ["SRV", "RTR", "SW"] else "N/A"

        # Vendor selection
        vend = cls.vendor()

        # Costing
        cost = round(random.uniform(15000.0, 350000.0), 2)
        currency = "INR" if cost > 10000 else random.choice(CURRENCIES)

        # Technical networking spec dependencies
        mac_address = fake.mac_address() if prefix in ["LAP", "DT", "SRV", "RTR", "SW", "AP", "PRN"] else "N/A"
        ip_address = f"192.168.{random.randint(10, 50)}.{random.randint(2, 254)}" if prefix in ["SRV", "RTR", "SW", "AP", "PRN"] else "N/A"
        imei = fake.numerify("35##############") if prefix == "MOB" else "N/A"

        # Assigned employee
        assigned_employee = f"{fake.first_name()} {fake.last_name()}"
        employee_id = f"EMP-{random.randint(1000, 9999)}"

        useful_life = random.choice([3, 5, 7])
        description = f"Enterprise asset deployed in {department} at {branch} branch."
        remarks = f"Quality audit passed on {installation_date}."

        return AssetData(
            company=company,
            branch=branch,
            department=department,
            category=category,
            sub_category=sub_category,
            asset_name=asset_name,
            asset_code=asset_code,
            asset_tag=asset_tag,
            brand=brand,
            model=model,
            serial_number=serial_number,
            manufacturer=brand,
            vendor_name=vend.name,
            vendor_email=vend.email,
            vendor_phone=vend.phone,
            vendor_gstin=vend.gst,
            po_number=f"PO-{random.randint(10000, 99999)}",
            invoice_number=f"INV-{random.randint(10000, 99999)}",
            purchase_date=purchase_date.strftime("%d-%m-%Y"),
            installation_date=installation_date.strftime("%d-%m-%Y"),
            warranty_start=warranty_start.strftime("%d-%m-%Y"),
            warranty_end=warranty_end.strftime("%d-%m-%Y"),
            cost=cost,
            currency=currency,
            location=location,
            floor=floor,
            room_number=room_number,
            rack_number=rack_number,
            assigned_employee=assigned_employee,
            employee_id=employee_id,
            condition=random.choice(CONDITIONS),
            status=random.choice(STATUSES),
            ownership=random.choice(OWNERSHIPS),
            useful_life_years=useful_life,
            depreciation_method=random.choice(DEPRECIATION_METHODS),
            mac_address=mac_address,
            imei=imei,
            ip_address=ip_address,
            os=spec.get("os", "N/A"),
            processor=spec.get("processor", "N/A"),
            ram=spec.get("ram", "N/A"),
            storage=spec.get("storage", "N/A"),
            screen_size=spec.get("screen_size", "N/A"),
            color=spec.get("color", "N/A"),
            description=description,
            remarks=remarks
        )

    @classmethod
    def get_branch_dictionary_by_name(cls, city_name: str = "Agra") -> list[dict]:
        """Grab all branch dictionaries matching a city name from the branch API."""
        try:
            from utils.api.payroll_api import get_branches
            all_branches = get_branches()
            matched = [
                {
                    "id": b.get("id"),
                    "branch_name": b.get("branch_Name"),
                    "company_name": b.get("company_Name")
                }
                for b in all_branches
                if b.get("branch_Name") and city_name.lower() in b.get("branch_Name").lower()
            ]
            return matched
        except Exception:
            return []

    @classmethod
    def get_branch_groups_map_from_api(cls) -> dict[str, list[str]]:
        """
        Fetch all branches via API (GET /Hrlense_Branch) and group them by branch city/name.
        Returns a dictionary mapping each branch city to all company branch records lying in that city.
        e.g. {"Varanasi": ["Varanasi"], "Agra": ["Agra"], "Noida": ["Noida"]}
        """
        try:
            from utils.api.payroll_api import get_branches
            all_branches = get_branches()
            branch_map = {}
            for b in all_branches:
                b_name = b.get("branch_Name", "").strip()
                if not b_name:
                    continue
                city = b_name.split("(")[0].strip() if "(" in b_name else b_name
                if city not in branch_map:
                    branch_map[city] = []
                if b_name not in branch_map[city]:
                    branch_map[city].append(b_name)
            return branch_map
        except Exception:
            return {"Varanasi": ["Varanasi"], "Agra": ["Agra"], "Noida": ["Noida"]}

    @classmethod
    def get_employees_by_department(cls, department_filter_ids: list[int] = None) -> list[dict]:
        """Fetch employees filtered by department ID(s) from the Employee API (daily disk cached)."""
        try:
            from utils.api.payroll_api import get_employees_by_department
            from testdata.dynamic.daily_cache import get_daily_cached_data
            dept_ids = department_filter_ids or [4]
            key = f"employees_dept_{'_'.join(map(str, dept_ids))}"
            return get_daily_cached_data(key, lambda: get_employees_by_department(department_filter_ids=dept_ids))
        except Exception:
            return []

    @classmethod
    def get_companies(cls) -> list[dict]:
        """Fetch company master records from the Company API (daily disk cached)."""
        try:
            from utils.api.payroll_api import get_companies
            from testdata.dynamic.daily_cache import get_daily_cached_data
            return get_daily_cached_data("us_companies_master", get_companies)
        except Exception:
            return []

    @classmethod
    def get_payroll_companies(cls) -> list[dict]:
        """Fetch payroll company master records from the Payroll Company API (daily disk cached)."""
        try:
            from utils.api.payroll_api import get_payroll_companies
            from testdata.dynamic.daily_cache import get_daily_cached_data
            return get_daily_cached_data("payroll_companies_master", get_payroll_companies)
        except Exception:
            return []


class VendorTestData:
    @staticmethod
    def generate(name_prefix: str = None) -> VendorData:
        return BusinessTestData.vendor(company_name=name_prefix)


@dataclass
class DirectorData:
    director_name: str
    us_company_shares: dict
    payroll_company_shares: dict


@dataclass
class DirectorDocumentData:
    document_type: str
    document_number: str
    issue_date: str
    expiry_date: str
    file_name: str


class DirectorTestData:
    @staticmethod
    def generate_manual_director() -> dict:
        fn = fake.first_name()
        ln = fake.last_name()
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{random.randint(100, 999)}@tekinspirations.com"
        phone = fake.numerify("9#########")
        return {
            "name": name,
            "email": email,
            "phone": phone
        }

    @staticmethod
    def generate_director() -> DirectorData:
        return DirectorData(
            director_name=f"{fake.first_name()} {fake.last_name()}",
            us_company_shares={"CompanyA": random.randint(10, 50)},
            payroll_company_shares={"Adventa": random.randint(10, 50)}
        )

    @staticmethod
    def generate_document(doc_type: str = "PAN") -> DirectorDocumentData:
        if doc_type.upper() == "PAN":
            num = f"{fake.lexify('?????').upper()}{fake.numerify('####')}{fake.lexify('?').upper()}"
        elif doc_type.upper() == "AADHAAR":
            num = fake.numerify("############")
        elif doc_type.upper() == "PASSPORT":
            num = f"{fake.lexify('?').upper()}{fake.numerify('#######')}"
        else:
            num = f"DOC-{fake.numerify('#####')}"

        today = fake.date_this_year()
        future = fake.date_between(start_date="+1y", end_date="+5y")

        return DirectorDocumentData(
            document_type=doc_type,
            document_number=num,
            issue_date=today.strftime("%Y-%m-%d"),
            expiry_date=future.strftime("%Y-%m-%d"),
            file_name=f"{doc_type.lower()}_sample.pdf"
        )

class LocationTestData:
    """Provides a list of all countries with valid zip codes for dynamic country selection and location lookup."""

    COUNTRY_ZIP_MAP = [
        # India
        {"country": "India", "zip_code": "221005", "expected_state": "Uttar Pradesh", "expected_city": "Varanasi"},
        # {"country": "India", "zip_code": "110001", "expected_state": "Delhi", "expected_city": "Central Delhi"},
        {"country": "India", "zip_code": "400001", "expected_state": "Maharashtra", "expected_city": "Mumbai"},
        {"country": "India", "zip_code": "560001", "expected_state": "Karnataka", "expected_city": "Bangalore"},
        # United States
        {"country": "United States", "zip_code": "90210", "expected_state": "California", "expected_city": "Beverly Hills"},
        {"country": "United States", "zip_code": "10001", "expected_state": "New York", "expected_city": "New York"},
        # Australia
        {"country": "Australia", "zip_code": "2000", "expected_state": "New South Wales", "expected_city": "Sydney"},
        # Germany
        {"country": "Germany", "zip_code": "10115", "expected_state": "Berlin", "expected_city": "Berlin"}
    ]

    @classmethod
    def get_random_country_and_zip(cls) -> dict:
        """Pick a country at random with equal probability among all unique countries, then pick its valid zip code."""
        unique_countries = sorted(list({loc["country"] for loc in cls.COUNTRY_ZIP_MAP}))
        chosen_country = random.choice(unique_countries)
        country_locations = [loc for loc in cls.COUNTRY_ZIP_MAP if loc["country"] == chosen_country]
        return random.choice(country_locations)

    @classmethod
    def get_locations_by_country(cls, country: str) -> list[dict]:
        return [loc for loc in cls.COUNTRY_ZIP_MAP if country.lower() in loc["country"].lower()]
