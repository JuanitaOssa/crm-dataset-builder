"""
Account Generator Module

Generates realistic company data for CRM datasets.
Business-specific constants (names, industries, etc.) come from the profile;
this module contains only the distribution logic.
"""

import random
from dataclasses import dataclass
from typing import List

from faker import Faker


@dataclass
class Account:
    """
    Represents a company account.

    Attributes:
        id: Unique identifier for the account
        company_name: Name of the company
        industry: Industry/sector the company operates in
        employee_count: Number of employees
        annual_revenue: Annual revenue in USD
        street_address: Street address
        city: City name
        state: US state (full name)
        zip_code: ZIP code
        country: Country (default: United States)
        region: Geographic region derived from state
        founded_year: Year the company was founded
        website: Company website URL
        description: Brief company description
    """
    id: int
    company_name: str
    industry: str
    employee_count: int
    annual_revenue: int
    street_address: str
    city: str
    state: str
    zip_code: str
    country: str
    region: str
    founded_year: int
    website: str
    description: str


class AccountGenerator:
    """
    Generates realistic company account data using a business-type profile.

    Uses a combination of Faker library and profile-provided word lists to
    create believable company names and attributes.

    Example:
        generator = AccountGenerator()
        accounts = generator.generate(100)
    """

    # US state to region mapping (geographic, not business-specific)
    STATE_TO_REGION = {
        "Alabama": "Southeast", "Alaska": "Northwest", "Arizona": "Southwest",
        "Arkansas": "Southeast", "California": "West", "Colorado": "West",
        "Connecticut": "Northeast", "Delaware": "East", "Florida": "Southeast",
        "Georgia": "Southeast", "Hawaii": "West", "Idaho": "Northwest",
        "Illinois": "Midwest", "Indiana": "Midwest", "Iowa": "Midwest",
        "Kansas": "Central", "Kentucky": "Southeast", "Louisiana": "Southeast",
        "Maine": "Northeast", "Maryland": "East", "Massachusetts": "Northeast",
        "Michigan": "Midwest", "Minnesota": "Midwest", "Mississippi": "Southeast",
        "Missouri": "Midwest", "Montana": "Northwest", "Nebraska": "Central",
        "Nevada": "West", "New Hampshire": "Northeast", "New Jersey": "Northeast",
        "New Mexico": "Southwest", "New York": "Northeast",
        "North Carolina": "Southeast", "North Dakota": "Central",
        "Ohio": "Midwest", "Oklahoma": "Southwest", "Oregon": "Northwest",
        "Pennsylvania": "East", "Rhode Island": "Northeast",
        "South Carolina": "Southeast", "South Dakota": "Central",
        "Tennessee": "Southeast", "Texas": "Southwest", "Utah": "West",
        "Vermont": "Northeast", "Virginia": "Southeast", "Washington": "Northwest",
        "West Virginia": "East", "Wisconsin": "Midwest", "Wyoming": "Northwest",
        "District of Columbia": "East",
    }

    def __init__(self, seed: int = None, profile=None):
        """
        Initialize the account generator.

        Args:
            seed: Optional random seed for reproducible data generation.
            profile: A BaseProfile instance. Defaults to B2BSaaSProfile.
        """
        self.faker = Faker()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        if profile is None:
            from profiles.b2b_saas import B2BSaaSProfile
            profile = B2BSaaSProfile()
        self.profile = profile

    def _generate_company_name(self) -> str:
        """
        Generate a realistic company name using profile-provided word lists.

        Uses strategies defined by the profile (prefix_suffix, prefix_word, faker).
        """
        strategy = random.choice(self.profile.company_name_strategies)

        if strategy == "prefix_suffix":
            prefix = random.choice(self.profile.name_prefixes)
            suffix = random.choice(self.profile.name_suffixes)
            return f"{prefix}{suffix}"

        elif strategy == "prefix_word":
            prefix = random.choice(self.profile.name_prefixes)
            word = self.faker.word().capitalize()
            return f"{prefix}{word}"

        else:
            name = self.faker.company()
            for suffix in [" Inc", " LLC", " Ltd", " and Sons", " Group", " PLC"]:
                name = name.replace(suffix, "")
            return name.strip()

    def _generate_employee_count(self) -> int:
        """Generate a realistic employee count using profile-weighted tiers."""
        tiers = []
        weights = []
        for min_emp, max_emp, weight in self.profile.employee_tiers:
            tiers.append((min_emp, max_emp))
            weights.append(weight)

        selected_tier = random.choices(tiers, weights=weights)[0]
        return random.randint(selected_tier[0], selected_tier[1])

    def _generate_annual_revenue(self, employee_count: int) -> int:
        """
        Generate realistic annual revenue based on employee count.

        Revenue is correlated with employee count using a revenue-per-employee
        multiplier from the profile.
        """
        revenue_per_employee = random.randint(
            self.profile.revenue_per_employee_range[0],
            self.profile.revenue_per_employee_range[1]
        )

        revenue = employee_count * revenue_per_employee
        revenue = max(100000, min(revenue, 50000000))
        return round(revenue, -4)

    def _generate_website(self, company_name: str) -> str:
        """Generate a website URL based on company name."""
        clean_name = "".join(c for c in company_name if c.isalnum())
        clean_name = clean_name.lower()
        tld = random.choice(self.profile.website_tlds)
        return f"https://www.{clean_name}{tld}"

    def _generate_description(self, industry: str) -> str:
        """Generate a brief company description based on industry."""
        template = random.choice(self.profile.description_templates)
        return template.format(industry=industry.lower())

    def _generate_address(self) -> dict:
        """Generate a realistic US address with state-derived region."""
        state = random.choice(list(self.STATE_TO_REGION.keys()))
        return {
            "street_address": self.faker.street_address(),
            "city": self.faker.city(),
            "state": state,
            "zip_code": self.faker.zipcode(),
            "country": "United States",
            "region": self.STATE_TO_REGION[state],
        }

    def generate_one(self, id: int) -> Account:
        """
        Generate a single account with all attributes.

        Args:
            id: Unique identifier for this account.

        Returns:
            An Account dataclass instance with all fields populated.
        """
        company_name = self._generate_company_name()
        industry = random.choice(self.profile.industries)
        employee_count = self._generate_employee_count()
        annual_revenue = self._generate_annual_revenue(employee_count)
        address = self._generate_address()
        yr_min, yr_max = self.profile.founded_year_range
        founded_year = random.randint(yr_min, yr_max)
        website = self._generate_website(company_name)
        description = self._generate_description(industry)

        return Account(
            id=id,
            company_name=company_name,
            industry=industry,
            employee_count=employee_count,
            annual_revenue=annual_revenue,
            street_address=address["street_address"],
            city=address["city"],
            state=address["state"],
            zip_code=address["zip_code"],
            country=address["country"],
            region=address["region"],
            founded_year=founded_year,
            website=website,
            description=description,
        )

    def generate(self, count: int) -> List[Account]:
        """
        Generate multiple accounts.

        Args:
            count: Number of accounts to generate.

        Returns:
            A list of Account instances.
        """
        return [self.generate_one(id=i + 1) for i in range(count)]
