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

    def __init__(self, accounts_df, contacts_df, deals_df, activities_df, profile=None):
        super().__init__(accounts_df, contacts_df, deals_df, activities_df, profile=profile)

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
        mapping = {
            "deal_name": "Name",
            "stage": "StageName",
            "amount": "Amount",
            "created_date": "CreatedDate",
            "close_date": "CloseDate",
            "deal_status": "Status",
            "deal_owner": "Owner",
        }
        if "subscription_type" in self.profile.deal_fields:
            mapping["subscription_type"] = "Subscription_Type__c"
        return mapping

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
    #  Master import file                                                  #
    # ------------------------------------------------------------------ #

    def generate_master_file(self) -> pd.DataFrame:
        """
        Generate a single denormalized Salesforce master import file.

        Each row has a Record Type (Account, Contact, Opportunity, Task) and
        only populates the columns relevant to that record type. External_ID__c
        fields link records across objects.
        """
        # Master file column order — prefixed names avoid Salesforce collisions
        # (Name is used for both Account and Opportunity, Description for both)
        columns = [
            "Record Type",
            # External ID references
            "External_ID__c", "Account_External_ID__c",
            "Contact_External_ID__c", "Opportunity_External_ID__c",
            # Account fields
            "Account_Name", "Industry", "AnnualRevenue", "NumberOfEmployees",
            "BillingStreet", "BillingCity", "BillingState", "BillingPostalCode",
            "BillingCountry", "Website", "Account_Description",
            # Contact fields
            "Email", "FirstName", "LastName", "Title", "Phone", "Department",
            # Opportunity fields
            "Opportunity_Name", "StageName", "Amount",
            "CreatedDate", "CloseDate", "Status",
            # Activity fields
            "Type", "Subject", "ActivityDate", "DurationInMinutes",
            "Activity_Description",
            # Owner (shared)
            "Owner",
        ]

        # Check if subscription_type is in this profile's deal fields
        has_subscription = "subscription_type" in self.profile.deal_fields
        if has_subscription:
            idx = columns.index("Status") + 1
            columns.insert(idx, "Subscription_Type__c")

        def _empty_row():
            return {c: "" for c in columns}

        rows = []

        # --- Account rows ---
        for _, acc in self.accounts_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "Account"
            row["External_ID__c"] = f"ACC-{acc['id']}"
            row["Account_Name"] = acc["company_name"]
            row["Industry"] = acc["industry"]
            row["AnnualRevenue"] = acc["annual_revenue"]
            row["NumberOfEmployees"] = acc["employee_count"]
            row["BillingStreet"] = acc["street_address"]
            row["BillingCity"] = acc["city"]
            row["BillingState"] = acc["state"]
            row["BillingPostalCode"] = acc["zip_code"]
            row["BillingCountry"] = acc["country"]
            row["Website"] = acc["website"]
            row["Account_Description"] = acc.get("description", "")
            rows.append(row)

        # --- Contact rows ---
        for _, con in self.contacts_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "Contact"
            row["External_ID__c"] = f"CON-{con['contact_id']}"
            row["Account_External_ID__c"] = f"ACC-{con['account_id']}"
            row["Email"] = con["email"]
            row["FirstName"] = con["first_name"]
            row["LastName"] = con["last_name"]
            row["Title"] = con["title"]
            row["Phone"] = con["phone"]
            row["Department"] = con["department"]
            row["Owner"] = self.format_owner(con["contact_owner"]) if con["contact_owner"] else ""
            rows.append(row)

        # --- Opportunity rows ---
        for _, deal in self.deals_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "Opportunity"
            row["External_ID__c"] = f"OPP-{deal['deal_id']}"
            row["Account_External_ID__c"] = f"ACC-{deal['account_id']}"
            row["Contact_External_ID__c"] = f"CON-{deal['contact_id']}"
            row["Opportunity_Name"] = deal["deal_name"]
            row["StageName"] = deal["stage"]
            row["Amount"] = deal["amount"]
            row["CreatedDate"] = deal["created_date"]
            row["CloseDate"] = deal["close_date"]
            row["Status"] = deal["deal_status"]
            if has_subscription:
                row["Subscription_Type__c"] = deal.get("subscription_type", "")
            row["Owner"] = self.format_owner(deal["deal_owner"]) if deal["deal_owner"] else ""
            rows.append(row)

        # --- Task/Event rows (activities) ---
        type_map = self.activity_type_mapping()
        for _, act in self.activities_df.iterrows():
            row = _empty_row()
            row["Record Type"] = "Task"
            row["Account_External_ID__c"] = f"ACC-{act['account_id']}"
            row["Contact_External_ID__c"] = f"CON-{act['contact_id']}"
            if act["deal_id"]:
                row["Opportunity_External_ID__c"] = f"OPP-{act['deal_id']}"
            row["Type"] = type_map.get(act["activity_type"], act["activity_type"])
            row["Subject"] = act["subject"]
            row["ActivityDate"] = act["activity_date"]
            row["DurationInMinutes"] = act["duration_minutes"] if act["duration_minutes"] else ""
            row["Activity_Description"] = act["notes"] if act["notes"] else ""
            row["Owner"] = self.format_owner(act["activity_owner"]) if act["activity_owner"] else ""
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

        # Multi-pipeline note
        multi_pipeline_note = ""
        if len(profile.pipelines) > 1:
            multi_pipeline_note = (
                "\n> **Multiple pipelines**: Salesforce uses a single Stage picklist on Opportunities. "
                "To support multiple pipelines, either create a custom `Pipeline__c` text field "
                "or use **Record Types** to separate pipeline-specific stage picklists."
            )

        return f"""# Salesforce Import Guide — {profile.name}

## Prerequisites

1. **Create users** in Salesforce matching the usernames in `salesforce_users_reference.csv`:
{users_list}
2. Create a custom text field **`External_ID__c`** on Account, Contact, and Opportunity objects
   - Mark it as **External ID** and **Unique**
3. Configure Opportunity stages to match the data (see Pipeline Setup below)

## Pipeline Setup ({profile.name})

Add the following stage values to the Opportunity **StageName** picklist:
{pipeline_section}
{multi_pipeline_note}

---

## Option A — Master File Import (Recommended)

Use `salesforce_master_import.csv` for the simplest experience with all associations pre-linked.

1. Open **Data Loader**
2. Choose `salesforce_master_import.csv`
3. The **Record Type** column identifies each row: Account, Contact, Opportunity, or Task
4. Filter by Record Type and import each object type in order:
   - **Accounts** first (Record Type = "Account")
   - **Contacts** second (Record Type = "Contact") — use `Account_External_ID__c` for account lookup
   - **Opportunities** third (Record Type = "Opportunity") — use `Account_External_ID__c` and `Contact_External_ID__c`
   - **Tasks** last (Record Type = "Task") — use all External ID references
5. All `External_ID__c` references are pre-populated for cross-object linking

---

## Option B — Individual Files (Advanced)

Use individual files if you need more control over each object type.

### Step 1: Import Accounts
1. Open **Data Loader** (or Setup → Data Import Wizard)
2. Select **Insert** operation on the **Account** object
3. Choose `salesforce_accounts.csv`
4. Map fields:
   - `External_ID__c` → External_ID__c
   - `Name` → Account Name
   - `AnnualRevenue` → Annual Revenue
   - `NumberOfEmployees` → Employees
   - `BillingStreet`, `BillingCity`, `BillingState`, `BillingPostalCode` → Billing Address fields
5. Complete the import

### Step 2: Import Contacts
1. Select **Insert** on the **Contact** object
2. Choose `salesforce_contacts.csv`
3. Map fields:
   - `External_ID__c` → External_ID__c
   - `Account_External_ID__c` → Account (External ID lookup)
   - `FirstName`, `LastName`, `Email`, `Phone`, `Title`, `Department`
4. Complete the import — contacts will auto-link to accounts via External ID

### Step 3: Import Opportunities
1. Select **Insert** on the **Opportunity** object
2. Choose `salesforce_opportunities.csv`
3. Map fields:
   - `External_ID__c` → External_ID__c
   - `Account_External_ID__c` → Account (External ID lookup)
   - `Contact_External_ID__c` → Primary Contact (External ID lookup)
   - `Name` → Opportunity Name
   - `StageName` → Stage
   - `Amount`, `CloseDate`, `CreatedDate`
4. Complete the import

### Step 4: Import Activities
1. For **Events** (Meetings): Filter `salesforce_activities.csv` for Type = "Event"
2. For **Tasks** (Calls, Emails, LinkedIn, Notes): Filter for Type != "Event"
3. Import each subset to the appropriate object
4. Use `Account_External_ID__c` and `Contact_External_ID__c` for lookups

---

## Field Mapping Reference

| Generated Field | Salesforce Field |
|----------------|-----------------|
| Account_Name / Name | Account Name |
| Opportunity_Name / Name | Opportunity Name |
| External_ID__c | External ID (custom) |
| AnnualRevenue | Annual Revenue |
| NumberOfEmployees | Employees |
| BillingStreet | Billing Street |
| FirstName / LastName | First Name / Last Name |
| Email | Email |
| Title | Title |
| StageName | Stage |
| Amount | Amount |
| CloseDate | Close Date |

## Data Quality Notes
- **External_ID__c** enables upsert operations — use it for future data refreshes without creating duplicates
- Contact **emails are unique** per company domain — no duplicates
- **Phone numbers** use consistent `(XXX) XXX-XXXX` format
- The `Owner` field maps to Salesforce usernames — assign via Data Loader's owner lookup
- Meetings map to Events; Calls, LinkedIn, and Notes map to Tasks
- **Stage values must match** your Salesforce org's picklist exactly — configure them in the Pipeline Setup step above
- The `salesforce_users_reference.csv` file lists all sales reps — create these as users in Salesforce before importing data
"""
