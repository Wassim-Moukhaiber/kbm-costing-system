"""
KBM Pricing Delegation & Approval Matrix - Configuration Data
LOB hierarchies, approval matrices, cost sheet sections, and reference data.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# LOB & PROJECT CODE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PCS_LOB_OPTIONS = {
    "DIS": {
        "Networking": [
            "Network - Products Cisco & Non Cisco",
            "Network - SDDC",
            "Network - Professional Services",
        ],
        "Security Solutions": [
            "Security - Professional Services",
            "IBM SW - New",
            "IBM SW - Renewal",
            "Security Non IBM",
        ],
        "Infrastructure": [
            "Infra - Products",
            "Infra - Professional Services",
        ],
        "SDDC": [
            "PC", "Retail", "SDDC - HW, SW",
            "SDDC - Services", "Support Services",
        ],
        "NW Maint - Attached": [
            "Cisco & Non Cisco Maintenance",
            "KBM Comprehensive and Manufacture warranty",
            "NW Maint - Renewal",
        ],
    },
    "Digital Solution": {
        "Digital Solution": [
            "IBM New", "IBM Renewal",
            "Non IBM New & Renewal", "Services", "TSS",
        ],
    },
    "Managed Services": {
        "Managed Services": ["Managed Services"],
    },
    "Enterprise Systems": {
        "Enterprise Systems": ["Services", "Hardware"],
    },
}

PCS_TYPES = ["New", "Customer Change Request", "Correction"]
OPPORTUNITY_STATUSES = ["Qualifying", "Proposing", "Negotiating", "Closed Won"]

DOC_TYPES = [
    "Cost Sheet", "KBM Proposal", "Vendor / Supplier Quote",
    "Request for Proposal (RFP)", "Cisco Deal ID", "IBM SBO",
    "Email Correspondence", "Opportunity Qualification Sheet",
    "Quality Assurance Review (PQAR/SQAR)", "KBM Final Proposal", "Other",
]

PCM_CATEGORIES = {
    "TSS": ["IBM", "SystemX", "OEM", "Support Line"],
    "DIS": ["NW Maintenance", "NW Security"],
}

# ═══════════════════════════════════════════════════════════════════════════════
# APPROVAL MATRIX DATA
# ═══════════════════════════════════════════════════════════════════════════════

DIS_BID_SIZE_LEVELS = [
    {"level": 1, "role": "Delivery Manager",    "min_bid": 1},
    {"level": 2, "role": "User Manager",        "min_bid": 1},
    {"level": 3, "role": "SDDC & IBM Leader",   "min_bid": 300_000},
    {"level": 4, "role": "LOB Director",        "min_bid": 1_000_000},
    {"level": 5, "role": "BFO Finance Manager", "min_bid": 2_500_001},
    {"level": 6, "role": "CFO Finance",         "min_bid": 10_000_000},
    {"level": 7, "role": "CEO",                 "min_bid": 10_000_001},
]

DIS_MARGIN_MATRIX = {
    ("Networking", "Network - Products Cisco & Non Cisco"):
        [50.0, 50.0, 5.0, 4.0, 0.0, 0.0, -100.0],
    ("Networking", "Network - SDDC"):
        [50.0, 50.0, 5.0, 4.0, 0.0, 0.0, -100.0],
    ("Networking", "Network - Professional Services"):
        [50.0, 50.0, 20.0, 15.0, 0.0, 0.0, -100.0],
    ("Security Solutions", "Security - Professional Services"):
        [50.0, 50.0, 20.0, 15.0, 0.0, 0.0, -100.0],
    ("Security Solutions", "IBM SW - New"):
        [10.0, 7.0, 7.0, 7.0, -2.2, -2.2, -100.0],
    ("Security Solutions", "IBM SW - Renewal"):
        [4.0, 2.5, 2.5, 2.5, -7.8, -7.8, -100.0],
    ("Security Solutions", "Security Non IBM"):
        [20.0, 15.0, 10.0, 10.0, 0.0, 0.0, -100.0],
    ("Infrastructure", "Infra - Products"):
        [50.0, 49.0, 15.0, 8.5, 0.0, 0.0, -100.0],
    ("Infrastructure", "Infra - Professional Services"):
        [50.0, 50.0, 20.0, 15.0, 0.0, 0.0, -100.0],
    ("Infrastructure", "IBM HW - New (Power/Storage/FlashSystem)"):
        [50, 49, 15, 8.5, 0, 0, -100],
    ("Infrastructure", "IBM HW - Maintenance & Support"):
        [10, 7, 5, 0, 0, 0, -100],
    ("SDDC", "IBM SW - New"):
        [10, 7, 7, 7, -2.2, -2.2, -100],
    ("SDDC", "IBM SW - Renewal (Passport Advantage)"):
        [4, 2.5, 2.5, 2.5, -7.8, -7.8, -100],
    ("SDDC", "IBM SW - S&S (New)"):
        [4, 2.5, 2.5, 2.5, -7.8, -7.8, -100],
    ("Network Security", "IBM Security - Products (QRadar/Guardium)"):
        [10, 7, 5, 0, 0, 0, -100],
    ("Network Security", "IBM Security - Software Licenses"):
        [10, 7, 7, 7, -2.2, -2.2, -100],
    ("Other Services", "IBM/GBM Professional Services"):
        [50, 50, 20, 15, 0, 0, -100],
    ("SDDC", "SDDC - SW - New"):
        [10, 7, 5, 0, 0, 0, -100],
    ("SDDC", "SDDC - SW - Renewal"):
        [4, 2.5, 2.5, 2.5, -7.8, -7.8, -100],
    ("SDDC", "SDDC - Professional Services (GBM - Inhouse)"):
        [50, 50, 20, 15, 0, 0, -100],
    ("SDDC", "SDDC - HW (Hardware)"):
        [50, 49, 15, 8.5, 0, 0, -100],
    ("Network Security", "Security - Products Non-Cisco"):
        [50, 50, 5, 4, 0, 0, -100],
    ("Network Security", "Security - Professional Services (GBM)"):
        [50, 50, 20, 15, 0, 0, -100],
    ("Network Security", "Security - SW Add-ons"):
        [10, 7, 5, 0, 0, 0, -100],
    ("SDDC", "PC"):
        [10.0, 8.0, 4.0, 0.0, 0.0, 0.0, -100.0],
    ("SDDC", "Retail"):
        [15.0, 10.0, 4.0, 0.0, 0.0, 0.0, -100.0],
    ("SDDC", "SDDC - HW, SW"):
        [15.0, 10.0, 5.0, 4.0, 0.0, 0.0, -100.0],
    ("SDDC", "SDDC - Services"):
        [15.0, 12.0, 10.0, 5.0, 0.0, 0.0, -100.0],
    ("SDDC", "Support Services"):
        [10.0, 5.0, 4.0, 3.0, 2.0, 1.0, -100.0],
    ("NW Maint - Attached", "Cisco & Non Cisco Maintenance"):
        [50.0, 50.0, 10.0, 10.0, 10.0, 0.0, -100.0],
    ("NW Maint - Attached", "KBM Comprehensive and Manufacture warranty"):
        [50.0, 50.0, 30.0, 25.0, 25.0, 10.0, -100.0],
    ("NW Maint - Attached", "NW Maint - Renewal"):
        [25.0, 25.0, 15.0, 10.0, 0.0, 0.0, -100.0],
}

DS_BID_SIZE_LEVELS = [
    {"level": 1, "role": "Services Leader",      "min_bid": 500_000},
    {"level": 2, "role": "IBM Digital Leader",   "min_bid": 750_000},
    {"level": 3, "role": "Services Manager",     "min_bid": 750_001},
    {"level": 4, "role": "BFO Financial",        "min_bid": 750_003},
    {"level": 5, "role": "LOB Digital Solutions", "min_bid": 2_500_000},
    {"level": 6, "role": "CFO Finance",          "min_bid": 10_000_000},
    {"level": 7, "role": "CEO",                  "min_bid": 10_000_001},
]

DS_SERVICES_BID_SIZE_LEVELS = [
    {"level": 1, "role": "Services Leader",      "min_bid": 300_000},
    {"level": 2, "role": "IBM Digital Leader",   "min_bid": 500_000},
    {"level": 3, "role": "Services Manager",     "min_bid": 750_001},
    {"level": 4, "role": "BFO Financial",        "min_bid": 750_003},
    {"level": 5, "role": "LOB Digital Solutions", "min_bid": 2_500_000},
    {"level": 6, "role": "CFO Finance",          "min_bid": 10_000_000},
    {"level": 7, "role": "CEO",                  "min_bid": 10_000_001},
]

DS_MARGIN_MATRIX = {
    "IBM New":              [10.0,  7.0,  7.0,  7.0,  0.0,  0.0, -100.0],
    "IBM Renewal":          [ 4.0,  2.5,  2.49, 2.48, 0.0,  0.0, -100.0],
    "Non IBM New & Renewal":[16.0, 12.5, 12.49, 8.0, -1.8,  0.0, -100.0],
    "Services":             [16.0, 12.5, 12.49, 8.0, -1.8,  0.0, -100.0],
    "TSS":                  [10.0,  7.0,  6.99, 6.98, 0.0,  0.0, -100.0],
}

MS_BID_SIZE_LEVELS = [
    {"level": 1, "role": "MS Leader",                 "min_bid": 300_000},
    {"level": 2, "role": "BFO Finance",               "min_bid": 500_002},
    {"level": 3, "role": "Managed Services Manager",  "min_bid": 2_500_000},
    {"level": 4, "role": "CFO Finance",               "min_bid": 10_000_000},
    {"level": 5, "role": "CEO",                       "min_bid": 10_000_001},
]

MS_MARGIN_LEVELS = {
    2: 4.98,
    3: 0.0,
    5: -100.0,
}

ES_BID_SIZE_LEVELS = [
    {"level": 1, "role": "ES Leader",             "min_bid": 300_000},
    {"level": 2, "role": "ES Manager",            "min_bid": 500_000},
    {"level": 3, "role": "Director Ent Systems",  "min_bid": 500_001},
    {"level": 4, "role": "BFO Finance",           "min_bid": 5_000_000},
    {"level": 5, "role": "CFO Finance",           "min_bid": 10_000_000},
    {"level": 6, "role": "CEO",                   "min_bid": 10_000_001},
]

ES_MARGIN_MATRIX = {
    "Services": [10.0,  5.0,   0.0,   0.0, -100.0],
    "Hardware": [99.99, 99.98, 99.87, 0.0, -100.0],
}

PCM_DELEGATION = {
    "IBM":          [
        {"role": "TSS Manager",          "max_discount": 15},
        {"role": "BFO",                  "max_discount": 40},
        {"role": "CFO",                  "max_discount": 100},
    ],
    "SystemX":      [
        {"role": "TSS Manager",          "max_discount": 15},
        {"role": "BFO",                  "max_discount": 40},
        {"role": "CFO",                  "max_discount": 100},
    ],
    "OEM":          [
        {"role": "TSS Manager",          "max_discount": 0},
        {"role": "BFO",                  "max_discount": 20},
        {"role": "CFO",                  "max_discount": 100},
    ],
    "Support Line": [
        {"role": "Support Line Manager", "max_discount": 20},
        {"role": "BFO",                  "max_discount": 40},
        {"role": "CFO",                  "max_discount": 100},
    ],
    "NW Maintenance": [
        {"role": "DIS Director of Customer Success", "max_discount": 100},
    ],
    "NW Security": [
        {"role": "DIS Director of Customer Success", "max_discount": 100},
    ],
}

COST_SHEET_SECTIONS = {
    "NS_11_A": {"section": "Networking", "subsection": "NW - In House Services"},
    "NS_11_C": {"section": "Networking", "subsection": "NW - Products Cisco"},
    "NS_11_D": {"section": "Networking", "subsection": "NW - Products Non Cisco"},
    "DI_21_A": {"section": "SDDC", "subsection": "SDDC - Professional Services (GBM - Inhouse)"},
    "DI_22_A": {"section": "SDDC", "subsection": "SDDC - HW (Hardware)"},
    "DI_24_A": {"section": "SDDC", "subsection": "SDDC - SW - New"},
    "DI_25_A": {"section": "SDDC", "subsection": "SDDC - SW - Renewal"},
    "DI_12_A": {"section": "Network Security", "subsection": "Security - Professional Services (GBM)"},
    "DI_12_D": {"section": "Network Security", "subsection": "Security - Products Non-Cisco"},
    "IBM_HW_A": {"section": "Infrastructure", "subsection": "IBM HW - New (Power/Storage/FlashSystem)"},
    "IBM_HW_B": {"section": "Infrastructure", "subsection": "IBM HW - Maintenance & Support"},
    "IBM_SW_A": {"section": "SDDC", "subsection": "IBM SW - New"},
    "IBM_SW_C": {"section": "SDDC", "subsection": "IBM SW - Renewal (Passport Advantage)"},
    "IBM_SEC_A": {"section": "Network Security", "subsection": "IBM Security - Products (QRadar/Guardium)"},
    "IBM_SVC_A": {"section": "Other Services", "subsection": "IBM/GBM Professional Services"},
    "NS_15_A": {"section": "Maintenance", "subsection": "Cisco 1st Year Maintenance"},
    "NS_15_B": {"section": "Maintenance", "subsection": "Non-Cisco Maintenance"},
    "NS_16_A": {"section": "Other Services", "subsection": "Licensing Services"},
    "NS_16_E": {"section": "Other Services", "subsection": "Project Management"},
    "NS_16_F": {"section": "Other Services", "subsection": "Training"},
}

PCS_TECHNOLOGY_SELECTIONS = {
    "Networking - Cisco": {"lob": "DIS", "section": "Networking", "sub_lob": "Networking"},
    "Network Security - Cisco": {"lob": "DIS", "section": "Network Security", "sub_lob": "Network Security"},
    "Network Security - Fortinet/Palo Alto": {"lob": "DIS", "section": "Network Security", "sub_lob": "Network Security"},
    "SDDC - Nutanix": {"lob": "DIS", "section": "SDDC", "sub_lob": "SDDC"},
    "SDDC - VMware": {"lob": "DIS", "section": "SDDC", "sub_lob": "SDDC"},
    "SDDC - Servers (HPE/Dell/Lenovo)": {"lob": "DIS", "section": "SDDC", "sub_lob": "SDDC"},
    "Infrastructure - Storage": {"lob": "DIS", "section": "Infrastructure", "sub_lob": "Infrastructure"},
    "Infrastructure - Compute": {"lob": "DIS", "section": "Infrastructure", "sub_lob": "Infrastructure"},
    "Maintenance & Support": {"lob": "DIS", "section": "Maintenance", "sub_lob": "Maintenance"},
    "IBM - Power Systems (HW)": {"lob": "DIS", "section": "Infrastructure", "sub_lob": "IBM HW"},
    "IBM - Software (New)": {"lob": "DIS", "section": "SDDC", "sub_lob": "IBM SW"},
    "IBM - Software (Renewal)": {"lob": "DIS", "section": "SDDC", "sub_lob": "IBM SW"},
    "IBM - Security (QRadar/Guardium)": {"lob": "DIS", "section": "Network Security", "sub_lob": "IBM Security"},
    "IBM - Storage (FlashSystem/Spectrum)": {"lob": "DIS", "section": "Infrastructure", "sub_lob": "IBM Storage"},
}

COUNTRY_DATA = {
    "Kuwait": {"currency": "KWD", "exchange_rate": 0.3125, "vat_pct": 0.0, "customs_pct": 5.0, "local_charges_pct": 6.45},
    "Saudi Arabia": {"currency": "SAR", "exchange_rate": 3.75, "vat_pct": 15.0, "customs_pct": 5.0, "local_charges_pct": 5.0},
    "UAE": {"currency": "AED", "exchange_rate": 3.67, "vat_pct": 5.0, "customs_pct": 5.0, "local_charges_pct": 5.0},
    "Bahrain": {"currency": "BHD", "exchange_rate": 0.376, "vat_pct": 10.0, "customs_pct": 5.0, "local_charges_pct": 5.0},
    "Qatar": {"currency": "QAR", "exchange_rate": 3.64, "vat_pct": 0.0, "customs_pct": 5.0, "local_charges_pct": 5.0},
    "Oman": {"currency": "OMR", "exchange_rate": 0.385, "vat_pct": 5.0, "customs_pct": 5.0, "local_charges_pct": 5.0},
}

STATUS_COLORS = {
    "Draft": "#6c757d",
    "Submitted": "#007bff",
    "Under Review": "#fd7e14",
    "Approved": "#28a745",
    "Rejected": "#dc3545",
    "Interfaced": "#17a2b8",
}
