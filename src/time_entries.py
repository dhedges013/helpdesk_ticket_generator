"""Utilities for generating realistic technician time entries for tickets."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from .config import (
    TIME_ENTRY_DURATION_INTERVAL_MINUTES,
    TIME_ENTRY_MAX_COUNT,
    TIME_ENTRY_MAX_DURATION_MINUTES,
    TIME_ENTRY_MIN_COUNT,
    TIME_ENTRY_MIN_DURATION_MINUTES,
    get_logger,
)
from .utils import (
    get_all_techs,
    get_all_time_entry_labor_types,
    get_all_time_entry_note_templates,
)

logger = get_logger(__name__)

DEFAULT_LABOR_TYPES: Sequence[str] = (
    "Remote Support",
    "Onsite Support",
    "Project Work",
    "Maintenance",
    "Research",
)

DEFAULT_NOTE_TEMPLATES: Sequence[str] = (
    "Documented progress on {subject}.",
    "Updated troubleshooting notes for {subject}.",
    "Recorded configuration changes related to {subject}.",
    "Added findings while reviewing {subject}.",
    "Captured follow-up actions for {subject}.",
)


def _load_labor_types() -> Sequence[str]:
    labor_types = [item for item in get_all_time_entry_labor_types() if item]
    if labor_types:
        return labor_types
    logger.warning(
        "Falling back to default labor types because time entry labor type data is unavailable."
    )
    return list(DEFAULT_LABOR_TYPES)


def _load_note_templates() -> Sequence[str]:
    note_templates = [item for item in get_all_time_entry_note_templates() if item]
    if note_templates:
        return note_templates
    logger.warning(
        "Falling back to default time entry note templates because dataset is unavailable."
    )
    return list(DEFAULT_NOTE_TEMPLATES)


LABOR_TYPES: Sequence[str] = tuple(_load_labor_types())
NOTE_TEMPLATES: Sequence[str] = tuple(_load_note_templates())

VISIBILITY_OPTIONS: Sequence[str] = ("Public", "Private")
VISIBILITY_WEIGHTS: Sequence[int] = (1, 3)

BILLABLE_OPTIONS: Sequence[str] = ("Billable", "Non-Billable")
BILLABLE_WEIGHTS: Sequence[int] = (3, 1)


@dataclass
class TimeEntryRecord:
    """Data representation for a single time entry."""

    customer: str
    ticket_number: int
    entry_sequence: int
    tech: str
    duration_minutes: int
    visibility: str
    billable_status: str
    labor_type: str
    created_at: datetime
    notes: str
    dependencies: List[int] = field(default_factory=list)

    def to_row(self) -> dict:
        """Convert the dataclass into a dictionary for CSV output."""

        return {
            "Customer": self.customer,
            "Ticket Number": self.ticket_number,
            "Entry Sequence": self.entry_sequence,
            "Tech": self.tech,
            "Duration Minutes": self.duration_minutes,
            "Visibility": self.visibility,
            "Billable Status": self.billable_status,
            "Labor Type": self.labor_type,
            "Created At": self.created_at,
            "Notes": self.notes,
            "Dependencies": ";".join(str(dep) for dep in self.dependencies),
        }


def _duration_choices() -> List[int]:
    """Return a list of allowed durations that honour the configured interval."""

    step = max(1, TIME_ENTRY_DURATION_INTERVAL_MINUTES)
    minimum = max(step, TIME_ENTRY_MIN_DURATION_MINUTES)
    maximum = max(minimum, TIME_ENTRY_MAX_DURATION_MINUTES)
    return list(range(minimum, maximum + step, step))


def _select_tech(assigned_tech: Optional[str], available_techs: Sequence[str]) -> str:
    """Select the technician responsible for the time entry."""

    if available_techs:
        weights = [3 if tech == assigned_tech and assigned_tech else 1 for tech in available_techs]
        return random.choices(available_techs, weights=weights, k=1)[0]

    if assigned_tech:
        return assigned_tech

    return "Unassigned"


def _generate_offsets(
    count: int,
    start_time: datetime,
    end_time: datetime,
    step: int,
) -> List[int]:
    """Generate time offsets (in minutes) for when entries were created."""

    if count <= 0:
        return []

    if end_time <= start_time:
        end_time = start_time + timedelta(minutes=step * count)

    total_minutes = max(step, int((end_time - start_time).total_seconds() // 60))
    possible_offsets = list(range(0, total_minutes + step, step))

    if len(possible_offsets) <= count:
        return [min(idx * step, possible_offsets[-1]) for idx in range(count)]

    return sorted(random.sample(possible_offsets, count))


def _prepare_dependencies(prior_entries: Sequence[dict]) -> List[int]:
    """Placeholder for future dependency mapping between time entries."""

    if not prior_entries:
        return []

    available = [entry.get("Entry Sequence") for entry in prior_entries if entry.get("Entry Sequence") is not None]
    if not available:
        return []

    max_dependencies = min(2, len(available))
    selected = random.sample(available, k=random.randint(0, max_dependencies)) if max_dependencies else []
    return sorted(selected)


def generate_time_entries(ticket: dict, prior_entries: Optional[Sequence[dict]] = None) -> List[dict]:
    """Generate discrete technician time entries for a ticket.

    Args:
        ticket: Ticket data dictionary.
        prior_entries: Existing time entries. Not currently used but available for
            future dependency-aware logic.

    Returns:
        A list of dictionaries representing generated time entries.
    """

    min_count = max(0, TIME_ENTRY_MIN_COUNT)
    max_count = max(min_count, TIME_ENTRY_MAX_COUNT)

    if max_count == 0:
        logger.info("Time entry generation skipped because the maximum count is 0.")
        return []

    entry_count = random.randint(min_count, max_count)
    if entry_count == 0:
        logger.info("No time entries generated for this ticket based on configuration.")
        return []

    durations = _duration_choices()
    if not durations:
        logger.warning("Unable to determine valid time entry durations. Skipping generation.")
        return []

    available_techs = [tech for tech in get_all_techs() if tech]
    assigned_tech = ticket.get("Assigned Tech")
    if assigned_tech and assigned_tech not in available_techs:
        available_techs.append(assigned_tech)

    customer = ticket.get("Customer", "Unknown Customer")
    ticket_number = ticket.get("Ticket Number", "Unknown Ticket")
    subject = ticket.get("Subject", "ticket work")

    start_time = ticket.get("Start Time")
    end_time = ticket.get("End Time")

    if not isinstance(start_time, datetime):
        start_time = datetime.now()
    if not isinstance(end_time, datetime):
        end_time = start_time + timedelta(minutes=durations[-1])

    offsets = _generate_offsets(entry_count, start_time, end_time, max(1, TIME_ENTRY_DURATION_INTERVAL_MINUTES))
    dependency_source = list(prior_entries) if prior_entries else None

    generated_entries: List[dict] = []

    for index in range(entry_count):
        duration = random.choice(durations)
        tech = _select_tech(assigned_tech, available_techs)
        visibility = random.choices(VISIBILITY_OPTIONS, weights=VISIBILITY_WEIGHTS, k=1)[0]
        billable = random.choices(BILLABLE_OPTIONS, weights=BILLABLE_WEIGHTS, k=1)[0]
        labor_type = random.choice(LABOR_TYPES)
        created_at = start_time + timedelta(minutes=offsets[index])
        notes = random.choice(NOTE_TEMPLATES).format(subject=subject, duration=duration, tech=tech)
        dependencies = _prepare_dependencies(dependency_source) if dependency_source else []

        record = TimeEntryRecord(
            customer=customer,
            ticket_number=ticket_number,
            entry_sequence=index + 1,
            tech=tech,
            duration_minutes=duration,
            visibility=visibility,
            billable_status=billable,
            labor_type=labor_type,
            created_at=created_at,
            notes=notes,
            dependencies=dependencies,
        )
        row = record.to_row()
        generated_entries.append(row)
        if dependency_source is not None:
            dependency_source.append(row)

    logger.info("Generated %s time entries for Ticket %s.", len(generated_entries), ticket_number)
    return generated_entries


__all__ = ["generate_time_entries"]
