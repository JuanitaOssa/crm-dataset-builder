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
            "activity_date": "hs_timestamp",
            "activity_owner": "hubspot_owner_id",
            # Note fields
            "note_body": "hs_note_body",
            # Email fields
            "email_subject": "hs_email_subject",
            "email_body": "hs_email_text",
            "email_direction": "hs_email_direction",
            "email_status": "hs_email_status",
            # Call fields
            "call_notes": "hs_call_body",
            "call_duration": "hs_call_duration",
            "call_disposition": "hs_call_disposition",
            "call_direction": "hs_call_direction",
            # Meeting fields
            "meeting_title": "hs_meeting_title",
            "meeting_description": "hs_meeting_body",
            "meeting_start_time": "hs_meeting_start_time",
            "meeting_end_time": "hs_meeting_end_time",
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
    #  Master records file (companies + contacts + deals)                  #
    # ------------------------------------------------------------------ #

    def generate_master_records(self) -> pd.DataFrame:
        """
        Generate HubSpot master records file.

        One row per contact. Deals appear once, on the row of their primary contact.

        Row structure:
        - Company-only rows: company fields filled, contact/deal blank
        - Company+Contact rows: company + contact filled, deal blank
        - Company+Contact+Deal rows: all filled (one row per deal)
        """
        columns = [
            # Company fields
            "Company Domain Name", "Company Name", "Industry",
            "Number of Employees", "Annual Revenue", "Street Address",
            "City", "State", "Zip Code", "Country",
            # Contact fields
            "Contact Email", "Contact First Name", "Contact Last Name",
            "Contact Title", "Contact Phone", "Contact Department",
            # Deal fields
            "Deal Name", "Pipeline", "Deal Stage", "Amount",
            "Close Date", "Create Date", "Deal Status", "Loss Reason",
        ]
        has_subscription = "subscription_type" in self.profile.deal_fields
        if has_subscription:
            columns.append("Subscription Type")
        columns.append("Owner Email")

        def _empty_row():
            return {c: "" for c in columns}

        def _fill_company(row, acc):
            row["Company Domain Name"] = self._get_domain(acc["website"])
            row["Company Name"] = acc["company_name"]
            row["Industry"] = acc["industry"]
            row["Number of Employees"] = acc["employee_count"]
            row["Annual Revenue"] = acc["annual_revenue"]
            row["Street Address"] = acc["street_address"]
            row["City"] = acc["city"]
            row["State"] = acc["state"]
            row["Zip Code"] = acc["zip_code"]
            row["Country"] = acc["country"]

        def _fill_contact(row, con):
            row["Contact Email"] = con["email"]
            row["Contact First Name"] = con["first_name"]
            row["Contact Last Name"] = con["last_name"]
            row["Contact Title"] = con["title"]
            row["Contact Phone"] = con["phone"]
            row["Contact Department"] = con["department"]

        def _fill_deal(row, deal):
            row["Deal Name"] = deal["deal_name"]
            row["Pipeline"] = deal["pipeline"]
            row["Deal Stage"] = deal["stage"]
            row["Amount"] = deal["amount"]
            row["Close Date"] = deal["close_date"]
            row["Create Date"] = deal["created_date"]
            row["Deal Status"] = deal["deal_status"]
            row["Loss Reason"] = deal.get("loss_reason", "")
            if has_subscription:
                row["Subscription Type"] = deal.get("subscription_type", "")
            row["Owner Email"] = self.format_owner(deal["deal_owner"]) if deal["deal_owner"] else ""

        # Build indexes
        contacts_by_account = {}
        for _, con in self.contacts_df.iterrows():
            contacts_by_account.setdefault(str(con["account_id"]), []).append(con)

        deals_by_contact = {}
        for _, deal in self.deals_df.iterrows():
            deals_by_contact.setdefault(str(deal["contact_id"]), []).append(deal)

        rows = []

        # Walk: account → contact → deal (each deal appears exactly once)
        for _, acc in self.accounts_df.iterrows():
            acc_id = str(acc["id"])
            acc_contacts = contacts_by_account.get(acc_id, [])

            if not acc_contacts:
                # Company with no contacts
                row = _empty_row()
                _fill_company(row, acc)
                rows.append(row)
                continue

            for con in acc_contacts:
                con_id = str(con["contact_id"])
                con_deals = deals_by_contact.get(con_id, [])

                if not con_deals:
                    # Company + Contact (no deals)
                    row = _empty_row()
                    _fill_company(row, acc)
                    _fill_contact(row, con)
                    row["Owner Email"] = self.format_owner(con["contact_owner"]) if con["contact_owner"] else ""
                    rows.append(row)
                else:
                    # One row per deal (deal appears exactly once)
                    for deal in con_deals:
                        row = _empty_row()
                        _fill_company(row, acc)
                        _fill_contact(row, con)
                        _fill_deal(row, deal)
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

Two files that cover all records and activities:

### Step 1: Import Records (`hubspot_master_records.csv`)

This file contains companies, contacts, and deals. Each deal appears exactly once (preventing duplicates). Companies and contacts are deduplicated automatically.

1. Go to **Contacts → Import** → **Start an import**
2. Select **File from computer** → **One file** → **Multiple objects**
3. Choose `hubspot_master_records.csv`
4. Select object types: **Companies**, **Contacts**, **Deals**
5. Map columns:
   - **Company Domain Name** → Company domain (matching + association)
   - **Contact Email** → Email (matching + association)
   - **Deal Name** → Deal name
   - Map remaining fields to their HubSpot equivalents
6. Complete the import — all records created with proper associations

### Step 2: Import Activities (`hubspot_activities.csv`)

This file contains all activities, one per row, with association references to existing records.

1. Go to **Contacts → Import** → **Start an import**
2. Choose `hubspot_activities.csv`
3. Map association columns:
   - **Company Domain Name** → Company lookup
   - **Contact Email** → Contact lookup
   - **Deal Name** → Deal lookup
4. Map activity fields (type-specific columns per activity type)
5. Complete the import — activities linked to records from Step 1

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

## Activity Column Layout

Activities use type-specific columns. Each row populates only the columns matching its type:

| Activity Type | Populated Columns |
|--------------|-------------------|
| NOTE | Note Body |
| EMAIL | Email Subject, Email Body, Email Direction, Email Status |
| CALL | Call Notes, Call Duration, Call Disposition, Call Direction |
| MEETING | Meeting Title, Meeting Description, Meeting Start, Meeting End |

All other activity columns on the row will be empty.

---

## Field Mapping Reference

| Generated Field | HubSpot Field |
|----------------|---------------|
| Company Domain Name | Company domain name |
| Company Name | Company name |
| Annual Revenue | Annual revenue |
| Number of Employees | Number of employees |
| Contact First Name | First name |
| Contact Last Name | Last name |
| Contact Email | Email |
| Contact Title | Job title |
| Deal Name | Deal name |
| Pipeline | Pipeline |
| Deal Stage | Deal stage |
| Loss Reason | Loss reason (custom property) |
| Amount | Amount |
| Create Date | Create date |
| Close Date | Close date |
| Note Body | Note body (`hs_note_body`) |
| Email Subject | Email subject (`hs_email_subject`) |
| Email Body | Email text (`hs_email_text`) |
| Email Direction | Email direction (`hs_email_direction`) |
| Email Status | Email status (`hs_email_status`) |
| Call Notes | Call body (`hs_call_body`) |
| Call Duration | Call duration (`hs_call_duration`) |
| Call Disposition | Call disposition (`hs_call_disposition`) |
| Call Direction | Call direction (`hs_call_direction`) |
| Meeting Title | Meeting title (`hs_meeting_title`) |
| Meeting Description | Meeting body (`hs_meeting_body`) |
| Meeting Start | Meeting start time (`hs_meeting_start_time`) |
| Meeting End | Meeting end time (`hs_meeting_end_time`) |

## Data Quality Notes
- **Company Domain Name** contains clean domains (e.g., `clouddata.io`) — consistent across all files
- Contact **emails are unique** per company domain — no duplicates
- **Phone numbers** use consistent `(XXX) XXX-XXXX` format
- The **Owner Email** / `hubspot_owner_id` field maps to user emails — ensure users exist before importing
- Activity types are mapped to HubSpot engagement types (EMAIL, CALL, MEETING, NOTE)
- Deal stages must match the pipeline configuration created above
- The `hubspot_users_reference.csv` file lists all sales reps — create these as users in HubSpot before importing data
"""
