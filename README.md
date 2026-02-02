# CRM Dataset Builder

A command-line tool that generates realistic B2B SaaS CRM datasets — accounts, contacts, deals, and activities — with interconnected foreign keys and statistically plausible distributions.

## Overview

This tool generates synthetic CRM data that mimics real-world B2B SaaS sales patterns. Useful for:

- Testing CRM applications and dashboards
- Demonstrating data analysis workflows
- Populating development/staging databases
- Training and educational purposes

## Generated Datasets

| File | Records (50 accounts) | Description |
|------|----------------------|-------------|
| `accounts.csv` | 50 | B2B SaaS companies with industry, employee count, revenue, region |
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

**Accounts** — Weighted toward smaller companies (50-500 employees), with revenue correlated to headcount.

**Contacts** — 2-5 per account, department-weighted toward Sales/Marketing/Customer Success for CRM realism. Each assigned to one of 6 sales reps.

**Deals** — Three pipelines with distinct behavior:
- **New Business** (~70% of accounts): 22% win rate, 30-180 day cycles by segment
- **Renewals**: spawned ~12 months after won NB deals, 85% win rate
- **Expansions**: 50% chance per won NB deal, 3-9 months later, 45% win rate
- Segment-based ACV: SMB $8-25K, Mid-Market $25-100K, Enterprise $100-350K

**Activities** — Phase-based engagement patterns:
- Won deals: 10-20 activities with strong multi-channel engagement
- Lost deals: 4-8 activities showing drop-off
- Enterprise deals generate more activities than SMB (more stakeholders)
- LinkedIn-heavy early in cycle, Meeting-heavy mid, Email-heavy late
- ~10% of accounts have zero activities (untouched imports)

## Project Structure

```
crm-dataset-builder/
├── src/
│   ├── main.py                    # CLI menu and workflow orchestration
│   └── generators/
│       ├── __init__.py
│       ├── accounts.py            # AccountGenerator
│       ├── contacts.py            # ContactGenerator
│       ├── deals.py               # DealGenerator
│       └── activities.py          # ActivityGenerator
├── output/                        # Generated CSV files
├── requirements.txt
└── README.md
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the tool
python src/main.py
```

The interactive menu lets you generate each dataset individually or all four in sequence:

```
What would you like to generate?
  1) Accounts
  2) Contacts
  3) Deals
  4) Activities
  5) All (accounts + contacts + deals + activities)
```

Datasets must be generated in order — contacts depend on accounts, deals depend on both, and activities depend on all three.

## Built With

- Python 3.x
- [Faker](https://faker.readthedocs.io/) for realistic name/company generation
- Claude Code (AI-assisted development)

## License

MIT
