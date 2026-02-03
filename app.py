"""
CRM Dataset Builder — Streamlit Web Interface

A web UI for generating realistic, relational CRM datasets for multiple
business types. Wraps the generator classes with an interactive Streamlit
frontend.

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

from profiles import PROFILE_REGISTRY
from generators import AccountGenerator, ContactGenerator
from generators.deals import DealGenerator, Deal
from generators.activities import ActivityGenerator, Activity
from exporters import HubSpotExporter, SalesforceExporter, ZohoExporter


# ===================================================================== #
#  Helper functions                                                      #
# ===================================================================== #

def to_dataframe(objects: list, columns: list) -> pd.DataFrame:
    """Convert a list of dataclass instances to a pandas DataFrame."""
    rows = [dataclasses.asdict(obj) for obj in objects]
    # Only keep columns that exist in the data
    if rows:
        available = set(rows[0].keys())
        columns = [c for c in columns if c in available]
    return pd.DataFrame(rows, columns=columns)


def write_csv(objects: list, columns: list, path: str) -> None:
    """Write a list of dataclass instances to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
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

def run_generation(num_accounts: int, date_years: int, profile) -> dict:
    """
    Run the full generation pipeline: accounts -> contacts -> deals -> activities.

    Uses temporary CSV files to bridge generators that expect file paths.
    Overrides date range constants based on the selected history length.

    Args:
        num_accounts: Number of accounts to generate.
        date_years: Years of history (1, 2, or 3).
        profile: A BaseProfile instance.

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
    acc_gen = AccountGenerator(profile=profile)
    accounts = acc_gen.generate(num_accounts)
    accounts_df = to_dataframe(accounts, profile.account_fields)
    progress.progress(25, text="Generating contacts...")

    # --- Write accounts to temp CSV for downstream generators ---
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_acc:
        tmp_acc_path = tmp_acc.name
        write_csv(accounts, profile.account_fields, tmp_acc_path)

    # --- Step 2: Contacts ---
    con_gen = ContactGenerator(tmp_acc_path, profile=profile)
    contacts = con_gen.generate()
    contacts_df = to_dataframe(contacts, profile.contact_fields)
    progress.progress(50, text="Generating deals...")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_con:
        tmp_con_path = tmp_con.name
        write_csv(contacts, profile.contact_fields, tmp_con_path)

    # --- Step 3: Deals ---
    deal_gen = DealGenerator(tmp_acc_path, tmp_con_path, profile=profile)
    deals = deal_gen.generate()
    deals_df = to_dataframe(deals, profile.deal_fields)
    progress.progress(75, text="Generating activities...")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as tmp_deal:
        tmp_deal_path = tmp_deal.name
        write_csv(deals, profile.deal_fields, tmp_deal_path)

    # --- Step 4: Activities ---
    act_gen = ActivityGenerator(tmp_acc_path, tmp_con_path, tmp_deal_path, profile=profile)
    activities = act_gen.generate()
    activities_df = to_dataframe(activities, profile.activity_fields)
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
        "Generate realistic, relational CRM datasets "
        "for testing, demos, and development."
    )

    # ------------------------------------------------------------------ #
    #  Sidebar configuration                                              #
    # ------------------------------------------------------------------ #
    with st.sidebar:
        st.header("Configuration")

        # Business type selector
        business_type = st.selectbox(
            "Business Type",
            options=list(PROFILE_REGISTRY.keys()),
        )
        profile = PROFILE_REGISTRY[business_type]()
        st.caption(profile.description)

        num_accounts = st.slider(
            "Number of accounts",
            min_value=25,
            max_value=500,
            value=50,
            step=25,
            help="How many companies to generate.",
        )

        # Dynamic pipeline checkboxes from profile
        st.subheader("Pipelines")
        pipeline_selections = {}
        for pipeline_name in profile.pipelines.keys():
            pipeline_selections[pipeline_name] = st.checkbox(
                pipeline_name, value=True
            )

        date_years = st.radio(
            "Date range (years of history)",
            options=[3, 2, 1],
            format_func=lambda y: f"{y} year{'s' if y > 1 else ''} (from {2026 - y})",
            index=0,
            help="How many years of deal and activity history to generate.",
        )

        st.subheader("Export Format")
        export_format = st.selectbox(
            "Target CRM",
            options=["Standard CSV", "HubSpot", "Salesforce", "Zoho"],
            help="Choose a CRM to get formatted import files with field mappings and association files.",
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
        data = run_generation(num_accounts, date_years, profile)
        st.session_state["data"] = data
        st.session_state["profile_name"] = business_type

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
        selected_pipelines = [
            name for name, checked in pipeline_selections.items() if checked
        ]

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
        #  Generate master import file if CRM format selected             #
        # -------------------------------------------------------------- #
        master_df = None
        if export_format != "Standard CSV":
            exporter_map = {
                "HubSpot": HubSpotExporter,
                "Salesforce": SalesforceExporter,
                "Zoho": ZohoExporter,
            }
            ExporterClass = exporter_map[export_format]
            exporter = ExporterClass(
                accounts_df, contacts_df, filtered_deals, filtered_activities,
                profile=profile,
            )
            crm_files = exporter.export()
            master_key = [k for k in crm_files if "master_import" in k][0]
            master_df = crm_files[master_key]

        # -------------------------------------------------------------- #
        #  Tabbed data preview                                            #
        # -------------------------------------------------------------- #
        st.subheader("Data Preview")

        tab_labels = [
            f"Accounts ({len(accounts_df)})",
            f"Contacts ({len(contacts_df)})",
            f"Deals ({len(filtered_deals)})",
            f"Activities ({len(filtered_activities)})",
        ]
        if master_df is not None:
            tab_labels.append(f"Master Import ({len(master_df)} rows)")

        tabs = st.tabs(tab_labels)

        with tabs[0]:
            st.dataframe(accounts_df, use_container_width=True, hide_index=True)
        with tabs[1]:
            st.dataframe(contacts_df, use_container_width=True, hide_index=True)
        with tabs[2]:
            st.dataframe(filtered_deals, use_container_width=True, hide_index=True)
        with tabs[3]:
            st.dataframe(filtered_activities, use_container_width=True, hide_index=True)
        if master_df is not None:
            with tabs[4]:
                st.dataframe(master_df.head(25), use_container_width=True, hide_index=True)

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
            for pipeline_name in profile.pipelines.keys():
                pipe_deals = deals_df[deals_df["pipeline"] == pipeline_name]
                if len(pipe_deals) == 0:
                    continue
                won = (pipe_deals["deal_status"] == "Won").sum()
                lost = (pipe_deals["deal_status"] == "Lost").sum()
                active = (pipe_deals["deal_status"] == "Open").sum()
                n = len(pipe_deals)
                st.markdown(
                    f"- **{pipeline_name}**: Won {won}/{n} ({won/n*100:.0f}%) · "
                    f"Lost {lost}/{n} ({lost/n*100:.0f}%) · "
                    f"Open {active}/{n} ({active/n*100:.0f}%)"
                )

        with stat_right:
            st.markdown("**Avg deal size by segment**")
            for segment in profile.segments:
                seg_deals = deals_df[deals_df["segment"] == segment]
                if len(seg_deals) == 0:
                    continue
                avg_amount = seg_deals["amount"].mean()
                st.markdown(f"- **{segment}**: ${avg_amount:,.0f}")

        # Row 4: Activity type distribution
        st.markdown("**Activity type distribution**")
        act_type_counts = activities_df["activity_type"].value_counts()
        act_total = len(activities_df)

        act_cols = st.columns(len(profile.activity_types))
        for i, atype in enumerate(profile.activity_types):
            cnt = act_type_counts.get(atype, 0)
            pct = cnt / act_total * 100 if act_total else 0
            act_cols[i].metric(atype, f"{cnt}", f"{pct:.0f}%")

        # -------------------------------------------------------------- #
        #  Download buttons                                               #
        # -------------------------------------------------------------- #
        st.subheader("Download")

        if export_format == "Standard CSV":
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
        else:
            # CRM-specific export (exporter and crm_files already created above)
            st.info(
                f"**{export_format} format selected.** "
                "Create users/owners in your CRM before importing data."
            )

            # --- Recommended: Master Import File ---
            master_key = [k for k in crm_files if "master_import" in k][0]
            master_df = crm_files[master_key]
            st.markdown("**Recommended: Master Import File**")
            st.download_button(
                label=f"Download {master_key}",
                data=master_df.to_csv(index=False),
                file_name=master_key,
                mime="text/csv",
                key="crm_dl_master",
            )

            # --- Individual Object Files (collapsible) ---
            individual_files = {
                k: v for k, v in crm_files.items()
                if k.endswith(".csv") and "master" not in k
            }
            with st.expander("Individual Object Files"):
                cols = st.columns(min(len(individual_files), 4))
                for i, (filename, df) in enumerate(individual_files.items()):
                    col_idx = i % min(len(individual_files), 4)
                    cols[col_idx].download_button(
                        label=filename,
                        data=df.to_csv(index=False),
                        file_name=filename,
                        mime="text/csv",
                        key=f"crm_dl_{filename}",
                    )

            # --- ZIP download with all CRM files ---
            crm_zip = exporter.export_zip()
            st.download_button(
                label=f"Download all {export_format} files as ZIP",
                data=crm_zip,
                file_name=f"{export_format.lower()}_import.zip",
                mime="application/zip",
            )

            # --- Import guide ---
            guide_key = [k for k in crm_files if k.endswith(".md")]
            if guide_key:
                with st.expander("Import Guide"):
                    st.markdown(crm_files[guide_key[0]])

    # ------------------------------------------------------------------ #
    #  About section                                                      #
    # ------------------------------------------------------------------ #
    st.divider()
    with st.expander("About this tool"):
        st.markdown("""
**CRM Dataset Builder** generates realistic, interconnected CRM datasets
for testing, demos, and development.

**Business types:** B2B SaaS, Manufacturer, and Consultancy — each with
industry-specific companies, pipelines, deal sizes, and activity patterns.

**Data relationships:**

```
accounts
  ├── contacts        (2-5 per account)
  ├── deals           (Primary → Renewals → Expansions)
  │    └── activities (phase-based: LinkedIn early, Meetings mid, Emails late)
  └── activities      (non-deal relationship touchpoints)
```

**How it works:**
- Select a business type to get industry-specific data (names, pipelines, deal sizes)
- Accounts are generated with realistic company names, industries, and revenue
- Contacts are linked to accounts with department-weighted titles
- Deals follow profile-specific pipelines with segment-based pricing and win rates
- Activities shift across the deal lifecycle with phase-based type weighting
- Data is generated fresh each time — nothing is stored on the server

**Built with:** Python, Streamlit, and
[Claude Code](https://claude.ai/claude-code)

**Source:** [github.com/JuanitaOssa/crm-dataset-builder](https://github.com/JuanitaOssa/crm-dataset-builder)
""")


if __name__ == "__main__":
    main()
