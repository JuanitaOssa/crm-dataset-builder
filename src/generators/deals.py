"""
Deal/Opportunity Generator Module

Generates realistic deal data for CRM datasets.
Each deal is linked to an existing account and contact, with profile-driven
pipelines, outcome rates, stage progressions, and date relationships.
"""

import csv
import datetime
import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Deal:
    """
    Represents a CRM deal/opportunity.

    Attributes:
        deal_id: Unique sequential identifier
        deal_name: Human-readable name (format varies by profile)
        account_id: Foreign key to accounts CSV
        contact_id: Foreign key to contacts CSV
        pipeline: Pipeline name (profile-specific)
        segment: Account segment (e.g. SMB, Mid-Market, Enterprise)
        stage: Current pipeline stage
        amount: Deal value in USD
        created_date: When the deal was created (YYYY-MM-DD)
        close_date: When the deal closed (YYYY-MM-DD), empty for Open deals
        deal_status: Won, Lost, or Open (derived from stage)
        deal_owner: Sales rep who owns the deal
        loss_reason: Reason for loss, empty for Won/Open deals
        subscription_type: Subscription type (e.g. Annual/Monthly), empty if N/A
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
    loss_reason: str
    subscription_type: str = ""


class DealGenerator:
    """
    Generates realistic deal data linked to existing accounts and contacts.

    Uses a multi-phase algorithm:
      1. New Business deals for a fraction of accounts
      1b. Self-Serve deals (if profile supports it)
      2. Renewals and Expansions spawned from won deals
      3. Sort all deals by date, assign sequential IDs and names
    """

    # --- Date boundaries ---
    DATE_RANGE_START = datetime.date(2023, 1, 1)
    DATE_RANGE_END = datetime.date(2026, 2, 1)
    ACTIVE_WINDOW_START = datetime.date(2025, 8, 1)

    def __init__(
        self,
        accounts_csv_path: str,
        contacts_csv_path: str,
        seed: int = None,
        profile=None,
    ):
        if seed is not None:
            random.seed(seed)

        if profile is None:
            from profiles.b2b_saas import B2BSaaSProfile
            profile = B2BSaaSProfile()
        self.profile = profile

        self.accounts = self._load_accounts(accounts_csv_path)
        self.contacts = self._load_contacts(contacts_csv_path)

        self.contacts_by_account: Dict[int, List[dict]] = {}
        for c in self.contacts:
            aid = int(c["account_id"])
            self.contacts_by_account.setdefault(aid, []).append(c)

        self._assigned_contacts: Dict[int, set] = {}

        self.account_segments: Dict[int, str] = {}
        self.account_names: Dict[int, str] = {}
        for a in self.accounts:
            aid = int(a["id"])
            self.account_segments[aid] = self.profile.classify_segment(
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
    def _derive_status(stage: str) -> str:
        """Derive deal_status from the stage name."""
        if stage == "Closed Won":
            return "Won"
        elif stage == "Closed Lost":
            return "Lost"
        return "Open"

    def _pick_outcome(self, pipeline: str) -> str:
        rates = self.profile.outcome_rates[pipeline]
        return random.choices(
            list(rates.keys()), weights=list(rates.values()), k=1
        )[0]

    def _pick_loss_reason(self, segment: str) -> str:
        weights = (
            self.profile.loss_reasons_enterprise
            if segment == "Enterprise"
            else self.profile.loss_reasons_default
        )
        return random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

    def _pick_contact(self, aid: int) -> dict:
        """
        Pick a contact for a deal, preferring contacts not yet assigned
        to any deal at this account. Falls back to random if all assigned.
        """
        candidates = self.contacts_by_account[aid]
        assigned = self._assigned_contacts.get(aid, set())
        unassigned = [c for c in candidates if int(c["contact_id"]) not in assigned]
        contact = random.choice(unassigned) if unassigned else random.choice(candidates)
        self._assigned_contacts.setdefault(aid, set()).add(int(contact["contact_id"]))
        return contact

    def _pick_active_stage(self, pipeline: str) -> str:
        """Pick an open-deal stage using weighted probabilities."""
        weights = self.profile.active_stage_weights[pipeline]
        return random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

    # ------------------------------------------------------------------ #
    #  Amount generation                                                  #
    # ------------------------------------------------------------------ #

    def _generate_amount(
        self, pipeline: str, segment: str, original_amount: int = 0
    ) -> int:
        if pipeline == self.profile.primary_pipeline_name:
            lo, hi = self.profile.acv_ranges[segment]
            return round(random.randint(lo, hi) / 500) * 500
        elif pipeline == self.profile.renewal_pipeline_name:
            r_lo, r_hi = self.profile.renewal_amount_factor
            raw = int(original_amount * random.uniform(r_lo, r_hi))
            return round(raw / 100) * 100
        else:  # Expansion / follow-on
            e_lo, e_hi = self.profile.expansion_amount_factor
            raw = int(original_amount * random.uniform(e_lo, e_hi))
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
        if pipeline == self.profile.primary_pipeline_name:
            lo, hi = self.profile.nb_cycle_days[segment]
        elif pipeline == self.profile.renewal_pipeline_name:
            lo, hi = self.profile.renewal_cycle_days
        else:
            lo, hi = self.profile.expansion_cycle_days
        return random.randint(lo, hi)

    # ------------------------------------------------------------------ #
    #  Account / deal-count selection                                     #
    # ------------------------------------------------------------------ #

    def _select_accounts_with_deals(self) -> List[int]:
        all_ids = [int(a["id"]) for a in self.accounts]
        k = max(1, round(len(all_ids) * self.profile.accounts_with_deals_fraction))
        return sorted(random.sample(all_ids, k))

    def _generate_nb_deal_count(self) -> int:
        counts, weights = self.profile.nb_deal_count_weights
        return random.choices(counts, weights=weights, k=1)[0]

    # ------------------------------------------------------------------ #
    #  Follow-up deal helper (Renewal / Expansion)                        #
    # ------------------------------------------------------------------ #

    def _generate_followup_deal(
        self,
        deals: List[Deal],
        aid: int,
        segment: str,
        pipeline: str,
        created: datetime.date,
        original_amount: int,
    ) -> None:
        """Generate a single Renewal or Expansion deal and append it."""
        contact = self._pick_contact(aid)
        cid = int(contact["contact_id"])
        owner = random.choice(self.profile.sales_reps)
        amount = self._generate_amount(pipeline, segment, original_amount)

        outcome = self._pick_outcome(pipeline)

        # Active-window enforcement: old deals can't stay Open
        if outcome == "Open" and created < self.ACTIVE_WINDOW_START:
            outcome = random.choices(
                ["Won", "Lost"],
                weights=[85, 15] if pipeline == self.profile.renewal_pipeline_name else [60, 40],
                k=1,
            )[0]

        if outcome == "Open":
            stage = self._pick_active_stage(pipeline)
            deals.append(Deal(
                deal_id=0,
                deal_name="",
                account_id=aid,
                contact_id=cid,
                pipeline=pipeline,
                segment=segment,
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date="",
                deal_status=self._derive_status(stage),
                deal_owner=owner,
                loss_reason="",
            ))
            return

        # Won or Lost
        cycle = self._cycle_days(pipeline, segment)
        close = created + datetime.timedelta(days=cycle)

        if close > self.DATE_RANGE_END:
            stage = self._pick_active_stage(pipeline)
            deals.append(Deal(
                deal_id=0,
                deal_name="",
                account_id=aid,
                contact_id=cid,
                pipeline=pipeline,
                segment=segment,
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date="",
                deal_status=self._derive_status(stage),
                deal_owner=owner,
                loss_reason="",
            ))
            return

        if outcome == "Won":
            stage = "Closed Won"
            reason = ""
        else:
            stage = "Closed Lost"
            reason = self._pick_loss_reason(segment)

        deals.append(Deal(
            deal_id=0,
            deal_name="",
            account_id=aid,
            contact_id=cid,
            pipeline=pipeline,
            segment=segment,
            stage=stage,
            amount=amount,
            created_date=created.isoformat(),
            close_date=close.isoformat(),
            deal_status=self._derive_status(stage),
            deal_owner=owner,
            loss_reason=reason,
        ))

    # ------------------------------------------------------------------ #
    #  Self-serve deal generation                                         #
    # ------------------------------------------------------------------ #

    def _generate_self_serve_deals(
        self,
        deals: List[Deal],
        all_account_ids: List[int],
        plg_to_nb_accounts: set,
    ) -> None:
        """Generate self-serve (PLG) deals if the profile supports it."""
        config = self.profile.self_serve_config
        if config is None:
            return

        pipeline_name = config["pipeline_name"]
        conversion_rate = config["conversion_rate"]
        sub_split = config["subscription_split"]
        fraction = config["fraction_of_accounts"]
        plg_to_sales_prob = config["plg_to_sales_probability"]

        # Select a fraction of all accounts for self-serve
        k = max(1, round(len(all_account_ids) * fraction))
        ss_accounts = random.sample(all_account_ids, min(k, len(all_account_ids)))

        for aid in ss_accounts:
            if aid not in self.contacts_by_account:
                continue

            contact = self._pick_contact(aid)
            cid = int(contact["contact_id"])

            # Determine subscription type
            sub_type = random.choices(
                list(sub_split.keys()),
                weights=list(sub_split.values()),
                k=1,
            )[0]

            # Determine amount
            if sub_type == "Monthly":
                lo, hi = config["monthly_amount_range"]
            else:
                lo, hi = config["yearly_amount_range"]
            amount = round(random.randint(lo, hi) / 50) * 50

            # Determine outcome: converted or churned
            converted = random.random() < conversion_rate
            created = self._random_date(self.DATE_RANGE_START, self.DATE_RANGE_END)

            if converted:
                stage = "Converted"
                status = "Won"
                cycle = random.randint(1, 14)
                close = created + datetime.timedelta(days=cycle)
                if close > self.DATE_RANGE_END:
                    close = self.DATE_RANGE_END
            else:
                stage = "Churned"
                status = "Lost"
                cycle = random.randint(1, 30)
                close = created + datetime.timedelta(days=cycle)
                if close > self.DATE_RANGE_END:
                    close = self.DATE_RANGE_END

            deals.append(Deal(
                deal_id=0,
                deal_name="",
                account_id=aid,
                contact_id=cid,
                pipeline=pipeline_name,
                segment="Self-Serve",
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date=close.isoformat(),
                deal_status=status,
                deal_owner="",  # No sales rep for self-serve
                loss_reason="",
                subscription_type=sub_type,
            ))

            # PLG-to-sales: small chance converted self-serve gets a NB deal later
            if converted and random.random() < plg_to_sales_prob:
                plg_to_nb_accounts.add(aid)

    # ------------------------------------------------------------------ #
    #  Core multi-phase generation                                        #
    # ------------------------------------------------------------------ #

    def generate(self) -> List[Deal]:
        deals: List[Deal] = []
        won_nb: Dict[int, list] = {}   # account_id -> [{close_date, amount}]

        selected = self._select_accounts_with_deals()
        all_account_ids = [int(a["id"]) for a in self.accounts]

        primary = self.profile.primary_pipeline_name
        renewal = self.profile.renewal_pipeline_name
        expansion = self.profile.expansion_pipeline_name

        # ---- Phase 1: New Business deals ----
        for aid in selected:
            if aid not in self.contacts_by_account:
                print(f"  [warning] Account {aid} has no contacts, skipping.")
                continue

            segment = self.account_segments[aid]

            for _ in range(self._generate_nb_deal_count()):
                contact = self._pick_contact(aid)
                cid = int(contact["contact_id"])
                owner = random.choice(self.profile.sales_reps)
                amount = self._generate_amount(primary, segment)

                # Assign subscription_type for sales-assisted SaaS deals
                sub_type = ""
                if self.profile.subscription_type_weights:
                    stw = self.profile.subscription_type_weights
                    sub_type = random.choices(
                        list(stw.keys()), weights=list(stw.values()), k=1
                    )[0]

                outcome = self._pick_outcome(primary)

                if outcome == "Open":
                    created = self._random_date(
                        self.ACTIVE_WINDOW_START, self.DATE_RANGE_END
                    )
                    stage = self._pick_active_stage(primary)
                    deals.append(Deal(
                        deal_id=0,
                        deal_name="",
                        account_id=aid,
                        contact_id=cid,
                        pipeline=primary,
                        segment=segment,
                        stage=stage,
                        amount=amount,
                        created_date=created.isoformat(),
                        close_date="",
                        deal_status=self._derive_status(stage),
                        deal_owner=owner,
                        loss_reason="",
                        subscription_type=sub_type,
                    ))
                    continue

                # Won or Lost — pick cycle, compute dates
                cycle = self._cycle_days(primary, segment)
                latest_start = self.DATE_RANGE_END - datetime.timedelta(
                    days=cycle
                )

                if latest_start <= self.DATE_RANGE_START:
                    created = self._random_date(
                        self.ACTIVE_WINDOW_START, self.DATE_RANGE_END
                    )
                    stage = self._pick_active_stage(primary)
                    deals.append(Deal(
                        deal_id=0,
                        deal_name="",
                        account_id=aid,
                        contact_id=cid,
                        pipeline=primary,
                        segment=segment,
                        stage=stage,
                        amount=amount,
                        created_date=created.isoformat(),
                        close_date="",
                        deal_status=self._derive_status(stage),
                        deal_owner=owner,
                        loss_reason="",
                        subscription_type=sub_type,
                    ))
                    continue

                created = self._random_date(self.DATE_RANGE_START, latest_start)
                close = created + datetime.timedelta(days=cycle)

                if outcome == "Won":
                    stage = "Closed Won"
                    reason = ""
                    won_nb.setdefault(aid, []).append(
                        {"close_date": close, "amount": amount}
                    )
                else:
                    stage = "Closed Lost"
                    reason = self._pick_loss_reason(segment)

                deals.append(Deal(
                    deal_id=0,
                    deal_name="",
                    account_id=aid,
                    contact_id=cid,
                    pipeline=primary,
                    segment=segment,
                    stage=stage,
                    amount=amount,
                    created_date=created.isoformat(),
                    close_date=close.isoformat(),
                    deal_status=self._derive_status(stage),
                    deal_owner=owner,
                    loss_reason=reason,
                    subscription_type=sub_type,
                ))

        # ---- Phase 1b: Self-Serve deals ----
        plg_to_nb_accounts: set = set()
        self._generate_self_serve_deals(deals, all_account_ids, plg_to_nb_accounts)

        # Generate NB deals for PLG-to-sales accounts (if not already in selected)
        for aid in plg_to_nb_accounts:
            if aid in set(selected) or aid not in self.contacts_by_account:
                continue
            segment = self.account_segments[aid]
            contact = self._pick_contact(aid)
            cid = int(contact["contact_id"])
            owner = random.choice(self.profile.sales_reps)
            amount = self._generate_amount(primary, segment)
            sub_type = ""
            if self.profile.subscription_type_weights:
                stw = self.profile.subscription_type_weights
                sub_type = random.choices(
                    list(stw.keys()), weights=list(stw.values()), k=1
                )[0]

            created = self._random_date(self.ACTIVE_WINDOW_START, self.DATE_RANGE_END)
            stage = self._pick_active_stage(primary)
            deals.append(Deal(
                deal_id=0,
                deal_name="",
                account_id=aid,
                contact_id=cid,
                pipeline=primary,
                segment=segment,
                stage=stage,
                amount=amount,
                created_date=created.isoformat(),
                close_date="",
                deal_status=self._derive_status(stage),
                deal_owner=owner,
                loss_reason="",
                subscription_type=sub_type,
            ))

        # ---- Phase 2: Renewals + Expansions ----
        r_lo_days, r_hi_days = self.profile.renewal_timing_days
        e_lo_days, e_hi_days = self.profile.expansion_timing_days

        for aid, wins in won_nb.items():
            segment = self.account_segments[aid]

            for nb in wins:
                nb_close = nb["close_date"]
                nb_amount = nb["amount"]

                # Renewal
                r_created = nb_close + datetime.timedelta(
                    days=random.randint(r_lo_days, r_hi_days)
                )
                if r_created <= self.DATE_RANGE_END:
                    self._generate_followup_deal(
                        deals, aid, segment, renewal,
                        r_created, nb_amount,
                    )

                # Expansion
                if random.random() < self.profile.expansion_probability:
                    e_created = nb_close + datetime.timedelta(
                        days=random.randint(e_lo_days, e_hi_days)
                    )
                    if e_created <= self.DATE_RANGE_END:
                        self._generate_followup_deal(
                            deals, aid, segment, expansion,
                            e_created, nb_amount,
                        )

        # ---- Phase 3: Sort, assign sequential IDs and names ----
        deals.sort(key=lambda d: (d.created_date, d.account_id))
        name_tracker: Dict[str, int] = {}
        for idx, deal in enumerate(deals, start=1):
            deal.deal_id = idx
            company = self.account_names[deal.account_id]
            base = self.profile.format_deal_name(company, deal.created_date)
            count = name_tracker.get(base, 0)
            deal.deal_name = base if count == 0 else base + chr(ord('a') + count - 1)
            name_tracker[base] = count + 1

        return deals
