"""
Deal/Opportunity Generator Module

Generates realistic B2B SaaS deal data for CRM datasets.
Each deal is linked to an existing account and contact, with three
pipelines (New Business, Renewal, Expansion) and realistic outcome
rates, stage progressions, and date relationships.
"""

import csv
import datetime
import random
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class Deal:
    """
    Represents a CRM deal/opportunity.

    Attributes:
        deal_id: Unique sequential identifier
        deal_name: Human-readable name (CompanyName - Pipeline - N)
        account_id: Foreign key to accounts CSV
        contact_id: Foreign key to contacts CSV
        pipeline: New Business, Renewal, or Expansion
        segment: SMB, Mid-Market, or Enterprise
        stage: Current pipeline stage
        amount: Deal value in USD
        created_date: When the deal was created (YYYY-MM-DD)
        close_date: When the deal closed (YYYY-MM-DD), empty for Active
        deal_status: Won, Lost, or Active
        deal_owner: Sales rep who owns the deal
        probability: Win probability percentage based on stage
        loss_reason: Reason for loss, empty for Won/Active deals
    """

    deal_id: int
    deal_name: str
    account_id: int
    contact_id: int
    pipeline: str
    segment: str
    stage: str
    amount: int
    created_date: str
    close_date: str
    deal_status: str
    deal_owner: str
    probability: int
    loss_reason: str


class DealGenerator:
    """
    Generates realistic B2B SaaS deal data linked to existing accounts
    and contacts.

    Uses a three-phase algorithm:
      1. New Business deals for ~70% of accounts
      2. Renewals and Expansions spawned from won NB deals
      3. Sort all deals by date and assign sequential IDs

    Example:
        generator = DealGenerator("output/accounts.csv", "output/contacts.csv")
        deals = generator.generate()
    """

    # --- Date boundaries ---
    DATE_RANGE_START = datetime.date(2023, 1, 1)
    DATE_RANGE_END = datetime.date(2026, 2, 1)
    ACTIVE_WINDOW_START = datetime.date(2025, 8, 1)

    # --- Sales reps (same as ContactGenerator.CONTACT_OWNERS) ---
    DEAL_OWNERS = [
        "Sarah Chen",
        "Marcus Johnson",
        "Emily Rodriguez",
        "David Kim",
        "Rachel Thompson",
        "James O'Brien",
    ]

    # --- ACV ranges by segment ---
    ACV_RANGES = {
        "SMB": (8_000, 25_000),
        "Mid-Market": (25_000, 100_000),
        "Enterprise": (100_000, 350_000),
    }

    # --- Ordered stages per pipeline ---
    STAGES = {
        "New Business": [
            "Lead",
            "Qualified",
            "Discovery",
            "Demo/Evaluation",
            "Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ],
        "Renewal": [
            "Upcoming Renewal",
            "Customer Review",
            "Renewal Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ],
        "Expansion": [
            "Expansion Identified",
            "Needs Analysis",
            "Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ],
    }

    # --- Outcome weights: Won / Lost / Active ---
    OUTCOME_RATES = {
        "New Business": {"Won": 22, "Lost": 58, "Active": 20},
        "Renewal": {"Won": 85, "Lost": 10, "Active": 5},
        "Expansion": {"Won": 45, "Lost": 30, "Active": 25},
    }

    # --- Sales cycle lengths (days) ---
    NB_CYCLE_DAYS = {
        "SMB": (30, 45),
        "Mid-Market": (60, 90),
        "Enterprise": (90, 180),
    }
    RENEWAL_CYCLE_DAYS = (15, 30)
    EXPANSION_CYCLE_DAYS = (30, 60)

    # --- Loss reason weights ---
    LOSS_REASONS_DEFAULT_WEIGHTS = {
        "Budget Constraints": 20,
        "Chose Competitor": 25,
        "No Decision / Timing": 20,
        "Product Fit": 15,
        "Security Review Failed": 5,
        "Internal Reorganization": 10,
        "Champion Left": 5,
    }

    LOSS_REASONS_ENTERPRISE_WEIGHTS = {
        "Budget Constraints": 25,
        "Chose Competitor": 15,
        "No Decision / Timing": 15,
        "Product Fit": 10,
        "Security Review Failed": 20,
        "Internal Reorganization": 10,
        "Champion Left": 5,
    }

    # --- Stage -> probability % per pipeline ---
    STAGE_PROBABILITIES = {
        "New Business": {
            "Lead": 5,
            "Qualified": 10,
            "Discovery": 20,
            "Demo/Evaluation": 35,
            "Proposal": 50,
            "Negotiation": 70,
            "Closed Won": 100,
            "Closed Lost": 0,
        },
        "Renewal": {
            "Upcoming Renewal": 70,
            "Customer Review": 80,
            "Renewal Proposal": 85,
            "Negotiation": 90,
            "Closed Won": 100,
            "Closed Lost": 0,
        },
        "Expansion": {
            "Expansion Identified": 15,
            "Needs Analysis": 30,
            "Proposal": 50,
            "Negotiation": 65,
            "Closed Won": 100,
            "Closed Lost": 0,
        },
    }

    def __init__(
        self,
        accounts_csv_path: str,
        contacts_csv_path: str,
        seed: int = None,
    ):
        if seed is not None:
            random.seed(seed)

        self.accounts = self._load_accounts(accounts_csv_path)
        self.contacts = self._load_contacts(contacts_csv_path)

        self.contacts_by_account: Dict[int, List[dict]] = {}
        for c in self.contacts:
            aid = int(c["account_id"])
            self.contacts_by_account.setdefault(aid, []).append(c)

        self.account_segments: Dict[int, str] = {}
        self.account_names: Dict[int, str] = {}
        for a in self.accounts:
            aid = int(a["id"])
            self.account_segments[aid] = self._classify_segment(
                int(a["employee_count"])
            )
            self.account_names[aid] = a["company_name"]

    # ------------------------------------------------------------------ #
    #  CSV loaders                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_accounts(path: str) -> List[dict]:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"id", "company_name", "employee_count"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Accounts CSV missing columns: {missing}")
            return list(reader)

    @staticmethod
    def _load_contacts(path: str) -> List[dict]:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"contact_id", "account_id"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Contacts CSV missing columns: {missing}")
            return list(reader)

    # ------------------------------------------------------------------ #
    #  Classifiers / pickers                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _classify_segment(employee_count: int) -> str:
        if employee_count < 200:
            return "SMB"
        elif employee_count <= 1000:
            return "Mid-Market"
        return "Enterprise"

    def _pick_outcome(self, pipeline: str) -> str:
        rates = self.OUTCOME_RATES[pipeline]
        return random.choices(
            list(rates.keys()), weights=list(rates.values()), k=1
        )[0]

    def _pick_loss_reason(self, segment: str) -> str:
        weights = (
            self.LOSS_REASONS_ENTERPRISE_WEIGHTS
            if segment == "Enterprise"
            else self.LOSS_REASONS_DEFAULT_WEIGHTS
        )
        return random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

    def _pick_active_stage(self, pipeline: str) -> str:
        non_terminal = [
            s
            for s in self.STAGES[pipeline]
            if s not in ("Closed Won", "Closed Lost")
        ]
        return random.choice(non_terminal)

    # ------------------------------------------------------------------ #
    #  Amount generation                                                  #
    # ------------------------------------------------------------------ #

    def _generate_amount(
        self, pipeline: str, segment: str, original_amount: int = 0
    ) -> int:
        if pipeline == "New Business":
            lo, hi = self.ACV_RANGES[segment]
            return round(random.randint(lo, hi) / 500) * 500
        elif pipeline == "Renewal":
            raw = int(original_amount * random.uniform(0.95, 1.05))
            return round(raw / 100) * 100
        else:  # Expansion
            raw = int(original_amount * random.uniform(0.20, 0.50))
            return round(raw / 100) * 100

    # ------------------------------------------------------------------ #
    #  Date helpers                                                       #
    # ------------------------------------------------------------------ #

    def _random_date(
        self, start: datetime.date, end: datetime.date
    ) -> datetime.date:
        if start >= end:
            return start
        return start + datetime.timedelta(
            days=random.randint(0, (end - start).days)
        )

    def _cycle_days(self, pipeline: str, segment: str) -> int:
        if pipeline == "New Business":
            lo, hi = self.NB_CYCLE_DAYS[segment]
        elif pipeline == "Renewal":
            lo, hi = self.RENEWAL_CYCLE_DAYS
        else:
            lo, hi = self.EXPANSION_CYCLE_DAYS
        return random.randint(lo, hi)

    # ------------------------------------------------------------------ #
    #  Deal-name helper                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_deal_name(
        company_name: str, pipeline: str, seq: int
    ) -> str:
        return f"{company_name} - {pipeline} - {seq}"

    # ------------------------------------------------------------------ #
    #  Account / deal-count selection                                     #
    # ------------------------------------------------------------------ #

    def _select_accounts_with_deals(self) -> List[int]:
        all_ids = [int(a["id"]) for a in self.accounts]
        k = max(1, round(len(all_ids) * 0.70))
        return sorted(random.sample(all_ids, k))

    @staticmethod
    def _generate_nb_deal_count() -> int:
        return random.choices([1, 2, 3], weights=[50, 35, 15], k=1)[0]

    # ------------------------------------------------------------------ #
    #  Follow-up deal helper (Renewal / Expansion)                        #
    # ------------------------------------------------------------------ #

    def _generate_followup_deal(
        self,
        deals: List[Deal],
        aid: int,
        company: str,
        segment: str,
        pipeline: str,
        created: datetime.date,
        original_amount: int,
        next_seq: Callable[[int], int],
    ) -> None:
        """Generate a single Renewal or Expansion deal and append it."""
        seq = next_seq(aid)
        contact = random.choice(self.contacts_by_account[aid])
        cid = int(contact["contact_id"])
        owner = random.choice(self.DEAL_OWNERS)
        amount = self._generate_amount(pipeline, segment, original_amount)

        outcome = self._pick_outcome(pipeline)

        # Active-window enforcement: old deals can't stay Active
        if outcome == "Active" and created < self.ACTIVE_WINDOW_START:
            outcome = random.choices(
                ["Won", "Lost"],
                weights=[85, 15] if pipeline == "Renewal" else [60, 40],
                k=1,
            )[0]

        if outcome == "Active":
            stage = self._pick_active_stage(pipeline)
            deals.append(Deal(
                deal_id=0,
                deal_name=self._generate_deal_name(company, pipeline, seq),
                account_id=aid,
                contact_id=cid,
                pipeline=pipeline,
                segment=segment,
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date="",
                deal_status="Active",
                deal_owner=owner,
                probability=self.STAGE_PROBABILITIES[pipeline][stage],
                loss_reason="",
            ))
            return

        # Won or Lost
        cycle = self._cycle_days(pipeline, segment)
        close = created + datetime.timedelta(days=cycle)

        if close > self.DATE_RANGE_END:
            # Close-date overflow -> convert to Active
            stage = self._pick_active_stage(pipeline)
            deals.append(Deal(
                deal_id=0,
                deal_name=self._generate_deal_name(company, pipeline, seq),
                account_id=aid,
                contact_id=cid,
                pipeline=pipeline,
                segment=segment,
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date="",
                deal_status="Active",
                deal_owner=owner,
                probability=self.STAGE_PROBABILITIES[pipeline][stage],
                loss_reason="",
            ))
            return

        if outcome == "Won":
            stage, prob, reason = "Closed Won", 100, ""
        else:
            stage, prob, reason = "Closed Lost", 0, self._pick_loss_reason(segment)

        deals.append(Deal(
            deal_id=0,
            deal_name=self._generate_deal_name(company, pipeline, seq),
            account_id=aid,
            contact_id=cid,
            pipeline=pipeline,
            segment=segment,
            stage=stage,
            amount=amount,
            created_date=created.isoformat(),
            close_date=close.isoformat(),
            deal_status=outcome,
            deal_owner=owner,
            probability=prob,
            loss_reason=reason,
        ))

    # ------------------------------------------------------------------ #
    #  Core three-phase generation                                        #
    # ------------------------------------------------------------------ #

    def generate(self) -> List[Deal]:
        deals: List[Deal] = []
        won_nb: Dict[int, list] = {}   # account_id -> [{close_date, amount}]
        seq_counter: Dict[int, int] = {}

        def next_seq(account_id: int) -> int:
            seq_counter[account_id] = seq_counter.get(account_id, 0) + 1
            return seq_counter[account_id]

        selected = self._select_accounts_with_deals()

        # ---- Phase 1: New Business deals ----
        for aid in selected:
            if aid not in self.contacts_by_account:
                print(f"  [warning] Account {aid} has no contacts, skipping.")
                continue

            segment = self.account_segments[aid]
            company = self.account_names[aid]

            for _ in range(self._generate_nb_deal_count()):
                seq = next_seq(aid)
                contact = random.choice(self.contacts_by_account[aid])
                cid = int(contact["contact_id"])
                owner = random.choice(self.DEAL_OWNERS)
                amount = self._generate_amount("New Business", segment)

                outcome = self._pick_outcome("New Business")

                if outcome == "Active":
                    created = self._random_date(
                        self.ACTIVE_WINDOW_START, self.DATE_RANGE_END
                    )
                    stage = self._pick_active_stage("New Business")
                    deals.append(Deal(
                        deal_id=0,
                        deal_name=self._generate_deal_name(
                            company, "New Business", seq
                        ),
                        account_id=aid,
                        contact_id=cid,
                        pipeline="New Business",
                        segment=segment,
                        stage=stage,
                        amount=amount,
                        created_date=created.isoformat(),
                        close_date="",
                        deal_status="Active",
                        deal_owner=owner,
                        probability=self.STAGE_PROBABILITIES["New Business"][
                            stage
                        ],
                        loss_reason="",
                    ))
                    continue

                # Won or Lost — pick cycle, compute dates
                cycle = self._cycle_days("New Business", segment)
                latest_start = self.DATE_RANGE_END - datetime.timedelta(
                    days=cycle
                )

                if latest_start <= self.DATE_RANGE_START:
                    # Can't fit a full cycle — force Active
                    created = self._random_date(
                        self.ACTIVE_WINDOW_START, self.DATE_RANGE_END
                    )
                    stage = self._pick_active_stage("New Business")
                    deals.append(Deal(
                        deal_id=0,
                        deal_name=self._generate_deal_name(
                            company, "New Business", seq
                        ),
                        account_id=aid,
                        contact_id=cid,
                        pipeline="New Business",
                        segment=segment,
                        stage=stage,
                        amount=amount,
                        created_date=created.isoformat(),
                        close_date="",
                        deal_status="Active",
                        deal_owner=owner,
                        probability=self.STAGE_PROBABILITIES["New Business"][
                            stage
                        ],
                        loss_reason="",
                    ))
                    continue

                created = self._random_date(self.DATE_RANGE_START, latest_start)
                close = created + datetime.timedelta(days=cycle)

                if outcome == "Won":
                    stage, prob, reason = "Closed Won", 100, ""
                    won_nb.setdefault(aid, []).append(
                        {"close_date": close, "amount": amount}
                    )
                else:
                    stage, prob, reason = (
                        "Closed Lost",
                        0,
                        self._pick_loss_reason(segment),
                    )

                deals.append(Deal(
                    deal_id=0,
                    deal_name=self._generate_deal_name(
                        company, "New Business", seq
                    ),
                    account_id=aid,
                    contact_id=cid,
                    pipeline="New Business",
                    segment=segment,
                    stage=stage,
                    amount=amount,
                    created_date=created.isoformat(),
                    close_date=close.isoformat(),
                    deal_status=outcome,
                    deal_owner=owner,
                    probability=prob,
                    loss_reason=reason,
                ))

        # ---- Phase 2: Renewals + Expansions ----
        for aid, wins in won_nb.items():
            segment = self.account_segments[aid]
            company = self.account_names[aid]

            for nb in wins:
                nb_close = nb["close_date"]
                nb_amount = nb["amount"]

                # Renewal (~12 months later)
                r_created = nb_close + datetime.timedelta(
                    days=random.randint(350, 380)
                )
                if r_created <= self.DATE_RANGE_END:
                    self._generate_followup_deal(
                        deals, aid, company, segment, "Renewal",
                        r_created, nb_amount, next_seq,
                    )

                # Expansion (50% chance, 3-9 months later)
                if random.random() < 0.50:
                    e_created = nb_close + datetime.timedelta(
                        days=random.randint(90, 270)
                    )
                    if e_created <= self.DATE_RANGE_END:
                        self._generate_followup_deal(
                            deals, aid, company, segment, "Expansion",
                            e_created, nb_amount, next_seq,
                        )

        # ---- Phase 3: Sort and assign sequential IDs ----
        deals.sort(key=lambda d: (d.created_date, d.account_id))
        for idx, deal in enumerate(deals, start=1):
            deal.deal_id = idx

        return deals
