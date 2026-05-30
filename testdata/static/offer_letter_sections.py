# ── Offer Letter Template — Section Definitions ───────────────────────────────
# Real template content for each section.
# Each entry:
#   key     → section type identifier (used for duplicate detection)
#   title   → section heading entered in the Title field of the form
#   content → body text, use | to separate items within a section
#
# Available placeholders in content:
#   {CANDIDATE_NAME}  {JOB_PROFILE}  {JOB_PROFILE_UPPER}  {DOJ}
#   {ANNUAL_CTC}      {ANNUAL_CTC_WORDS}  {COMPANY_NAME}

OFFER_LETTER_SECTIONS = [
    {
        "order": 1,
        "key": "OPENING",
        "title": "Opening",
        "content": (
            "With reference to your application and subsequent interview, we are pleased to offer you"
            " a promising career with us. Your appointment as a \"{JOB_PROFILE_UPPER}\" will be subject"
            " to your reporting from office on \"{DOJ}\"."
            "|Accordingly, the validity of this letter is subject to your joining as per the aforesaid"
            " date; else the letter shall automatically stand invalidated without any further obligations"
            " on the part of the organization."
        ),
    },
    {
        "order": 2,
        "key": "SALARY",
        "title": "Salary and Perks",
        "content": (
            "Your annual employment will cost the organization a total amount of Rs. {ANNUAL_CTC}/-"
            " ({ANNUAL_CTC_WORDS}) which will be your Annual CTC. For an overview on deductions,"
            " please refer to Annexure - B."
            "|Besides salary, based on your performance and the organizations overall performance,"
            " you will be eligible for variable pay/incentives or performance bonus."
            "|The organization reserves all the rights to make all kinds of decisions related to"
            " variable pay/incentives or performance bonus."
        ),
    },
    {
        "order": 3,
        "key": "PROBATION",
        "title": "Probation Period",
        "content": (
            "You will be on probation for a period of 90 days from the date of your joining the company,"
            " which may be extended if found necessary. While on probation, your services can be terminated"
            " at any time by the company, without notice or wages/compensation in lieu thereof."
        ),
    },
    {
        "order": 4,
        "key": "LEAVE",
        "title": "Leave",
        "content": (
            "You will be eligible for leave after completion of 90 days of your probation period."
            " There will be one paid leave per month, although we are 5 days working."
            "|Any leave taken during the probation period will result in a corresponding salary deduction."
            "|Accumulated leaves can be encashed in any subsequent month."
        ),
    },
    {
        "order": 5,
        "key": "NOTICE",
        "title": "Notice on Confirmation",
        "content": (
            "This engagement may be terminated by either party by giving the other a notice of 3 months"
            " in writing, or by paying wages/compensation for 90 days in lieu of notice."
        ),
    },
    {
        "order": 6,
        "key": "REPORTING",
        "title": "Reporting and Supervision",
        "content": (
            "You are appointed as {JOB_PROFILE} in the company. Reporting and supervision will be"
            " carried out with the help of analytics data received through the company portal."
            "|All charges for the company software will be borne by the company. You are not authorized"
            " to use the number or the software assigned to you for personal use."
            "|Your salary will be released as per the salary cycle of the company, i.e., salary from"
            " 1st to 30th released by 7th of the following month."
        ),
    },
    {
        "order": 7,
        "key": "CUSTOM",
        "title": "Custom Clause",
        "content": (
            "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor."
            " Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur"
            " ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem."
            " Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate"
            " eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum"
            " felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi."
            " Aenean vulputate eleifend tellus."
        ),
    },
    {
        "order": 8,
        "key": "CLOSING",
        "title": "Closing",
        "content": (
            "If you agree to all the terms and conditions, please acknowledge your acceptance by signing"
            " this letter. We look forward to a mutually rewarding relationship."
        ),
    },
]
