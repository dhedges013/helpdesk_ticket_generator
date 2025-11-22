import json
import logging
import os
from datetime import datetime
from typing import Dict

# Path to the JSON configuration file that holds runtime-tunable values.
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "default_config.json")

# Defaults for the runtime-configurable knobs that can be tweaked via the CLI.
RUNTIME_DEFAULTS: Dict[str, int] = {
    "DAYS_AGO": 21,
    "MAX_CONVERSATION_ROUNDS": 4,
    "TIME_ENTRY_MIN_COUNT": 1,
    "TIME_ENTRY_MAX_COUNT": 4,
    "TIME_ENTRY_MIN_DURATION_MINUTES": 5,
    "TIME_ENTRY_MAX_DURATION_MINUTES": 90,
    "TIME_ENTRY_DURATION_INTERVAL_MINUTES": 5,
    "DAILY_TICKET_CAP": 10,
    "TIME_ENTRY_BUFFER_MINUTES": 5,
    "MAX_OPEN_TICKETS_PER_TECH": 10,
    "MAX_OPEN_TICKETS_UNASSIGNED": 500,
}

# Non-numeric runtime toggles
RUNTIME_FLAGS = {
    "OVERFLOW_BEHAVIOR": "reassign",
    "CLAMP_TO_NOW": True,
}

_runtime_settings: Dict[str, int] = {}


def _coerce_int(key: str, value: object) -> int:
    """Attempt to coerce *value* to an int, falling back to defaults on failure."""

    default_value = RUNTIME_DEFAULTS[key]
    try:
        return int(value)
    except (TypeError, ValueError):
        logging.warning(
            "Invalid value '%s' for %s. Reverting to default (%s).",
            value,
            key,
            default_value,
        )
        return default_value


def _normalize_settings(raw_settings: Dict[str, int]) -> Dict[str, int]:
    """Merge raw settings with defaults and ensure they are valid integers."""

    normalized: Dict[str, int] = {}
    for key, default_value in RUNTIME_DEFAULTS.items():
        normalized[key] = _coerce_int(key, raw_settings.get(key, default_value))
    return normalized


def _save_runtime_settings(settings: Dict[str, int]) -> None:
    """Persist runtime settings to the JSON configuration file."""

    payload = dict(settings)
    payload.update(RUNTIME_FLAGS)
    with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
        json.dump(payload, config_file, indent=2)


def _load_runtime_settings() -> Dict[str, int]:
    """Load runtime settings from disk, creating the file if necessary."""

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            file_settings = json.load(config_file)
    except FileNotFoundError:
        normalized = dict(RUNTIME_DEFAULTS)
        _save_runtime_settings(normalized)
        return normalized
    except json.JSONDecodeError:
        logging.warning(
            "Could not parse %s. Recreating the configuration file with defaults.",
            CONFIG_FILE,
        )
        normalized = dict(RUNTIME_DEFAULTS)
        _save_runtime_settings(normalized)
        return normalized

    # Refresh runtime flags from file while keeping defaults as fallback
    for key in RUNTIME_FLAGS:
        if key in file_settings:
            RUNTIME_FLAGS[key] = file_settings[key]

    return _normalize_settings(file_settings)


def _apply_runtime_settings(settings: Dict[str, int]) -> None:
    """Update module-level variables to reflect the latest runtime settings."""

    global _runtime_settings
    global DAYS_AGO
    global MAX_CONVERSATION_ROUNDS
    global TIME_ENTRY_MIN_COUNT
    global TIME_ENTRY_MAX_COUNT
    global TIME_ENTRY_MIN_DURATION_MINUTES
    global TIME_ENTRY_MAX_DURATION_MINUTES
    global TIME_ENTRY_DURATION_INTERVAL_MINUTES
    global DAILY_TICKET_CAP
    global TIME_ENTRY_BUFFER_MINUTES
    global MAX_OPEN_TICKETS_PER_TECH
    global MAX_OPEN_TICKETS_UNASSIGNED
    global OVERFLOW_BEHAVIOR
    global CLAMP_TO_NOW

    _runtime_settings = settings
    DAYS_AGO = settings["DAYS_AGO"]
    MAX_CONVERSATION_ROUNDS = settings["MAX_CONVERSATION_ROUNDS"]
    TIME_ENTRY_MIN_COUNT = settings["TIME_ENTRY_MIN_COUNT"]
    TIME_ENTRY_MAX_COUNT = settings["TIME_ENTRY_MAX_COUNT"]
    TIME_ENTRY_MIN_DURATION_MINUTES = settings["TIME_ENTRY_MIN_DURATION_MINUTES"]
    TIME_ENTRY_MAX_DURATION_MINUTES = settings["TIME_ENTRY_MAX_DURATION_MINUTES"]
    TIME_ENTRY_DURATION_INTERVAL_MINUTES = settings["TIME_ENTRY_DURATION_INTERVAL_MINUTES"]
    DAILY_TICKET_CAP = settings["DAILY_TICKET_CAP"]
    TIME_ENTRY_BUFFER_MINUTES = settings["TIME_ENTRY_BUFFER_MINUTES"]
    MAX_OPEN_TICKETS_PER_TECH = settings["MAX_OPEN_TICKETS_PER_TECH"]
    MAX_OPEN_TICKETS_UNASSIGNED = settings["MAX_OPEN_TICKETS_UNASSIGNED"]

    OVERFLOW_BEHAVIOR = RUNTIME_FLAGS.get("OVERFLOW_BEHAVIOR", "reassign")
    CLAMP_TO_NOW = bool(RUNTIME_FLAGS.get("CLAMP_TO_NOW", True))


def get_runtime_settings() -> Dict[str, int]:
    """Return a copy of the runtime settings currently in effect."""

    return dict(_runtime_settings)


def update_runtime_settings(overrides: Dict[str, int]) -> Dict[str, int]:
    """Merge overrides into the runtime settings, persist them, and return the result."""

    merged = dict(_runtime_settings)
    merged.update(overrides)
    normalized = _normalize_settings(merged)
    _save_runtime_settings(normalized)
    _apply_runtime_settings(normalized)
    return get_runtime_settings()


# Initialize runtime settings on import.
_apply_runtime_settings(_load_runtime_settings())


# Define base directory for generator data
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)

# Paths to specific files

TICKET_CONTACTS = os.path.join(BASE_DIR, 'data/generatorData/ticketContacts.csv')
TICKET_CUSTOMER = os.path.join(BASE_DIR, 'data/generatorData/ticketCustomer.csv')
TICKET_DESCRIPTION = os.path.join(BASE_DIR, 'data/generatorData/ticketDescription.csv')
TICKET_ISSUE_TYPES = os.path.join(BASE_DIR, 'data/generatorData/ticketIssueTypes.csv')
TICKET_PRIORITY = os.path.join(BASE_DIR, 'data/generatorData/ticketPriorities.csv')
TICKET_STATUS = os.path.join(BASE_DIR, 'data/generatorData/ticketStatus.csv')
TICKET_SUBJECT = os.path.join(BASE_DIR, 'data/generatorData/ticketSubject.csv')
TICKET_TECH = os.path.join(BASE_DIR, 'data/generatorData/ticketTech.csv')
TIME_ENTRY_LABOR_TYPES = os.path.join(BASE_DIR, 'data/generatorData/timeEntryLaborTypes.csv')
TIME_ENTRY_NOTE_TEMPLATES = os.path.join(BASE_DIR, 'data/generatorData/timeEntryNoteTemplates.csv')
OUTPUT_TICKETS = os.path.join(BASE_DIR, 'results/outputTickets.csv')
OUTPUT_CONVERSTATIONS = os.path.join(BASE_DIR, 'results/outputConversations.csv')
OUTPUT_TIME_ENTRIES = os.path.join(BASE_DIR, 'results/outputTimeEntries.csv')

# Feature toggles
ENABLE_TICKET_REVIEW_PROMPT = True

INITIAL_COMPLAINT = os.path.join(BASE_DIR, 'data/generatorData/initial_complaints.csv')
CUSTOMER_FOLLOWUP = os.path.join(BASE_DIR, 'data/generatorData/customer_followups.csv')
HELPDESK_RESPONSE = os.path.join(BASE_DIR, 'data/generatorData/helpdesk_responses.csv')

LOG_DIR = os.path.join(BASE_DIR, 'logs')

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a new log file with the current date and time
    log_file_name = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = os.path.join(LOG_DIR, log_file_name)
    os.makedirs(LOG_DIR, exist_ok=True)

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Remove other handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    return logger

# Reset root logger to prevent console logging
logging.getLogger().handlers.clear()
