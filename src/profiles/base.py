"""
Base Profile Module

Defines the abstract base class that all business-type profiles must implement.
Each profile provides business-specific constants (company names, industries,
pipelines, deal sizes, activity subjects, etc.) while generators contain only
the distribution logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class BaseProfile(ABC):
    """
    Abstract base class defining the contract every business-type profile must follow.

    Subclasses provide all business-specific data constants so that generators
    remain pure distribution logic with no hardcoded business knowledge.
    """

    # ------------------------------------------------------------------ #
    #  Identity                                                            #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable profile name (e.g. 'B2B SaaS')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description for UI display."""

    # ------------------------------------------------------------------ #
    #  Sales team                                                          #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def sales_reps(self) -> List[str]:
        """List of 6 full sales rep names."""

    # ------------------------------------------------------------------ #
    #  Account generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def name_prefixes(self) -> List[str]:
        """Company name prefixes for generated names."""

    @property
    @abstractmethod
    def name_suffixes(self) -> List[str]:
        """Company name suffixes for generated names."""

    @property
    @abstractmethod
    def industries(self) -> List[str]:
        """Industry/sector list for account generation."""

    @property
    @abstractmethod
    def employee_tiers(self) -> List[Tuple[int, int, int]]:
        """Employee count tiers: list of (min, max, weight)."""

    @property
    @abstractmethod
    def revenue_per_employee_range(self) -> Tuple[int, int]:
        """(min, max) revenue per employee in USD."""

    @property
    @abstractmethod
    def website_tlds(self) -> List[str]:
        """Top-level domains for generated websites."""

    @property
    @abstractmethod
    def description_templates(self) -> List[str]:
        """Company description templates with {industry} placeholder."""

    @property
    @abstractmethod
    def founded_year_range(self) -> Tuple[int, int]:
        """(earliest, latest) founded year."""

    @property
    def company_name_strategies(self) -> List[str]:
        """Strategies for generating company names."""
        return ["prefix_suffix", "prefix_word", "faker"]

    # ------------------------------------------------------------------ #
    #  Contact generation                                                  #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def title_by_department(self) -> Dict[str, List[str]]:
        """Department -> list of realistic job titles."""

    @property
    @abstractmethod
    def department_weights(self) -> Dict[str, int]:
        """Department -> weight for random selection."""

    @property
    def contacts_per_account_weights(self) -> Tuple[List[int], List[int]]:
        """(counts, weights) for contacts per account."""
        return ([2, 3, 4, 5], [35, 35, 20, 10])

    # ------------------------------------------------------------------ #
    #  Deal generation                                                     #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def pipelines(self) -> Dict[str, List[str]]:
        """Pipeline name -> ordered list of stages."""

    @property
    @abstractmethod
    def primary_pipeline_name(self) -> str:
        """Name of the primary new-business pipeline."""

    @property
    @abstractmethod
    def renewal_pipeline_name(self) -> str:
        """Name of the renewal pipeline."""

    @property
    @abstractmethod
    def expansion_pipeline_name(self) -> str:
        """Name of the expansion pipeline."""

    @property
    @abstractmethod
    def outcome_rates(self) -> Dict[str, Dict[str, int]]:
        """Pipeline -> {Won: weight, Lost: weight, Open: weight}."""

    @property
    @abstractmethod
    def segments(self) -> List[str]:
        """Ordered list of segment names."""

    @abstractmethod
    def classify_segment(self, employee_count: int) -> str:
        """Classify an account into a segment based on employee count."""

    @property
    @abstractmethod
    def acv_ranges(self) -> Dict[str, Tuple[int, int]]:
        """Segment -> (min, max) annual contract value."""

    @property
    @abstractmethod
    def nb_cycle_days(self) -> Dict[str, Tuple[int, int]]:
        """Segment -> (min, max) new-business sales cycle days."""

    @property
    @abstractmethod
    def renewal_cycle_days(self) -> Tuple[int, int]:
        """(min, max) days for renewal cycle."""

    @property
    @abstractmethod
    def expansion_cycle_days(self) -> Tuple[int, int]:
        """(min, max) days for expansion cycle."""

    @property
    @abstractmethod
    def loss_reasons_default(self) -> Dict[str, int]:
        """Default loss reasons with weights."""

    @property
    @abstractmethod
    def loss_reasons_enterprise(self) -> Dict[str, int]:
        """Enterprise-specific loss reasons with weights."""

    @property
    @abstractmethod
    def active_stage_weights(self) -> Dict[str, Dict[str, int]]:
        """Pipeline -> {stage: weight} for open deal stage selection."""

    @property
    def accounts_with_deals_fraction(self) -> float:
        """Fraction of accounts that get deals."""
        return 0.70

    @property
    def nb_deal_count_weights(self) -> Tuple[List[int], List[int]]:
        """(counts, weights) for NB deals per account."""
        return ([1, 2, 3], [50, 35, 15])

    @property
    def renewal_timing_days(self) -> Tuple[int, int]:
        """(min, max) days after NB close for renewal creation."""
        return (350, 380)

    @property
    def expansion_probability(self) -> float:
        """Probability of an expansion deal per won NB deal."""
        return 0.50

    @property
    def expansion_timing_days(self) -> Tuple[int, int]:
        """(min, max) days after NB close for expansion creation."""
        return (90, 270)

    @property
    def renewal_amount_factor(self) -> Tuple[float, float]:
        """(min, max) multiplier for renewal amount vs original."""
        return (0.95, 1.05)

    @property
    def expansion_amount_factor(self) -> Tuple[float, float]:
        """(min, max) multiplier for expansion amount vs original."""
        return (0.20, 0.50)

    @abstractmethod
    def format_deal_name(self, company_name: str, created_date: str, **kwargs) -> str:
        """Generate a deal name given company name and created_date (YYYY-MM-DD)."""

    @property
    def self_serve_config(self) -> Optional[dict]:
        """Self-serve pipeline configuration. None if not applicable."""
        return None

    @property
    def subscription_type_weights(self) -> Optional[Dict[str, float]]:
        """Subscription type weights for sales-assisted deals. None if N/A."""
        return None

    # ------------------------------------------------------------------ #
    #  Activity generation                                                 #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def activity_types(self) -> List[str]:
        """Ordered list of activity type names."""

    @property
    @abstractmethod
    def activity_type_weights(self) -> Dict[str, int]:
        """Activity type -> weight for non-deal activities."""

    @property
    @abstractmethod
    def phase_weights(self) -> Dict[str, Dict[str, int]]:
        """Phase (early/mid/late) -> {activity_type: weight}."""

    @property
    @abstractmethod
    def activity_count_ranges(self) -> Dict[str, Tuple[int, int]]:
        """Deal outcome (Won/Lost) -> (min, max) activity count."""

    @property
    @abstractmethod
    def segment_activity_multiplier(self) -> Dict[str, float]:
        """Segment -> activity count multiplier."""

    @property
    @abstractmethod
    def subjects(self) -> Dict[str, List[str]]:
        """Activity type -> list of subject lines."""

    @property
    @abstractmethod
    def phase_biased_subjects(self) -> Dict[str, Dict[str, List[str]]]:
        """Phase -> {activity_type: [subject lines]}."""

    @property
    @abstractmethod
    def duration_ranges(self) -> Dict[str, Optional[Tuple[int, int]]]:
        """Activity type -> (min, max) minutes or None."""

    @property
    def outreach_type_weights(self) -> List[int]:
        """Weights for outreach activity types: [Email, Call, Meeting, LinkedIn, Note]."""
        return [30, 15, 5, 40, 10]

    @property
    def zero_activity_fraction(self) -> float:
        """Fraction of accounts with zero activities."""
        return 0.10

    # ------------------------------------------------------------------ #
    #  Field definitions                                                   #
    # ------------------------------------------------------------------ #

    @property
    def account_fields(self) -> List[str]:
        """Ordered list of account CSV field names."""
        return [
            "id", "company_name", "industry", "employee_count",
            "annual_revenue", "street_address", "city", "state", "zip_code",
            "country", "region", "founded_year", "website", "description",
        ]

    @property
    def contact_fields(self) -> List[str]:
        """Ordered list of contact CSV field names."""
        return [
            "contact_id", "first_name", "last_name", "email", "phone",
            "title", "department", "account_id", "contact_owner",
        ]

    @property
    def deal_fields(self) -> List[str]:
        """Ordered list of deal CSV field names."""
        fields = [
            "deal_id", "deal_name", "account_id", "contact_id", "pipeline",
            "segment", "stage", "amount", "created_date", "close_date",
            "deal_status", "deal_owner", "loss_reason",
        ]
        if self.self_serve_config is not None or self.subscription_type_weights is not None:
            fields.append("subscription_type")
        return fields

    @property
    def activity_fields(self) -> List[str]:
        """Ordered list of activity CSV field names."""
        return [
            "activity_id", "activity_type", "subject", "activity_date",
            "account_id", "contact_id", "deal_id", "completed",
            "duration_minutes", "notes", "activity_owner",
        ]
