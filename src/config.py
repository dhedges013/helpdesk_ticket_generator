import os
import logging
from datetime import datetime

DAYS_AGO = 365
MAX_CONVERSATION_ROUNDS = 7

TIME_ENTRY_MIN_COUNT = 1
TIME_ENTRY_MAX_COUNT = 4
TIME_ENTRY_MIN_DURATION_MINUTES = 15
TIME_ENTRY_MAX_DURATION_MINUTES = 120
TIME_ENTRY_DURATION_INTERVAL_MINUTES = 5


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
