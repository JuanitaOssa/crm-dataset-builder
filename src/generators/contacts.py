"""
Contact Generator Module

Generates realistic contact data for CRM datasets.
Each contact is linked to an existing account via account_id.
Business-specific constants come from the profile.
"""

import csv
import random
from dataclasses import dataclass
from typing import Dict, List, Set

from faker import Faker


@dataclass
class Contact:
    """
    Represents a contact person at a company.

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
    Generates realistic contact data linked to existing accounts.

    Reads an accounts CSV file and generates multiple contacts per account
    with realistic names, emails, titles, and department assignments.

    Example:
        generator = ContactGenerator("output/accounts.csv")
        contacts = generator.generate()
    """

    def __init__(self, accounts_csv_path: str, seed: int = None, profile=None):
        """
        Initialize the contact generator.

        Args:
            accounts_csv_path: Path to the accounts CSV file to read.
            seed: Optional random seed for reproducible data generation.
            profile: A BaseProfile instance. Defaults to B2BSaaSProfile.
        """
        self.accounts_csv_path = accounts_csv_path
        self.faker = Faker()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        if profile is None:
            from profiles.b2b_saas import B2BSaaSProfile
            profile = B2BSaaSProfile()
        self.profile = profile

        self._used_emails: Dict[str, Set[str]] = {}
        self.accounts = self._load_accounts()

    def _load_accounts(self) -> List[dict]:
        """Load accounts from the CSV file."""
        try:
            with open(self.accounts_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
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
        """Extract an email-friendly domain from a website URL."""
        domain = website
        for prefix in ["https://www.", "http://www.", "https://", "http://"]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
                break
        return domain

    def _generate_name(self) -> tuple:
        """Generate a realistic first and last name."""
        return self.faker.first_name(), self.faker.last_name()

    def _generate_email(self, first_name: str, last_name: str, domain: str) -> str:
        """Generate a unique work email in first.last@domain format."""
        clean_first = first_name.lower().replace("'", "").replace(" ", "")
        clean_last = last_name.lower().replace("'", "").replace(" ", "")
        base_local = f"{clean_first}.{clean_last}"

        if domain not in self._used_emails:
            self._used_emails[domain] = set()

        local = base_local
        counter = 2
        while local in self._used_emails[domain]:
            local = f"{base_local}{counter}"
            counter += 1

        self._used_emails[domain].add(local)
        return f"{local}@{domain}"

    def _generate_phone(self) -> str:
        """Generate a US phone number in consistent (XXX) XXX-XXXX format."""
        area = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"({area}) {prefix}-{line}"

    def _generate_title_and_department(self) -> tuple:
        """Pick a department (weighted) then a random title within it."""
        departments = list(self.profile.department_weights.keys())
        weights = list(self.profile.department_weights.values())

        department = random.choices(departments, weights=weights, k=1)[0]
        title = random.choice(self.profile.title_by_department[department])

        return title, department

    def _generate_contact_count(self) -> int:
        """Determine how many contacts to generate for a single account."""
        counts, weights = self.profile.contacts_per_account_weights
        return random.choices(counts, weights=weights, k=1)[0]

    def generate(self) -> List[Contact]:
        """
        Generate contacts for all loaded accounts.

        Iterates over every account, creates a weighted-random number of
        contacts per account, and assigns globally sequential contact IDs.
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
                contact_owner = random.choice(self.profile.sales_reps)

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
