"""
Generators package for creating realistic CRM data.

This package contains modules for generating different types of CRM entities
such as accounts, contacts, opportunities, etc.
"""

from .accounts import AccountGenerator
from .contacts import ContactGenerator
from .deals import DealGenerator

__all__ = ["AccountGenerator", "ContactGenerator", "DealGenerator"]
