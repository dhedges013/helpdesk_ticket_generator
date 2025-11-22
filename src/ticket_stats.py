"""Summarize generated ticket stats by technician."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from .config import OUTPUT_TICKETS, get_logger
from .probability import ProbabilityProfileRegistry, get_registry

logger = get_logger(__name__)


def _load_ticket_rows() -> List[Dict[str, Any]]:
    """Return ticket rows from the generated CSV, or an empty list if missing."""

    path = Path(OUTPUT_TICKETS)
    if not path.exists():
        logger.info("Ticket output not found at %s", OUTPUT_TICKETS)
        return []

    try:
        with path.open(newline="", encoding="utf-8") as csv_file:
            return list(csv.DictReader(csv_file))
    except Exception as exc:  # pragma: no cover - defensive logging only
        logger.error("Failed to load ticket data from %s: %s", OUTPUT_TICKETS, exc)
        return []


def _resolve_profile_name(registry: ProbabilityProfileRegistry, tech: str) -> str:
    """Look up the assigned profile for a tech, falling back to the default."""

    assignments = registry.get_tech_profile_mapping()
    if tech in assignments:
        return assignments[tech]
    return registry.get_default_profile().name


def summarize_ticket_stats() -> Dict[str, Dict[str, int | str]]:
    """Summarize ticket counts per technician, including resolved totals."""

    rows = _load_ticket_rows()
    if not rows:
        print("No ticket data available to summarize.")
        return {}

    registry = get_registry()
    summary: Dict[str, Dict[str, int | str]] = defaultdict(
        lambda: {"profile": "", "total": 0, "resolved": 0}
    )

    for row in rows:
        tech = (row.get("Assigned Tech") or "Unassigned").strip() or "Unassigned"
        status = (row.get("Status") or "").strip().lower()

        bucket = summary[tech]
        if not bucket["profile"]:
            bucket["profile"] = _resolve_profile_name(registry, tech)

        bucket["total"] += 1
        if status.startswith("resolved"):
            bucket["resolved"] += 1

    return dict(summary)


def display_ticket_stats() -> None:
    """Print a readable summary of ticket stats by technician."""

    summary = summarize_ticket_stats()
    if not summary:
        return

    print("\nTicket stats by technician:")
    for tech in sorted(summary):
        stats = summary[tech]
        total = int(stats.get("total", 0))
        resolved = int(stats.get("resolved", 0))
        profile = stats.get("profile", "")
        open_or_pending = max(0, total - resolved)
        print(
            f"- {tech} (profile: {profile}): {total} tickets "
            f"({resolved} resolved, {open_or_pending} open/pending)"
        )


if __name__ == "__main__":
    display_ticket_stats()
