"""
Salesforce CRM Exporter

Transforms generated CRM data into Salesforce-compatible import files.
Uses External ID references for object associations, compatible with
both Data Import Wizard and Data Loader.
"""

from typing import Dict

import pandas as pd

from .base import BaseCRMExporter


class SalesforceExporter(BaseCRMExporter):
    """
    Exports CRM data in Salesforce-compatible format.

    Salesforce associations use External ID references:
    - Accounts get an External_ID__c field
    - Contacts reference accounts via Account_External_ID__c
    - Opportunities reference accounts and contacts via External_ID__c

    Owner identifiers use username format: sarah.chen
    """

    def crm_name(self) -> str:
        return "Salesforce"

    # ------------------------------------------------------------------ #
    #  Field mappings                                                      #
    # ------------------------------------------------------------------ #

    def account_field_mapping(self) -> Dict[str, str]:
        return {
            "company_name": "Name",
            "industry": "Industry",
            "annual_revenue": "AnnualRevenue",
            "employee_count": "NumberOfEmployees",
            "street_address": "BillingStreet",
            "city": "BillingCity",
            "state": "BillingState",
            "zip_code": "BillingPostalCode",
            "country": "BillingCountry",
            "website": "Website",
            "description": "Description",
        }

    def contact_field_mapping(self) -> Dict[str, str]:
        return {
            "first_name": "FirstName",
            "last_name": "LastName",
            "email": "Email",
            "phone": "Phone",
            "title": "Title",
            "department": "Department",
            "contact_owner": "Owner",
        }

    def deal_field_mapping(self) -> Dict[str, str]:
        return {
            "deal_name": "Name",
            "stage": "StageName",
            "amount": "Amount",
            "created_date": "CreatedDate",
            "close_date": "CloseDate",
            "deal_status": "Status",
            "deal_owner": "Owner",
        }

    def activity_field_mapping(self) -> Dict[str, str]:
        return {
            "activity_type": "Type",
            "subject": "Subject",
            "activity_date": "ActivityDate",
            "completed": "Status",
            "duration_minutes": "DurationInMinutes",
            "notes": "Description",
            "activity_owner": "Owner",
        }

    def activity_type_mapping(self) -> Dict[str, str]:
        return {
            "Email": "Email",
            "Phone Call": "Call",
            "Meeting": "Event",
            "LinkedIn": "Task",
            "Note": "Task",
        }

    def format_owner(self, name: str) -> str:
        """Convert 'Sarah Chen' -> 'sarah.chen'."""
        parts = name.lower().replace("'", "").split()
        return ".".join(parts)

    # ------------------------------------------------------------------ #
    #  Association files (External ID references)                          #
    # ------------------------------------------------------------------ #

    def generate_association_files(self) -> Dict[str, pd.DataFrame]:
        """
        Generate Salesforce import files with External ID references.

        Salesforce uses External_ID__c fields for cross-object lookups
        during Data Loader imports.
        """
        files = {}

        # --- Accounts with External ID ---
        acc_mapped = self._map_dataframe(
            self.accounts_df, self.account_field_mapping()
        )
        acc_mapped.insert(0, "External_ID__c", self.accounts_df["id"].astype(str).apply(
            lambda x: f"ACC-{x}"
        ))
        files["salesforce_accounts.csv"] = acc_mapped

        # --- Contacts with Account External ID ---
        con_mapped = self._map_dataframe(
            self.contacts_df, self.contact_field_mapping(), owner_col="contact_owner"
        )
        con_mapped.insert(0, "External_ID__c", self.contacts_df["contact_id"].astype(str).apply(
            lambda x: f"CON-{x}"
        ))
        con_mapped["Account_External_ID__c"] = self.contacts_df["account_id"].astype(str).apply(
            lambda x: f"ACC-{x}"
        )
        files["salesforce_contacts.csv"] = con_mapped

        # --- Opportunities with Account and Contact External IDs ---
        deal_mapped = self._map_dataframe(
            self.deals_df, self.deal_field_mapping(), owner_col="deal_owner"
        )
        deal_mapped.insert(0, "External_ID__c", self.deals_df["deal_id"].astype(str).apply(
            lambda x: f"OPP-{x}"
        ))
        deal_mapped["Account_External_ID__c"] = self.deals_df["account_id"].astype(str).apply(
            lambda x: f"ACC-{x}"
        )
        deal_mapped["Contact_External_ID__c"] = self.deals_df["contact_id"].astype(str).apply(
            lambda x: f"CON-{x}"
        )
        files["salesforce_opportunities.csv"] = deal_mapped

        # --- Activities with references ---
        act_mapped = self._map_dataframe(
            self.activities_df, self.activity_field_mapping(),
            owner_col="activity_owner", activity_type_col="activity_type"
        )
        act_mapped["Account_External_ID__c"] = self.activities_df["account_id"].astype(str).apply(
            lambda x: f"ACC-{x}"
        )
        act_mapped["Contact_External_ID__c"] = self.activities_df["contact_id"].astype(str).apply(
            lambda x: f"CON-{x}"
        )
        # Only add deal reference for deal-linked activities
        act_mapped["Opportunity_External_ID__c"] = self.activities_df["deal_id"].apply(
            lambda x: f"OPP-{x}" if x else ""
        )
        files["salesforce_activities.csv"] = act_mapped

        return files

    # ------------------------------------------------------------------ #
    #  Import guide                                                        #
    # ------------------------------------------------------------------ #

    def generate_import_guide(self) -> str:
        return """# Salesforce Import Guide

## Prerequisites
1. Create users in Salesforce matching the usernames in `salesforce_users.csv`
2. Create a custom text field `External_ID__c` on Account, Contact, and Opportunity objects
   - Mark it as **External ID** and **Unique**
3. Ensure pipeline stages in Salesforce match the StageName values in the data

## Import Order

Import files in this exact order using **Data Loader** or **Data Import Wizard**:

### Step 1: Import Accounts
1. Open **Data Loader** (or Setup > Data Import Wizard)
2. Select **Insert** operation on the **Account** object
3. Choose `salesforce_accounts.csv`
4. Map fields:
   - `External_ID__c` -> External_ID__c
   - `Name` -> Account Name
   - `AnnualRevenue` -> Annual Revenue
   - `NumberOfEmployees` -> Employees
   - `BillingStreet`, `BillingCity`, `BillingState`, `BillingPostalCode` -> Billing Address fields
5. Complete the import

### Step 2: Import Contacts
1. Select **Insert** on the **Contact** object
2. Choose `salesforce_contacts.csv`
3. Map fields:
   - `External_ID__c` -> External_ID__c
   - `Account_External_ID__c` -> Account (External ID lookup)
   - `FirstName`, `LastName`, `Email`, `Phone`, `Title`, `Department`
4. Complete the import — contacts will auto-link to accounts via External ID

### Step 3: Import Opportunities
1. Select **Insert** on the **Opportunity** object
2. Choose `salesforce_opportunities.csv`
3. Map fields:
   - `External_ID__c` -> External_ID__c
   - `Account_External_ID__c` -> Account (External ID lookup)
   - `Contact_External_ID__c` -> Primary Contact (External ID lookup)
   - `Name` -> Opportunity Name
   - `StageName` -> Stage
   - `Amount`, `CloseDate`, `CreatedDate`
4. Complete the import

### Step 4: Import Activities
1. For **Events** (Meetings): Filter `salesforce_activities.csv` for Type = "Event"
2. For **Tasks** (Calls, Emails, LinkedIn, Notes): Filter for Type != "Event"
3. Import each subset to the appropriate object
4. Use `Account_External_ID__c` and `Contact_External_ID__c` for lookups

## Field Mapping Reference

| Generated Field | Salesforce Field |
|----------------|-----------------|
| Name | Account Name / Opportunity Name |
| AnnualRevenue | Annual Revenue |
| NumberOfEmployees | Employees |
| BillingStreet | Billing Street |
| FirstName / LastName | First Name / Last Name |
| Email | Email |
| Title | Title |
| StageName | Stage |
| Amount | Amount |
| CloseDate | Close Date |

## Notes
- External_ID__c enables upsert operations for future data refreshes
- The `Owner` field maps to Salesforce usernames — assign via Data Loader's owner lookup
- Meetings map to Events; Calls, LinkedIn, and Notes map to Tasks
- Ensure Opportunity stage values match your Salesforce org's picklist
"""
