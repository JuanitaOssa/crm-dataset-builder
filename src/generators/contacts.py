"""
Contact Generator Module

Generates realistic B2B SaaS contact data for CRM datasets.
Each contact is linked to an existing account via account_id.
"""

import csv
import random
from dataclasses import dataclass
from typing import List

from faker import Faker


@dataclass
class Contact:
    """
    Represents a contact person at a B2B SaaS company.

    Attributes:
        contact_id: Unique identifier for the contact
        first_name: Contact's first name
        last_name: Contact's last name
        email: Contact's work email address
        phone: Contact's phone number
        title: Job title
        department: Department within the company
        account_id: Foreign key linking to the parent account
        contact_owner: CRM rep who owns the contact
    """
    contact_id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    title: str
    department: str
    account_id: int
    contact_owner: str


class ContactGenerator:
    """
    Generates realistic B2B SaaS contact data linked to existing accounts.

    Reads an accounts CSV file and generates multiple contacts per account
    with realistic names, emails, titles, and department assignments.

    Example:
        generator = ContactGenerator("output/accounts.csv")
        contacts = generator.generate()
    """

    # Department -> list of realistic titles
    TITLE_BY_DEPARTMENT = {
        "Sales": [
            "Account Executive",
            "Sales Manager",
            "VP of Sales",
            "Sales Development Representative",
            "Director of Sales",
            "Chief Revenue Officer",
            "Regional Sales Manager",
        ],
        "Engineering": [
            "Software Engineer",
            "Engineering Manager",
            "VP of Engineering",
            "CTO",
            "Senior Software Engineer",
            "Principal Engineer",
        ],
        "Marketing": [
            "Marketing Manager",
            "VP of Marketing",
            "CMO",
            "Content Marketing Manager",
            "Demand Generation Manager",
            "Director of Marketing",
        ],
        "Operations": [
            "Operations Manager",
            "COO",
            "Director of Operations",
            "Business Operations Analyst",
            "VP of Operations",
        ],
        "Customer Success": [
            "Customer Success Manager",
            "VP of Customer Success",
            "Director of Customer Success",
            "Customer Success Associate",
            "Head of Customer Success",
        ],
        "Executive": [
            "CEO",
            "President",
            "Co-Founder",
            "Managing Director",
        ],
        "Finance": [
            "CFO",
            "Finance Manager",
            "Controller",
            "Director of Finance",
            "Financial Analyst",
        ],
        "Product": [
            "Product Manager",
            "VP of Product",
            "Chief Product Officer",
            "Senior Product Manager",
            "Director of Product",
        ],
    }

    # Department weights — biased toward customer-facing roles for CRM realism
    DEPARTMENT_WEIGHTS = {
        "Sales": 25,
        "Marketing": 15,
        "Customer Success": 15,
        "Engineering": 10,
        "Product": 10,
        "Operations": 10,
        "Executive": 8,
        "Finance": 7,
    }

    # Pool of CRM contact owners (sales reps)
    CONTACT_OWNERS = [
        "Sarah Chen",
        "Marcus Johnson",
        "Emily Rodriguez",
        "David Kim",
        "Rachel Thompson",
        "James O'Brien",
    ]

    def __init__(self, accounts_csv_path: str, seed: int = None):
        """
        Initialize the contact generator.

        Args:
            accounts_csv_path: Path to the accounts CSV file to read.
            seed: Optional random seed for reproducible data generation.
        """
        self.accounts_csv_path = accounts_csv_path
        self.faker = Faker()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        self.accounts = self._load_accounts()

    def _load_accounts(self) -> List[dict]:
        """
        Load accounts from the CSV file.

        Returns:
            A list of dictionaries, one per account row.

        Raises:
            FileNotFoundError: If the accounts CSV file doesn't exist.
            ValueError: If required columns are missing from the CSV.
        """
        try:
            with open(self.accounts_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Validate required columns exist
                required_columns = {"id", "company_name", "website"}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    missing = required_columns - set(reader.fieldnames or [])
                    raise ValueError(
                        f"Accounts CSV is missing required columns: {missing}"
                    )

                return list(reader)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Accounts file not found: {self.accounts_csv_path}\n"
                "Please generate accounts first (option 1)."
            )

    def _extract_email_domain(self, website: str) -> str:
        """
        Extract an email-friendly domain from a website URL.

        Strips the 'https://www.' prefix that the accounts generator adds.

        Args:
            website: The full website URL (e.g., 'https://www.cloudstack.io')

        Returns:
            The domain string (e.g., 'cloudstack.io')
        """
        domain = website
        for prefix in ["https://www.", "http://www.", "https://", "http://"]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
                break
        return domain

    def _generate_name(self) -> tuple:
        """
        Generate a realistic first and last name.

        Returns:
            A tuple of (first_name, last_name).
        """
        return self.faker.first_name(), self.faker.last_name()

    def _generate_email(self, first_name: str, last_name: str, domain: str) -> str:
        """
        Generate a work email in first.last@domain format.

        Strips apostrophes and spaces from names for clean email addresses.

        Args:
            first_name: Contact's first name.
            last_name: Contact's last name.
            domain: The company's email domain.

        Returns:
            A formatted email address string.
        """
        clean_first = first_name.lower().replace("'", "").replace(" ", "")
        clean_last = last_name.lower().replace("'", "").replace(" ", "")
        return f"{clean_first}.{clean_last}@{domain}"

    def _generate_phone(self) -> str:
        """
        Generate a US phone number.

        Returns:
            A formatted phone number string.
        """
        return self.faker.phone_number()

    def _generate_title_and_department(self) -> tuple:
        """
        Pick a department (weighted) then a random title within it.

        Departments are weighted toward Sales, Marketing, and Customer Success
        to reflect realistic CRM contact distributions.

        Returns:
            A tuple of (title, department).
        """
        departments = list(self.DEPARTMENT_WEIGHTS.keys())
        weights = list(self.DEPARTMENT_WEIGHTS.values())

        department = random.choices(departments, weights=weights, k=1)[0]
        title = random.choice(self.TITLE_BY_DEPARTMENT[department])

        return title, department

    def _generate_contact_count(self) -> int:
        """
        Determine how many contacts to generate for a single account.

        Weighted distribution:
            2 contacts: 35%
            3 contacts: 35%
            4 contacts: 20%
            5 contacts: 10%

        Returns:
            An integer contact count (2-5).
        """
        return random.choices(
            [2, 3, 4, 5],
            weights=[35, 35, 20, 10],
            k=1,
        )[0]

    def generate(self) -> List[Contact]:
        """
        Generate contacts for all loaded accounts.

        Iterates over every account, creates a weighted-random number of
        contacts per account, and assigns globally sequential contact IDs.

        Returns:
            A list of Contact dataclass instances.
        """
        contacts = []
        contact_id = 1

        for account in self.accounts:
            account_id = int(account["id"])
            domain = self._extract_email_domain(account["website"])
            count = self._generate_contact_count()

            for _ in range(count):
                first_name, last_name = self._generate_name()
                email = self._generate_email(first_name, last_name, domain)
                phone = self._generate_phone()
                title, department = self._generate_title_and_department()
                contact_owner = random.choice(self.CONTACT_OWNERS)

                contacts.append(Contact(
                    contact_id=contact_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    title=title,
                    department=department,
                    account_id=account_id,
                    contact_owner=contact_owner,
                ))

                contact_id += 1

        return contacts
