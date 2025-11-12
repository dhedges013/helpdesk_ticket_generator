"""Command-line interface for managing helpdesk ticket generation workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from src import config, preferences, utils
import main as ticket_main


def _format_config_name(name: str) -> str:
    """Convert CONSTANT_STYLE names into friendlier labels."""

    return name.replace("_", " ").title()


def _format_horizontal_preview(values: Sequence[str], limit: int = 10) -> str:
    """Return a compact horizontal string of values with overflow indicator."""

    preview = [str(value) for value in values[:limit]]
    remainder = max(0, len(values) - len(preview))
    horizontal = " | ".join(preview) if preview else "(no entries)"
    if remainder:
        horizontal += f" | ... (+{remainder} more)"
    return horizontal


def _display_dataset(label: str, values: List[str]) -> None:
    """Pretty-print dataset values in a horizontal preview."""

    print(f"\n{label} ({len(values)} entries)")
    if not values:
        print("  No data available.")
        return

    print(f"  {_format_horizontal_preview(values)}")


def prompt_review_ticket_metadata() -> None:
    """Display the datasets that power ticket generation."""

    datasets = [
        ("Customers", utils.get_all_customers),
        ("Technicians", utils.get_all_techs),
        ("Labor Types", utils.get_all_time_entry_labor_types),
        ("Ticket Statuses", utils.get_all_statuses),
        ("Issue Types", utils.get_all_issue_types),
    ]

    print("\nTicket metadata overview:")
    for label, loader in datasets:
        try:
            values = loader() or []
        except Exception as exc:  # pragma: no cover - defensive CLI logging
            print(f"\n{label}: Unable to load data ({exc})")
            continue
        _display_dataset(label, list(values))


def _prompt_yes_no_memorized(key: str, message: str, *, default: bool | None = None) -> bool:
    """Return a remembered yes/no choice, prompting only the first time."""

    stored_choice = preferences.get_bool(key)
    if isinstance(stored_choice, bool):
        response_text = "Yes" if stored_choice else "No"
        print(f"{message} {response_text} (remembered).")
        return stored_choice

    choice = prompt_yes_no(message, default=default)
    preferences.remember_bool(key, choice)
    return choice


def prompt_for_runtime_configuration() -> None:
    """Display current generator settings and offer an interactive editor."""

    settings = config.get_runtime_settings()

    print("\nCurrent generator settings:")
    for key in config.RUNTIME_DEFAULTS:
        print(f"  {_format_config_name(key)}: {settings.get(key)}")

    if not prompt_yes_no("Would you like to change and save any of these values?", default=False):
        return

    updates = {}
    for key in config.RUNTIME_DEFAULTS:
        current_value = settings.get(key)
        prompt = (
            f"Enter a new value for {_format_config_name(key)} "
            f"(current: {current_value}) or press Enter to keep: "
        )
        response = input(prompt).strip()
        if not response:
            continue
        try:
            updates[key] = int(response)
        except ValueError:
            print("Invalid input. Please enter a whole number or press Enter to keep the current value.")

    if not updates:
        print("No configuration changes saved.")
        return

    new_settings = config.update_runtime_settings(updates)
    print("\nUpdated generator settings:")
    for key in config.RUNTIME_DEFAULTS:
        print(f"  {_format_config_name(key)}: {new_settings.get(key)}")


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

    prompt_for_runtime_configuration()
    prompt_review_ticket_metadata()

    if _prompt_yes_no_memorized("clear_results", "Clear existing result CSV files?", default=False):
        clear_results_outputs()

    if _prompt_yes_no_memorized("clear_logs", "Delete existing log files?", default=False):
        clear_logs()

    if _prompt_yes_no_memorized("run_generator", "Run the ticket generator now?", default=True):
        run_ticket_generation()
    else:
        print("Ticket generation skipped.")


if __name__ == "__main__":
    main()
