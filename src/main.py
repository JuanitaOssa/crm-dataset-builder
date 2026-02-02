"""
CRM Dataset Builder

A command-line tool for generating realistic CRM data for testing,
demonstrations, and development purposes.

Usage:
    python src/main.py

The tool presents a menu to generate accounts, contacts, deals, or all three.
Output CSV files are saved to the output directory.
"""

import csv
import os
import sys
from collections import Counter

# Add the src directory to the path so we can import our modules
# This allows running the script from the project root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators import AccountGenerator, ContactGenerator, DealGenerator


# Path helpers
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_PATH = os.path.join(PROJECT_ROOT, "output", "accounts.csv")
CONTACTS_PATH = os.path.join(PROJECT_ROOT, "output", "contacts.csv")
DEALS_PATH = os.path.join(PROJECT_ROOT, "output", "deals.csv")


def display_menu() -> str:
    """
    Display the main menu and return the user's choice.

    Returns:
        The selected option as a string ('1', '2', '3', or '4').
    """
    print("\nWhat would you like to generate?")
    print("  1) Accounts")
    print("  2) Contacts")
    print("  3) Deals")
    print("  4) All (accounts + contacts + deals)")

    while True:
        choice = input("\nSelect an option [1/2/3/4]: ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_user_input() -> int:
    """
    Prompt the user for the number of companies to generate.

    Validates that the input is a positive integer.
    Provides a default value of 100 if user presses Enter.

    Returns:
        The number of companies to generate.
    """
    while True:
        try:
            # Prompt user with a default option
            user_input = input("\nHow many companies would you like to generate? [default: 100]: ")

            # Use default if user just presses Enter
            if user_input.strip() == "":
                return 100

            # Convert to integer and validate
            count = int(user_input)

            if count <= 0:
                print("Please enter a positive number.")
                continue

            if count > 10000:
                print("Maximum is 10,000 companies. Please enter a smaller number.")
                continue

            return count

        except ValueError:
            print("Invalid input. Please enter a number.")


def save_to_csv(accounts: list, filepath: str) -> None:
    """
    Save generated accounts to a CSV file.

    Creates the output directory if it doesn't exist.
    Writes all account fields as columns with headers.

    Args:
        accounts: List of Account dataclass instances.
        filepath: Path where the CSV file should be saved.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Define the column headers (matching Account dataclass fields)
    fieldnames = [
        "id",
        "company_name",
        "industry",
        "employee_count",
        "annual_revenue",
        "region",
        "founded_year",
        "website",
        "description"
    ]

    # Write the CSV file
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # Write each account as a row
        for account in accounts:
            writer.writerow({
                "id": account.id,
                "company_name": account.company_name,
                "industry": account.industry,
                "employee_count": account.employee_count,
                "annual_revenue": account.annual_revenue,
                "region": account.region,
                "founded_year": account.founded_year,
                "website": account.website,
                "description": account.description
            })


def save_contacts_to_csv(contacts: list, filepath: str) -> None:
    """
    Save generated contacts to a CSV file.

    Creates the output directory if it doesn't exist.

    Args:
        contacts: List of Contact dataclass instances.
        filepath: Path where the CSV file should be saved.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        "contact_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "title",
        "department",
        "account_id",
        "contact_owner",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            writer.writerow({
                "contact_id": contact.contact_id,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "phone": contact.phone,
                "title": contact.title,
                "department": contact.department,
                "account_id": contact.account_id,
                "contact_owner": contact.contact_owner,
            })


def generate_accounts_flow() -> None:
    """Run the accounts generation workflow."""
    count = get_user_input()

    generator = AccountGenerator()

    print(f"\nGenerating {count} companies...")
    accounts = generator.generate(count)

    save_to_csv(accounts, ACCOUNTS_PATH)

    print("\n" + "-" * 50)
    print("Success!")
    print(f"  Generated {count} company records")
    print(f"  Saved to: {ACCOUNTS_PATH}")
    print("-" * 50)

    # Preview first few records
    print("\nPreview of generated data:")
    print("-" * 50)
    for account in accounts[:3]:
        print(f"  - {account.company_name}")
        print(f"    Industry: {account.industry}")
        print(f"    Employees: {account.employee_count:,} | Revenue: ${account.annual_revenue:,}")
        print()


def generate_contacts_flow() -> None:
    """Run the contacts generation workflow."""
    if not os.path.exists(ACCOUNTS_PATH):
        print("\n[!] accounts.csv not found at: " + ACCOUNTS_PATH)
        print("    Please generate accounts first (option 1) or run all (option 3).")
        return

    print(f"\nLoading accounts from: {ACCOUNTS_PATH}")
    generator = ContactGenerator(ACCOUNTS_PATH)

    print(f"Generating contacts for {len(generator.accounts)} accounts...")
    contacts = generator.generate()

    save_contacts_to_csv(contacts, CONTACTS_PATH)

    # Summary stats
    total = len(contacts)
    contacts_per_account = Counter(c.account_id for c in contacts)
    count_distribution = Counter(contacts_per_account.values())
    owner_distribution = Counter(c.contact_owner for c in contacts)

    print("\n" + "-" * 50)
    print("Success!")
    print(f"  Generated {total} contacts across {len(contacts_per_account)} accounts")
    print(f"  Saved to: {CONTACTS_PATH}")
    print("-" * 50)

    print("\nContacts per account breakdown:")
    for n in sorted(count_distribution):
        pct = count_distribution[n] / len(contacts_per_account) * 100
        print(f"  {n} contacts: {count_distribution[n]} accounts ({pct:.0f}%)")

    print("\nContact owner distribution:")
    for owner, cnt in owner_distribution.most_common():
        print(f"  {owner}: {cnt} contacts")

    # Preview first few records
    print("\nPreview of generated contacts:")
    print("-" * 50)
    for contact in contacts[:3]:
        print(f"  - {contact.first_name} {contact.last_name}")
        print(f"    {contact.title}, {contact.department}")
        print(f"    {contact.email} | Account #{contact.account_id}")
        print()


def save_deals_to_csv(deals: list, filepath: str) -> None:
    """
    Save generated deals to a CSV file.

    Creates the output directory if it doesn't exist.

    Args:
        deals: List of Deal dataclass instances.
        filepath: Path where the CSV file should be saved.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        "deal_id",
        "deal_name",
        "account_id",
        "contact_id",
        "pipeline",
        "segment",
        "stage",
        "amount",
        "created_date",
        "close_date",
        "deal_status",
        "deal_owner",
        "probability",
        "loss_reason",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for deal in deals:
            writer.writerow({
                "deal_id": deal.deal_id,
                "deal_name": deal.deal_name,
                "account_id": deal.account_id,
                "contact_id": deal.contact_id,
                "pipeline": deal.pipeline,
                "segment": deal.segment,
                "stage": deal.stage,
                "amount": deal.amount,
                "created_date": deal.created_date,
                "close_date": deal.close_date,
                "deal_status": deal.deal_status,
                "deal_owner": deal.deal_owner,
                "probability": deal.probability,
                "loss_reason": deal.loss_reason,
            })


def generate_deals_flow() -> None:
    """Run the deals generation workflow."""
    if not os.path.exists(ACCOUNTS_PATH):
        print("\n[!] accounts.csv not found at: " + ACCOUNTS_PATH)
        print("    Please generate accounts first (option 1) or run all (option 4).")
        return

    if not os.path.exists(CONTACTS_PATH):
        print("\n[!] contacts.csv not found at: " + CONTACTS_PATH)
        print("    Please generate contacts first (option 2) or run all (option 4).")
        return

    print(f"\nLoading accounts from: {ACCOUNTS_PATH}")
    print(f"Loading contacts from: {CONTACTS_PATH}")
    generator = DealGenerator(ACCOUNTS_PATH, CONTACTS_PATH)

    print(f"Generating deals for {len(generator.accounts)} accounts...")
    deals = generator.generate()

    save_deals_to_csv(deals, DEALS_PATH)

    # Summary stats
    total = len(deals)
    accounts_with_deals = len(set(d.account_id for d in deals))
    total_accounts = len(generator.accounts)
    accounts_without_deals = total_accounts - accounts_with_deals

    pipeline_counts = Counter(d.pipeline for d in deals)
    segment_counts = Counter(d.segment for d in deals)

    print("\n" + "-" * 50)
    print("Success!")
    print(f"  Generated {total} deals")
    print(f"  Accounts with deals: {accounts_with_deals}")
    print(f"  Accounts without deals: {accounts_without_deals}")
    print(f"  Saved to: {DEALS_PATH}")
    print("-" * 50)

    print("\nPipeline breakdown:")
    for pipeline in ["New Business", "Renewal", "Expansion"]:
        print(f"  {pipeline}: {pipeline_counts.get(pipeline, 0)} deals")

    print("\nSegment breakdown:")
    for segment in ["SMB", "Mid-Market", "Enterprise"]:
        print(f"  {segment}: {segment_counts.get(segment, 0)} deals")

    print("\nOutcome rates by pipeline:")
    for pipeline in ["New Business", "Renewal", "Expansion"]:
        pipe_deals = [d for d in deals if d.pipeline == pipeline]
        if not pipe_deals:
            continue
        won = sum(1 for d in pipe_deals if d.deal_status == "Won")
        lost = sum(1 for d in pipe_deals if d.deal_status == "Lost")
        active = sum(1 for d in pipe_deals if d.deal_status == "Active")
        n = len(pipe_deals)
        print(
            f"  {pipeline}: Won {won}/{n} ({won/n*100:.0f}%) | "
            f"Lost {lost}/{n} ({lost/n*100:.0f}%) | "
            f"Active {active}/{n} ({active/n*100:.0f}%)"
        )

    print("\nAverage deal size by segment:")
    for segment in ["SMB", "Mid-Market", "Enterprise"]:
        seg_deals = [d for d in deals if d.segment == segment]
        if seg_deals:
            avg = sum(d.amount for d in seg_deals) / len(seg_deals)
            print(f"  {segment}: ${avg:,.0f}")

    # Preview first 3 deals
    print("\nPreview of generated deals:")
    print("-" * 50)
    for deal in deals[:3]:
        print(f"  - {deal.deal_name}")
        print(f"    {deal.pipeline} | {deal.stage} | ${deal.amount:,}")
        print(f"    Account #{deal.account_id} | {deal.deal_status}")
        print()


def generate_all_flow() -> None:
    """Run accounts, contacts, then deals generation sequentially."""
    generate_accounts_flow()
    generate_contacts_flow()
    generate_deals_flow()


def main():
    """
    Main entry point for the CRM Dataset Builder.

    Displays a menu and routes to the selected generation workflow.
    """
    # Display welcome banner
    print("\n" + "=" * 50)
    print("  CRM Dataset Builder")
    print("  Generate realistic B2B SaaS company data")
    print("=" * 50)

    choice = display_menu()

    if choice == "1":
        generate_accounts_flow()
    elif choice == "2":
        generate_contacts_flow()
    elif choice == "3":
        generate_deals_flow()
    elif choice == "4":
        generate_all_flow()


if __name__ == "__main__":
    main()
