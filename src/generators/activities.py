"""
Activity Generator Module

Generates realistic B2B SaaS sales activity history for CRM datasets.
Each activity is linked to an account and contact, and optionally to a deal.

Activities follow realistic patterns:
  - Won deals have heavy multi-channel engagement (10-20 activities)
  - Lost deals show engagement drop-off (4-8 activities)
  - Active deals have recent activity proportional to time open
  - Activity types shift across the deal lifecycle:
      Early → LinkedIn-heavy (prospecting)
      Mid   → Meeting-heavy (demos, deep dives)
      Late  → Email-heavy (proposals, contracts)
  - Enterprise deals generate more activities than SMB
  - Some accounts have non-deal relationship activities
  - ~10% of accounts are completely untouched (zero activities)
"""

import csv
import datetime
import random
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Activity:
    """
    Represents a CRM activity/touchpoint.

    Attributes:
        activity_id: Unique sequential identifier
        activity_type: Email, Phone Call, Meeting, LinkedIn, or Note
        subject: Short description of the activity
        activity_date: When the activity occurred (YYYY-MM-DD)
        account_id: Foreign key to accounts CSV
        contact_id: Foreign key to contacts CSV
        deal_id: Foreign key to deals CSV (empty string for non-deal activities)
        completed: Whether the activity is completed ("Yes" or "No")
        duration_minutes: Duration in minutes (empty string for Email/LinkedIn/Note)
        notes: Brief notes about the activity
        activity_owner: Sales rep who performed the activity
    """

    activity_id: int
    activity_type: str
    subject: str
    activity_date: str
    account_id: int
    contact_id: int
    deal_id: str            # int-as-string when linked, "" when not
    completed: str           # "Yes" or "No"
    duration_minutes: str    # int-as-string when applicable, "" otherwise
    notes: str
    activity_owner: str


class ActivityGenerator:
    """
    Generates realistic CRM activity data linked to existing accounts,
    contacts, and deals.

    Uses a three-phase algorithm:
      1. Generate deal-linked activities with phase-based type weighting
      2. Generate non-deal relationship-building activities
      3. Sort all activities by date and assign sequential IDs

    Example:
        generator = ActivityGenerator(
            "output/accounts.csv",
            "output/contacts.csv",
            "output/deals.csv",
        )
        activities = generator.generate()
    """

    # ------------------------------------------------------------------ #
    #  Date boundaries (same range as DealGenerator)                      #
    # ------------------------------------------------------------------ #

    DATE_RANGE_START = datetime.date(2023, 1, 1)
    DATE_RANGE_END = datetime.date(2026, 2, 1)

    # Activities on Active deals must include at least some within
    # the last 2 weeks to look "current"
    RECENT_ACTIVITY_CUTOFF = datetime.date(2026, 1, 18)

    # ------------------------------------------------------------------ #
    #  Sales reps (identical across all generators)                       #
    # ------------------------------------------------------------------ #

    ACTIVITY_OWNERS = [
        "Sarah Chen",
        "Marcus Johnson",
        "Emily Rodriguez",
        "David Kim",
        "Rachel Thompson",
        "James O'Brien",
    ]

    # ------------------------------------------------------------------ #
    #  Activity type weights — overall and per-phase                      #
    # ------------------------------------------------------------------ #

    ACTIVITY_TYPES = ["Email", "Phone Call", "Meeting", "LinkedIn", "Note"]

    # Overall weights used for non-deal activities
    ACTIVITY_TYPE_WEIGHTS = {
        "Email": 35,
        "Phone Call": 20,
        "Meeting": 20,
        "LinkedIn": 15,
        "Note": 10,
    }

    # Phase-based weights for deal-linked activities
    # "early" = first 25% of deal cycle  → LinkedIn-heavy (prospecting)
    # "mid"   = 25%-75%                  → Meeting-heavy (demos, deep dives)
    # "late"  = last 25%                 → Email-heavy (proposals, contracts)
    PHASE_WEIGHTS = {
        "early": {"Email": 20, "Phone Call": 20, "Meeting": 10, "LinkedIn": 40, "Note": 10},
        "mid":   {"Email": 25, "Phone Call": 20, "Meeting": 35, "LinkedIn": 10, "Note": 10},
        "late":  {"Email": 45, "Phone Call": 20, "Meeting": 20, "LinkedIn": 5,  "Note": 10},
    }

    # ------------------------------------------------------------------ #
    #  Activity count ranges by deal outcome                              #
    # ------------------------------------------------------------------ #

    # Base ranges before segment multiplier is applied
    ACTIVITY_COUNT_RANGES = {
        "Won": (10, 20),
        "Lost": (4, 8),
    }

    # Enterprise deals involve more stakeholders → more touchpoints
    SEGMENT_ACTIVITY_MULTIPLIER = {
        "SMB": 0.8,
        "Mid-Market": 1.0,
        "Enterprise": 1.4,
    }

    # ------------------------------------------------------------------ #
    #  Subject lines per activity type                                    #
    # ------------------------------------------------------------------ #

    SUBJECTS = {
        "Email": [
            "Follow-up on pricing proposal",
            "Introduction to platform",
            "Sending case study",
            "Contract review",
            "ROI analysis attached",
            "Nurture - industry report",
        ],
        "Phone Call": [
            "Discovery call",
            "Quarterly business review",
            "Cold outreach",
            "Champion check-in",
            "Negotiation follow-up",
            "Renewal discussion",
        ],
        "Meeting": [
            "On-site demo",
            "Executive alignment",
            "Technical deep dive",
            "Kick-off call",
            "QBR",
            "Security review walkthrough",
        ],
        "LinkedIn": [
            "Connection request",
            "InMail outreach",
            "Commented on post",
            "Shared company content",
            "Intro message via mutual connection",
        ],
        "Note": [
            "Met at SaaStr conference",
            "Referred by existing customer",
            "Internal handoff notes",
            "Competitor intel",
            "Budget cycle starts Q1",
        ],
    }

    # Phase-biased subject subsets — used 70% of the time for deal-linked
    # activities so that early activities sound like prospecting, mid like
    # evaluation, and late like closing.
    PHASE_BIASED_SUBJECTS = {
        "early": {
            "Email": ["Introduction to platform", "Sending case study", "Nurture - industry report"],
            "Phone Call": ["Discovery call", "Cold outreach"],
            "Meeting": ["Kick-off call", "Technical deep dive"],
            "LinkedIn": ["Connection request", "InMail outreach", "Intro message via mutual connection"],
            "Note": ["Met at SaaStr conference", "Referred by existing customer"],
        },
        "mid": {
            "Email": ["Sending case study", "ROI analysis attached"],
            "Phone Call": ["Champion check-in", "Quarterly business review"],
            "Meeting": ["On-site demo", "Technical deep dive", "Executive alignment"],
            "LinkedIn": ["Commented on post", "Shared company content"],
            "Note": ["Competitor intel", "Internal handoff notes"],
        },
        "late": {
            "Email": ["Follow-up on pricing proposal", "Contract review", "ROI analysis attached"],
            "Phone Call": ["Negotiation follow-up", "Renewal discussion"],
            "Meeting": ["Executive alignment", "QBR", "Security review walkthrough"],
            "LinkedIn": ["Shared company content"],
            "Note": ["Budget cycle starts Q1", "Internal handoff notes"],
        },
    }

    # ------------------------------------------------------------------ #
    #  Duration ranges (minutes) by activity type                         #
    # ------------------------------------------------------------------ #

    # None means the activity type has no duration (Email, LinkedIn, Note)
    DURATION_RANGES = {
        "Email": None,
        "Phone Call": (10, 45),
        "Meeting": (30, 90),
        "LinkedIn": None,
        "Note": None,
    }

    # ------------------------------------------------------------------ #
    #  Non-deal activity settings                                         #
    # ------------------------------------------------------------------ #

    # Accounts WITH deals get 1-3 general relationship-building activities
    NON_DEAL_WITH_DEAL_COUNT = (1, 3)

    # Accounts WITHOUT deals (that aren't zero-activity) get 1-3 outreach
    NON_DEAL_NO_DEAL_COUNT = (1, 3)

    # ~50% of no-deal accounts get initial outreach activities
    FRACTION_NO_DEAL_WITH_OUTREACH = 0.50

    # ~10% of ALL accounts have zero activities (untouched, just imported)
    FRACTION_ZERO_ACTIVITY = 0.10

    # Outreach-type weights: heavier on LinkedIn + Email for prospecting
    OUTREACH_TYPE_WEIGHTS = [30, 15, 5, 40, 10]  # Email, Call, Meeting, LinkedIn, Note

    # ------------------------------------------------------------------ #
    #  Constructor                                                        #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        accounts_csv_path: str,
        contacts_csv_path: str,
        deals_csv_path: str,
        seed: int = None,
    ):
        if seed is not None:
            random.seed(seed)

        # Load source data
        self.accounts = self._load_accounts(accounts_csv_path)
        self.contacts = self._load_contacts(contacts_csv_path)
        self.deals = self._load_deals(deals_csv_path)

        # Build contacts-by-account lookup
        self.contacts_by_account: Dict[int, List[dict]] = {}
        for c in self.contacts:
            aid = int(c["account_id"])
            self.contacts_by_account.setdefault(aid, []).append(c)

        # Build deals-by-account lookup
        self.deals_by_account: Dict[int, List[dict]] = {}
        for d in self.deals:
            aid = int(d["account_id"])
            self.deals_by_account.setdefault(aid, []).append(d)

        # Segment classification from employee_count
        self.account_segments: Dict[int, str] = {}
        for a in self.accounts:
            aid = int(a["id"])
            self.account_segments[aid] = self._classify_segment(
                int(a["employee_count"])
            )

        # Quick-lookup sets
        self.all_account_ids = [int(a["id"]) for a in self.accounts]
        self.accounts_with_deals = set(self.deals_by_account.keys())
        self.accounts_without_deals = (
            set(self.all_account_ids) - self.accounts_with_deals
        )

    # ------------------------------------------------------------------ #
    #  CSV loaders                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_accounts(path: str) -> List[dict]:
        """Load accounts CSV, validate required columns."""
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"id", "employee_count"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Accounts CSV missing columns: {missing}")
            return list(reader)

    @staticmethod
    def _load_contacts(path: str) -> List[dict]:
        """Load contacts CSV, validate required columns."""
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"contact_id", "account_id", "contact_owner"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Contacts CSV missing columns: {missing}")
            return list(reader)

    @staticmethod
    def _load_deals(path: str) -> List[dict]:
        """Load deals CSV, validate required columns."""
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {
                "deal_id", "account_id", "contact_id", "deal_status",
                "deal_owner", "created_date", "close_date", "segment",
            }
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Deals CSV missing columns: {missing}")
            return list(reader)

    # ------------------------------------------------------------------ #
    #  Classifiers / pickers                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _classify_segment(employee_count: int) -> str:
        """Classify account into SMB, Mid-Market, or Enterprise."""
        if employee_count < 200:
            return "SMB"
        elif employee_count <= 1000:
            return "Mid-Market"
        return "Enterprise"

    @staticmethod
    def _get_deal_phase(
        activity_date: datetime.date,
        deal_start: datetime.date,
        deal_end: datetime.date,
    ) -> str:
        """
        Classify where in the deal lifecycle an activity falls.

        Returns:
            'early'  — first 25% of the deal's duration
            'mid'    — middle 50%
            'late'   — last 25%
        """
        total_days = (deal_end - deal_start).days
        if total_days <= 0:
            return "mid"
        elapsed = (activity_date - deal_start).days
        progress = elapsed / total_days
        if progress < 0.25:
            return "early"
        elif progress < 0.75:
            return "mid"
        return "late"

    def _pick_activity_type(self, phase: str) -> str:
        """Pick an activity type using phase-weighted probabilities."""
        weights = self.PHASE_WEIGHTS[phase]
        return random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

    def _pick_activity_type_general(self) -> str:
        """Pick an activity type using overall type weights (non-deal)."""
        w = self.ACTIVITY_TYPE_WEIGHTS
        return random.choices(
            list(w.keys()), weights=list(w.values()), k=1
        )[0]

    def _pick_subject(self, activity_type: str, phase: str = None) -> str:
        """
        Pick a realistic subject line for the given activity type.

        If a phase is provided, uses phase-biased subjects 70% of the time
        so that early activities sound like prospecting, mid like evaluation,
        and late like closing. Falls back to the general subject list.
        """
        if phase and random.random() < 0.70:
            biased = self.PHASE_BIASED_SUBJECTS.get(phase, {}).get(activity_type)
            if biased:
                return random.choice(biased)
        return random.choice(self.SUBJECTS[activity_type])

    # ------------------------------------------------------------------ #
    #  Duration and completion helpers                                    #
    # ------------------------------------------------------------------ #

    def _generate_duration(self, activity_type: str) -> str:
        """
        Generate a realistic duration for the activity type.

        Returns empty string for Email, LinkedIn, and Note.
        Returns a random duration rounded to nearest 5 minutes for
        Phone Call (10-45 min) and Meeting (30-90 min).
        """
        dur_range = self.DURATION_RANGES[activity_type]
        if dur_range is None:
            return ""
        raw = random.randint(dur_range[0], dur_range[1])
        return str(round(raw / 5) * 5)

    @staticmethod
    def _pick_completed(activity_date: datetime.date) -> str:
        """
        Determine if the activity is completed.

        All activities on or before DATE_RANGE_END (synthetic "today")
        are marked completed. Future scheduled activities are not.
        """
        return "Yes" if activity_date <= datetime.date(2026, 2, 1) else "No"

    # ------------------------------------------------------------------ #
    #  Date helper                                                        #
    # ------------------------------------------------------------------ #

    def _random_date(
        self, start: datetime.date, end: datetime.date
    ) -> datetime.date:
        """Return a random date between start and end (inclusive)."""
        if start >= end:
            return start
        return start + datetime.timedelta(
            days=random.randint(0, (end - start).days)
        )

    # ------------------------------------------------------------------ #
    #  Activity count for Active deals                                    #
    # ------------------------------------------------------------------ #

    def _active_deal_activity_count(self, deal: dict, segment: str) -> int:
        """
        Calculate activity count for an Active deal.

        Baseline: ~1 activity per week the deal has been open, capped at 15.
        Then multiplied by the segment multiplier (Enterprise gets more).
        Minimum of 2 activities guaranteed.
        """
        created = datetime.date.fromisoformat(deal["created_date"])
        days_open = (self.DATE_RANGE_END - created).days
        weeks_open = max(1, days_open // 7)
        base_count = min(weeks_open, 15)
        multiplier = self.SEGMENT_ACTIVITY_MULTIPLIER[segment]
        return max(2, round(base_count * multiplier))

    # ------------------------------------------------------------------ #
    #  Core three-phase generation                                        #
    # ------------------------------------------------------------------ #

    def generate(self) -> List[Activity]:
        """
        Generate all activities using a three-phase algorithm.

        Phase 1: Deal-linked activities with phase-based type weighting
        Phase 2: Non-deal relationship and outreach activities
        Phase 3: Sort by date and assign sequential IDs
        """
        activities: List[Activity] = []

        # --- Determine which accounts get zero activities (~10% of all) ---
        # Only no-deal accounts can be zero-activity; accounts with deals
        # must have activities to match their deal engagement.
        zero_count = max(1, round(
            len(self.all_account_ids) * self.FRACTION_ZERO_ACTIVITY
        ))
        zero_activity_accounts = set(random.sample(
            list(self.accounts_without_deals),
            min(zero_count, len(self.accounts_without_deals)),
        ))

        # ============================================================== #
        #  Phase 1: Deal-linked activities                                #
        # ============================================================== #

        for deal in self.deals:
            deal_id = int(deal["deal_id"])
            aid = int(deal["account_id"])
            cid = int(deal["contact_id"])
            status = deal["deal_status"]
            segment = deal.get("segment", "SMB")
            created = datetime.date.fromisoformat(deal["created_date"])
            owner = deal["deal_owner"]

            # End boundary: close_date for Won/Lost, DATE_RANGE_END for Active
            if deal["close_date"]:
                deal_end = datetime.date.fromisoformat(deal["close_date"])
            else:
                deal_end = self.DATE_RANGE_END

            # --- Determine how many activities this deal gets ---
            multiplier = self.SEGMENT_ACTIVITY_MULTIPLIER.get(segment, 1.0)

            if status in ("Won", "Lost"):
                base_lo, base_hi = self.ACTIVITY_COUNT_RANGES[status]
                count = random.randint(
                    round(base_lo * multiplier),
                    round(base_hi * multiplier),
                )
            else:  # Active
                count = self._active_deal_activity_count(deal, segment)

            # Contacts available for this account (for multi-stakeholder)
            account_contacts = self.contacts_by_account.get(aid, [])

            # --- Generate each activity ---
            for i in range(count):
                # Pick a date within the deal's lifecycle
                act_date = self._random_date(created, deal_end)

                # For Active deals: force the first 2 activities to be
                # within the last 2 weeks so the deal looks "current".
                # Use max() so we never pick a date before the deal opened.
                if status == "Open" and i < 2:
                    recent_start = max(self.RECENT_ACTIVITY_CUTOFF, created)
                    act_date = self._random_date(
                        recent_start, self.DATE_RANGE_END
                    )

                # Determine the deal phase for this activity's date
                phase = self._get_deal_phase(act_date, created, deal_end)

                # Pick activity type weighted by phase
                activity_type = self._pick_activity_type(phase)

                # Pick subject biased by phase
                subject = self._pick_subject(activity_type, phase)

                # 70% primary contact, 30% another contact from the account
                # (simulates multi-stakeholder engagement)
                if account_contacts and random.random() < 0.30:
                    contact = random.choice(account_contacts)
                    contact_id = int(contact["contact_id"])
                else:
                    contact_id = cid

                activities.append(Activity(
                    activity_id=0,  # assigned in Phase 3
                    activity_type=activity_type,
                    subject=subject,
                    activity_date=act_date.isoformat(),
                    account_id=aid,
                    contact_id=contact_id,
                    deal_id=str(deal_id),
                    completed=self._pick_completed(act_date),
                    duration_minutes=self._generate_duration(activity_type),
                    notes="",
                    activity_owner=owner,
                ))

        # ============================================================== #
        #  Phase 2: Non-deal activities                                   #
        # ============================================================== #

        # --- 2a: Accounts WITH deals get general relationship activities ---
        for aid in self.accounts_with_deals:
            account_contacts = self.contacts_by_account.get(aid, [])
            if not account_contacts:
                continue

            # Pick owner from the first deal's owner for consistency
            account_deals = self.deals_by_account.get(aid, [])
            fallback_owner = (
                account_deals[0]["deal_owner"]
                if account_deals
                else random.choice(self.ACTIVITY_OWNERS)
            )

            non_deal_count = random.randint(*self.NON_DEAL_WITH_DEAL_COUNT)

            for _ in range(non_deal_count):
                contact = random.choice(account_contacts)
                contact_id = int(contact["contact_id"])
                # Use the contact's owner for non-deal activities
                owner = contact.get("contact_owner", fallback_owner)

                activity_type = self._pick_activity_type_general()
                subject = self._pick_subject(activity_type)
                act_date = self._random_date(
                    self.DATE_RANGE_START, self.DATE_RANGE_END
                )

                activities.append(Activity(
                    activity_id=0,
                    activity_type=activity_type,
                    subject=subject,
                    activity_date=act_date.isoformat(),
                    account_id=aid,
                    contact_id=contact_id,
                    deal_id="",  # not linked to any deal
                    completed=self._pick_completed(act_date),
                    duration_minutes=self._generate_duration(activity_type),
                    notes="",
                    activity_owner=owner,
                ))

        # --- 2b: Accounts WITHOUT deals — ~50% get initial outreach ---
        eligible_no_deal = [
            aid for aid in self.accounts_without_deals
            if aid not in zero_activity_accounts
        ]
        outreach_count = round(
            len(eligible_no_deal) * self.FRACTION_NO_DEAL_WITH_OUTREACH
        )
        no_deal_with_outreach = random.sample(
            eligible_no_deal, min(outreach_count, len(eligible_no_deal))
        )

        for aid in no_deal_with_outreach:
            account_contacts = self.contacts_by_account.get(aid, [])
            if not account_contacts:
                continue

            act_count = random.randint(*self.NON_DEAL_NO_DEAL_COUNT)

            for _ in range(act_count):
                contact = random.choice(account_contacts)
                contact_id = int(contact["contact_id"])
                owner = contact.get(
                    "contact_owner", random.choice(self.ACTIVITY_OWNERS)
                )

                # Outreach skews toward LinkedIn + Email (prospecting)
                activity_type = random.choices(
                    self.ACTIVITY_TYPES,
                    weights=self.OUTREACH_TYPE_WEIGHTS,
                    k=1,
                )[0]
                subject = self._pick_subject(activity_type, "early")
                act_date = self._random_date(
                    self.DATE_RANGE_START, self.DATE_RANGE_END
                )

                activities.append(Activity(
                    activity_id=0,
                    activity_type=activity_type,
                    subject=subject,
                    activity_date=act_date.isoformat(),
                    account_id=aid,
                    contact_id=contact_id,
                    deal_id="",
                    completed=self._pick_completed(act_date),
                    duration_minutes=self._generate_duration(activity_type),
                    notes="",
                    activity_owner=owner,
                ))

        # ============================================================== #
        #  Phase 3: Sort and assign sequential IDs                        #
        # ============================================================== #

        activities.sort(key=lambda a: (a.activity_date, a.account_id))
        for idx, activity in enumerate(activities, start=1):
            activity.activity_id = idx

        return activities
