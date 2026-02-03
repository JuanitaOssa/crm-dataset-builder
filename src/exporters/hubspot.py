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

    def _build_lookups(self):
        """Build reusable association lookups for HubSpot exports."""
        # account_id -> clean domain
        domain_lookup = dict(zip(
            self.accounts_df["id"].astype(str),
            self.accounts_df["website"].apply(self._get_domain),
        ))
        # contact_id -> email
        email_lookup = dict(zip(
            self.contacts_df["contact_id"].astype(str),
            self.contacts_df["email"],
        ))
        # deal_id -> deal_name (for activity association)
        deal_name_lookup = dict(zip(
            self.deals_df["deal_id"].astype(str),
            self.deals_df["deal_name"],
        ))
        return domain_lookup, email_lookup, deal_name_lookup

    def generate_association_files(self) -> Dict[str, pd.DataFrame]:
        """
        Generate individual HubSpot object files with association columns.

        Each file includes the association fields needed for CRM import:
        - Contacts include Company Domain Name
        - Deals include Company Domain Name + Contact Email
        - Activities include Company Domain Name + Contact Email + Deal Name
        """
        files = {}
        domain_lookup, email_lookup, deal_name_lookup = self._build_lookups()

        # --- Companies (with clean domain) ---
        acc_copy = self.accounts_df.copy()
        acc_copy["website"] = acc_copy["website"].apply(self._get_domain)
        files["hubspot_companies.csv"] = self._map_dataframe(
            acc_copy, self.account_field_mapping()
        )

        # --- Contacts (with Company Domain Name) ---
        con_mapped = self._map_dataframe(
            self.contacts_df, self.contact_field_mapping(), owner_col="contact_owner"
        )
        con_mapped["Company Domain Name"] = (
            self.contacts_df["account_id"].astype(str).map(domain_lookup)
        )
        files["hubspot_contacts.csv"] = con_mapped

        # --- Deals (with Company Domain Name + Contact Email) ---
        deal_mapped = self._map_dataframe(
            self.deals_df, self.deal_field_mapping(), owner_col="deal_owner"
        )
        deal_mapped["Company Domain Name"] = (
            self.deals_df["account_id"].astype(str).map(domain_lookup)
        )
        deal_mapped["Contact Email"] = (
            self.deals_df["contact_id"].astype(str).map(email_lookup)
        )
        files["hubspot_deals.csv"] = deal_mapped

        # --- Activities (with Company Domain Name + Contact Email + Deal Name) ---
        act_mapped = self._map_dataframe(
            self.activities_df, self.activity_field_mapping(),
            owner_col="activity_owner", activity_type_col="activity_type"
        )
        act_mapped["Company Domain Name"] = (
            self.activities_df["account_id"].astype(str).map(domain_lookup)
        )
        act_mapped["Contact Email"] = (
            self.activities_df["contact_id"].astype(str).map(email_lookup)
        )
        act_mapped["Deal Name"] = (
            self.activities_df["deal_id"].astype(str).map(deal_name_lookup).fillna("")
        )
        files["hubspot_activities.csv"] = act_mapped

        return files

    # ------------------------------------------------------------------ #
    #  Master import file                                                  #
    # ------------------------------------------------------------------ #

    def generate_master_file(self) -> pd.DataFrame:
        """
        Generate a single denormalized HubSpot master import file.

        Each row has a Record Type (COMPANY, CONTACT, DEAL, ACTIVITY) and
        only populates the columns relevant to that record type. Association
        fields (Company Domain Name, Contact Email, Deal Name) link records.
        """
        domain_lookup, email_lookup, deal_name_lookup = self._build_lookups()

        # Master file column order
        columns = [
            "Record Type",
            # Company fields
            "Company Domain Name", "Company Name", "Industry",
            "Employee Count", "Annual Revenue", "Street Address",
            "City", "State", "Zip Code", "Country", "Description",
            "Founded Year",
            # Contact fields
            "Contact Email", "Contact First Name", "Contact Last Name",
            "Contact Title", "Contact Phone", "Contact Department",
            # Deal fields
            "Deal Name", "Pipeline", "Stage", "Amount",
            "Close Date", "Created Date", "Deal Status",
            # Activity fields
            "Activity Type", "Activity Subject", "Activity Date",
            "Activity Duration", "Activity Notes",
            # Owner (shared)
            "Owner Email",
        ]

        # Check if subscription_type is in this profile's deal fields
        has_subscription = "subscription_type" in self.profile.deal_fields
        if has_subscription:
            # Insert Subscription Type after Deal Status
            idx = columns.index("Deal Status") + 1
            columns.insert(idx, "Subscription Type")

        def _empty_row():
            return {c: "" for c in columns}

        rows = []

        # --- COMPANY rows ---
        for _, acc in self.accounts_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "COMPANY"
            row["Company Domain Name"] = self._get_domain(acc["website"])
            row["Company Name"] = acc["company_name"]
            row["Industry"] = acc["industry"]
            row["Employee Count"] = acc["employee_count"]
            row["Annual Revenue"] = acc["annual_revenue"]
            row["Street Address"] = acc["street_address"]
            row["City"] = acc["city"]
            row["State"] = acc["state"]
            row["Zip Code"] = acc["zip_code"]
            row["Country"] = acc["country"]
            row["Description"] = acc.get("description", "")
            row["Founded Year"] = acc.get("founded_year", "")
            rows.append(row)

        # --- CONTACT rows ---
        for _, con in self.contacts_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "CONTACT"
            row["Company Domain Name"] = domain_lookup.get(str(con["account_id"]), "")
            row["Contact Email"] = con["email"]
            row["Contact First Name"] = con["first_name"]
            row["Contact Last Name"] = con["last_name"]
            row["Contact Title"] = con["title"]
            row["Contact Phone"] = con["phone"]
            row["Contact Department"] = con["department"]
            row["Owner Email"] = self.format_owner(con["contact_owner"]) if con["contact_owner"] else ""
            rows.append(row)

        # --- DEAL rows ---
        for _, deal in self.deals_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "DEAL"
            row["Company Domain Name"] = domain_lookup.get(str(deal["account_id"]), "")
            row["Contact Email"] = email_lookup.get(str(deal["contact_id"]), "")
            row["Deal Name"] = deal["deal_name"]
            row["Pipeline"] = deal["pipeline"]
            row["Stage"] = deal["stage"]
            row["Amount"] = deal["amount"]
            row["Close Date"] = deal["close_date"]
            row["Created Date"] = deal["created_date"]
            row["Deal Status"] = deal["deal_status"]
            if has_subscription:
                row["Subscription Type"] = deal.get("subscription_type", "")
            row["Owner Email"] = self.format_owner(deal["deal_owner"]) if deal["deal_owner"] else ""
            rows.append(row)

        # --- ACTIVITY rows ---
        type_map = self.activity_type_mapping()
        for _, act in self.activities_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "ACTIVITY"
            row["Company Domain Name"] = domain_lookup.get(str(act["account_id"]), "")
            row["Contact Email"] = email_lookup.get(str(act["contact_id"]), "")
            deal_id = str(act["deal_id"]) if act["deal_id"] else ""
            row["Deal Name"] = deal_name_lookup.get(deal_id, "")
            row["Activity Type"] = type_map.get(act["activity_type"], act["activity_type"])
            row["Activity Subject"] = act["subject"]
            row["Activity Date"] = act["activity_date"]
            row["Activity Duration"] = act["duration_minutes"] if act["duration_minutes"] else ""
            row["Activity Notes"] = act["notes"] if act["notes"] else ""
            row["Owner Email"] = self.format_owner(act["activity_owner"]) if act["activity_owner"] else ""
            rows.append(row)

        return pd.DataFrame(rows, columns=columns)

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

1. **Create users** in HubSpot matching the emails in `hubspot_users_reference.csv`:
{users_list}
2. Ensure you have **admin access** to the HubSpot account

## Pipeline Setup ({profile.name})

Create the following pipelines in **Settings → Objects → Deals → Pipelines**:
{pipeline_section}

---

## Option A — Master File Import (Recommended)

Use `hubspot_master_import.csv` for the simplest experience with all associations pre-linked.

1. Go to **Contacts → Import** → **Start an import**
2. Select **File from computer** → **One file** → **Multiple objects**
3. Choose `hubspot_master_import.csv`
4. Map the **Record Type** column to identify object types (COMPANY, CONTACT, DEAL, ACTIVITY)
5. Map association fields:
   - **Company Domain Name** — links contacts, deals, and activities to companies
   - **Contact Email** — links deals and activities to contacts
   - **Deal Name** — links activities to deals
6. Map remaining fields to their HubSpot equivalents
7. Complete the import — all records are created with associations in one step

---

## Option B — Individual Files (Advanced)

Use individual files if you need more control over each object type.

### Step 1: Import Companies
1. Go to **Contacts → Companies** → **Import**
2. Select **One file** → **One object**
3. Choose `hubspot_companies.csv`
4. Map all fields and complete the import

### Step 2: Import Contacts
1. Go to **Contacts → Contacts** → **Import**
2. Select **One file** → **Two objects** → **Contacts** and **Companies**
3. Choose `hubspot_contacts.csv`
4. HubSpot uses the **Company Domain Name** column to match contacts to companies

### Step 3: Import Deals
1. Go to **Sales → Deals** → **Import**
2. Select **One file** → **Two objects** → **Deals** and **Companies**
3. Choose `hubspot_deals.csv`
4. HubSpot uses **Company Domain Name** for company association and **Contact Email** for contact association

### Step 4: Import Activities
1. Go to **Contacts → Import**
2. Choose `hubspot_activities.csv`
3. Map activity fields including **Company Domain Name**, **Contact Email**, and **Deal Name** for associations

---

## Field Mapping Reference

| Generated Field | HubSpot Field |
|----------------|---------------|
| name / Company Name | Company name |
| domain / Company Domain Name | Company domain name |
| annualrevenue / Annual Revenue | Annual revenue |
| numberofemployees / Employee Count | Number of employees |
| firstname / Contact First Name | First name |
| lastname / Contact Last Name | Last name |
| email / Contact Email | Email |
| jobtitle / Contact Title | Job title |
| dealname / Deal Name | Deal name |
| pipeline / Pipeline | Pipeline |
| dealstage / Stage | Deal stage |
| amount / Amount | Amount |
| createdate / Created Date | Create date |
| closedate / Close Date | Close date |

## Data Quality Notes
- **Company Domain Name** contains clean domains (e.g., `clouddata.io`) — consistent across all files
- Contact **emails are unique** per company domain — no duplicates
- **Phone numbers** use consistent `(XXX) XXX-XXXX` format
- The **Owner Email** / `hubspot_owner_id` field maps to user emails — ensure users exist before importing
- Activity types are mapped to HubSpot engagement types (EMAIL, CALL, MEETING, NOTE)
- Deal stages must match the pipeline configuration created above
- The `hubspot_users_reference.csv` file lists all sales reps — create these as users in HubSpot before importing data
"""
