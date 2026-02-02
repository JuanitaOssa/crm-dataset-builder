"""
B2B SaaS Profile

Defines all business-specific constants for a B2B SaaS company:
company names, industries, pipelines, deal sizes, activity subjects, etc.
"""

from typing import Dict, List, Optional, Tuple

from .base import BaseProfile


class B2BSaaSProfile(BaseProfile):
    """Profile for B2B SaaS companies with product-led and sales-led motions."""

    # ------------------------------------------------------------------ #
    #  Identity                                                            #
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "B2B SaaS"

    @property
    def description(self) -> str:
        return "Software-as-a-Service companies with subscription-based sales cycles."

    # ------------------------------------------------------------------ #
    #  Sales team                                                          #
    # ------------------------------------------------------------------ #

    @property
    def sales_reps(self) -> List[str]:
        return [
            "Sarah Chen",
            "Marcus Johnson",
            "Emily Rodriguez",
            "David Kim",
            "Rachel Thompson",
            "James O'Brien",
        ]

    # ------------------------------------------------------------------ #
    #  Account generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def name_prefixes(self) -> List[str]:
        return [
            "Cloud", "Data", "Cyber", "Tech", "Net", "Digi", "Info", "Smart",
            "Sync", "Flow", "Stack", "Grid", "Node", "Pixel", "Byte", "Core",
            "Meta", "Hyper", "Ultra", "Prime", "Alpha", "Beta", "Quantum",
            "Vector", "Logic", "Signal", "Pulse", "Wave",
        ]

    @property
    def name_suffixes(self) -> List[str]:
        return [
            "Labs", "Systems", "Solutions", "Tech", "Software", "IO", "AI",
            "Analytics", "Cloud", "Networks", "Dynamics", "Ware", "Works",
            "Hub", "Base", "Stack", "Logic", "Mind", "Sense", "Force",
            "Bridge", "Link", "Path", "Scale", "Shift", "Stream", "Vault",
        ]

    @property
    def industries(self) -> List[str]:
        return [
            "Enterprise Software",
            "Cloud Infrastructure",
            "Cybersecurity",
            "Data Analytics",
            "Artificial Intelligence",
            "Developer Tools",
            "Marketing Technology",
            "Sales Enablement",
            "Human Resources Tech",
            "Financial Technology",
            "Healthcare Technology",
            "Supply Chain Software",
            "Customer Success",
            "Business Intelligence",
            "E-commerce Platform",
            "Communication & Collaboration",
            "Project Management",
            "Identity & Access Management",
            "DevOps & CI/CD",
            "API & Integration Platform",
        ]

    @property
    def employee_tiers(self) -> List[Tuple[int, int, int]]:
        return [
            (50, 100, 30),
            (101, 250, 25),
            (251, 500, 20),
            (501, 1000, 15),
            (1001, 2500, 7),
            (2501, 5000, 3),
        ]

    @property
    def revenue_per_employee_range(self) -> Tuple[int, int]:
        return (50_000, 200_000)

    @property
    def website_tlds(self) -> List[str]:
        return [".com", ".io", ".co", ".ai", ".tech"]

    @property
    def description_templates(self) -> List[str]:
        return [
            "Leading provider of {industry} solutions for modern enterprises.",
            "Innovative {industry} platform helping businesses scale.",
            "Next-generation {industry} tools for growing teams.",
            "Enterprise-grade {industry} solutions with a focus on simplicity.",
            "Transforming how businesses approach {industry}.",
        ]

    @property
    def founded_year_range(self) -> Tuple[int, int]:
        return (2010, 2024)

    # ------------------------------------------------------------------ #
    #  Contact generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def title_by_department(self) -> Dict[str, List[str]]:
        return {
            "Sales": [
                "Account Executive",
                "Sales Manager",
                "VP of Sales",
                "Sales Development Representative",
                "Director of Sales",
                "Chief Revenue Officer",
                "Regional Sales Manager",
            ],
            "Engineering": [
                "Software Engineer",
                "Engineering Manager",
                "VP of Engineering",
                "CTO",
                "Senior Software Engineer",
                "Principal Engineer",
            ],
            "Marketing": [
                "Marketing Manager",
                "VP of Marketing",
                "CMO",
                "Content Marketing Manager",
                "Demand Generation Manager",
                "Director of Marketing",
            ],
            "Operations": [
                "Operations Manager",
                "COO",
                "Director of Operations",
                "Business Operations Analyst",
                "VP of Operations",
            ],
            "Customer Success": [
                "Customer Success Manager",
                "VP of Customer Success",
                "Director of Customer Success",
                "Customer Success Associate",
                "Head of Customer Success",
            ],
            "Executive": [
                "CEO",
                "President",
                "Co-Founder",
                "Managing Director",
            ],
            "Finance": [
                "CFO",
                "Finance Manager",
                "Controller",
                "Director of Finance",
                "Financial Analyst",
            ],
            "Product": [
                "Product Manager",
                "VP of Product",
                "Chief Product Officer",
                "Senior Product Manager",
                "Director of Product",
            ],
        }

    @property
    def department_weights(self) -> Dict[str, int]:
        return {
            "Sales": 25,
            "Marketing": 15,
            "Customer Success": 15,
            "Engineering": 10,
            "Product": 10,
            "Operations": 10,
            "Executive": 8,
            "Finance": 7,
        }

    # ------------------------------------------------------------------ #
    #  Deal generation                                                     #
    # ------------------------------------------------------------------ #

    @property
    def pipelines(self) -> Dict[str, List[str]]:
        return {
            "New Business": [
                "Lead", "Qualified", "Discovery", "Demo/Evaluation",
                "Proposal", "Negotiation", "Closed Won", "Closed Lost",
            ],
            "Renewal": [
                "Upcoming Renewal", "Customer Review", "Renewal Proposal",
                "Negotiation", "Closed Won", "Closed Lost",
            ],
            "Expansion": [
                "Expansion Identified", "Needs Analysis", "Proposal",
                "Negotiation", "Closed Won", "Closed Lost",
            ],
            "Self-Serve": [
                "Signed Up", "Activated", "Trial", "Converted", "Churned",
            ],
        }

    @property
    def primary_pipeline_name(self) -> str:
        return "New Business"

    @property
    def renewal_pipeline_name(self) -> str:
        return "Renewal"

    @property
    def expansion_pipeline_name(self) -> str:
        return "Expansion"

    @property
    def outcome_rates(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Business": {"Won": 22, "Lost": 58, "Open": 20},
            "Renewal": {"Won": 85, "Lost": 10, "Open": 5},
            "Expansion": {"Won": 45, "Lost": 30, "Open": 25},
        }

    @property
    def segments(self) -> List[str]:
        return ["SMB", "Mid-Market", "Enterprise", "Self-Serve"]

    def classify_segment(self, employee_count: int) -> str:
        if employee_count < 200:
            return "SMB"
        elif employee_count <= 1000:
            return "Mid-Market"
        return "Enterprise"

    @property
    def acv_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (8_000, 25_000),
            "Mid-Market": (25_000, 100_000),
            "Enterprise": (100_000, 350_000),
            "Self-Serve": (600, 5_000),
        }

    @property
    def nb_cycle_days(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (30, 45),
            "Mid-Market": (60, 90),
            "Enterprise": (90, 180),
        }

    @property
    def renewal_cycle_days(self) -> Tuple[int, int]:
        return (15, 30)

    @property
    def expansion_cycle_days(self) -> Tuple[int, int]:
        return (30, 60)

    @property
    def loss_reasons_default(self) -> Dict[str, int]:
        return {
            "Budget Constraints": 20,
            "Went with Competitor": 25,
            "No Decision Made": 20,
            "Bad Timing": 10,
            "Champion Left Company": 5,
            "Failed Security Review": 5,
            "Lost to Open Source": 10,
            "Chose to Build In-House": 5,
        }

    @property
    def loss_reasons_enterprise(self) -> Dict[str, int]:
        return {
            "Budget Constraints": 25,
            "Went with Competitor": 15,
            "No Decision Made": 15,
            "Bad Timing": 5,
            "Champion Left Company": 5,
            "Failed Security Review": 20,
            "Lost to Open Source": 5,
            "Chose to Build In-House": 10,
        }

    @property
    def active_stage_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Business": {
                "Lead": 10,
                "Qualified": 15,
                "Discovery": 25,
                "Demo/Evaluation": 25,
                "Proposal": 15,
                "Negotiation": 10,
            },
            "Renewal": {
                "Upcoming Renewal": 20,
                "Customer Review": 30,
                "Renewal Proposal": 30,
                "Negotiation": 20,
            },
            "Expansion": {
                "Expansion Identified": 15,
                "Needs Analysis": 30,
                "Proposal": 30,
                "Negotiation": 25,
            },
        }

    def format_deal_name(self, company_name: str, created_date: str, **kwargs) -> str:
        yymm = created_date[2:4] + created_date[5:7]
        return f"{company_name} {yymm}"

    @property
    def self_serve_config(self) -> Optional[dict]:
        return {
            "pipeline_name": "Self-Serve",
            "stages": ["Signed Up", "Activated", "Trial", "Converted", "Churned"],
            "conversion_rate": 0.15,
            "monthly_amount_range": (50, 500),
            "yearly_amount_range": (500, 5_000),
            "subscription_split": {"Monthly": 0.60, "Annual": 0.40},
            "fraction_of_accounts": 0.20,
            "plg_to_sales_probability": 0.10,
        }

    @property
    def subscription_type_weights(self) -> Optional[Dict[str, float]]:
        return {"Annual": 0.70, "Monthly": 0.30}

    # ------------------------------------------------------------------ #
    #  Activity generation                                                 #
    # ------------------------------------------------------------------ #

    @property
    def activity_types(self) -> List[str]:
        return ["Email", "Phone Call", "Meeting", "LinkedIn", "Note"]

    @property
    def activity_type_weights(self) -> Dict[str, int]:
        return {
            "Email": 35,
            "Phone Call": 20,
            "Meeting": 20,
            "LinkedIn": 15,
            "Note": 10,
        }

    @property
    def phase_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "early": {"Email": 20, "Phone Call": 20, "Meeting": 10, "LinkedIn": 40, "Note": 10},
            "mid":   {"Email": 25, "Phone Call": 20, "Meeting": 35, "LinkedIn": 10, "Note": 10},
            "late":  {"Email": 45, "Phone Call": 20, "Meeting": 20, "LinkedIn": 5,  "Note": 10},
        }

    @property
    def activity_count_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "Won": (10, 20),
            "Lost": (4, 8),
        }

    @property
    def segment_activity_multiplier(self) -> Dict[str, float]:
        return {
            "SMB": 0.8,
            "Mid-Market": 1.0,
            "Enterprise": 1.4,
        }

    @property
    def subjects(self) -> Dict[str, List[str]]:
        return {
            "Email": [
                "Follow-up on pricing proposal",
                "Introduction to platform",
                "Sending case study",
                "Contract review",
                "ROI analysis attached",
                "Nurture - industry report",
            ],
            "Phone Call": [
                "Discovery call",
                "Quarterly business review",
                "Cold outreach",
                "Champion check-in",
                "Negotiation follow-up",
                "Renewal discussion",
            ],
            "Meeting": [
                "On-site demo",
                "Executive alignment",
                "Technical deep dive",
                "Kick-off call",
                "QBR",
                "Security review walkthrough",
            ],
            "LinkedIn": [
                "Connection request",
                "InMail outreach",
                "Commented on post",
                "Shared company content",
                "Intro message via mutual connection",
            ],
            "Note": [
                "Met at SaaStr conference",
                "Referred by existing customer",
                "Internal handoff notes",
                "Competitor intel",
                "Budget cycle starts Q1",
            ],
        }

    @property
    def phase_biased_subjects(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "early": {
                "Email": ["Introduction to platform", "Sending case study", "Nurture - industry report"],
                "Phone Call": ["Discovery call", "Cold outreach"],
                "Meeting": ["Kick-off call", "Technical deep dive"],
                "LinkedIn": ["Connection request", "InMail outreach", "Intro message via mutual connection"],
                "Note": ["Met at SaaStr conference", "Referred by existing customer"],
            },
            "mid": {
                "Email": ["Sending case study", "ROI analysis attached"],
                "Phone Call": ["Champion check-in", "Quarterly business review"],
                "Meeting": ["On-site demo", "Technical deep dive", "Executive alignment"],
                "LinkedIn": ["Commented on post", "Shared company content"],
                "Note": ["Competitor intel", "Internal handoff notes"],
            },
            "late": {
                "Email": ["Follow-up on pricing proposal", "Contract review", "ROI analysis attached"],
                "Phone Call": ["Negotiation follow-up", "Renewal discussion"],
                "Meeting": ["Executive alignment", "QBR", "Security review walkthrough"],
                "LinkedIn": ["Shared company content"],
                "Note": ["Budget cycle starts Q1", "Internal handoff notes"],
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
