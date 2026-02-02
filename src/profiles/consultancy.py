"""
Consultancy Profile

Defines all business-specific constants for consulting and professional
services firms with engagement-based sales cycles.
"""

import random
from typing import Dict, List, Optional, Tuple

from .base import BaseProfile


class ConsultancyProfile(BaseProfile):
    """Profile for consulting and professional services firms."""

    # Engagement types used in deal naming
    ENGAGEMENT_TYPES = [
        "Digital Transformation",
        "Process Optimization",
        "Strategic Planning",
        "Org Restructuring",
        "System Implementation",
        "Market Entry Strategy",
        "Operational Assessment",
        "Change Management",
        "Cost Reduction Initiative",
        "Growth Strategy",
        "M&A Due Diligence",
        "Technology Roadmap",
    ]

    # ------------------------------------------------------------------ #
    #  Identity                                                            #
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "Consultancy"

    @property
    def description(self) -> str:
        return "Consulting and professional services firms with engagement-based sales cycles."

    # ------------------------------------------------------------------ #
    #  Sales team                                                          #
    # ------------------------------------------------------------------ #

    @property
    def sales_reps(self) -> List[str]:
        return [
            "Catherine Brooks",
            "Daniel Reeves",
            "Patricia Morales",
            "Andrew Fleming",
            "Jessica Thornton",
            "Michael Lancaster",
        ]

    # ------------------------------------------------------------------ #
    #  Account generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def name_prefixes(self) -> List[str]:
        return [
            "Meridian", "Elevate", "Catalyst", "Pinnacle", "Sterling",
            "Keystone", "Vantage", "Summit", "Nexus", "Beacon",
            "Clarity", "Stratton", "Archer", "Crestview", "Whitfield",
        ]

    @property
    def name_suffixes(self) -> List[str]:
        return [
            "Consulting Group", "Advisory", "Partners", "& Associates",
            "Solutions", "Strategy Group", "Consulting", "Group",
        ]

    @property
    def industries(self) -> List[str]:
        return [
            "Management Consulting",
            "IT Consulting",
            "Financial Advisory",
            "Human Capital Consulting",
            "Strategy Consulting",
            "Operations Consulting",
            "Risk & Compliance",
            "Digital Transformation",
            "Healthcare Consulting",
            "Environmental Consulting",
            "Legal Consulting",
            "Marketing & Brand Strategy",
        ]

    @property
    def employee_tiers(self) -> List[Tuple[int, int, int]]:
        return [
            (10, 30, 25),
            (31, 75, 25),
            (76, 200, 20),
            (201, 500, 15),
            (501, 1500, 10),
            (1501, 5000, 5),
        ]

    @property
    def revenue_per_employee_range(self) -> Tuple[int, int]:
        return (80_000, 250_000)

    @property
    def website_tlds(self) -> List[str]:
        return [".com", ".co", ".consulting", ".net"]

    @property
    def description_templates(self) -> List[str]:
        return [
            "Trusted {industry} partner helping organizations drive growth.",
            "Boutique {industry} firm delivering measurable business outcomes.",
            "Leading {industry} practice serving Fortune 500 and mid-market clients.",
            "Expert {industry} advisors with deep domain expertise.",
            "Results-driven {industry} consultancy focused on sustainable impact.",
        ]

    @property
    def founded_year_range(self) -> Tuple[int, int]:
        return (1990, 2023)

    # ------------------------------------------------------------------ #
    #  Contact generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    def title_by_department(self) -> Dict[str, List[str]]:
        return {
            "Sales": [
                "Business Development Director",
                "Client Partner",
                "VP of Business Development",
                "Engagement Manager",
                "Sales Director",
            ],
            "Consulting": [
                "Senior Consultant",
                "Principal Consultant",
                "Managing Consultant",
                "Associate Consultant",
                "Director of Consulting",
            ],
            "Operations": [
                "COO",
                "Director of Operations",
                "Practice Manager",
                "Resource Manager",
                "VP of Operations",
            ],
            "Executive": [
                "Managing Partner",
                "Senior Partner",
                "CEO",
                "Founder",
                "President",
            ],
            "Finance": [
                "CFO",
                "Finance Director",
                "Controller",
                "Billing Manager",
            ],
            "Marketing": [
                "Marketing Director",
                "VP of Marketing",
                "Content Strategist",
                "Thought Leadership Manager",
            ],
            "Human Resources": [
                "HR Director",
                "Talent Acquisition Lead",
                "VP of People",
                "Recruiting Manager",
            ],
        }

    @property
    def department_weights(self) -> Dict[str, int]:
        return {
            "Sales": 20,
            "Consulting": 25,
            "Operations": 15,
            "Executive": 15,
            "Finance": 8,
            "Marketing": 10,
            "Human Resources": 7,
        }

    # ------------------------------------------------------------------ #
    #  Deal generation                                                     #
    # ------------------------------------------------------------------ #

    @property
    def pipelines(self) -> Dict[str, List[str]]:
        return {
            "New Engagements": [
                "Opportunity Qualified", "Discovery", "Proposal",
                "Negotiation", "Verbal", "Closed Won", "Closed Lost",
            ],
            "Follow-On Projects": [
                "Opportunity Identified", "Scoping", "Proposal",
                "Verbal", "Closed Won", "Closed Lost",
            ],
            "Retainer Renewals": [
                "Renewal Discussion", "Scope Review", "Terms",
                "Verbal", "Closed Won", "Closed Lost",
            ],
        }

    @property
    def primary_pipeline_name(self) -> str:
        return "New Engagements"

    @property
    def renewal_pipeline_name(self) -> str:
        return "Retainer Renewals"

    @property
    def expansion_pipeline_name(self) -> str:
        return "Follow-On Projects"

    @property
    def outcome_rates(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Engagements": {"Won": 25, "Lost": 55, "Open": 20},
            "Follow-On Projects": {"Won": 60, "Lost": 20, "Open": 20},
            "Retainer Renewals": {"Won": 80, "Lost": 12, "Open": 8},
        }

    @property
    def segments(self) -> List[str]:
        return ["SMB", "Mid-Market", "Enterprise"]

    def classify_segment(self, employee_count: int) -> str:
        if employee_count < 200:
            return "SMB"
        elif employee_count <= 1000:
            return "Mid-Market"
        return "Enterprise"

    @property
    def acv_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (25_000, 100_000),
            "Mid-Market": (100_000, 500_000),
            "Enterprise": (500_000, 2_000_000),
        }

    @property
    def nb_cycle_days(self) -> Dict[str, Tuple[int, int]]:
        return {
            "SMB": (30, 60),
            "Mid-Market": (60, 120),
            "Enterprise": (120, 240),
        }

    @property
    def renewal_cycle_days(self) -> Tuple[int, int]:
        return (15, 45)

    @property
    def expansion_cycle_days(self) -> Tuple[int, int]:
        return (20, 60)

    @property
    def loss_reasons_default(self) -> Dict[str, int]:
        return {
            "Budget Constraints": 20,
            "Chose Competitor": 20,
            "Project Deprioritized": 15,
            "Internal Resources Preferred": 15,
            "Scope Mismatch": 10,
            "Timing / Budget Cycle": 10,
            "Key Stakeholder Left": 10,
        }

    @property
    def loss_reasons_enterprise(self) -> Dict[str, int]:
        return {
            "Budget Constraints": 15,
            "Chose Competitor": 25,
            "Project Deprioritized": 15,
            "Internal Resources Preferred": 10,
            "Scope Mismatch": 15,
            "Timing / Budget Cycle": 10,
            "Key Stakeholder Left": 10,
        }

    @property
    def active_stage_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "New Engagements": {
                "Opportunity Qualified": 10,
                "Discovery": 25,
                "Proposal": 30,
                "Negotiation": 20,
                "Verbal": 15,
            },
            "Follow-On Projects": {
                "Opportunity Identified": 15,
                "Scoping": 30,
                "Proposal": 30,
                "Verbal": 25,
            },
            "Retainer Renewals": {
                "Renewal Discussion": 20,
                "Scope Review": 30,
                "Terms": 30,
                "Verbal": 20,
            },
        }

    def format_deal_name(self, company_name: str, created_date: str, **kwargs) -> str:
        engagement_type = random.choice(self.ENGAGEMENT_TYPES)
        return f"{company_name} - {engagement_type}"

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
            "Phone Call": 15,
            "Meeting": 30,
            "LinkedIn": 15,
            "Note": 10,
        }

    @property
    def phase_weights(self) -> Dict[str, Dict[str, int]]:
        return {
            "early": {"Email": 20, "Phone Call": 15, "Meeting": 15, "LinkedIn": 40, "Note": 10},
            "mid":   {"Email": 25, "Phone Call": 15, "Meeting": 40, "LinkedIn": 10, "Note": 10},
            "late":  {"Email": 40, "Phone Call": 15, "Meeting": 25, "LinkedIn": 5,  "Note": 15},
        }

    @property
    def activity_count_ranges(self) -> Dict[str, Tuple[int, int]]:
        return {
            "Won": (10, 18),
            "Lost": (4, 8),
        }

    @property
    def segment_activity_multiplier(self) -> Dict[str, float]:
        return {
            "SMB": 0.8,
            "Mid-Market": 1.0,
            "Enterprise": 1.3,
        }

    @property
    def subjects(self) -> Dict[str, List[str]]:
        return {
            "Email": [
                "Proposal follow-up",
                "Engagement scope outline",
                "Case study - similar project",
                "Statement of work draft",
                "Rate card and availability",
                "Thought leadership piece",
            ],
            "Phone Call": [
                "Needs assessment call",
                "Stakeholder alignment call",
                "Scope clarification",
                "Partner introduction",
                "Project status check-in",
                "Retainer renewal discussion",
            ],
            "Meeting": [
                "Discovery workshop",
                "Proposal presentation",
                "Executive sponsor meeting",
                "Project kick-off",
                "Quarterly business review",
                "Strategy alignment session",
            ],
            "LinkedIn": [
                "Connection request",
                "Thought leadership share",
                "InMail introduction",
                "Conference follow-up",
                "Article engagement",
            ],
            "Note": [
                "Met at industry conference",
                "Referral from partner firm",
                "Internal team briefing",
                "Competitive intelligence",
                "Budget cycle timing note",
            ],
        }

    @property
    def phase_biased_subjects(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "early": {
                "Email": ["Engagement scope outline", "Case study - similar project", "Thought leadership piece"],
                "Phone Call": ["Needs assessment call", "Partner introduction"],
                "Meeting": ["Discovery workshop", "Strategy alignment session"],
                "LinkedIn": ["Connection request", "InMail introduction", "Conference follow-up"],
                "Note": ["Met at industry conference", "Referral from partner firm"],
            },
            "mid": {
                "Email": ["Case study - similar project", "Rate card and availability"],
                "Phone Call": ["Stakeholder alignment call", "Scope clarification"],
                "Meeting": ["Proposal presentation", "Executive sponsor meeting"],
                "LinkedIn": ["Thought leadership share", "Article engagement"],
                "Note": ["Competitive intelligence", "Internal team briefing"],
            },
            "late": {
                "Email": ["Proposal follow-up", "Statement of work draft", "Rate card and availability"],
                "Phone Call": ["Project status check-in", "Retainer renewal discussion"],
                "Meeting": ["Executive sponsor meeting", "Quarterly business review"],
                "LinkedIn": ["Article engagement"],
                "Note": ["Budget cycle timing note", "Internal team briefing"],
            },
        }

    @property
    def duration_ranges(self) -> Dict[str, Optional[Tuple[int, int]]]:
        return {
            "Email": None,
            "Phone Call": (15, 45),
            "Meeting": (45, 120),
            "LinkedIn": None,
            "Note": None,
        }
