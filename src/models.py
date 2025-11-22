"""Shared data models for tickets, conversations, and time entries."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

Ticket = TypedDict(
    "Ticket",
    {
        "Customer": str,
        "Ticket Number": int | str,
        "Contact": str,
        "Subject": str,
        "Status": str,
        "Description": str,
        "Issue Type": str,
        "Assigned Tech": str,
        "Priority": str,
        "Start Time": datetime,
        "End Time": datetime,
    },
)

ConversationMessage = TypedDict(
    "ConversationMessage",
    {
        "Customer": str,
        "Ticket Number": int | str,
        "speaker": str,
        "message": str,
        "timestamp": datetime,
    },
)

TimeEntry = TypedDict(
    "TimeEntry",
    {
        "Customer": str,
        "Ticket Number": int | str,
        "Entry Sequence": int,
        "Tech": str,
        "Duration Minutes": int,
        "Visibility": str,
        "Billable Status": str,
        "Labor Type": str,
        "Created At": datetime,
        "Notes": str,
        "Dependencies": str,
    },
)


__all__ = ["Ticket", "ConversationMessage", "TimeEntry"]
