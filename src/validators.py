"""Validation helpers for ensuring generated data remains realistic."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from . import config
from .utils import get_all_techs

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
    open_tickets_by_tech_day: Dict[Tuple[str, date], int] = field(
        default_factory=lambda: defaultdict(int)
    )
    available_techs: List[str] = field(default_factory=list)


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
        if state.tickets_by_tech_day[(tech, day)] >= self.daily_cap:
            logger.info(
                "Daily cap reached for %s on %s; attempting reassignment.",
                tech,
                day,
            )
            overflow_tech = self._reassign(ticket, state)
            if overflow_tech:
                tech = overflow_tech
                ticket["Assigned Tech"] = tech
                day = ticket["Start Time"].date()

        state.tickets_by_tech_day[(tech, day)] += 1
        return ticket

    def _reassign(self, ticket: dict, state: ValidationState) -> Optional[str]:
        candidates = state.available_techs
        original = ticket.get("Assigned Tech")
        day = ticket.get("Start Time").date() if isinstance(ticket.get("Start Time"), datetime) else None
        for tech in candidates:
            if tech == original:
                continue
            if day is None:
                continue
            if state.tickets_by_tech_day[(tech, day)] < self.daily_cap:
                logger.info("Reassigning ticket %s from %s to %s to respect daily cap.", ticket.get("Ticket Number"), original, tech)
                return tech

        return "Unassigned"


class MaxOpenTicketsValidator(TicketValidator):
    """Prevent exceeding concurrent open-ticket caps by reassignment, not future dates."""

    def __init__(self, per_tech_cap: int, unassigned_cap: int, clamp_to_now: bool, available_techs: List[str]):
        self.per_tech_cap = max(1, per_tech_cap)
        self.unassigned_cap = max(1, unassigned_cap)
        self.clamp_to_now = clamp_to_now
        self.available_techs = [tech for tech in available_techs if tech]

    def _clamp_times(self, ticket: dict) -> dict:
        if not self.clamp_to_now:
            return ticket

        now = datetime.now()
        start_time = ticket.get("Start Time")
        end_time = ticket.get("End Time")

        if isinstance(start_time, datetime) and start_time > now:
            ticket["Start Time"] = now
            start_time = now

        if isinstance(end_time, datetime):
            if end_time > now:
                ticket["End Time"] = now
                end_time = now
        else:
            ticket["End Time"] = now
            end_time = now

        if isinstance(start_time, datetime) and isinstance(end_time, datetime) and end_time < start_time:
            ticket["End Time"] = start_time

        return ticket

    def _occupancy_days(self, start_time: datetime, closed_time: datetime) -> List[date]:
        start_day = start_time.date()
        end_day = closed_time.date()
        if end_day < start_day:
            end_day = start_day

        days: List[date] = []
        current = start_day
        while current <= end_day:
            days.append(current)
            current += timedelta(days=1)
        return days

    def _increment_open(self, tech: str, days: List[date], state: ValidationState) -> None:
        for day in days:
            state.open_tickets_by_tech_day[(tech, day)] += 1

    def _open_cap(self, tech: str, day: date, state: ValidationState) -> int:
        return state.open_tickets_by_tech_day[(tech, day)]

    def _span_over_cap(self, tech: str, days: List[date], cap: int, state: ValidationState) -> bool:
        return any(self._open_cap(tech, day, state) >= cap for day in days)

    def _select_overflow_tech(self, original: str, days: List[date], state: ValidationState) -> str:
        for tech in self.available_techs:
            if tech == original:
                continue
            if not self._span_over_cap(tech, days, self.per_tech_cap, state):
                logger.info("Reassigning ticket from %s to %s due to open-cap overflow.", original, tech)
                return tech

        unassigned_over = self._span_over_cap("Unassigned", days, self.unassigned_cap, state)
        if unassigned_over:
            logger.warning("Unassigned open-cap exceeded; continuing to assign to Unassigned.")
        return "Unassigned"

    def validate(self, ticket: dict, state: ValidationState) -> dict:
        ticket = self._clamp_times(ticket)

        tech = ticket.get("Assigned Tech") or "Unassigned"
        start_time = ticket.get("Start Time")
        closed_time = ticket.get("Closed At") or start_time

        if not isinstance(start_time, datetime) or not isinstance(closed_time, datetime):
            return ticket

        days = self._occupancy_days(start_time, closed_time)

        current_over = self._span_over_cap(tech, days, self.unassigned_cap if tech == "Unassigned" else self.per_tech_cap, state)
        if tech == "Unassigned":
            cap = self.unassigned_cap
        else:
            cap = self.per_tech_cap

        if current_over or self._span_over_cap(tech, days, cap, state):
            tech = self._select_overflow_tech(tech, days, state)
            ticket["Assigned Tech"] = tech

        self._increment_open(tech, days, state)
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
                ticket["End Time"] = min(datetime.now(), max(ticket_end, actual_end))
            else:
                ticket["End Time"] = min(datetime.now(), actual_end)

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
        now = datetime.now()

        while True:
            key = (tech, start_candidate.date())
            blocks = state.time_blocks_by_tech_day[key]
            conflict_end = self._find_conflict(blocks, start_candidate, duration_delta)

            if conflict_end:
                start_candidate = conflict_end
                continue

            # Do not allow blocks to extend into the future
            latest_start = now - duration_delta
            if start_candidate > latest_start:
                start_candidate = latest_start
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
        available_techs = get_all_techs() or []
        if "Unassigned" not in available_techs:
            available_techs.append("Unassigned")

        self.state = ValidationState(daily_cap=daily_ticket_cap, available_techs=available_techs)
        self.ticket_validators: List[TicketValidator] = [
            MaxOpenTicketsValidator(
                per_tech_cap=config.MAX_OPEN_TICKETS_PER_TECH,
                unassigned_cap=config.MAX_OPEN_TICKETS_UNASSIGNED,
                clamp_to_now=config.CLAMP_TO_NOW,
                available_techs=available_techs,
            ),
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
