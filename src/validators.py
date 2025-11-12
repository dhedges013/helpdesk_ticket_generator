"""Validation helpers for ensuring generated data remains realistic."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from . import config

logger = config.get_logger(__name__)


@dataclass
class ValidationState:
    daily_cap: int
    tickets_by_tech_day: Dict[Tuple[str, date], int] = field(
        default_factory=lambda: defaultdict(int)
    )
    time_blocks_by_tech_day: Dict[Tuple[str, date], List[Tuple[datetime, datetime]]] = field(
        default_factory=lambda: defaultdict(list)
    )


class TicketValidator:
    def validate(self, ticket: dict, state: ValidationState) -> dict:  # pragma: no cover - interface
        raise NotImplementedError


class TimeEntryValidator:
    def validate(self, ticket: dict, entries: Sequence[dict], state: ValidationState) -> List[dict]:  # pragma: no cover - interface
        raise NotImplementedError


class DailyCapValidator(TicketValidator):
    """Ensure a technician does not exceed the configured tickets-per-day cap."""

    def __init__(self, daily_cap: int):
        self.daily_cap = max(1, daily_cap)

    def validate(self, ticket: dict, state: ValidationState) -> dict:
        tech = ticket.get("Assigned Tech")
        start_time = ticket.get("Start Time")
        end_time = ticket.get("End Time")
        if not tech or not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            return ticket

        day = start_time.date()
        while state.tickets_by_tech_day[(tech, day)] >= self.daily_cap:
            start_time += timedelta(days=1)
            end_time += timedelta(days=1)
            day = start_time.date()
            logger.debug(
                "Adjusted ticket %s for %s to %s to respect daily cap.",
                ticket.get("Ticket Number"),
                tech,
                day,
            )

        ticket["Start Time"] = start_time
        ticket["End Time"] = end_time
        state.tickets_by_tech_day[(tech, day)] += 1
        return ticket


class NonOverlapTimeEntryValidator(TimeEntryValidator):
    """Enforce sequential, non-overlapping time entries for a tech on a given day."""

    def __init__(self, buffer_minutes: int):
        self.buffer = max(0, buffer_minutes)

    def validate(self, ticket: dict, entries: Sequence[dict], state: ValidationState) -> List[dict]:
        if not entries:
            return list(entries)

        adjusted_entries: List[dict] = []

        for entry in sorted(entries, key=lambda item: item.get("Created At") or datetime.min):
            created_at = entry.get("Created At")
            duration = entry.get("Duration Minutes")
            tech = entry.get("Tech") or ticket.get("Assigned Tech") or "Unassigned"

            if not isinstance(created_at, datetime):
                adjusted_entries.append(entry)
                continue

            try:
                duration_minutes = int(duration)
            except (TypeError, ValueError):
                duration_minutes = 0

            if duration_minutes <= 0:
                adjusted_entries.append(entry)
                continue

            duration_delta = timedelta(minutes=duration_minutes)
            scheduled_start = self._schedule_entry(tech, created_at, duration_delta, state)

            entry["Created At"] = scheduled_start
            actual_end = scheduled_start + duration_delta

            ticket_end = ticket.get("End Time")
            if isinstance(ticket_end, datetime):
                ticket["End Time"] = max(ticket_end, actual_end)
            else:
                ticket["End Time"] = actual_end

            adjusted_entries.append(entry)

        return adjusted_entries

    def _schedule_entry(
        self,
        tech: str,
        desired_start: datetime,
        duration_delta: timedelta,
        state: ValidationState,
    ) -> datetime:
        """Find the next available, non-overlapping start time."""

        start_candidate = desired_start
        buffer_delta = timedelta(minutes=self.buffer)

        while True:
            key = (tech, start_candidate.date())
            blocks = state.time_blocks_by_tech_day[key]
            conflict_end = self._find_conflict(blocks, start_candidate, duration_delta)

            if conflict_end:
                start_candidate = conflict_end
                continue

            block_end = start_candidate + duration_delta + buffer_delta
            blocks.append((start_candidate, block_end))
            blocks.sort(key=lambda pair: pair[0])
            return start_candidate

    @staticmethod
    def _find_conflict(
        blocks: Sequence[Tuple[datetime, datetime]],
        start: datetime,
        duration_delta: timedelta,
    ) -> Optional[datetime]:
        """Return the end of the block causing a conflict, if any."""

        end = start + duration_delta
        for existing_start, existing_end in blocks:
            if end <= existing_start:
                return None
            if start < existing_end:
                return existing_end
        return None


class ValidatorPipeline:
    """Co-ordinate the configured ticket and time-entry validators."""

    def __init__(self, daily_ticket_cap: int, time_entry_buffer_minutes: int):
        self.state = ValidationState(daily_cap=daily_ticket_cap)
        self.ticket_validators: List[TicketValidator] = [
            DailyCapValidator(daily_ticket_cap),
        ]
        self.time_entry_validators: List[TimeEntryValidator] = [
            NonOverlapTimeEntryValidator(time_entry_buffer_minutes),
        ]

    def validate_ticket(self, ticket: dict) -> dict:
        for validator in self.ticket_validators:
            ticket = validator.validate(ticket, self.state)
        return ticket

    def validate_time_entries(self, ticket: dict, entries: Optional[Sequence[dict]]) -> List[dict]:
        normalized_entries = list(entries) if entries else []
        for validator in self.time_entry_validators:
            normalized_entries = validator.validate(ticket, normalized_entries, self.state)
        return normalized_entries


__all__ = [
    "ValidatorPipeline",
]
