"""
Base CRM Exporter Module

Provides the abstract base class for CRM-specific export adapters.
Each CRM adapter (HubSpot, Salesforce, Zoho) inherits from BaseCRMExporter
and implements its own field mappings, association files, and import guide.
"""

import io
import zipfile
from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class BaseCRMExporter(ABC):
    """
    Abstract base class for CRM export adapters.

    Takes the 4 standard DataFrames (accounts, contacts, deals, activities)
    and transforms them into CRM-specific CSV files with proper field
    mappings, association files, and import guides.

    To add a new CRM adapter:
        1. Create a new file in src/exporters/ (e.g., pipedrive.py)
        2. Subclass BaseCRMExporter
        3. Implement all abstract methods
        4. Add the import to src/exporters/__init__.py
    """

    def __init__(
        self,
        accounts_df: pd.DataFrame,
        contacts_df: pd.DataFrame,
        deals_df: pd.DataFrame,
        activities_df: pd.DataFrame,
        profile=None,
    ):
        self.accounts_df = accounts_df.copy()
        self.contacts_df = contacts_df.copy()
        self.deals_df = deals_df.copy()
        self.activities_df = activities_df.copy()

        if profile is None:
            from profiles.b2b_saas import B2BSaaSProfile
            profile = B2BSaaSProfile()
        self.profile = profile

    # ------------------------------------------------------------------ #
    #  Abstract methods — subclasses must implement these                  #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def crm_name(self) -> str:
        """Return the CRM name (e.g., 'HubSpot', 'Salesforce', 'Zoho')."""

    @abstractmethod
    def account_field_mapping(self) -> Dict[str, str]:
        """Return mapping: internal field name -> CRM field name for accounts."""

    @abstractmethod
    def contact_field_mapping(self) -> Dict[str, str]:
        """Return mapping for contacts."""

    @abstractmethod
    def deal_field_mapping(self) -> Dict[str, str]:
        """Return mapping for deals."""

    @abstractmethod
    def activity_field_mapping(self) -> Dict[str, str]:
        """Return mapping for activities."""

    @abstractmethod
    def activity_type_mapping(self) -> Dict[str, str]:
        """Map internal activity types to CRM-specific types.
        e.g., {'Email': 'EMAIL', 'Phone Call': 'CALL', ...}
        """

    @abstractmethod
    def format_owner(self, name: str) -> str:
        """Convert a sales rep name to CRM-specific owner identifier.
        e.g., 'Sarah Chen' -> 'sarah.chen@testcompany.com'
        """

    @abstractmethod
    def generate_association_files(self) -> Dict[str, pd.DataFrame]:
        """Generate CRM-specific individual object files with association columns.
        Returns dict of filename -> DataFrame.
        """

    @abstractmethod
    def generate_master_file(self) -> pd.DataFrame:
        """Generate a single denormalized master import file.
        One Record Type column identifies each row (Company, Contact, Deal, Activity).
        Association fields link child records to parents.
        """

    @abstractmethod
    def generate_import_guide(self) -> str:
        """Generate a markdown import guide for this CRM."""

    # ------------------------------------------------------------------ #
    #  Common methods                                                      #
    # ------------------------------------------------------------------ #

    def _map_dataframe(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        owner_col: str = None,
        activity_type_col: str = None,
    ) -> pd.DataFrame:
        """
        Apply field mapping to a DataFrame.

        Args:
            df: Source DataFrame.
            mapping: Dict of internal_field -> crm_field.
            owner_col: If set, apply format_owner() to this column before rename.
            activity_type_col: If set, apply activity_type_mapping() to this column.
        """
        result = df.copy()

        # Map owner values before renaming columns — skip empty owners
        if owner_col and owner_col in result.columns:
            result[owner_col] = result[owner_col].apply(
                lambda v: self.format_owner(v) if v else ""
            )

        # Map activity types before renaming columns
        if activity_type_col and activity_type_col in result.columns:
            type_map = self.activity_type_mapping()
            result[activity_type_col] = result[activity_type_col].map(type_map).fillna(
                result[activity_type_col]
            )

        # Only keep columns that are in the mapping and rename them
        cols_to_keep = [c for c in mapping.keys() if c in result.columns]
        result = result[cols_to_keep].rename(columns=mapping)
        return result

    def generate_users_file(self) -> pd.DataFrame:
        """Generate a users/owners reference file for the CRM."""
        rows = []
        for name in self.profile.sales_reps:
            parts = name.split()
            rows.append({
                "full_name": name,
                "first_name": parts[0],
                "last_name": parts[-1],
                "identifier": self.format_owner(name),
            })
        return pd.DataFrame(rows)

    def _get_domain(self, website: str) -> str:
        """Extract domain from website URL (e.g., 'https://www.foo.com' -> 'foo.com')."""
        domain = website.replace("https://", "").replace("http://", "").replace("www.", "")
        return domain.strip("/")

    def export(self) -> Dict[str, object]:
        """
        Export all CRM-formatted files.

        Returns:
            Dict mapping filename -> content (DataFrame for CSVs, str for .md files).
        """
        name = self.crm_name().lower()
        files = {}

        # Master import file (recommended for import)
        files[f"{name}_master_import.csv"] = self.generate_master_file()

        # Individual object files with association columns
        for filename, df in self.generate_association_files().items():
            files[filename] = df

        # Users reference file
        files[f"{name}_users_reference.csv"] = self.generate_users_file()

        # Import guide
        files[f"IMPORT_GUIDE_{name.upper()}.md"] = self.generate_import_guide()

        return files

    def export_zip(self) -> bytes:
        """Export all files as an in-memory ZIP archive."""
        files = self.export()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                if isinstance(content, pd.DataFrame):
                    zf.writestr(filename, content.to_csv(index=False))
                else:
                    zf.writestr(filename, content)
        return buf.getvalue()
