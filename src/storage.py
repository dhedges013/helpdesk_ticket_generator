"""Utilities for persisting generated ticket data to CSV outputs."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Mapping, Sequence

from . import config

LOGGER = logging.getLogger(__name__)


def _validate_data_dict(data_dict: Mapping[str, Sequence], dataset_name: str, required: bool) -> None:
    """Validate the provided data dictionary before writing."""

    if not data_dict:
        message = (
            f"The {dataset_name} dictionary is empty."
            if required
            else f"No {dataset_name} data provided for CSV export."
        )
        raise ValueError(message)

    try:
        lengths = {len(values) for values in data_dict.values()}
    except Exception as exc:
        raise ValueError(f"Invalid {dataset_name} data structure: {exc}") from exc

    if not lengths:
        raise ValueError(f"The {dataset_name} dictionary is empty.")
    if len(lengths) != 1:
        raise ValueError(f"{dataset_name} dictionary values must have the same length.")


def write_dataset_to_csv(
    data_dict: Mapping[str, Sequence],
    file_path: Path,
    dataset_name: str,
) -> None:
    """Persist a dataset to CSV after validation."""

    _validate_data_dict(data_dict, dataset_name, required=True)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_exists = file_path.exists()
        with file_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(data_dict.keys())
            for row in zip(*data_dict.values()):
                writer.writerow(row)

        LOGGER.info("Appended %s data to %s", dataset_name, file_path)
    except Exception as exc:
        raise IOError(f"Failed to append {dataset_name} data to {file_path}: {exc}") from exc


def write_tickets(ticket_data: Mapping[str, Sequence], *, path: Path | None = None) -> None:
    """Write ticket data to CSV."""

    target = Path(path) if path else Path(config.OUTPUT_TICKETS)
    write_dataset_to_csv(ticket_data, target, "Ticket")


def write_conversations(conversation_data: Mapping[str, Sequence], *, path: Path | None = None) -> None:
    """Write conversation data to CSV."""

    target = Path(path) if path else Path(config.OUTPUT_CONVERSTATIONS)
    write_dataset_to_csv(conversation_data, target, "Conversation")


def write_time_entries(time_entry_data: Mapping[str, Sequence] | None, *, path: Path | None = None) -> None:
    """Write time entry data to CSV if provided."""

    if time_entry_data is None:
        LOGGER.info("No time entry data provided for CSV export.")
        return

    target = Path(path) if path else Path(config.OUTPUT_TIME_ENTRIES)
    write_dataset_to_csv(time_entry_data, target, "Time entry")


def append_dict_to_csv(ticket_data, conversation_data, time_entry_data=None) -> None:
    """Compatibility wrapper used by legacy callers."""

    write_tickets(ticket_data)
    write_conversations(conversation_data)
    write_time_entries(time_entry_data)


__all__ = [
    "write_dataset_to_csv",
    "write_tickets",
    "write_conversations",
    "write_time_entries",
    "append_dict_to_csv",
]
