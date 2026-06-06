# ── Appointment Letter Template — Static Sections ────────────────────────────
# This defines the standardized sections required for the Appointment Letter Template.
# These will be enforced across all companies.

APPOINTMENT_LETTER_SECTIONS = [
    {
        "order": 1,
        "key": "OPENING",
        "title": "Opening",
        "content": (
            "We are pleased to appoint you in our organization as {JOB_PROFILE}."
            " Your appointment is subject to your joining on or before {DOJ}."
            "|Please ensure you bring all required documentation on your first day."
        ),
        "style": "Paragraph"
    },
    {
        "order": 2,
        "key": "ASSIGNMENT",
        "title": "Assignment",
        "content": (
            "You will be assigned to work on the primary project immediately."
            "|Your duties and responsibilities will be outlined by your reporting manager."
            "|You may be transferred to any other department or branch as required."
        ),
        "style": "Paragraph"
    },
    {
        "order": 3,
        "key": "COMPENSATION",
        "title": "Compensation",
        "content": (
            "Your total Annual CTC will be Rs. {ANNUAL_CTC}/-."
            "|Your Monthly CTC will be Rs. {MONTHLY_CTC}/-."
            "|All payments are subject to standard statutory deductions."
        ),
        "style": "Bullet Points"
    },
    {
        "order": 4,
        "key": "DEDUCTION",
        "title": "Deduction",
        "content": (
            "Statutory deductions like PF, PT, and TDS will be applicable as per law."
            "|Any unauthorized absence will result in a deduction from your monthly salary."
        ),
        "style": "Bullet Points"
    },
    {
        "order": 5,
        "key": "RESTRAINTS",
        "title": "Restraints",
        "content": (
            "You are not allowed to take up any other employment during your tenure with {COMPANY_NAME}."
            "|You must strictly maintain the confidentiality of all company data and trade secrets."
        ),
        "style": "Numbered List"
    },
    {
        "order": 6,
        "key": "PROBATION",
        "title": "Probation",
        "content": (
            "You will be on a probation period of 90 days from your Date of Joining ({DOJ})."
            "|Your confirmation will be subject to a performance review at the end of this period."
        ),
        "style": "Paragraph"
    },
    {
        "order": 7,
        "key": "LEAVE",
        "title": "Leave",
        "content": (
            "You are entitled to leaves as per the company leave policy."
            "|Leaves can only be availed after the successful completion of your probation period."
        ),
        "style": "Bullet Points"
    },
    {
        "order": 8,
        "key": "TERMINATION",
        "title": "Termination",
        "content": (
            "The company reserves the right to terminate your employment with 30 days notice."
            "|In case of gross misconduct, the company may terminate your employment immediately without notice."
        ),
        "style": "Numbered List"
    },
    {
        "order": 9,
        "key": "GENERAL",
        "title": "General Terms",
        "content": (
            "You will be governed by the standard rules and regulations of {COMPANY_NAME}."
            "|Any disputes will be subject to the local jurisdiction."
        ),
        "style": "Paragraph"
    },
    {
        "order": 10,
        "key": "CUSTOM",
        "title": "Custom Clause",
        "content": (
            "Any custom terms specific to this candidate will be listed here."
            "|These terms supersede any standard terms mentioned above."
        ),
        "style": "Paragraph"
    },
    {
        "order": 11,
        "key": "CLOSING",
        "title": "Closing",
        "content": (
            "Please sign and return a copy of this letter as a token of your acceptance."
            "|We welcome you to {COMPANY_NAME} and wish you a successful career with us!"
        ),
        "style": "Signature Block"
    }
]
