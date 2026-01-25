"""
Generators package for creating realistic CRM data.

This package contains modules for generating different types of CRM entities
such as accounts, contacts, opportunities, etc.
"""

from .accounts import AccountGenerator

__all__ = ["AccountGenerator"]
