"""
Activity Generator Module

Generates realistic sales activity history for CRM datasets.
Each activity is linked to an account and contact, and optionally to a deal.
Business-specific constants come from the profile.
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

    Core fields are populated for every activity. Type-specific fields are
    populated only when the activity_type matches (others stay "").
    """

    # Core fields (always populated)
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

    # Type-specific fields (populated only for matching activity_type)
    note_body: str = ""
    email_subject: str = ""
    email_body: str = ""
    email_direction: str = ""
    email_status: str = ""
    call_notes: str = ""
    call_duration: str = ""
    call_disposition: str = ""
    call_direction: str = ""
    meeting_title: str = ""
    meeting_description: str = ""
    meeting_start_time: str = ""
    meeting_end_time: str = ""


class ActivityGenerator:
    """
    Generates realistic CRM activity data linked to existing accounts,
    contacts, and deals. Business-specific constants come from the profile.

    Uses a three-phase algorithm:
      1. Generate deal-linked activities with phase-based type weighting
      2. Generate non-deal relationship-building activities
      3. Sort all activities by date and assign sequential IDs
    """

    # ------------------------------------------------------------------ #
    #  Date boundaries (same range as DealGenerator)                      #
    # ------------------------------------------------------------------ #

    DATE_RANGE_START = datetime.date(2023, 1, 1)
    DATE_RANGE_END = datetime.date(2026, 2, 1)
    RECENT_ACTIVITY_CUTOFF = datetime.date(2026, 1, 18)

    # ------------------------------------------------------------------ #
    #  Non-deal activity settings (not profile-specific)                  #
    # ------------------------------------------------------------------ #

    NON_DEAL_WITH_DEAL_COUNT = (1, 3)
    NON_DEAL_NO_DEAL_COUNT = (1, 3)
    FRACTION_NO_DEAL_WITH_OUTREACH = 0.50

    # ------------------------------------------------------------------ #
    #  Constructor                                                        #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        accounts_csv_path: str,
        contacts_csv_path: str,
        deals_csv_path: str,
        seed: int = None,
        profile=None,
    ):
        if seed is not None:
            random.seed(seed)

        if profile is None:
            from profiles.b2b_saas import B2BSaaSProfile
            profile = B2BSaaSProfile()
        self.profile = profile

        # Load source data
        self.accounts = self._load_accounts(accounts_csv_path)
        self.contacts = self._load_contacts(contacts_csv_path)
        self.deals = self._load_deals(deals_csv_path)

        # Build contacts-by-account and contacts-by-id lookups
        self.contacts_by_account: Dict[int, List[dict]] = {}
        self.contacts_by_id: Dict[int, dict] = {}
        for c in self.contacts:
            aid = int(c["account_id"])
            self.contacts_by_account.setdefault(aid, []).append(c)
            self.contacts_by_id[int(c["contact_id"])] = c

        # Build deals-by-account lookup
        self.deals_by_account: Dict[int, List[dict]] = {}
        for d in self.deals:
            aid = int(d["account_id"])
            self.deals_by_account.setdefault(aid, []).append(d)

        # Segment classification from employee_count
        self.account_segments: Dict[int, str] = {}
        for a in self.accounts:
            aid = int(a["id"])
            self.account_segments[aid] = self.profile.classify_segment(
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
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"id", "employee_count"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Accounts CSV missing columns: {missing}")
            return list(reader)

    @staticmethod
    def _load_contacts(path: str) -> List[dict]:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"contact_id", "account_id", "contact_owner"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Contacts CSV missing columns: {missing}")
            return list(reader)

    @staticmethod
    def _load_deals(path: str) -> List[dict]:
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
    def _get_deal_phase(
        activity_date: datetime.date,
        deal_start: datetime.date,
        deal_end: datetime.date,
    ) -> str:
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
        weights = self.profile.phase_weights[phase]
        return random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

    def _pick_activity_type_general(self) -> str:
        """Pick an activity type using overall type weights (non-deal)."""
        w = self.profile.activity_type_weights
        return random.choices(
            list(w.keys()), weights=list(w.values()), k=1
        )[0]

    def _pick_subject(self, activity_type: str, phase: str = None) -> str:
        """Pick a realistic subject line for the given activity type."""
        if phase and random.random() < 0.70:
            biased = self.profile.phase_biased_subjects.get(phase, {}).get(activity_type)
            if biased:
                return random.choice(biased)
        return random.choice(self.profile.subjects[activity_type])

    # ------------------------------------------------------------------ #
    #  Duration and completion helpers                                    #
    # ------------------------------------------------------------------ #

    def _generate_duration(self, activity_type: str) -> str:
        dur_range = self.profile.duration_ranges[activity_type]
        if dur_range is None:
            return ""
        raw = random.randint(dur_range[0], dur_range[1])
        return str(round(raw / 5) * 5)

    @staticmethod
    def _pick_completed(activity_date: datetime.date) -> str:
        return "Yes" if activity_date <= datetime.date(2026, 2, 1) else "No"

    # ------------------------------------------------------------------ #
    #  Date helper                                                        #
    # ------------------------------------------------------------------ #

    def _random_date(
        self, start: datetime.date, end: datetime.date
    ) -> datetime.date:
        if start >= end:
            return start
        return start + datetime.timedelta(
            days=random.randint(0, (end - start).days)
        )

    # ------------------------------------------------------------------ #
    #  Activity count for Active deals                                    #
    # ------------------------------------------------------------------ #

    def _active_deal_activity_count(self, deal: dict, segment: str) -> int:
        created = datetime.date.fromisoformat(deal["created_date"])
        days_open = (self.DATE_RANGE_END - created).days
        weeks_open = max(1, days_open // 7)
        base_count = min(weeks_open, 15)
        multiplier = self.profile.segment_activity_multiplier.get(segment, 1.0)
        return max(2, round(base_count * multiplier))

    # ------------------------------------------------------------------ #
    #  Type-specific field generators                                     #
    # ------------------------------------------------------------------ #

    EMAIL_BODY_TEMPLATES = [
        "Hi {first_name},\n\nI wanted to follow up on {subject}. Let me know if you have any questions.\n\nBest regards",
        "Hi {first_name},\n\nThank you for your time. I'm sending over the {subject} for your review.\n\nBest",
        "Hi {first_name},\n\nJust circling back on {subject}. Would love to schedule some time to discuss next steps.\n\nThanks",
        "Hi {first_name},\n\nGreat speaking with you earlier. As discussed, here are the details regarding {subject}.\n\nRegards",
        "Hi {first_name},\n\nI hope this finds you well. Sharing some information about {subject}.\n\nBest regards",
        "Hi {first_name},\n\nFollowing up on our conversation about {subject}. Please find the requested information below.\n\nThanks",
    ]

    NOTE_BODY_TEMPLATES = [
        "{subject} - logged by {owner}.",
        "Internal note: {subject}. Follow-up required.",
        "{subject}. Key takeaway documented for team reference.",
        "Note regarding {subject}. See CRM history for context.",
        "{subject} - important context for upcoming discussions.",
    ]

    CALL_DISPOSITIONS = [
        ("Connected", 40),
        ("Left Voicemail", 25),
        ("No Answer", 15),
        ("Busy", 10),
        ("Wrong Number", 5),
        ("Gatekeeper", 5),
    ]

    MEETING_HOURS = list(range(8, 17))

    def _generate_email_body(self, contact_id: int, subject: str) -> str:
        contact = self.contacts_by_id.get(contact_id, {})
        first_name = contact.get("first_name", "there")
        template = random.choice(self.EMAIL_BODY_TEMPLATES)
        return template.format(first_name=first_name, subject=subject.lower())

    def _generate_email_fields(self) -> tuple:
        """Return (direction, status)."""
        direction = random.choices(
            ["OUTBOUND", "INBOUND"], weights=[75, 25], k=1
        )[0]
        if direction == "OUTBOUND":
            status = random.choices(
                ["SENT", "OPENED", "REPLIED", "BOUNCED"],
                weights=[40, 30, 25, 5], k=1,
            )[0]
        else:
            status = "RECEIVED"
        return direction, status

    def _generate_call_fields(self) -> tuple:
        """Return (disposition, direction)."""
        dispositions, weights = zip(*self.CALL_DISPOSITIONS)
        disposition = random.choices(dispositions, weights=weights, k=1)[0]
        direction = random.choices(
            ["OUTBOUND", "INBOUND"], weights=[80, 20], k=1
        )[0]
        return disposition, direction

    def _generate_meeting_times(self, activity_date: str, duration_minutes: str) -> tuple:
        """Return (start_iso, end_iso) as ISO datetime strings."""
        date_obj = datetime.date.fromisoformat(activity_date)
        hour = random.choice(self.MEETING_HOURS)
        minute = random.choice([0, 15, 30, 45])
        start_dt = datetime.datetime(
            date_obj.year, date_obj.month, date_obj.day, hour, minute
        )
        dur = int(duration_minutes) if duration_minutes else 30
        end_dt = start_dt + datetime.timedelta(minutes=dur)
        return start_dt.strftime("%Y-%m-%dT%H:%M:%S"), end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    def _generate_note_body(self, subject: str, owner: str) -> str:
        template = random.choice(self.NOTE_BODY_TEMPLATES)
        return template.format(subject=subject, owner=owner)

    def _fill_type_specific_fields(
        self, activity_type: str, subject: str, activity_date: str,
        duration: str, contact_id: int, owner: str,
    ) -> dict:
        """Return dict of type-specific field values for the given activity type."""
        fields = {}

        if activity_type in ("Note", "LinkedIn"):
            fields["note_body"] = self._generate_note_body(subject, owner)

        elif activity_type == "Email":
            direction, status = self._generate_email_fields()
            fields["email_subject"] = subject
            fields["email_body"] = self._generate_email_body(contact_id, subject)
            fields["email_direction"] = direction
            fields["email_status"] = status

        elif activity_type == "Phone Call":
            disposition, direction = self._generate_call_fields()
            fields["call_notes"] = f"{subject} - {disposition.lower()}"
            fields["call_duration"] = duration
            fields["call_disposition"] = disposition
            fields["call_direction"] = direction

        elif activity_type == "Meeting":
            start_time, end_time = self._generate_meeting_times(activity_date, duration)
            fields["meeting_title"] = subject
            fields["meeting_description"] = f"Meeting: {subject}"
            fields["meeting_start_time"] = start_time
            fields["meeting_end_time"] = end_time

        return fields

    # ------------------------------------------------------------------ #
    #  Core three-phase generation                                        #
    # ------------------------------------------------------------------ #

    def generate(self) -> List[Activity]:
        activities: List[Activity] = []

        # --- Determine which accounts get zero activities ---
        zero_count = max(1, round(
            len(self.all_account_ids) * self.profile.zero_activity_fraction
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

            # Skip self-serve deals (no owner = no sales activities)
            if not owner:
                continue

            # End boundary: close_date for Won/Lost, DATE_RANGE_END for Active
            if deal["close_date"]:
                deal_end = datetime.date.fromisoformat(deal["close_date"])
            else:
                deal_end = self.DATE_RANGE_END

            # --- Determine how many activities this deal gets ---
            multiplier = self.profile.segment_activity_multiplier.get(segment, 1.0)

            if status in ("Won", "Lost"):
                base_lo, base_hi = self.profile.activity_count_ranges[status]
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
                act_date = self._random_date(created, deal_end)

                # For Active deals: force the first 2 activities to be recent
                if status == "Open" and i < 2:
                    recent_start = max(self.RECENT_ACTIVITY_CUTOFF, created)
                    act_date = self._random_date(
                        recent_start, self.DATE_RANGE_END
                    )

                phase = self._get_deal_phase(act_date, created, deal_end)
                activity_type = self._pick_activity_type(phase)
                subject = self._pick_subject(activity_type, phase)

                # 70% primary contact, 30% another contact
                if account_contacts and random.random() < 0.30:
                    contact = random.choice(account_contacts)
                    contact_id = int(contact["contact_id"])
                else:
                    contact_id = cid

                duration = self._generate_duration(activity_type)
                type_fields = self._fill_type_specific_fields(
                    activity_type, subject, act_date.isoformat(),
                    duration, contact_id, owner,
                )
                activities.append(Activity(
                    activity_id=0,
                    activity_type=activity_type,
                    subject=subject,
                    activity_date=act_date.isoformat(),
                    account_id=aid,
                    contact_id=contact_id,
                    deal_id=str(deal_id),
                    completed=self._pick_completed(act_date),
                    duration_minutes=duration,
                    notes="",
                    activity_owner=owner,
                    **type_fields,
                ))

        # ============================================================== #
        #  Phase 2: Non-deal activities                                   #
        # ============================================================== #

        # --- 2a: Accounts WITH deals get general relationship activities ---
        for aid in self.accounts_with_deals:
            account_contacts = self.contacts_by_account.get(aid, [])
            if not account_contacts:
                continue

            account_deals = self.deals_by_account.get(aid, [])
            # Find first deal with an owner for consistency
            fallback_owner = random.choice(self.profile.sales_reps)
            for d in account_deals:
                if d["deal_owner"]:
                    fallback_owner = d["deal_owner"]
                    break

            non_deal_count = random.randint(*self.NON_DEAL_WITH_DEAL_COUNT)

            for _ in range(non_deal_count):
                contact = random.choice(account_contacts)
                contact_id = int(contact["contact_id"])
                owner = contact.get("contact_owner", fallback_owner)

                activity_type = self._pick_activity_type_general()
                subject = self._pick_subject(activity_type)
                act_date = self._random_date(
                    self.DATE_RANGE_START, self.DATE_RANGE_END
                )

                duration = self._generate_duration(activity_type)
                type_fields = self._fill_type_specific_fields(
                    activity_type, subject, act_date.isoformat(),
                    duration, contact_id, owner,
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
                    duration_minutes=duration,
                    notes="",
                    activity_owner=owner,
                    **type_fields,
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
                    "contact_owner", random.choice(self.profile.sales_reps)
                )

                # Outreach skews toward LinkedIn + Email (prospecting)
                activity_type = random.choices(
                    self.profile.activity_types,
                    weights=self.profile.outreach_type_weights,
                    k=1,
                )[0]
                subject = self._pick_subject(activity_type, "early")
                act_date = self._random_date(
                    self.DATE_RANGE_START, self.DATE_RANGE_END
                )

                duration = self._generate_duration(activity_type)
                type_fields = self._fill_type_specific_fields(
                    activity_type, subject, act_date.isoformat(),
                    duration, contact_id, owner,
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
                    duration_minutes=duration,
                    notes="",
                    activity_owner=owner,
                    **type_fields,
                ))

        # ============================================================== #
        #  Phase 3: Sort and assign sequential IDs                        #
        # ============================================================== #

        activities.sort(key=lambda a: (a.activity_date, a.account_id))
        for idx, activity in enumerate(activities, start=1):
            activity.activity_id = idx

        return activities
