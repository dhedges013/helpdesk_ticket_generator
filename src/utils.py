import logging
import csv
import random
import os
from datetime import datetime
from typing import Optional, Sequence

from .config import (
    TICKET_CONTACTS,
    TICKET_CUSTOMER,
    TICKET_DESCRIPTION,
    TICKET_ISSUE_TYPES,
    TICKET_PRIORITY,
    TICKET_STATUS,
    TICKET_SUBJECT,
    TICKET_TECH,
    TIME_ENTRY_LABOR_TYPES,
    TIME_ENTRY_NOTE_TEMPLATES,
)
from .storage import append_dict_to_csv
from .config import get_logger
from .probability import ProbabilityProfile

logger = get_logger(__name__)


def _weighted_choice(category: str, values: Sequence[str], profile: Optional[ProbabilityProfile]) -> Optional[str]:
    """Return a weighted selection using the provided profile, if any."""

    filtered = [value for value in values if value]
    if not filtered:
        return None

    if profile:
        selection = profile.pick(category, filtered)
        if selection:
            return selection

    return random.choice(filtered)

# Base function to load data from a CSV file
def load_csv_data(file_path):
    try:
        logging.debug(f"Attempting to load data from {file_path}")
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = [row[0] for row in reader]  # Assumes single-column CSV
            if not data:
                logging.warning(f"Warning: {file_path} is empty.")
            logging.info(f"Loaded {len(data)} records from {file_path}")
            return data
    except FileNotFoundError:
        logging.error(f"Error: File not found at {file_path}")
        return []
    except PermissionError:
        logging.error(f"Error: Permission denied while trying to read {file_path}")
        return []
    except UnicodeDecodeError:
        logging.error(f"Error: Could not decode the file {file_path}. Please check the file encoding.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading file {file_path}: {e}")
        return []

# Retrieve all data from CSV files
def get_all_contacts():
    logging.debug("Fetching all contacts.")
    contacts = load_csv_data(TICKET_CONTACTS)
    if not contacts:
        logging.error("Failed to fetch contacts data.")
    return contacts

def get_all_customers():
    logging.debug("Fetching all customers.")
    customers = load_csv_data(TICKET_CUSTOMER)
    if not customers:
        logging.error("Failed to fetch customer data.")
    return customers

def get_all_descriptions():
    logging.debug("Fetching all descriptions.")
    descriptions = load_csv_data(TICKET_DESCRIPTION)
    if not descriptions:
        logging.error("Failed to fetch description data.")
    return descriptions

def get_all_issue_types():
    logging.debug("Fetching all issue types.")
    issue_types = load_csv_data(TICKET_ISSUE_TYPES)
    if not issue_types:
        logging.error("Failed to fetch issue type data.")
    return issue_types

def get_all_priorities():
    logging.debug("Fetching all priorities.")
    priorities = load_csv_data(TICKET_PRIORITY)
    if not priorities:
        logging.error("Failed to fetch priority data.")
    return priorities

def get_all_statuses():
    logging.debug("Fetching all statuses.")
    statuses = load_csv_data(TICKET_STATUS)
    if not statuses:
        logging.error("Failed to fetch status data.")
    return statuses

def get_all_subjects():
    logging.debug("Fetching all subjects.")
    subjects = load_csv_data(TICKET_SUBJECT)
    if not subjects:
        logging.error("Failed to fetch subject data.")
    return subjects

def get_all_techs():
    logging.debug("Fetching all techs.")
    techs = load_csv_data(TICKET_TECH)
    if not techs:
        logging.error("Failed to fetch tech data.")
    return techs


def get_all_time_entry_labor_types():
    logging.debug("Fetching all time entry labor types.")
    labor_types = load_csv_data(TIME_ENTRY_LABOR_TYPES)
    if not labor_types:
        logging.error("Failed to fetch time entry labor type data.")
    return labor_types


def get_all_time_entry_note_templates():
    logging.debug("Fetching all time entry note templates.")
    note_templates = load_csv_data(TIME_ENTRY_NOTE_TEMPLATES)
    if not note_templates:
        logging.error("Failed to fetch time entry note template data.")
    return note_templates

# Retrieve random data from CSV files
def get_random_contact():
    try:
        contacts = get_all_contacts()
        if contacts:
            contact = random.choice(contacts)
            logging.info(f"Random contact selected: {contact}")
            return contact
        else:
            logging.error("Error: No contacts available.")
            return None
    except Exception as e:
        logging.error(f"Error selecting random contact: {e}")
        return None

def get_random_customer():
    try:
        customers = get_all_customers()
        if customers:
            customer = random.choice(customers)
            logging.info(f"Random customer selected: {customer}")
            return customer
        else:
            logging.error("Error: No customers available.")
            return None
    except Exception as e:
        logging.error(f"Error selecting random customer: {e}")
        return None

def get_random_description():
    try:
        descriptions = get_all_descriptions()
        if descriptions:
            description = random.choice(descriptions)
            logging.info(f"Random description selected: {description}")
            return description
        else:
            logging.error("Error: No descriptions available.")
            return None
    except Exception as e:
        logging.error(f"Error selecting random description: {e}")
        return None

def get_random_issue_type(profile: Optional[ProbabilityProfile] = None):
    try:
        issue_types = get_all_issue_types()
        if issue_types:
            issue_type = _weighted_choice("issue_type", issue_types, profile)
            if issue_type:
                logging.info(f"Random issue type selected: {issue_type}")
                return issue_type
        logging.error("Error: No issue types available.")
        return None
    except Exception as e:
        logging.error(f"Error selecting random issue type: {e}")
        return None

def get_random_priority(profile: Optional[ProbabilityProfile] = None):
    try:
        priorities = get_all_priorities()
        if priorities:
            priority = _weighted_choice("priority", priorities, profile)
            if priority:
                logging.info(f"Random priority selected: {priority}")
                return priority
        logging.error("Error: No priorities available.")
        return None
    except Exception as e:
        logging.error(f"Error selecting random priority: {e}")
        return None

def get_random_status(profile: Optional[ProbabilityProfile] = None):
    try:
        statuses = get_all_statuses()
        if statuses:
            status = _weighted_choice("status", statuses, profile)
            if status:
                logging.info(f"Random status selected: {status}")
                return status
        logging.error("Error: No statuses available.")
        return None
    except Exception as e:
        logging.error(f"Error selecting random status: {e}")
        return None

def get_random_subject(profile: Optional[ProbabilityProfile] = None):
    try:
        subjects = get_all_subjects()
        if subjects:
            subject = _weighted_choice("subject", subjects, profile)
            if subject:
                logging.info(f"Random subject selected: {subject}")
                return subject
        logging.error("Error: No subjects available.")
        return None
    except Exception as e:
        logging.error(f"Error selecting random subject: {e}")
        return None

def get_random_tech():
    try:
        techs = get_all_techs()
        if techs:
            tech = random.choice(techs)
            logging.info(f"Random tech selected: {tech}")
            return tech
        else:
            logging.error("Error: No techs available.")
            return None
    except Exception as e:
        logging.error(f"Error selecting random tech: {e}")
        return None
