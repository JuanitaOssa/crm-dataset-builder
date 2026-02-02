"""
Profiles package for business-type-specific CRM data generation.

Each profile defines all business-specific constants (company names, industries,
pipelines, stages, deal sizes, activity subjects, etc.) while generators contain
only the distribution logic.
"""

from .base import BaseProfile
from .b2b_saas import B2BSaaSProfile
from .manufacturer import ManufacturerProfile
from .consultancy import ConsultancyProfile

PROFILE_REGISTRY = {
    "B2B SaaS Company": B2BSaaSProfile,
    "Manufacturer / Distributor": ManufacturerProfile,
    "Consultancy / Professional Services": ConsultancyProfile,
}

__all__ = [
    "BaseProfile",
    "B2BSaaSProfile",
    "ManufacturerProfile",
    "ConsultancyProfile",
    "PROFILE_REGISTRY",
]
