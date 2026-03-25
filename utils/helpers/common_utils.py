import random
import string
from datetime import datetime


def random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"{random_string()}@test.com"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
