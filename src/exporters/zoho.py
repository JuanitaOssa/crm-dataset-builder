"""
Zoho CRM Exporter

Transforms generated CRM data into Zoho CRM-compatible import files.
Uses name-based matching for object associations, which is Zoho's
default import behavior.
"""

from typing import Dict

import pandas as pd

from .base import BaseCRMExporter


class ZohoExporter(BaseCRMExporter):
    """
    Exports CRM data in Zoho CRM-compatible format.

    Zoho associations use name-based matching:
    - Contacts reference accounts by Account_Name
    - Deals reference accounts and contacts by name

    Owner identifiers use email format: sarah.chen@testcompany.com
    """

    def __init__(self, accounts_df, contacts_df, deals_df, activities_df, profile=None):
        super().__init__(accounts_df, contacts_df, deals_df, activities_df, profile=profile)

    def crm_name(self) -> str:
        return "Zoho"

    # ------------------------------------------------------------------ #
    #  Field mappings                                                      #
    # ------------------------------------------------------------------ #

    def account_field_mapping(self) -> Dict[str, str]:
        return {
            "company_name": "Account_Name",
            "industry": "Industry",
            "annual_revenue": "Annual_Revenue",
            "employee_count": "Employees",
            "street_address": "Billing_Street",
            "city": "Billing_City",
            "state": "Billing_State",
            "zip_code": "Billing_Code",
            "country": "Billing_Country",
            "website": "Website",
            "description": "Description",
        }

    def contact_field_mapping(self) -> Dict[str, str]:
        return {
            "first_name": "First_Name",
            "last_name": "Last_Name",
            "email": "Email",
            "phone": "Phone",
            "title": "Title",
            "department": "Department",
            "contact_owner": "Owner",
        }

    def deal_field_mapping(self) -> Dict[str, str]:
        mapping = {
            "deal_name": "Deal_Name",
            "pipeline": "Pipeline",
            "stage": "Stage",
            "amount": "Amount",
            "created_date": "Created_Time",
            "close_date": "Closing_Date",
            "deal_status": "Status",
            "deal_owner": "Owner",
        }
        if "subscription_type" in self.profile.deal_fields:
            mapping["subscription_type"] = "Subscription_Type"
        return mapping

    def activity_field_mapping(self) -> Dict[str, str]:
        return {
            "activity_type": "Activity_Type",
            "subject": "Subject",
            "activity_date": "Activity_Date",
            "completed": "Status",
            "duration_minutes": "Duration",
            "notes": "Description",
            "activity_owner": "Owner",
        }

    def activity_type_mapping(self) -> Dict[str, str]:
        return {
            "Email": "Emails",
            "Phone Call": "Calls",
            "Meeting": "Meetings",
            "LinkedIn": "Notes",
            "Note": "Notes",
        }

    def format_owner(self, name: str) -> str:
        """Convert 'Sarah Chen' -> 'sarah.chen@testcompany.com'."""
        parts = name.lower().replace("'", "").split()
        return f"{'.'.join(parts)}@testcompany.com"

    # ------------------------------------------------------------------ #
    #  Association files (name-based matching)                             #
    # ------------------------------------------------------------------ #

    def generate_association_files(self) -> Dict[str, pd.DataFrame]:
        """
        Generate Zoho import files with name-based association columns.

        Zoho uses Account_Name and Contact_Name for matching
        during CSV imports.
        """
        files = {}

        # Build lookups
        account_name_lookup = dict(zip(
            self.accounts_df["id"].astype(str),
            self.accounts_df["company_name"],
        ))
        contact_name_lookup = dict(zip(
            self.contacts_df["contact_id"].astype(str),
            self.contacts_df["first_name"] + " " + self.contacts_df["last_name"],
        ))

        # --- Accounts (standard mapped) ---
        files["zoho_accounts.csv"] = self._map_dataframe(
            self.accounts_df, self.account_field_mapping()
        )

        # --- Contacts with Account_Name ---
        con_mapped = self._map_dataframe(
            self.contacts_df, self.contact_field_mapping(), owner_col="contact_owner"
        )
        con_mapped["Account_Name"] = self.contacts_df["account_id"].astype(str).map(
            account_name_lookup
        )
        files["zoho_contacts.csv"] = con_mapped

        # --- Deals with Account_Name and Contact_Name ---
        deal_mapped = self._map_dataframe(
            self.deals_df, self.deal_field_mapping(), owner_col="deal_owner"
        )
        deal_mapped["Account_Name"] = self.deals_df["account_id"].astype(str).map(
            account_name_lookup
        )
        deal_mapped["Contact_Name"] = self.deals_df["contact_id"].astype(str).map(
            contact_name_lookup
        )
        files["zoho_deals.csv"] = deal_mapped

        # --- Activities with references ---
        act_mapped = self._map_dataframe(
            self.activities_df, self.activity_field_mapping(),
            owner_col="activity_owner", activity_type_col="activity_type"
        )
        act_mapped["Account_Name"] = self.activities_df["account_id"].astype(str).map(
            account_name_lookup
        )
        act_mapped["Contact_Name"] = self.activities_df["contact_id"].astype(str).map(
            contact_name_lookup
        )
        files["zoho_activities.csv"] = act_mapped

        return files

    # ------------------------------------------------------------------ #
    #  Import guide                                                        #
    # ------------------------------------------------------------------ #

    def generate_import_guide(self) -> str:
        return """# Zoho CRM Import Guide

## Prerequisites
1. Create users in Zoho CRM matching the emails in `zoho_users.csv`
2. Ensure deal stages in Zoho match the Stage values in the data
3. Have admin access to the Zoho CRM account

## Import Order

Import files in this exact order to preserve relationships:

### Step 1: Import Accounts
1. Go to **Accounts** module
2. Click the **...** menu > **Import**
3. Choose `zoho_accounts.csv`
4. Map fields:
   - `Account_Name` -> Account Name
   - `Annual_Revenue` -> Annual Revenue
   - `Employees` -> Employees
   - `Billing_Street`, `Billing_City`, `Billing_State`, `Billing_Code` -> Billing address fields
5. Complete the import

### Step 2: Import Contacts
1. Go to **Contacts** module
2. Click **Import**
3. Choose `zoho_contacts.csv`
4. Map fields:
   - `First_Name`, `Last_Name`, `Email`, `Phone`, `Title`
   - `Account_Name` -> Account Name (Zoho will match by name)
5. Complete the import — contacts will auto-link to accounts by name

### Step 3: Import Deals
1. Go to **Deals** module
2. Click **Import**
3. Choose `zoho_deals.csv`
4. Map fields:
   - `Deal_Name` -> Deal Name
   - `Stage` -> Stage
   - `Amount` -> Amount
   - `Closing_Date` -> Closing Date
   - `Account_Name` -> Account Name (lookup)
   - `Contact_Name` -> Contact Name (lookup)
5. Complete the import

### Step 4: Import Activities
1. For **Calls**: Filter `zoho_activities.csv` for Activity_Type = "Calls"
   - Go to **Activities > Calls** > Import
2. For **Meetings**: Filter for Activity_Type = "Meetings"
   - Go to **Activities > Meetings** > Import
3. For **Emails/Notes**: Import remaining as Notes
   - Go to module and import with account/contact lookup

## Field Mapping Reference

| Generated Field | Zoho Field |
|----------------|------------|
| Account_Name | Account Name |
| Annual_Revenue | Annual Revenue |
| Employees | Employees |
| First_Name / Last_Name | First Name / Last Name |
| Email | Email |
| Title | Title |
| Deal_Name | Deal Name |
| Stage | Stage |
| Amount | Amount |
| Closing_Date | Closing Date |

## Notes
- Zoho uses **name-based matching** — Account_Name and Contact_Name must match exactly
- The `Owner` field maps to Zoho user emails — create users before importing
- Activity types are mapped to Zoho modules: Calls, Meetings, and Notes
- Deals require a Closing_Date; open deals use an estimated future date
"""
