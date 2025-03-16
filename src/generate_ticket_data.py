import logging
from datetime import datetime, timedelta
import random
from .config import DAYS_AGO, get_logger
from .utils import (
    get_random_contact, get_random_customer, get_random_description,
    get_random_issue_type, get_random_priority, get_random_status,
    get_random_subject, get_random_tech
)

logger = get_logger(__name__)

# Generate a random datetime within the past week
def generate_random_datetime():
    try:
        now = datetime.now()
        past_time = now - timedelta(days=DAYS_AGO)
        random_datetime = past_time + (now - past_time) * random.random()
        logging.debug(f"Generated random datetime: {random_datetime}")
        return random_datetime
    except Exception as e:
        logging.error(f"Error generating random datetime: {e}")
        return None



def generate_random_ticket_number():
    try:
        logging.debug("Generating random ticket number.")
        return random.randint(1000, 9999)
    except Exception as e:
        logging.error(f"Error generating random ticket number: {e}")
        return None
    
def generate_ticket():
    # Ticket class or function to generate a ticket
    logging.debug("Starting ticket generation.")
    try:
        ticket_number = generate_random_ticket_number()
        # Ensure all fields are generated correctly
        contact = get_random_contact()
        if not contact:
            logging.warning("No contact generated. Setting default.")
            contact = "Unknown Contact"

        customer = get_random_customer()
        if not customer:
            logging.warning("No customer generated. Setting default.")
            customer = "Unknown Customer"

        description = get_random_description()
        if not description:
            logging.warning("No description generated. Setting default.")
            description = "No description provided."

        issue_type = get_random_issue_type()
        if not issue_type:
            logging.warning("No issue type generated. Setting default.")
            issue_type = "General Inquiry"

        priority = get_random_priority()
        if not priority:
            logging.warning("No priority generated. Setting default.")
            priority = "Low"

        status = get_random_status()
        if not status:
            logging.warning("No status generated. Setting default.")
            status = "Open"

        subject = get_random_subject()
        if not subject:
            logging.warning("No subject generated. Setting default.")
            subject = "General Issue"

        tech = get_random_tech()
        if not tech:
            logging.warning("No tech generated. Setting default.")
            tech = "Unassigned"

        start_time = generate_random_datetime()
        end_time = generate_random_datetime()

        # Ensure the end time is after the start time
        if end_time < start_time:
            logging.warning(f"End time {end_time} is before start time {start_time}. Adjusting end time.")
            end_time = start_time + timedelta(hours=1)

        ticket = {
            "Ticket Number": ticket_number,
            "Customer": customer,
            "Contact": contact,
            "Subject": subject,
            "Status": status,         
            "Description": description,
            "Issue Type": issue_type,
            "Assigned Tech": tech,
            "Priority": priority,                        
            "Start Time": start_time,
            "End Time": end_time
        }

        logging.info(f"Ticket generated successfully: {ticket}")
        return ticket
    except Exception as e:
        logging.error(f"Error generating ticket: {e}")
        return None

