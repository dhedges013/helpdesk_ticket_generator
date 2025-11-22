"""Utility for combining ticket and conversation CSVs into Syncro-friendly output."""
from __future__ import annotations

import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping

try:
    from src import config as app_config  # type: ignore
except Exception:  # pragma: no cover - fallback for standalone execution
    app_config = None


LOGGER = logging.getLogger(__name__)


HEADERS = [
    "ticket customer",
    "ticket number",
    "tech",
    "end user",
    "comment owner",
    "ticket subject",
    "ticket description",
    "ticket response",
    "timestamp",
    "email body",
    "ticket status",
    "ticket issue type",
    "ticket created date",
    "ticket priority",
]


def _default_results_path(attr_name: str, fallback_filename: str) -> Path:
    """Return the configured results path for *attr_name* or a sensible fallback."""

    if app_config is not None and hasattr(app_config, attr_name):
        return Path(getattr(app_config, attr_name))
    return Path(__file__).resolve().parent / "results" / fallback_filename


DEFAULT_TICKETS_PATH = _default_results_path("OUTPUT_TICKETS", "outputTickets.csv")
DEFAULT_CONVERSATIONS_PATH = _default_results_path(
    "OUTPUT_CONVERSTATIONS", "outputConversations.csv"
)
DEFAULT_OUTPUT_PATH = DEFAULT_TICKETS_PATH.parent / "syncro_combined.csv"


def read_csv_rows(path: Path) -> list[MutableMapping[str, str]]:
    """Read *path* as a CSV file and return a list of dictionaries."""

    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV at {path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Unable to read CSV {path}: {exc}") from exc


def normalize_key(value: str | None) -> str:
    """Normalize a string value for dictionary keys."""

    return (value or "").strip()


def select_first(*values: str | None) -> str:
    """Return the first non-empty string from *values* or an empty string."""

    for value in values:
        if value:
            candidate = value.strip()
            if candidate:
                return candidate
    return ""


def format_timestamp(value: str | None) -> str:
    """Strip microseconds from a timestamp string when possible."""

    text = (value or "").strip()
    if not text:
        return ""

    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        if "." in text:
            return text.split(".", 1)[0]
        return text


def build_output_row(
    ticket_row: Mapping[str, str] | None,
    conversation_row: Mapping[str, str] | None,
) -> dict[str, str]:
    """Create an output row from *ticket_row* and *conversation_row*."""

    ticket_customer = select_first(
        conversation_row.get("Customer") if conversation_row else None,
        ticket_row.get("Customer") if ticket_row else None,
    )
    ticket_number = select_first(
        conversation_row.get("Ticket Number") if conversation_row else None,
        ticket_row.get("Ticket Number") if ticket_row else None,
    )

    return {
        "ticket customer": ticket_customer,
        "ticket number": ticket_number,
        "tech": select_first(
            ticket_row.get("Assigned Tech") if ticket_row else None,
            conversation_row.get("speaker") if conversation_row else None,
        ),
        "end user": select_first(
            ticket_row.get("Contact") if ticket_row else None,
            conversation_row.get("speaker") if conversation_row else None,
        ),
        "comment owner": select_first(
            conversation_row.get("speaker") if conversation_row else None
        ),
        "ticket subject": select_first(ticket_row.get("Subject") if ticket_row else None),
        "ticket description": select_first(ticket_row.get("Description") if ticket_row else None),
        "ticket response": select_first(ticket_row.get("Description") if ticket_row else None),
        "timestamp": format_timestamp(
            select_first(conversation_row.get("timestamp") if conversation_row else None)
        ),
        "email body": select_first(conversation_row.get("message") if conversation_row else None),
        "ticket status": select_first(ticket_row.get("Status") if ticket_row else None),
        "ticket issue type": select_first(ticket_row.get("Issue Type") if ticket_row else None),
        "ticket created date": format_timestamp(
            select_first(ticket_row.get("Start Time") if ticket_row else None)
        ),
        "ticket priority": select_first(ticket_row.get("Priority") if ticket_row else None),
    }


def combine_data(
    tickets_rows: Iterable[Mapping[str, str]],
    conversation_rows: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Merge ticket and conversation rows keyed by ticket number and customer."""

    tickets_by_key: dict[tuple[str, str], Mapping[str, str]] = {}
    for row in tickets_rows:
        key = (
            normalize_key(row.get("Ticket Number")),
            normalize_key(row.get("Customer")),
        )
        if key not in tickets_by_key:
            tickets_by_key[key] = row

    conversations_by_key: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in conversation_rows:
        key = (
            normalize_key(row.get("Ticket Number")),
            normalize_key(row.get("Customer")),
        )
        conversations_by_key.setdefault(key, []).append(row)

    output_rows: list[dict[str, str]] = []
    all_keys = set(tickets_by_key) | set(conversations_by_key)

    for key in sorted(all_keys):
        ticket_row = tickets_by_key.get(key)
        conversations = conversations_by_key.get(key)

        if conversations:
            for conversation_row in sorted(
                conversations,
                key=lambda row: normalize_key(row.get("timestamp")),
            ):
                output_rows.append(build_output_row(ticket_row, conversation_row))
        else:
            output_rows.append(build_output_row(ticket_row, None))

    return output_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write *rows* to *path* with the expected headers."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_inputs(tickets_path: Path, conversations_path: Path) -> tuple[list[MutableMapping[str, str]], list[MutableMapping[str, str]]]:
    """Load ticket and conversation CSVs from disk."""

    if not tickets_path.exists():
        raise FileNotFoundError(f"Ticket CSV not found: {tickets_path}")
    if not conversations_path.exists():
        raise FileNotFoundError(f"Conversation CSV not found: {conversations_path}")

    tickets_rows = read_csv_rows(tickets_path)
    conversation_rows = read_csv_rows(conversations_path)
    return tickets_rows, conversation_rows


def merge_syncro_rows(
    tickets_rows: Iterable[Mapping[str, str]],
    conversation_rows: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Public wrapper to combine ticket and conversation rows."""

    return combine_data(tickets_rows, conversation_rows)


def write_syncro_csv(output_path: Path, rows: list[dict[str, str]]) -> None:
    """Persist merged rows to the Syncro-formatted CSV."""

    write_csv(output_path, rows)


def run(tickets_path: Path, conversations_path: Path, output_path: Path) -> int:
    """Execute the merge workflow and return an exit code."""

    tickets_rows, conversation_rows = load_inputs(tickets_path, conversations_path)
    combined_rows = merge_syncro_rows(tickets_rows, conversation_rows)
    write_syncro_csv(output_path, combined_rows)
    LOGGER.info("Combined %s rows into %s", len(combined_rows), output_path)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Combine ticket and conversation CSV exports into a Syncro-formatted "
            "CSV file."
        )
    )
    parser.add_argument(
        "--tickets",
        type=Path,
        default=DEFAULT_TICKETS_PATH,
        help="Path to OutputTickets.csv (default: results/outputTickets.csv).",
    )
    parser.add_argument(
        "--conversations",
        type=Path,
        default=DEFAULT_CONVERSATIONS_PATH,
        help="Path to outputConversations.csv (default: results/outputConversations.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination path for the combined Syncro CSV output.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for generating the combined Syncro CSV file."""

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)

    args = parse_args()

    try:
        raise SystemExit(run(args.tickets, args.conversations, args.output))
    except Exception as exc:
        LOGGER.error("Failed to generate combined Syncro CSV: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
