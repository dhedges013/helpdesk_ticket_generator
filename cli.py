"""Command-line interface for managing helpdesk ticket generation workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src import config
import main as ticket_main


def prompt_yes_no(message: str, *, default: bool | None = None) -> bool:
    """Prompt the user with a yes/no question and return the response as a boolean."""

    suffix = " [y/n]: "
    if default is True:
        suffix = " [Y/n]: "
    elif default is False:
        suffix = " [y/N]: "

    while True:
        response = input(f"{message}{suffix}").strip().lower()
        if not response and default is not None:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")


def remove_files(paths: Iterable[Path]) -> None:
    """Attempt to remove each file in *paths*, ignoring missing files."""

    for path in paths:
        try:
            if path.exists():
                path.unlink()
                print(f"Removed {path}.")
            else:
                print(f"No existing file at {path}; skipping.")
        except OSError as exc:
            print(f"Failed to remove {path}: {exc}")


def clear_results_outputs() -> None:
    """Delete generated CSV output files if they exist."""

    results_paths = [
        Path(config.OUTPUT_TICKETS),
        Path(config.OUTPUT_CONVERSTATIONS),
        Path(config.OUTPUT_TIME_ENTRIES),
    ]
    for path in results_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    remove_files(results_paths)


def clear_logs() -> None:
    """Delete log files within the configured log directory."""

    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        print("No log files found to delete.")
        return

    remove_files(log_files)


def run_ticket_generation() -> None:
    """Invoke the main ticket generation workflow."""

    try:
        ticket_main.main()
    except Exception as exc:  # pragma: no cover - defensive logging for CLI execution
        print(f"An error occurred while running the ticket generator: {exc}")


def main() -> None:
    """Entry point for the CLI workflow."""

    print("Helpdesk Ticket Generator CLI")
    print("-" * 35)

    if prompt_yes_no("Clear existing result CSV files?", default=False):
        clear_results_outputs()

    if prompt_yes_no("Delete existing log files?", default=False):
        clear_logs()

    if prompt_yes_no("Run the ticket generator now?", default=True):
        run_ticket_generation()
    else:
        print("Ticket generation skipped.")


if __name__ == "__main__":
    main()
