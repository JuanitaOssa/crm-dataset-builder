"""
HubSpot CRM Exporter

Transforms generated CRM data into HubSpot-compatible import files.
Uses HubSpot's two-object import method for associations (company domain
matching for contacts and deals).
"""

from typing import Dict

import pandas as pd

from .base import BaseCRMExporter


class HubSpotExporter(BaseCRMExporter):
    """
    Exports CRM data in HubSpot-compatible format.

    HubSpot associations use company domain matching:
    - Contacts are linked to companies via domain name
    - Deals are linked to companies and contacts via domain/email

    Owner identifiers use email format: sarah.chen@testcompany.com
    """

    def __init__(self, accounts_df, contacts_df, deals_df, activities_df, profile=None):
        super().__init__(accounts_df, contacts_df, deals_df, activities_df, profile=profile)

    def crm_name(self) -> str:
        return "HubSpot"

    # ------------------------------------------------------------------ #
    #  Field mappings                                                      #
    # ------------------------------------------------------------------ #

    def account_field_mapping(self) -> Dict[str, str]:
        return {
            "company_name": "name",
            "industry": "industry",
            "annual_revenue": "annualrevenue",
            "employee_count": "numberofemployees",
            "street_address": "address",
            "city": "city",
            "state": "state",
            "zip_code": "zip",
            "country": "country",
            "website": "domain",
            "description": "description",
            "founded_year": "founded_year",
        }

    def contact_field_mapping(self) -> Dict[str, str]:
        return {
            "first_name": "firstname",
            "last_name": "lastname",
            "email": "email",
            "phone": "phone",
            "title": "jobtitle",
            "department": "department",
            "contact_owner": "hubspot_owner_id",
        }

    def deal_field_mapping(self) -> Dict[str, str]:
        mapping = {
            "deal_name": "dealname",
            "pipeline": "pipeline",
            "stage": "dealstage",
            "amount": "amount",
            "created_date": "createdate",
            "close_date": "closedate",
            "deal_status": "deal_status",
            "deal_owner": "hubspot_owner_id",
        }
        if "subscription_type" in self.profile.deal_fields:
            mapping["subscription_type"] = "subscription_type"
        return mapping

    def activity_field_mapping(self) -> Dict[str, str]:
        return {
            "activity_type": "hs_activity_type",
            "subject": "hs_timestamp_subject",
            "activity_date": "hs_timestamp",
            "completed": "hs_activity_status",
            "duration_minutes": "hs_duration",
            "notes": "hs_body",
            "activity_owner": "hubspot_owner_id",
        }

    def activity_type_mapping(self) -> Dict[str, str]:
        return {
            "Email": "EMAIL",
            "Phone Call": "CALL",
            "Meeting": "MEETING",
            "LinkedIn": "NOTE",
            "Note": "NOTE",
        }

    def format_owner(self, name: str) -> str:
        """Convert 'Sarah Chen' -> 'sarah.chen@testcompany.com'."""
        parts = name.lower().replace("'", "").split()
        return f"{'.'.join(parts)}@testcompany.com"

    # ------------------------------------------------------------------ #
    #  Association files (two-object import)                               #
    # ------------------------------------------------------------------ #

    def generate_association_files(self) -> Dict[str, pd.DataFrame]:
        """
        Generate HubSpot two-object import association files.

        HubSpot links records via domain (companies) and email (contacts).
        """
        files = {}

        # Build lookup: account_id -> company domain
        domain_lookup = dict(zip(
            self.accounts_df["id"].astype(str),
            self.accounts_df["website"].apply(self._get_domain),
        ))

        # Build lookup: contact_id -> email
        email_lookup = dict(zip(
            self.contacts_df["contact_id"].astype(str),
            self.contacts_df["email"],
        ))

        # --- Companies (standalone, with clean domain) ---
        acc_copy = self.accounts_df.copy()
        acc_copy["website"] = acc_copy["website"].apply(self._get_domain)
        files["hubspot_companies.csv"] = self._map_dataframe(
            acc_copy, self.account_field_mapping()
        )

        # --- Contacts with Companies ---
        contacts_assoc = self.contacts_df.copy()
        contacts_assoc["Company Domain Name"] = contacts_assoc["account_id"].astype(str).map(domain_lookup)
        mapped_contacts = self._map_dataframe(
            contacts_assoc, self.contact_field_mapping(), owner_col="contact_owner"
        )
        mapped_contacts["Company Domain Name"] = contacts_assoc["Company Domain Name"]
        files["hubspot_contacts_with_companies.csv"] = mapped_contacts

        # --- Deals with Companies ---
        deals_assoc = self.deals_df.copy()
        deals_assoc["Company Domain Name"] = deals_assoc["account_id"].astype(str).map(domain_lookup)
        mapped_deals = self._map_dataframe(
            deals_assoc, self.deal_field_mapping(), owner_col="deal_owner"
        )
        mapped_deals["Company Domain Name"] = deals_assoc["Company Domain Name"]
        files["hubspot_deals_with_companies.csv"] = mapped_deals

        # --- Deals with Contacts ---
        deals_contact = self.deals_df.copy()
        deals_contact["Contact Email"] = deals_contact["contact_id"].astype(str).map(email_lookup)
        mapped_deals_c = self._map_dataframe(
            deals_contact, self.deal_field_mapping(), owner_col="deal_owner"
        )
        mapped_deals_c["Contact Email"] = deals_contact["Contact Email"]
        files["hubspot_deals_with_contacts.csv"] = mapped_deals_c

        # --- Activities (standalone) ---
        files["hubspot_activities.csv"] = self._map_dataframe(
            self.activities_df, self.activity_field_mapping(),
            owner_col="activity_owner", activity_type_col="activity_type"
        )

        return files

    # ------------------------------------------------------------------ #
    #  Import guide                                                        #
    # ------------------------------------------------------------------ #

    def generate_import_guide(self) -> str:
        profile = self.profile

        # Build pipeline/stage section dynamically
        pipeline_section = ""
        for pipeline_name, stages in profile.pipelines.items():
            active_stages = [s for s in stages if s not in ("Closed Won", "Closed Lost", "Churned")]
            terminal = [s for s in stages if s in ("Closed Won", "Closed Lost", "Churned")]
            stage_flow = " → ".join(active_stages)
            if terminal:
                stage_flow += " → " + " / ".join(terminal)
            pipeline_section += f"\n- **{pipeline_name}**: {stage_flow}"

        # Build users list
        users_list = "\n".join(f"   - `{self.format_owner(rep)}` ({rep})" for rep in profile.sales_reps)

        return f"""# HubSpot Import Guide — {profile.name}

## Prerequisites

1. **Create users** in HubSpot matching the emails in `hubspot_users.csv`:
{users_list}
2. Ensure you have **admin access** to the HubSpot account

## Pipeline Setup ({profile.name})

Create the following pipelines in **Settings → Objects → Deals → Pipelines**:
{pipeline_section}

## Import Order

Import files in this exact order to preserve relationships:

### Step 1: Import Companies
1. Go to **Contacts → Companies**
2. Click **Import** → **Start an import**
3. Select **File from computer** → **One file** → **One object**
4. Choose `hubspot_companies.csv`
5. Map all fields and complete the import

### Step 2: Import Contacts with Company Associations
1. Go to **Contacts → Contacts**
2. Click **Import** → **Start an import**
3. Select **File from computer** → **One file** → **Two objects**
4. Select **Contacts** and **Companies**
5. Choose `hubspot_contacts_with_companies.csv`
6. HubSpot will use the **Company Domain Name** column to match contacts to companies
7. Map all fields and complete the import

### Step 3: Import Deals with Company Associations
1. Go to **Sales → Deals**
2. Click **Import** → **Start an import**
3. Select **File from computer** → **One file** → **Two objects**
4. Select **Deals** and **Companies**
5. Choose `hubspot_deals_with_companies.csv`
6. Map all fields and complete the import

### Step 4: Import Deal-Contact Associations
1. Repeat the import process with `hubspot_deals_with_contacts.csv`
2. Select **Deals** and **Contacts** as the two objects
3. HubSpot will use the **Contact Email** column to match

### Step 5: Import Activities
1. Go to **Contacts → Contacts**
2. Click **Import** → **Start an import**
3. Choose `hubspot_activities.csv`
4. Map activity fields and complete the import

## Field Mapping Reference

| Generated Field | HubSpot Field |
|----------------|---------------|
| name | Company name |
| domain | Company domain name |
| annualrevenue | Annual revenue |
| numberofemployees | Number of employees |
| firstname | First name |
| lastname | Last name |
| email | Email |
| jobtitle | Job title |
| dealname | Deal name |
| pipeline | Pipeline |
| dealstage | Deal stage |
| amount | Amount |
| createdate | Create date |
| closedate | Close date |

## Data Quality Notes
- The **domain** field in `hubspot_companies.csv` contains clean domains (e.g., `clouddata.io`) — these match the `Company Domain Name` column in association files
- Contact **emails are unique** per company domain — no duplicates
- **Phone numbers** use consistent `(XXX) XXX-XXXX` format
- The `hubspot_owner_id` field maps to user emails — ensure users exist before importing
- Activity types are mapped to HubSpot engagement types (EMAIL, CALL, MEETING, NOTE)
- Deal stages must match the pipeline configuration created above
- The `hubspot_users.csv` file lists all sales reps — create these as users in HubSpot before importing data
"""
