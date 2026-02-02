# CRM Dataset Builder

A tool for generating realistic B2B SaaS CRM datasets — accounts, contacts, deals, and activities — with interconnected foreign keys, statistically plausible distributions, and CRM-specific export formats for HubSpot, Salesforce, and Zoho.

**Live demo:** [crm-dataset-builder.streamlit.app](https://crm-dataset-builder.streamlit.app)

## Overview

This tool generates synthetic CRM data that mimics real-world B2B SaaS sales patterns. Useful for:

- Testing CRM applications and dashboards
- Populating CRM platforms with realistic demo data
- Demonstrating data analysis workflows
- Populating development/staging databases
- Training and educational purposes

## Generated Datasets

| File | Records (50 accounts) | Description |
|------|----------------------|-------------|
| `accounts.csv` | 50 | B2B SaaS companies with industry, revenue, full US addresses |
| `contacts.csv` | ~160 | 2-5 contacts per account with realistic names, titles, departments |
| `deals.csv` | ~75 | New Business, Renewal, and Expansion pipelines with outcome rates |
| `activities.csv` | ~850 | Emails, calls, meetings, LinkedIn, and notes tied to deals |

### Data Relationships

```
accounts.csv
  └── contacts.csv        (account_id → accounts.id)
  └── deals.csv           (account_id → accounts.id, contact_id → contacts.contact_id)
       └── activities.csv  (deal_id → deals.deal_id, account_id, contact_id)
```

### Key Characteristics

**Accounts** — Weighted toward smaller companies (50-500 employees), with revenue correlated to headcount. Full US addresses with street, city, state, zip code, and region derived from state.

**Contacts** — 2-5 per account, department-weighted toward Sales/Marketing/Customer Success for CRM realism. Each assigned to one of 6 sales reps.

**Deals** — Three pipelines with distinct behavior:
- **New Business** (~70% of accounts): 22% win rate, 30-180 day cycles by segment
- **Renewals**: spawned ~12 months after won NB deals, 85% win rate
- **Expansions**: 50% chance per won NB deal, 3-9 months later, 45% win rate
- Segment-based ACV: SMB $8-25K, Mid-Market $25-100K, Enterprise $100-350K
- Deal names follow `{CompanyName} YYMM` format (e.g., "QuantumSense 2501")
- Open deals use weighted real pipeline stages (not a generic "Active" stage)
- Deal status is derived from stage: Won, Lost, or Open

**Activities** — Phase-based engagement patterns:
- Won deals: 10-20 activities with strong multi-channel engagement
- Lost deals: 4-8 activities showing drop-off
- Enterprise deals generate more activities than SMB (more stakeholders)
- LinkedIn-heavy early in cycle, Meeting-heavy mid, Email-heavy late
- ~10% of accounts have zero activities (untouched imports)

## CRM Export

Export datasets in CRM-specific formats ready for import into HubSpot, Salesforce, or Zoho. Each export includes:

- **Field-mapped CSVs** — columns renamed to match CRM field names
- **Association files** — relationship files using each CRM's linking method
- **Users file** — sales rep reference file with CRM-specific identifiers
- **Import guide** — step-by-step markdown guide for importing data

| CRM | Association Method | Owner Format | Key Files |
|-----|-------------------|--------------|-----------|
| **HubSpot** | Company domain matching | `sarah.chen@testcompany.com` | contacts_with_companies, deals_with_companies, deals_with_contacts |
| **Salesforce** | External ID references (ACC-N, CON-N, OPP-N) | `sarah.chen` | accounts, contacts, opportunities with External_ID__c |
| **Zoho** | Name-based matching | `sarah.chen@testcompany.com` | contacts, deals, activities with Account_Name/Contact_Name |

## Project Structure

```
crm-dataset-builder/
├── app.py                         # Streamlit web interface
├── src/
│   ├── main.py                    # CLI menu and workflow orchestration
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── accounts.py            # AccountGenerator
│   │   ├── contacts.py            # ContactGenerator
│   │   ├── deals.py               # DealGenerator
│   │   └── activities.py          # ActivityGenerator
│   └── exporters/
│       ├── __init__.py
│       ├── base.py                # BaseCRMExporter (abstract base class)
│       ├── hubspot.py             # HubSpotExporter
│       ├── salesforce.py          # SalesforceExporter
│       └── zoho.py                # ZohoExporter
├── output/                        # Generated CSV files
├── requirements.txt
└── README.md
```

## Getting Started

### Web Interface (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Configure accounts, pipelines, date range, and export format in the sidebar.

### CLI

```bash
pip install -r requirements.txt
python src/main.py
```

The interactive menu lets you generate each dataset individually, all four in sequence, or export for a specific CRM:

```
What would you like to generate?
  1) Accounts
  2) Contacts
  3) Deals
  4) Activities
  5) All (accounts + contacts + deals + activities)
  6) Export for CRM (HubSpot, Salesforce, Zoho)
```

Datasets must be generated in order — contacts depend on accounts, deals depend on both, and activities depend on all three. CRM export (option 6) requires all four datasets to exist.

## Built With

- Python 3.x
- [Streamlit](https://streamlit.io/) for the web interface
- [Faker](https://faker.readthedocs.io/) for realistic name/company generation
- [pandas](https://pandas.pydata.org/) for data manipulation and CRM export
- Claude Code (AI-assisted development)

## License

MIT
