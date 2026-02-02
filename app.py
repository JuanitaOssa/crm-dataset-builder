"""
CRM Dataset Builder — Streamlit Web Interface

A web UI for generating realistic, relational B2B SaaS CRM datasets.
Wraps the existing generator classes (AccountGenerator, ContactGenerator,
DealGenerator, ActivityGenerator) with an interactive Streamlit frontend.

Run with:
    streamlit run app.py
"""

import csv
import dataclasses
import datetime
import io
import sys
import os
import tempfile
import zipfile
from collections import Counter

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
#  Make the src/ package importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from generators import AccountGenerator, ContactGenerator
from generators.deals import DealGenerator, Deal
from generators.activities import ActivityGenerator, Activity


# ===================================================================== #
#  Helper functions                                                      #
# ===================================================================== #

# Column orders matching the dataclass fields (used for CSV and display)
ACCOUNT_FIELDS = [
    "id", "company_name", "industry", "employee_count",
    "annual_revenue", "region", "founded_year", "website", "description",
]
CONTACT_FIELDS = [
    "contact_id", "first_name", "last_name", "email", "phone",
    "title", "department", "account_id", "contact_owner",
]
DEAL_FIELDS = [
    "deal_id", "deal_name", "account_id", "contact_id", "pipeline",
    "segment", "stage", "amount", "created_date", "close_date",
    "deal_status", "deal_owner", "probability", "loss_reason",
]
ACTIVITY_FIELDS = [
    "activity_id", "activity_type", "subject", "activity_date",
    "account_id", "contact_id", "deal_id", "completed",
    "duration_minutes", "notes", "activity_owner",
]


def to_dataframe(objects: list, columns: list) -> pd.DataFrame:
    """Convert a list of dataclass instances to a pandas DataFrame."""
    rows = [dataclasses.asdict(obj) for obj in objects]
    return pd.DataFrame(rows, columns=columns)


def write_csv(objects: list, columns: list, path: str) -> None:
    """Write a list of dataclass instances to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for obj in objects:
            writer.writerow(dataclasses.asdict(obj))


def build_zip(dataframes: dict) -> bytes:
    """
    Build an in-memory ZIP file containing all dataset CSVs.

    Args:
        dataframes: dict mapping filename -> DataFrame
    Returns:
        ZIP file contents as bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, df in dataframes.items():
            zf.writestr(filename, df.to_csv(index=False))
    return buf.getvalue()


# ===================================================================== #
#  Generation pipeline                                                   #
# ===================================================================== #

def run_generation(num_accounts: int, date_years: int) -> dict:
    """
    Run the full generation pipeline: accounts -> contacts -> deals -> activities.

    Uses temporary CSV files to bridge generators that expect file paths.
    Overrides date range constants based on the selected history length.

    Args:
        num_accounts: Number of accounts to generate.
        date_years: Years of history (1, 2, or 3).

    Returns:
        Dict with keys 'accounts', 'contacts', 'deals', 'activities',
        each containing a pandas DataFrame.
    """
    # --- Configure date range based on user selection ---
    date_range_end = datetime.date(2026, 2, 1)
    if date_years == 3:
        date_range_start = datetime.date(2023, 1, 1)
    elif date_years == 2:
        date_range_start = datetime.date(2024, 2, 1)
    else:
        date_range_start = datetime.date(2025, 2, 1)

    # Active window is always 6 months before end
    active_window_start = datetime.date(2025, 8, 1)

    # Override DealGenerator class constants for this run
    DealGenerator.DATE_RANGE_START = date_range_start
    DealGenerator.DATE_RANGE_END = date_range_end
    DealGenerator.ACTIVE_WINDOW_START = active_window_start

    # Override ActivityGenerator class constants for this run
    ActivityGenerator.DATE_RANGE_START = date_range_start
    ActivityGenerator.DATE_RANGE_END = date_range_end
    ActivityGenerator.RECENT_ACTIVITY_CUTOFF = date_range_end - datetime.timedelta(days=14)

    progress = st.progress(0, text="Generating accounts...")

    # --- Step 1: Accounts ---
    acc_gen = AccountGenerator()
    accounts = acc_gen.generate(num_accounts)
    accounts_df = to_dataframe(accounts, ACCOUNT_FIELDS)
    progress.progress(25, text="Generating contacts...")

    # --- Write accounts to temp CSV for downstream generators ---
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_acc:
        tmp_acc_path = tmp_acc.name
        write_csv(accounts, ACCOUNT_FIELDS, tmp_acc_path)

    # --- Step 2: Contacts ---
    con_gen = ContactGenerator(tmp_acc_path)
    contacts = con_gen.generate()
    contacts_df = to_dataframe(contacts, CONTACT_FIELDS)
    progress.progress(50, text="Generating deals...")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_con:
        tmp_con_path = tmp_con.name
        write_csv(contacts, CONTACT_FIELDS, tmp_con_path)

    # --- Step 3: Deals ---
    deal_gen = DealGenerator(tmp_acc_path, tmp_con_path)
    deals = deal_gen.generate()
    deals_df = to_dataframe(deals, DEAL_FIELDS)
    progress.progress(75, text="Generating activities...")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_deal:
        tmp_deal_path = tmp_deal.name
        write_csv(deals, DEAL_FIELDS, tmp_deal_path)

    # --- Step 4: Activities ---
    act_gen = ActivityGenerator(tmp_acc_path, tmp_con_path, tmp_deal_path)
    activities = act_gen.generate()
    activities_df = to_dataframe(activities, ACTIVITY_FIELDS)
    progress.progress(100, text="Done!")

    # --- Clean up temp files ---
    for p in [tmp_acc_path, tmp_con_path, tmp_deal_path]:
        try:
            os.unlink(p)
        except OSError:
            pass

    return {
        "accounts": accounts_df,
        "contacts": contacts_df,
        "deals": deals_df,
        "activities": activities_df,
    }


# ===================================================================== #
#  Streamlit app                                                         #
# ===================================================================== #

def main():
    st.set_page_config(
        page_title="CRM Dataset Builder",
        page_icon=":bar_chart:",
        layout="wide",
    )

    # ------------------------------------------------------------------ #
    #  Header                                                             #
    # ------------------------------------------------------------------ #
    st.title("CRM Dataset Builder")
    st.caption("by Juanita Ossa")
    st.markdown(
        "Generate realistic, relational B2B SaaS CRM datasets "
        "for testing, demos, and development."
    )

    # ------------------------------------------------------------------ #
    #  Sidebar configuration                                              #
    # ------------------------------------------------------------------ #
    with st.sidebar:
        st.header("Configuration")

        num_accounts = st.slider(
            "Number of accounts",
            min_value=25,
            max_value=500,
            value=50,
            step=25,
            help="How many B2B SaaS companies to generate.",
        )

        st.subheader("Pipelines")
        show_nb = st.checkbox("New Business", value=True)
        show_renewal = st.checkbox("Renewals", value=True)
        show_expansion = st.checkbox("Expansions", value=True)

        date_years = st.radio(
            "Date range (years of history)",
            options=[3, 2, 1],
            format_func=lambda y: f"{y} year{'s' if y > 1 else ''} (from {2026 - y})",
            index=0,
            help="How many years of deal and activity history to generate.",
        )

        st.divider()
        generate_clicked = st.button(
            "Generate Dataset",
            type="primary",
            use_container_width=True,
        )

    # ------------------------------------------------------------------ #
    #  Generation trigger                                                 #
    # ------------------------------------------------------------------ #
    if generate_clicked:
        data = run_generation(num_accounts, date_years)
        st.session_state["data"] = data

    # ------------------------------------------------------------------ #
    #  Main area — display results if data exists                         #
    # ------------------------------------------------------------------ #
    if "data" not in st.session_state:
        st.info(
            "Configure your dataset in the sidebar and click "
            "**Generate Dataset** to get started."
        )
    else:
        data = st.session_state["data"]
        accounts_df = data["accounts"]
        contacts_df = data["contacts"]
        deals_df = data["deals"]
        activities_df = data["activities"]

        # Build pipeline filter mask for deals and activities
        selected_pipelines = []
        if show_nb:
            selected_pipelines.append("New Business")
        if show_renewal:
            selected_pipelines.append("Renewal")
        if show_expansion:
            selected_pipelines.append("Expansion")

        if selected_pipelines:
            filtered_deals = deals_df[deals_df["pipeline"].isin(selected_pipelines)]
        else:
            filtered_deals = deals_df

        # Filter activities to only those linked to visible deals (or non-deal)
        visible_deal_ids = set(filtered_deals["deal_id"].astype(str))
        filtered_activities = activities_df[
            (activities_df["deal_id"].astype(str) == "")
            | (activities_df["deal_id"].astype(str).isin(visible_deal_ids))
        ]

        # -------------------------------------------------------------- #
        #  Tabbed data preview                                            #
        # -------------------------------------------------------------- #
        st.subheader("Data Preview")
        tab_acc, tab_con, tab_deal, tab_act = st.tabs(
            [
                f"Accounts ({len(accounts_df)})",
                f"Contacts ({len(contacts_df)})",
                f"Deals ({len(filtered_deals)})",
                f"Activities ({len(filtered_activities)})",
            ]
        )

        with tab_acc:
            st.dataframe(accounts_df, use_container_width=True, hide_index=True)
        with tab_con:
            st.dataframe(contacts_df, use_container_width=True, hide_index=True)
        with tab_deal:
            st.dataframe(filtered_deals, use_container_width=True, hide_index=True)
        with tab_act:
            st.dataframe(filtered_activities, use_container_width=True, hide_index=True)

        # -------------------------------------------------------------- #
        #  Summary statistics                                             #
        # -------------------------------------------------------------- #
        st.subheader("Summary Statistics")

        # Row 1: Record counts
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accounts", f"{len(accounts_df):,}")
        col2.metric("Contacts", f"{len(contacts_df):,}")
        col3.metric("Deals", f"{len(filtered_deals):,}")
        col4.metric("Activities", f"{len(filtered_activities):,}")

        # Row 2: Key insights
        accounts_with_deals = deals_df["account_id"].nunique()
        zero_deal_accounts = len(accounts_df) - accounts_with_deals

        col5, col6 = st.columns(2)
        col5.metric("Accounts with deals", accounts_with_deals)
        col6.metric("Accounts with zero deals", zero_deal_accounts)

        # Row 3: Win rates by pipeline & avg deal size by segment
        stat_left, stat_right = st.columns(2)

        with stat_left:
            st.markdown("**Win rates by pipeline**")
            for pipeline in ["New Business", "Renewal", "Expansion"]:
                pipe_deals = deals_df[deals_df["pipeline"] == pipeline]
                if len(pipe_deals) == 0:
                    continue
                won = (pipe_deals["deal_status"] == "Won").sum()
                lost = (pipe_deals["deal_status"] == "Lost").sum()
                active = (pipe_deals["deal_status"] == "Active").sum()
                n = len(pipe_deals)
                st.markdown(
                    f"- **{pipeline}**: Won {won}/{n} ({won/n*100:.0f}%) · "
                    f"Lost {lost}/{n} ({lost/n*100:.0f}%) · "
                    f"Active {active}/{n} ({active/n*100:.0f}%)"
                )

        with stat_right:
            st.markdown("**Avg deal size by segment**")
            for segment in ["SMB", "Mid-Market", "Enterprise"]:
                seg_deals = deals_df[deals_df["segment"] == segment]
                if len(seg_deals) == 0:
                    continue
                avg_amount = seg_deals["amount"].mean()
                st.markdown(f"- **{segment}**: ${avg_amount:,.0f}")

        # Row 4: Activity type distribution
        st.markdown("**Activity type distribution**")
        act_type_counts = activities_df["activity_type"].value_counts()
        act_total = len(activities_df)

        act_cols = st.columns(5)
        for i, atype in enumerate(["Email", "Phone Call", "Meeting", "LinkedIn", "Note"]):
            cnt = act_type_counts.get(atype, 0)
            pct = cnt / act_total * 100 if act_total else 0
            act_cols[i].metric(atype, f"{cnt}", f"{pct:.0f}%")

        # -------------------------------------------------------------- #
        #  Download buttons                                               #
        # -------------------------------------------------------------- #
        st.subheader("Download")

        dl_cols = st.columns(5)

        dl_cols[0].download_button(
            label="Accounts CSV",
            data=accounts_df.to_csv(index=False),
            file_name="accounts.csv",
            mime="text/csv",
        )
        dl_cols[1].download_button(
            label="Contacts CSV",
            data=contacts_df.to_csv(index=False),
            file_name="contacts.csv",
            mime="text/csv",
        )
        dl_cols[2].download_button(
            label="Deals CSV",
            data=filtered_deals.to_csv(index=False),
            file_name="deals.csv",
            mime="text/csv",
        )
        dl_cols[3].download_button(
            label="Activities CSV",
            data=filtered_activities.to_csv(index=False),
            file_name="activities.csv",
            mime="text/csv",
        )

        # ZIP download with all four CSVs
        zip_data = build_zip({
            "accounts.csv": accounts_df,
            "contacts.csv": contacts_df,
            "deals.csv": filtered_deals,
            "activities.csv": filtered_activities,
        })
        dl_cols[4].download_button(
            label="All as ZIP",
            data=zip_data,
            file_name="crm_dataset.zip",
            mime="application/zip",
        )

    # ------------------------------------------------------------------ #
    #  About section                                                      #
    # ------------------------------------------------------------------ #
    st.divider()
    with st.expander("About this tool"):
        st.markdown("""
**CRM Dataset Builder** generates realistic, interconnected B2B SaaS CRM
datasets for testing, demos, and development.

**Data relationships:**

```
accounts
  ├── contacts        (2-5 per account)
  ├── deals           (New Business → Renewals → Expansions)
  │    └── activities (phase-based: LinkedIn early, Meetings mid, Emails late)
  └── activities      (non-deal relationship touchpoints)
```

**How it works:**
- Accounts are generated with realistic company names, industries, and revenue
- Contacts are linked to accounts with department-weighted titles
- Deals follow three pipelines with segment-based ACV and realistic win rates
- Activities shift across the deal lifecycle with phase-based type weighting
- Data is generated fresh each time — nothing is stored on the server

**Built with:** Python, Streamlit, and
[Claude Code](https://claude.ai/claude-code)

**Source:** [github.com/JuanitaOssa/crm-dataset-builder](https://github.com/JuanitaOssa/crm-dataset-builder)
""")


if __name__ == "__main__":
    main()
