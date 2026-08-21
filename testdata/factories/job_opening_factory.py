"""
Job Opening Test Data Factory.
Generates complete, valid, and realistic Job Opening entities for recruitment workflows.
"""

import random
import time
from faker import Faker

fake = Faker("en_IN")


class JobOpeningFactory:
    """Factory for generating realistic Job Opening test data."""

    ROLES = [
        {"title": "Senior Python Automation Engineer", "dept": "Quality Assurance", "skills": ["Python", "Playwright", "Pytest", "CI/CD"]},
        {"title": "Full Stack React Developer", "dept": "Software Engineering", "skills": ["React", "TypeScript", "Node.js", "PostgreSQL"]},
        {"title": "DevOps & Cloud Engineer", "dept": "Infrastructure", "skills": ["AWS", "Docker", "Kubernetes", "Terraform"]},
        {"title": "Backend Python Developer", "dept": "Software Engineering", "skills": ["Python", "FastAPI", "Redis", "SQLAlchemy"]},
    ]

    @classmethod
    def create(cls, **overrides) -> dict:
        preset = random.choice(cls.ROLES)
        unique_token = f"{int(time.time() * 1000) % 1000000:06d}{random.randint(100, 999)}"
        job_title = f"{preset['title']} - {unique_token}"
        min_exp = random.randint(1, 4)
        max_exp = min_exp + random.randint(2, 5)

        data = {
            "job_title": job_title,
            "department": preset["dept"],
            "designation": preset["title"].split()[0] + " Specialist",
            "branch": "Varanasi",
            "vacancies": str(random.randint(1, 5)),
            "experience_min": str(min_exp),
            "experience_max": str(max_exp),
            "salary_min": "500000",
            "salary_max": "1200000",
            "skills": preset["skills"],
            "work_mode": "Hybrid",
            "employment_type": "Full Time",
            "job_description": (
                f"We are seeking an experienced {job_title} to join our technology team in Varanasi. "
                f"The candidate must possess strong proficiency in {', '.join(preset['skills'])} and enterprise architecture."
            ),
        }
        data.update(overrides)
        return data
