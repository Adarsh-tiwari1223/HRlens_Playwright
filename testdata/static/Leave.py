import random


class Leave:
    LEAVE_DATA = [
        {"leave_type": "Vacation Leave"},
        {"leave_type": "Casual Leave"},
        {"leave_type": "Sick Leave"},
        {"leave_type": "Bereavement Leave"},
        {"leave_type": "Maternity Leave"},
        {"leave_type": "Paternity Leave"},
        {"leave_type": "Study Leave"},
        {"leave_type": "Emergency Leave"},
        {"leave_type": "Half-Day Leave"},
        {"leave_type": "Marriage Leave"},
        {"leave_type": "Personal Work Leave"},
        {"leave_type": "Medical Appointment"},
        {"leave_type": "Family Function"},
        {"leave_type": "Compensatory Off"},
    ]

    @classmethod
    def shuffled(cls) -> list:
        data = cls.LEAVE_DATA.copy()
        random.shuffle(data)
        return data
