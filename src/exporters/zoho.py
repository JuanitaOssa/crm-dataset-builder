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
    #  Master import file                                                  #
    # ------------------------------------------------------------------ #

    def generate_master_file(self) -> pd.DataFrame:
        """
        Generate a fully denormalized Zoho master import file.

        Each row represents a complete relationship chain (account + contact +
        deal + activity on one row). Zoho deduplicates by name matching
        (Account_Name, Contact_Name, Deal_Name). Activities are unique per row.
        """
        type_map = self.activity_type_mapping()

        # Master file column order — account → contact → deal → activity → owner
        columns = [
            # Account fields
            "Account_Name", "Industry", "Annual_Revenue", "Employees",
            "Billing_Street", "Billing_City", "Billing_State", "Billing_Code",
            "Billing_Country", "Website",
            # Contact fields
            "Contact_Name", "Email", "First_Name", "Last_Name",
            "Title", "Phone", "Department",
            # Deal fields
            "Deal_Name", "Pipeline", "Stage", "Amount",
            "Created_Time", "Closing_Date", "Status",
        ]
        has_subscription = "subscription_type" in self.profile.deal_fields
        if has_subscription:
            columns.append("Subscription_Type")
        # Activity fields + owner
        columns += [
            "Activity_Type", "Subject", "Activity_Date", "Duration",
            "Activity_Description",
            "Owner",
        ]

        def _empty_row():
            return {c: "" for c in columns}

        def _fill_account(row, acc):
            """Populate account columns on a row."""
            row["Account_Name"] = acc["company_name"]
            row["Industry"] = acc["industry"]
            row["Annual_Revenue"] = acc["annual_revenue"]
            row["Employees"] = acc["employee_count"]
            row["Billing_Street"] = acc["street_address"]
            row["Billing_City"] = acc["city"]
            row["Billing_State"] = acc["state"]
            row["Billing_Code"] = acc["zip_code"]
            row["Billing_Country"] = acc["country"]
            row["Website"] = acc["website"]

        def _fill_contact(row, con):
            """Populate contact columns on a row."""
            row["Contact_Name"] = f"{con['first_name']} {con['last_name']}"
            row["Email"] = con["email"]
            row["First_Name"] = con["first_name"]
            row["Last_Name"] = con["last_name"]
            row["Title"] = con["title"]
            row["Phone"] = con["phone"]
            row["Department"] = con["department"]

        def _fill_deal(row, deal):
            """Populate deal columns on a row."""
            row["Deal_Name"] = deal["deal_name"]
            row["Pipeline"] = deal["pipeline"]
            row["Stage"] = deal["stage"]
            row["Amount"] = deal["amount"]
            row["Created_Time"] = deal["created_date"]
            row["Closing_Date"] = deal["close_date"]
            row["Status"] = deal["deal_status"]
            if has_subscription:
                row["Subscription_Type"] = deal.get("subscription_type", "")
            row["Owner"] = self.format_owner(deal["deal_owner"]) if deal["deal_owner"] else ""

        def _fill_activity(row, act):
            """Populate activity columns on a row."""
            row["Activity_Type"] = type_map.get(act["activity_type"], act["activity_type"])
            row["Subject"] = act["subject"]
            row["Activity_Date"] = act["activity_date"]
            row["Duration"] = act["duration_minutes"] if act["duration_minutes"] else ""
            row["Activity_Description"] = act["notes"] if act["notes"] else ""
            row["Owner"] = self.format_owner(act["activity_owner"]) if act["activity_owner"] else ""

        # Build indexes: group contacts by account, deals by contact,
        # activities by deal_id and by contact_id (non-deal)
        contacts_by_account = {}
        for _, con in self.contacts_df.iterrows():
            contacts_by_account.setdefault(str(con["account_id"]), []).append(con)

        deals_by_contact = {}
        for _, deal in self.deals_df.iterrows():
            deals_by_contact.setdefault(str(deal["contact_id"]), []).append(deal)

        activities_by_deal = {}
        activities_by_contact_no_deal = {}
        for _, act in self.activities_df.iterrows():
            if act["deal_id"]:
                activities_by_deal.setdefault(str(act["deal_id"]), []).append(act)
            else:
                activities_by_contact_no_deal.setdefault(str(act["contact_id"]), []).append(act)

        rows = []

        # Walk the relationship tree: account → contact → deal → activity
        for _, acc in self.accounts_df.iterrows():
            acc_id = str(acc["id"])
            acc_contacts = contacts_by_account.get(acc_id, [])

            if not acc_contacts:
                row = _empty_row()
                _fill_account(row, acc)
                rows.append(row)
                continue

            for con in acc_contacts:
                con_id = str(con["contact_id"])
                con_deals = deals_by_contact.get(con_id, [])
                con_activities_no_deal = activities_by_contact_no_deal.get(con_id, [])

                if not con_deals and not con_activities_no_deal:
                    row = _empty_row()
                    _fill_account(row, acc)
                    _fill_contact(row, con)
                    row["Owner"] = self.format_owner(con["contact_owner"]) if con["contact_owner"] else ""
                    rows.append(row)
                    continue

                for deal in con_deals:
                    deal_id = str(deal["deal_id"])
                    deal_activities = activities_by_deal.get(deal_id, [])

                    if not deal_activities:
                        row = _empty_row()
                        _fill_account(row, acc)
                        _fill_contact(row, con)
                        _fill_deal(row, deal)
                        rows.append(row)
                    else:
                        for act in deal_activities:
                            row = _empty_row()
                            _fill_account(row, acc)
                            _fill_contact(row, con)
                            _fill_deal(row, deal)
                            _fill_activity(row, act)
                            rows.append(row)

                for act in con_activities_no_deal:
                    row = _empty_row()
                    _fill_account(row, acc)
                    _fill_contact(row, con)
                    _fill_activity(row, act)
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

        return f"""# Zoho CRM Import Guide — {profile.name}

## Prerequisites

1. **Create users** in Zoho CRM matching the emails in `zoho_users_reference.csv`:
{users_list}
2. Ensure you have **admin access** to the Zoho CRM account

## Pipeline Setup ({profile.name})

Create the following pipelines in **Setup → Customization → Pipelines**:
{pipeline_section}

---

## Option A — Master File Import (Recommended)

Use `zoho_master_import.csv` — a fully denormalized file where each row contains account, contact, deal, and activity data together. The CRM automatically deduplicates:
- **Accounts** are matched by `Account_Name` — the same account appearing on multiple rows is imported once
- **Contacts** are matched by email and automatically associated with the account on the same row
- **Deals** are matched by `Deal_Name` and associated with the account and contact on the same row
- **Activities** are created one per row and associated with the contact and deal on the same row

**Steps:**
1. Import each object in order from `zoho_master_import.csv`:
   - **Accounts** first → **Accounts** module → Import → map `Account_Name` and account fields
   - **Contacts** second → **Contacts** module → Import → map `Email`, `Account_Name` (for lookup), and contact fields
   - **Deals** third → **Deals** module → Import → map `Deal_Name`, `Account_Name`, `Contact_Name`, and deal fields
   - **Activities** last → Filter by `Activity_Type` and import to the appropriate module (Calls, Meetings, Notes)
2. All name-based association fields (`Account_Name`, `Contact_Name`, `Deal_Name`) are pre-populated on every row

---

## Option B — Individual Files (Advanced)

Use individual files if you need more control over each object type.

### Step 1: Import Accounts
1. Go to **Accounts** module
2. Click the **…** menu → **Import**
3. Choose `zoho_accounts.csv`
4. Map fields:
   - `Account_Name` → Account Name
   - `Annual_Revenue` → Annual Revenue
   - `Employees` → Employees
   - `Billing_Street`, `Billing_City`, `Billing_State`, `Billing_Code` → Billing address fields
5. Complete the import

### Step 2: Import Contacts
1. Go to **Contacts** module
2. Click **Import**
3. Choose `zoho_contacts.csv`
4. Map fields:
   - `First_Name`, `Last_Name`, `Email`, `Phone`, `Title`
   - `Account_Name` → Account Name (Zoho will match by name)
5. Complete the import — contacts will auto-link to accounts by name

### Step 3: Import Deals
1. Go to **Deals** module
2. Click **Import**
3. Choose `zoho_deals.csv`
4. Map fields:
   - `Deal_Name` → Deal Name
   - `Pipeline` → Pipeline
   - `Stage` → Stage
   - `Amount` → Amount
   - `Closing_Date` → Closing Date
   - `Account_Name` → Account Name (lookup)
   - `Contact_Name` → Contact Name (lookup)
5. Complete the import

### Step 4: Import Activities
1. For **Calls**: Filter `zoho_activities.csv` for Activity_Type = "Calls"
   - Go to **Activities → Calls** → Import
2. For **Meetings**: Filter for Activity_Type = "Meetings"
   - Go to **Activities → Meetings** → Import
3. For **Emails/Notes**: Import remaining as Notes
   - Go to module and import with account/contact lookup

---

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
| Pipeline | Pipeline |
| Stage | Stage |
| Amount | Amount |
| Closing_Date | Closing Date |
| Contact_Name | Contact Name |

## Data Quality Notes
- Zoho uses **name-based matching** — `Account_Name` and `Contact_Name` must match exactly. Import accounts first so lookups succeed.
- Contact **emails are unique** per company domain — no duplicates
- **Phone numbers** use consistent `(XXX) XXX-XXXX` format
- The `Owner` field maps to Zoho user emails — create users before importing
- Activity types are mapped to Zoho modules: Calls, Meetings, and Notes
- Deals require a `Closing_Date`; open deals use an estimated future date
- The `zoho_users_reference.csv` file lists all sales reps — create these as users in Zoho CRM before importing data
"""
