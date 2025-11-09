"""Utilities for interactively reviewing generated ticket data."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Iterable, List, Optional

from .config import (
    ENABLE_TICKET_REVIEW_PROMPT,
    OUTPUT_CONVERSTATIONS,
    OUTPUT_TICKETS,
    OUTPUT_TIME_ENTRIES,
    get_logger,
)

logger = get_logger(__name__)


def _load_structured_rows(file_path: str, dataset_name: str, required: bool = True) -> List[Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        log = logger.warning if required else logger.info
        log("%s does not exist at %s", dataset_name, file_path)
        return []

    try:
        with path.open(newline="", encoding="utf-8") as csv_file:
            return list(csv.DictReader(csv_file))
    except Exception as exc:  # pragma: no cover - defensive logging only
        logger.error("Failed to load %s data from %s: %s", dataset_name, file_path, exc)
        return []


def _format_timestamp(value: Any) -> Any:
    if not value:
        return value

    if isinstance(value, datetime):
        timestamp = value
    else:
        try:
            timestamp = datetime.fromisoformat(str(value))
        except ValueError:
            logger.debug("Unable to parse timestamp '%s'. Returning original value.", value)
            return value

    return timestamp.strftime("%B %d, %Y %I:%M %p")


def _format_ticket_info(ticket_row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not ticket_row:
        return {}

    return {
        "Customer": ticket_row.get("Customer", ""),
        "Contact": ticket_row.get("Contact", ""),
        "Subject": ticket_row.get("Subject", ""),
        "Status": ticket_row.get("Status", ""),
        "Description": ticket_row.get("Description", ""),
        "Issue Type": ticket_row.get("Issue Type", ""),
        "Assigned Tech": ticket_row.get("Assigned Tech", ""),
        "Priority": ticket_row.get("Priority", ""),
        "Start Time": _format_timestamp(ticket_row.get("Start Time")),
        "End Time": _format_timestamp(ticket_row.get("End Time")),
    }


def _format_conversations(conversation_rows: Iterable[Dict[str, Any]]) -> List[List[Any]]:
    formatted: List[List[Any]] = []
    for row in conversation_rows:
        formatted.append(
            [
                row.get("speaker", ""),
                row.get("message", ""),
                _format_timestamp(row.get("timestamp")),
            ]
        )
    return formatted


def _format_time_entries(time_entry_rows: Iterable[Dict[str, Any]]) -> List[List[Any]]:
    formatted: List[List[Any]] = []
    for row in time_entry_rows:
        duration = row.get("Duration Minutes", "")
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            pass

        formatted.append(
            [
                row.get("Tech", ""),
                duration,
                row.get("Visibility", ""),
                row.get("Billable Status", ""),
                row.get("Labor Type", ""),
                _format_timestamp(row.get("Created At")),
                row.get("Notes", ""),
            ]
        )
    return formatted


def _select_completed_ticket() -> Optional[Dict[str, Any]]:
    tickets = _load_structured_rows(OUTPUT_TICKETS, "Ticket data")
    conversations = _load_structured_rows(OUTPUT_CONVERSTATIONS, "Conversation data")
    time_entries = _load_structured_rows(OUTPUT_TIME_ENTRIES, "Time entry data", required=False)

    if not tickets or not conversations:
        logger.info("Insufficient data to build a completed ticket for review.")
        return None

    tickets_by_number = {
        str(ticket.get("Ticket Number")): ticket
        for ticket in tickets
        if ticket.get("Ticket Number")
    }

    conversations_by_number: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in conversations:
        ticket_number = row.get("Ticket Number")
        if ticket_number:
            conversations_by_number[str(ticket_number)].append(row)

    time_entries_by_number: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in time_entries:
        ticket_number = row.get("Ticket Number")
        if ticket_number:
            time_entries_by_number[str(ticket_number)].append(row)

    available_ticket_numbers = [
        ticket_number
        for ticket_number in tickets_by_number
        if ticket_number in conversations_by_number
    ]

    if not available_ticket_numbers:
        logger.info("No overlapping ticket and conversation data available for review.")
        return None

    selected_ticket_number = random.choice(available_ticket_numbers)
    ticket_info = _format_ticket_info(tickets_by_number[selected_ticket_number])
    conversation_items = _format_conversations(conversations_by_number[selected_ticket_number])
    time_entry_items = _format_time_entries(time_entries_by_number.get(selected_ticket_number, []))

    return {
        selected_ticket_number: {
            "Ticket Info": ticket_info,
            "Messages": conversation_items,
            "Time Entries": time_entry_items,
        }
    }


def prompt_for_ticket_review() -> None:
    """Interactively offer a preview of a completed ticket after generation."""

    if not ENABLE_TICKET_REVIEW_PROMPT:
        return

    while True:
        response = input("Would you like to review a completed ticket? (y/n): ").strip().lower()
        if response in {"y", "yes"}:
            completed_ticket = _select_completed_ticket()
            if completed_ticket:
                pprint(completed_ticket)
            else:
                print("No completed ticket data available for review.")
            break
        if response in {"n", "no"}:
            break
        print("Please enter 'y' or 'n'.")
