"""
Manufacturer Profile

Defines all business-specific constants for industrial manufacturers
and distributors with procurement-driven sales cycles.
"""

import random
from typing import Dict, List, Optional, Tuple

from .base import BaseProfile


class ManufacturerProfile(BaseProfile):
    """Profile for industrial manufacturers and distributors."""

    # ------------------------------------------------------------------ #
    #  Identity                                                            #
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "Manufacturer"

    @property
    def description(self) -> str:
        return "Industrial manufacturers and distributors with procurement-driven sales cycles."

    # ------------------------------------------------------------------ #
    #  Sales team                                                          #
    # ------------------------------------------------------------------ #

    @property
    def sales_reps(self) -> List[str]:
        return [
            "Tom Bradley",
            "Susan Park",
            "Robert Nguyen",
            "Lisa Martinez",
            "Brian Cooper",
            "Angela Wright",
        ]

    # ------------------------------------------------------------------ #
    #  Account generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def name_prefixes(self) -> List[str]:
        return [
            "Precision", "Allied", "National", "Superior", "Global",
            "Advanced", "Premier", "Continental", "Pacific", "Delta",
            "Atlas", "Sterling", "Apex", "Summit", "Pioneer",
            "Liberty", "Eagle", "Titan", "Patriot", "Crown",
        ]

    @property
    def name_suffixes(self) -> List[str]:
        return [
            "Manufacturing", "Industries", "Components", "Fabrication",
            "Metals", "Engineering", "Products", "Systems", "Solutions",
            "Supply Co.", "Materials", "Tools", "Works", "Corp",
            "Technologies",
        ]

    @property
    def industries(self) -> List[str]:
        return [
            "Automotive Parts",
            "Aerospace Components",
            "Industrial Machinery",
            "Metal Fabrication",
            "Plastics & Polymers",
            "Electronics Manufacturing",
            "Food & Beverage Processing",
            "Chemical Manufacturing",
            "Packaging & Containers",
            "Textile & Apparel",
            "Medical Devices",
            "Construction Materials",
        ]

    @property
    def employee_tiers(self) -> List[Tuple[int, int, int]]:
        return [
            (25, 75, 20),
            (76, 150, 25),
            (151, 300, 25),
            (301, 750, 15),
            (751, 2000, 10),
            (2001, 5000, 5),
        ]

    @property
    def revenue_per_employee_range(self) -> Tuple[int, int]:
        return (40_000, 120_000)

    @property
    def website_tlds(self) -> List[str]:
        return [".com", ".net", ".us", ".co"]

    @property
    def description_templates(self) -> List[str]:
        return [
            "Leading {industry} manufacturer serving customers worldwide.",
            "Precision {industry} solutions for demanding applications.",
            "Trusted supplier of high-quality {industry} products since establishment.",
            "Full-service {industry} provider with vertically integrated operations.",
            "ISO-certified {industry} specialist with rapid turnaround capabilities.",
        ]

    @property
    def founded_year_range(self) -> Tuple[int, int]:
        return (1965, 2020)

    # ------------------------------------------------------------------ #
    #  Contact generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def title_by_department(self) -> Dict[str, List[str]]:
        return {
            "Sales": [
                "Regional Sales Manager",
                "Account Manager",
                "VP of Sales",
                "Business Development Manager",
                "Sales Engineer",
                "Director of Sales",
            ],
            "Engineering": [
                "Manufacturing Engineer",
                "Quality Engineer",
                "Design Engineer",
                "VP of Engineering",
                "Process Engineer",
                "Chief Engineer",
            ],
            "Operations": [
                "Plant Manager",
                "Operations Director",
                "COO",
                "Production Manager",
                "Supply Chain Manager",
                "Logistics Coordinator",
            ],
            "Procurement": [
                "Purchasing Manager",
                "Procurement Director",
                "Buyer",
                "VP of Procurement",
                "Supply Chain Director",
            ],
            "Quality": [
                "Quality Manager",
                "QA Director",
                "Quality Control Inspector",
                "VP of Quality",
            ],
            "Executive": [
                "CEO",
                "President",
                "Owner",
                "General Manager",
            ],
            "Finance": [
                "CFO",
                "Controller",
                "Finance Director",
                "Accounting Manager",
            ],
        }

    @property
    def department_weights(self) -> Dict[str, int]:
        return {
            "Sales": 20,
            "Engineering": 20,
            "Operations": 20,
            "Procurement": 15,
            "Quality": 10,
            "Executive": 8,
            "Finance": 7,
        }

    # ------------------------------------------------------------------ #
    #  Deal generation                                                     #
    # ------------------------------------------------------------------ #

    @property
    def pipelines(self) -> Dict[str, List[str]]:
        return {
            "New Accounts": [
                "Lead", "Qualification", "Sample/Trial", "RFQ Response",
                "Quote", "PO Review", "Closed Won", "Closed Lost",
            ],
            "Reorders": [
                "Reorder Request", "Quote", "PO Received",
                "Closed Won", "Closed Lost",
            ],
            "Custom/Engineered Solutions": [
                "Requirements Gathering", "Engineering Review", "Prototype",
                "Quote", "Negotiation", "Closed Won", "Closed Lost",
            ],
        }

    @property
    def primary_pipeline_name(self) -> str:
        return "New Accounts"

    @property
    def renewal_pipeline_name(self) -> str:
        return "Reorders"

    @property
    def expansion_pipeline_name(self) -> str:
        return "Custom/Engineered Solutions"

    @property
    def outcome_rates(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Accounts": {"Won": 18, "Lost": 60, "Open": 22},
            "Reorders": {"Won": 90, "Lost": 5, "Open": 5},
            "Custom/Engineered Solutions": {"Won": 30, "Lost": 45, "Open": 25},
        }

    @property
    def segments(self) -> List[str]:
        return ["SMB", "Mid-Market", "Enterprise"]

    def classify_segment(self, employee_count: int) -> str:
        if employee_count < 100:
            return "SMB"
        elif employee_count <= 500:
            return "Mid-Market"
        return "Enterprise"

    @property
    def acv_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (5_000, 50_000),
            "Mid-Market": (50_000, 500_000),
            "Enterprise": (500_000, 5_000_000),
        }

    @property
    def nb_cycle_days(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (45, 90),
            "Mid-Market": (90, 180),
            "Enterprise": (180, 365),
        }

    @property
    def renewal_cycle_days(self) -> Tuple[int, int]:
        return (10, 30)

    @property
    def expansion_cycle_days(self) -> Tuple[int, int]:
        return (90, 270)

    @property
    def loss_reasons_default(self) -> Dict[str, int]:
        return {
            "Price Too High": 25,
            "Chose Competitor": 20,
            "Spec Non-Compliance": 15,
            "Lead Time Too Long": 15,
            "No Decision / Budget Freeze": 10,
            "Failed Quality Audit": 10,
            "Minimum Order Qty Issue": 5,
        }

    @property
    def loss_reasons_enterprise(self) -> Dict[str, int]:
        return {
            "Price Too High": 15,
            "Chose Competitor": 15,
            "Spec Non-Compliance": 20,
            "Lead Time Too Long": 10,
            "No Decision / Budget Freeze": 15,
            "Failed Quality Audit": 15,
            "Minimum Order Qty Issue": 10,
        }

    @property
    def active_stage_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Accounts": {
                "Lead": 10,
                "Qualification": 15,
                "Sample/Trial": 20,
                "RFQ Response": 25,
                "Quote": 20,
                "PO Review": 10,
            },
            "Reorders": {
                "Reorder Request": 30,
                "Quote": 40,
                "PO Received": 30,
            },
            "Custom/Engineered Solutions": {
                "Requirements Gathering": 15,
                "Engineering Review": 25,
                "Prototype": 25,
                "Quote": 20,
                "Negotiation": 15,
            },
        }

    def format_deal_name(self, company_name: str, created_date: str, **kwargs) -> str:
        yymm = created_date[2:4] + created_date[5:7]
        return f"PO-{yymm}-{company_name}"

    @property
    def self_serve_config(self) -> None:
        return None

    @property
    def subscription_type_weights(self) -> None:
        return None

    # ------------------------------------------------------------------ #
    #  Activity generation                                                 #
    # ------------------------------------------------------------------ #

    @property
    def activity_types(self) -> List[str]:
        return ["Email", "Phone Call", "Meeting", "LinkedIn", "Note"]

    @property
    def activity_type_weights(self) -> Dict[str, int]:
        return {
            "Email": 30,
            "Phone Call": 25,
            "Meeting": 25,
            "LinkedIn": 10,
            "Note": 10,
        }

    @property
    def phase_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "early": {"Email": 25, "Phone Call": 25, "Meeting": 10, "LinkedIn": 30, "Note": 10},
            "mid":   {"Email": 25, "Phone Call": 20, "Meeting": 35, "LinkedIn": 10, "Note": 10},
            "late":  {"Email": 40, "Phone Call": 25, "Meeting": 20, "LinkedIn": 5,  "Note": 10},
        }

    @property
    def activity_count_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "Won": (8, 16),
            "Lost": (3, 7),
        }

    @property
    def segment_activity_multiplier(self) -> Dict[str, float]:
        return {
            "SMB": 0.7,
            "Mid-Market": 1.0,
            "Enterprise": 1.5,
        }

    @property
    def subjects(self) -> Dict[str, List[str]]:
        return {
            "Email": [
                "RFQ response follow-up",
                "Updated pricing sheet",
                "Sample shipment tracking",
                "Quality cert attached",
                "Lead time confirmation",
                "PO acknowledgment",
            ],
            "Phone Call": [
                "Initial inquiry call",
                "Spec clarification",
                "Quote review call",
                "Production status update",
                "Reorder discussion",
                "Complaint resolution",
            ],
            "Meeting": [
                "Plant tour",
                "Technical review meeting",
                "Contract negotiation",
                "Annual business review",
                "Quality audit",
                "Engineering design review",
            ],
            "LinkedIn": [
                "Connection request",
                "Industry article share",
                "Trade show follow-up",
                "InMail introduction",
                "Company update engagement",
            ],
            "Note": [
                "Met at trade show",
                "Referral from distributor",
                "Internal capacity note",
                "Competitor pricing intel",
                "Seasonal demand note",
            ],
        }

    @property
    def phase_biased_subjects(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "early": {
                "Email": ["RFQ response follow-up", "Quality cert attached"],
                "Phone Call": ["Initial inquiry call", "Spec clarification"],
                "Meeting": ["Plant tour", "Technical review meeting"],
                "LinkedIn": ["Connection request", "InMail introduction", "Trade show follow-up"],
                "Note": ["Met at trade show", "Referral from distributor"],
            },
            "mid": {
                "Email": ["Sample shipment tracking", "Updated pricing sheet"],
                "Phone Call": ["Quote review call", "Production status update"],
                "Meeting": ["Engineering design review", "Technical review meeting"],
                "LinkedIn": ["Industry article share", "Company update engagement"],
                "Note": ["Competitor pricing intel", "Internal capacity note"],
            },
            "late": {
                "Email": ["PO acknowledgment", "Lead time confirmation", "Updated pricing sheet"],
                "Phone Call": ["Reorder discussion", "Complaint resolution"],
                "Meeting": ["Contract negotiation", "Annual business review", "Quality audit"],
                "LinkedIn": ["Company update engagement"],
                "Note": ["Seasonal demand note", "Internal capacity note"],
            },
        }

    @property
    def duration_ranges(self) -> Dict[str, Optional[Tuple[int, int]]]:
        return {
            "Email": None,
            "Phone Call": (10, 45),
            "Meeting": (30, 90),
            "LinkedIn": None,
            "Note": None,
        }
