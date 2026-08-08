"""
Static Enterprise Asset Category and Sub-Category Test Data.
Used across Asset Master, Procurement, Entry, and Assignment workflows.
"""

ASSET_CATEGORIES_DATASET = [
    {
        "name": "Hardware",
        "subcategories": [
            {"name": "Desktop Computer", "code_prefix": "DES"},
            {"name": "Laptop", "code_prefix": "LAP"},
            {"name": "Monitor", "code_prefix": "MON"}
        ]
    },
    {
        "name": "Software",
        "subcategories": [
            {"name": "Operating System License", "code_prefix": "OSL"},
            {"name": "Microsoft Office License", "code_prefix": "MOL"},
            {"name": "Antivirus License", "code_prefix": "AVL"}
        ]
    },
    {
        "name": "Networking",
        "subcategories": [
            {"name": "Router", "code_prefix": "RTR"},
            {"name": "Network Switch", "code_prefix": "SWT"},
            {"name": "Wireless Access Point", "code_prefix": "WAP"}
        ]
    },
    {
        "name": "Peripheral",
        "subcategories": [
            {"name": "Keyboard", "code_prefix": "KEY"},
            {"name": "Mouse", "code_prefix": "MOU"},
            {"name": "Webcam", "code_prefix": "WEB"}
        ]
    },
    {
        "name": "Communication Equipment",
        "subcategories": [
            {"name": "IP Phone", "code_prefix": "IPP"},
            {"name": "Headset", "code_prefix": "HDS"},
            {"name": "Conference Phone", "code_prefix": "CPF"}
        ]
    }
]
