"""
Account Generator Module

Generates realistic B2B SaaS company data for CRM datasets.
Includes company names, industries, employee counts, revenue, and more.
"""

import random
from dataclasses import dataclass
from typing import List

from faker import Faker


@dataclass
class Account:
    """
    Represents a B2B SaaS company account.

    Attributes:
        id: Unique identifier for the account
        company_name: Name of the company
        industry: Industry/sector the company operates in
        employee_count: Number of employees
        annual_revenue: Annual revenue in USD
        region: Geographic region (US-focused)
        founded_year: Year the company was founded
        website: Company website URL
        description: Brief company description
    """
    id: int
    company_name: str
    industry: str
    employee_count: int
    annual_revenue: int
    region: str
    founded_year: int
    website: str
    description: str


class AccountGenerator:
    """
    Generates realistic B2B SaaS company account data.

    Uses a combination of Faker library and custom word lists to create
    believable tech company names and attributes.

    Example:
        generator = AccountGenerator()
        accounts = generator.generate(100)
    """

    # Tech/SaaS style name prefixes - common patterns in startup names
    NAME_PREFIXES = [
        "Cloud", "Data", "Cyber", "Tech", "Net", "Digi", "Info", "Smart",
        "Sync", "Flow", "Stack", "Grid", "Node", "Pixel", "Byte", "Core",
        "Meta", "Hyper", "Ultra", "Prime", "Alpha", "Beta", "Quantum",
        "Vector", "Logic", "Signal", "Pulse", "Wave", "Spark", "Flux"
    ]

    # Tech/SaaS style name suffixes
    NAME_SUFFIXES = [
        "Labs", "Systems", "Solutions", "Tech", "Software", "IO", "AI",
        "Analytics", "Cloud", "Networks", "Dynamics", "Ware", "Works",
        "Hub", "Base", "Stack", "Logic", "Mind", "Sense", "Force",
        "Bridge", "Link", "Path", "Scale", "Shift", "Stream", "Vault"
    ]

    # Tech-focused industries for B2B SaaS companies
    INDUSTRIES = [
        "Enterprise Software",
        "Cloud Infrastructure",
        "Cybersecurity",
        "Data Analytics",
        "Artificial Intelligence",
        "Developer Tools",
        "Marketing Technology",
        "Sales Enablement",
        "Human Resources Tech",
        "Financial Technology",
        "Healthcare Technology",
        "Supply Chain Software",
        "Customer Success",
        "Business Intelligence",
        "E-commerce Platform",
        "Communication & Collaboration",
        "Project Management",
        "Identity & Access Management",
        "DevOps & CI/CD",
        "API & Integration Platform"
    ]

    # US geographic regions
    REGIONS = [
        "West",
        "East",
        "Central",
        "Southwest",
        "Southeast",
        "Northwest",
        "Northeast",
        "Midwest"
    ]

    # Employee count tiers with weights (smaller companies more common)
    # Format: (min, max, weight)
    EMPLOYEE_TIERS = [
        (50, 100, 30),      # Small startups - most common
        (101, 250, 25),     # Growing startups
        (251, 500, 20),     # Mid-size
        (501, 1000, 15),    # Larger mid-size
        (1001, 2500, 7),    # Enterprise
        (2501, 5000, 3),    # Large enterprise - least common
    ]

    # Revenue ranges correlated with employee count (revenue per employee varies)
    # Base revenue per employee ranges from $50K to $200K for SaaS companies
    REVENUE_PER_EMPLOYEE_RANGE = (50000, 200000)

    def __init__(self, seed: int = None):
        """
        Initialize the account generator.

        Args:
            seed: Optional random seed for reproducible data generation.
                  Useful for testing or creating consistent datasets.
        """
        # Initialize Faker for generating realistic business data
        self.faker = Faker()

        # Set seeds for reproducibility if provided
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

    def _generate_company_name(self) -> str:
        """
        Generate a realistic tech/SaaS company name.

        Uses three strategies randomly:
        1. Prefix + Suffix (e.g., "CloudStack", "DataVault")
        2. Prefix + random word (e.g., "SyncPoint", "FlowMetrics")
        3. Faker company name (for variety)

        Returns:
            A generated company name string.
        """
        strategy = random.choice(["prefix_suffix", "prefix_word", "faker"])

        if strategy == "prefix_suffix":
            # Combine a tech prefix with a tech suffix
            prefix = random.choice(self.NAME_PREFIXES)
            suffix = random.choice(self.NAME_SUFFIXES)
            return f"{prefix}{suffix}"

        elif strategy == "prefix_word":
            # Combine a tech prefix with a Faker word
            prefix = random.choice(self.NAME_PREFIXES)
            # Use catch_phrase_noun for tech-sounding words
            word = self.faker.word().capitalize()
            return f"{prefix}{word}"

        else:
            # Use Faker's company generator for variety
            # Remove common suffixes like "Inc" or "LLC" for cleaner names
            name = self.faker.company()
            for suffix in [" Inc", " LLC", " Ltd", " and Sons", " Group", " PLC"]:
                name = name.replace(suffix, "")
            return name.strip()

    def _generate_employee_count(self) -> int:
        """
        Generate a realistic employee count using weighted tiers.

        Smaller companies are more common than large enterprises,
        reflecting real-world distribution of B2B SaaS companies.

        Returns:
            An integer employee count between 50 and 5000.
        """
        # Build weighted list of tiers
        tiers = []
        weights = []
        for min_emp, max_emp, weight in self.EMPLOYEE_TIERS:
            tiers.append((min_emp, max_emp))
            weights.append(weight)

        # Select a tier based on weights
        selected_tier = random.choices(tiers, weights=weights)[0]

        # Generate random count within the selected tier
        return random.randint(selected_tier[0], selected_tier[1])

    def _generate_annual_revenue(self, employee_count: int) -> int:
        """
        Generate realistic annual revenue based on employee count.

        Revenue is correlated with employee count using a revenue-per-employee
        multiplier, which is typical for SaaS companies ($50K-$200K per employee).

        Args:
            employee_count: Number of employees at the company.

        Returns:
            Annual revenue in USD, rounded to nearest $10,000.
        """
        # Calculate revenue per employee (varies by company efficiency)
        revenue_per_employee = random.randint(
            self.REVENUE_PER_EMPLOYEE_RANGE[0],
            self.REVENUE_PER_EMPLOYEE_RANGE[1]
        )

        # Calculate base revenue
        revenue = employee_count * revenue_per_employee

        # Ensure revenue stays within our target range ($100K - $50M)
        revenue = max(100000, min(revenue, 50000000))

        # Round to nearest $10,000 for cleaner numbers
        return round(revenue, -4)

    def _generate_website(self, company_name: str) -> str:
        """
        Generate a website URL based on company name.

        Cleans the company name and creates a plausible domain.

        Args:
            company_name: The company's name.

        Returns:
            A website URL string.
        """
        # Clean the company name for use in URL
        # Remove special characters and spaces, convert to lowercase
        clean_name = "".join(c for c in company_name if c.isalnum())
        clean_name = clean_name.lower()

        # Randomly choose a TLD (top-level domain)
        tld = random.choice([".com", ".io", ".co", ".ai", ".tech"])

        return f"https://www.{clean_name}{tld}"

    def _generate_description(self, industry: str) -> str:
        """
        Generate a brief company description based on industry.

        Args:
            industry: The company's industry/sector.

        Returns:
            A brief description string.
        """
        # Templates for company descriptions
        templates = [
            f"Leading provider of {industry.lower()} solutions for modern enterprises.",
            f"Innovative {industry.lower()} platform helping businesses scale.",
            f"Next-generation {industry.lower()} tools for growing teams.",
            f"Enterprise-grade {industry.lower()} solutions with a focus on simplicity.",
            f"Transforming how businesses approach {industry.lower()}.",
        ]

        return random.choice(templates)

    def generate_one(self, id: int) -> Account:
        """
        Generate a single account with all attributes.

        Args:
            id: Unique identifier for this account.

        Returns:
            An Account dataclass instance with all fields populated.
        """
        # Generate core attributes
        company_name = self._generate_company_name()
        industry = random.choice(self.INDUSTRIES)
        employee_count = self._generate_employee_count()

        # Generate dependent attributes
        annual_revenue = self._generate_annual_revenue(employee_count)

        # Generate remaining attributes
        region = random.choice(self.REGIONS)
        founded_year = random.randint(2010, 2024)
        website = self._generate_website(company_name)
        description = self._generate_description(industry)

        return Account(
            id=id,
            company_name=company_name,
            industry=industry,
            employee_count=employee_count,
            annual_revenue=annual_revenue,
            region=region,
            founded_year=founded_year,
            website=website,
            description=description
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
