"""
CRM Dataset Builder

A command-line tool for generating realistic CRM data for testing,
demonstrations, and development purposes.

Usage:
    python src/main.py

The tool will prompt you for the number of companies to generate,
then create a CSV file in the output directory.
"""

import csv
import os
import sys

# Add the src directory to the path so we can import our modules
# This allows running the script from the project root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators import AccountGenerator


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
        # Convert dataclass to dict using __dict__
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


def main():
    """
    Main entry point for the CRM Dataset Builder.

    Workflow:
    1. Display welcome message
    2. Prompt user for number of companies
    3. Generate the account data
    4. Save to CSV file
    5. Display success message
    """
    # Display welcome banner
    print("\n" + "=" * 50)
    print("  CRM Dataset Builder")
    print("  Generate realistic B2B SaaS company data")
    print("=" * 50)

    # Get the number of companies to generate from user
    count = get_user_input()

    # Create the generator instance
    # Note: You can pass a seed for reproducible results, e.g., AccountGenerator(seed=42)
    generator = AccountGenerator()

    # Generate the accounts with a progress message
    print(f"\nGenerating {count} companies...")
    accounts = generator.generate(count)

    # Define the output file path
    # Using os.path to construct path relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(project_root, "output", "accounts.csv")

    # Save the generated data to CSV
    save_to_csv(accounts, output_path)

    # Display success message
    print("\n" + "-" * 50)
    print("✓ Success!")
    print(f"  Generated {count} company records")
    print(f"  Saved to: {output_path}")
    print("-" * 50)

    # Show a preview of the first few records
    print("\nPreview of generated data:")
    print("-" * 50)
    for account in accounts[:3]:
        print(f"  • {account.company_name}")
        print(f"    Industry: {account.industry}")
        print(f"    Employees: {account.employee_count:,} | Revenue: ${account.annual_revenue:,}")
        print()


if __name__ == "__main__":
    main()
